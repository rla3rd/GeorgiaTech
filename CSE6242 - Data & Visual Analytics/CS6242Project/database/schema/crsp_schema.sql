--
-- PostgreSQL database dump
--

-- Dumped from database version 11.5
-- Dumped by pg_dump version 11.5 (Ubuntu 11.5-1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: alpha_metrics_annualized(integer, timestamp without time zone, integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.alpha_metrics_annualized(p_permno integer, p_date timestamp without time zone, p_days integer DEFAULT 252) RETURNS double precision
    LANGUAGE sql IMMUTABLE
    AS $_$

    select q.cumret - m.beta * q.cumret_sp500 as alpha
    from (
        select m.permno, 
            m.date,
            m.ret,
            ((cumprod(1+m.ret) over (partition by m.permno order by m.date)) -1) as cumret,
            ((cumprod(1+m.ret_sp500) over (partition by m.permno order by m.date)) -1) as cumret_sp500
            
        from market_tradedays ed 
        inner join market_tradedays bd 
            on bd.idxdate = ed.idxdate - $3
        inner join metrics m 
            on m.date > bd.date 
                and m.date <= ed.date
        where ed.date = $2
            and m.permno = $1
        group by m.permno,
            m.date,
            m.beta,
            m.ret,
            m.ret_sp500
        order by m.permno
        offset $3 - 1
    ) q
    inner join metrics m 
        on m.permno = q.permno 
            and m.date = q.date;
$_$;


ALTER FUNCTION public.alpha_metrics_annualized(p_permno integer, p_date timestamp without time zone, p_days integer) OWNER TO crsp;

--
-- Name: array_mean(double precision[]); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.array_mean(p_array double precision[]) RETURNS double precision
    LANGUAGE sql IMMUTABLE
    AS $_$
    select avg(c1)
    from 
    unnest($1) as c1;
$_$;


ALTER FUNCTION public.array_mean(p_array double precision[]) OWNER TO crsp;

--
-- Name: array_mean2(double precision[]); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.array_mean2(p_array double precision[]) RETURNS double precision
    LANGUAGE plpgsql IMMUTABLE
    AS $$
declare
   v_sum double precision;
   v_length integer;
begin
    v_length = array_upper(p_array, 1);
    FOR i IN 1 .. v_length
    loop
        v_sum = v_sum + p_array[i];
    end loop;
    return v_sum/v_length;
end
$$;


ALTER FUNCTION public.array_mean2(p_array double precision[]) OWNER TO crsp;

--
-- Name: array_stddev(double precision[]); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.array_stddev(p_array double precision[]) RETURNS double precision
    LANGUAGE sql IMMUTABLE
    AS $_$
    select stddev(c1)
    from 
    unnest($1) as c1;
$_$;


ALTER FUNCTION public.array_stddev(p_array double precision[]) OWNER TO crsp;

--
-- Name: autoclose_positions(integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.autoclose_positions(p_userid integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare
    v_rec record;
begin
    -- this function auto closes position that are affected by a corporate
    -- action or bankruptcy
    for v_rec in 
    
        select h.user_id,
            h.permno, 
            h.date, 
            h.value, 
            h.value / dsf.prc / dsf.cfacpr as shares,
            dsf.prc / dsf.cfacpr as price
        from (
            select h.permno, max(date) as date
            from holdings h
            group by h.permno
            having max(h.date) < '2018-12-31' 
        ) q
        inner join holdings h 
            on h.permno = q.permno
                and h.date = q.date
                and h.value > 0
        inner join dsf 
            on dsf.permno = h.permno
                and dsf.date = h.date
        left join transactions t
            on h.user_id = t.user_id
                and t.permno = h.permno
                and t.date = h.date
                and t.code = 'S'
        where t.permno is null 
            and h.user_id = p_userid
            
    loop
    
        insert into transactions(
            user_id,
            date,
            code,
            permno,
            value,
            shares,
            price,
            auto)
        values(
            v_rec.user_id,
            v_rec.date,
            'S',
            v_rec.permno,
            v_rec.value,
            v_rec.shares,
            v_rec.price,
            true)
        on conflict (
            user_id,
            date,
            permno,
            code)
        do nothing;
        
        insert into transactions(
            user_id,
            date,
            code,
            permno,
            value,
            shares,
            price,
            auto)
        values(
            v_rec.user_id,
            v_rec.date,
            'B',
            0,
            v_rec.value,
            v_rec.value,
           1,
           true)
        on conflict (
            user_id,
            date,
            permno,
            code)
        do nothing;
    end loop;
end
$$;


ALTER FUNCTION public.autoclose_positions(p_userid integer) OWNER TO crsp;

--
-- Name: beta_dsf_monthly(integer, timestamp without time zone); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.beta_dsf_monthly(p_permno integer, p_date timestamp without time zone) RETURNS double precision
    LANGUAGE sql IMMUTABLE
    AS $_$

    select covar_samp(q.ret, q.ret_sp500) / var_samp(q.ret_sp500) as beta
    from (
        select 
        (
            dsf.prc / dsf.cfacpr + getdividend(dsf.permno::integer, dsf.date, 21)
            - coalesce(lag(dsf.prc / dsf.cfacpr + getdividend(dsf.permno::integer, dsf.date, 21), 1)  over (partition by dsf.permno order by dsf.date), dsf.prc / dsf.cfacpr)
        )
        / coalesce(lag(dsf.prc / dsf.cfacpr + getdividend(dsf.permno::integer, dsf.date, 21), 1)  over (partition by dsf.permno order by dsf.date), dsf.prc / dsf.cfacpr) as ret,
        (
            dsi.spindx - lag(dsi.spindx, 1) over (order by dsi.date)
        ) / lag(dsi.spindx, 1) over (order by dsi.date) as ret_sp500
        
        
        from market_tradedays ed
        inner join market_tradedays bd 
        on (
            bd.idxdate=ed.idxdate - 252 - 504
            or bd.idxdate=ed.idxdate - 231 - 504
            or bd.idxdate=ed.idxdate - 210 - 504
            or bd.idxdate=ed.idxdate - 189 - 504
            or bd.idxdate=ed.idxdate - 168 - 504
            or bd.idxdate=ed.idxdate - 147 - 504
            or bd.idxdate=ed.idxdate - 126 - 504
            or bd.idxdate=ed.idxdate - 105 - 504
            or bd.idxdate=ed.idxdate - 84 - 504
            or bd.idxdate=ed.idxdate - 63 - 504
            or bd.idxdate=ed.idxdate - 42 - 504
            or bd.idxdate=ed.idxdate - 21 - 504
            
            or bd.idxdate=ed.idxdate - 504
            or bd.idxdate=ed.idxdate - 231 - 252
            or bd.idxdate=ed.idxdate - 210 - 252
            or bd.idxdate=ed.idxdate - 189 - 252
            or bd.idxdate=ed.idxdate - 168 - 252
            or bd.idxdate=ed.idxdate - 147 - 252
            or bd.idxdate=ed.idxdate - 126 - 252
            or bd.idxdate=ed.idxdate - 105 - 252
            or bd.idxdate=ed.idxdate - 84 - 252
            or bd.idxdate=ed.idxdate - 63 - 252
            or bd.idxdate=ed.idxdate - 42 - 252
            or bd.idxdate=ed.idxdate - 21 - 252
            
            or bd.idxdate=ed.idxdate - 252
            or bd.idxdate=ed.idxdate - 231
            or bd.idxdate=ed.idxdate - 210
            or bd.idxdate=ed.idxdate - 189
            or bd.idxdate=ed.idxdate - 168
            or bd.idxdate=ed.idxdate - 147
            or bd.idxdate=ed.idxdate - 126
            or bd.idxdate=ed.idxdate - 105
            or bd.idxdate=ed.idxdate - 84
            or bd.idxdate=ed.idxdate - 63
            or bd.idxdate=ed.idxdate - 42
            or bd.idxdate=ed.idxdate - 21
            or bd.idxdate=ed.idxdate)
            
        inner join dsf on dsf.date = bd.date
        inner join dsi on dsf.date = dsi.date
        where dsf.permno = $1
        and ed.date = $2
        order by bd.date
    ) q
    where q.ret_sp500 is not null;

$_$;


ALTER FUNCTION public.beta_dsf_monthly(p_permno integer, p_date timestamp without time zone) OWNER TO crsp;

--
-- Name: beta_metrics_daily(integer, timestamp without time zone); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.beta_metrics_daily(p_permno integer, p_date timestamp without time zone) RETURNS double precision
    LANGUAGE sql IMMUTABLE
    AS $_$

    select covar_samp(q.ret, q.ret_sp500) / var_samp(q.ret_sp500) as beta
    from (
        select 
            m.ret,
            m.ret_sp500
        from market_tradedays ed
        inner join market_tradedays bd 
        on bd.idxdate=ed.idxdate - 756
        inner join metrics m on m.date between bd.date and ed.date
        where m.permno = $1
        and ed.date = $2
        order by bd.date
        offset 1
    ) q;
$_$;


ALTER FUNCTION public.beta_metrics_daily(p_permno integer, p_date timestamp without time zone) OWNER TO crsp;

--
-- Name: delete_txns(integer, integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.delete_txns(p_userid integer, p_idx integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare
    v_rec record;
    v_contra record;
    v_value double precision;
begin
    select *
    into v_rec
    from transactions
    where id = p_idx;
    
    select sum(value)
    into v_value
    from transactions
    where user_id = p_userid
        and code = v_rec.code
        and date = v_rec.date
        and id >= p_idx;
    
    -- contra is always not null on a buy
    -- so we will always be reducing or removing a sale
    if v_rec.contra is not null then
    
        select *
        into v_contra
        from transactions
        where id = v_rec.contra;
    
        if  v_contra.value > v_value then
        
            update transactions
            set value = v_contra.value - v_value
            where id = v_contra.id;
            
        else
        
            delete from transactions
            where id = v_contra.id;
                
        end if;
    end if;
    
    delete from transactions
    where user_id = p_userid
        and id >= p_idx;
                
   return;
   end
  $$;


ALTER FUNCTION public.delete_txns(p_userid integer, p_idx integer) OWNER TO crsp;

--
-- Name: getdividend(integer, timestamp without time zone, integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.getdividend(p_permno integer, p_date timestamp without time zone, p_tradedays integer) RETURNS double precision
    LANGUAGE plpgsql IMMUTABLE
    AS $$
declare
    v_div double precision;
begin

    select d.divamt
    into v_div
    from market_tradedays ed
    inner join market_tradedays bd on bd.idxdate = ed.idxdate - p_tradedays
    inner join dsedist d on d.exdt between bd.date and ed.date
    where permno = p_permno
        and ed.date = p_date;
    
    if not found then
    
        v_div := 0;
        
    end if;
    return v_div;
end
$$;


ALTER FUNCTION public.getdividend(p_permno integer, p_date timestamp without time zone, p_tradedays integer) OWNER TO crsp;

--
-- Name: getidxdate(timestamp without time zone); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.getidxdate(timestamp without time zone) RETURNS integer
    LANGUAGE sql IMMUTABLE
    AS $_$
	select idxdate from market_tradedays where date=getmarketdate($1);
$_$;


ALTER FUNCTION public.getidxdate(timestamp without time zone) OWNER TO crsp;

--
-- Name: getmarketdate(timestamp without time zone); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.getmarketdate(p_date timestamp without time zone) RETURNS timestamp without time zone
    LANGUAGE sql IMMUTABLE PARALLEL SAFE
    AS $_$
	select date from market_tradedays
		where date <= $1
		order by date desc
		limit 1;
$_$;


ALTER FUNCTION public.getmarketdate(p_date timestamp without time zone) OWNER TO crsp;

--
-- Name: getmarketidxdate(integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.getmarketidxdate(integer) RETURNS timestamp without time zone
    LANGUAGE sql IMMUTABLE
    AS $_$
        select date from market_tradedays
                where idxdate <= $1
                order by idxdate desc
                limit 1;
$_$;


ALTER FUNCTION public.getmarketidxdate(integer) OWNER TO crsp;

--
-- Name: insert_metrics_daily_ret(integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.insert_metrics_daily_ret(p_permno integer DEFAULT NULL::integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare
    v_rec record;
begin
    delete from metrics 
    where case when permno is not null then 
            permno = p_permno 
        else 
            1 = 1 
    end;
        
    insert into metrics(permno, date, ret, ret_sp500)
    select 
        dsf.permno,
        dsf.date,
        (
            dsf.prc / dsf.cfacshr + coalesce(d.divamt, 0) 
            - coalesce(lag(dsf.prc / dsf.cfacshr + coalesce(d.divamt, 0), 1)  over (partition by dsf.permno order by dsf.date), dsf.prc / dsf.cfacshr)
        )
        / coalesce(lag(dsf.prc / dsf.cfacshr + coalesce(d.divamt, 0), 1)  over (partition by dsf.permno order by dsf.date), dsf.prc / dsf.cfacshr) as ret,
        coalesce((
                dsi.spindx - lag(dsi.spindx, 1) over (partition by dsf.permno  order by dsf.date)
            ) / lag(dsi.spindx, 1) over (partition by dsf.permno  order by dsf.date), 0) as ret_sp500
    from dsf 
    inner join market_tradedays nd
        on nd.date = dsf.date
    inner join market_tradedays md
        on nd.idxdate - 1 = md.idxdate
    left join dsf nxt 
        on nxt.permno = dsf.permno
            and nxt.date = nd.date
    left join  (
        select d.permno,
            d.exdt,
            sum(d.divamt) as divamt
        from dsedist d 
        group by d.permno, d.exdt
    ) d on d.permno = dsf.permno
        and d.exdt = dsf.date
    inner join dsi on 
        dsf.date = dsi.date
    where nxt.date is not null 
        and dsf.date between '2003-12-31' and '2018-12-31'
    and case when p_permno is not null then
            dsf.permno = p_permno
        else
            1 = 1
        end
    group by
        dsf.permno, 
        dsf.date, 
        dsf.prc, 
        dsf.cfacshr, 
        d.divamt,
        dsi.spindx
    order by dsf.permno, dsf.date;
end
$$;


ALTER FUNCTION public.insert_metrics_daily_ret(p_permno integer) OWNER TO crsp;

--
-- Name: permnofromticker(text, timestamp without time zone); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.permnofromticker(p_ticker text, p_date timestamp without time zone DEFAULT '2018-12-31 00:00:00'::timestamp without time zone) RETURNS integer
    LANGUAGE sql STABLE
    AS $$
    select permno::integer 
    from stocknames 
    where ticker = p_ticker 
        and p_date <@ tsrange(st_date, end_date, '[]') 
    group by permno 
    order by permno 
    limit 1;
$$;


ALTER FUNCTION public.permnofromticker(p_ticker text, p_date timestamp without time zone) OWNER TO crsp;

--
-- Name: refreshportfolio(integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.refreshportfolio(p_userid integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare
    v_rec record;
begin
    -- reconstruct the portfolio after updateholdings is run
    delete from portfolio where user_id = p_userid;

    insert into portfolio(
        user_id, 
        date, 
        value, 
        ret, 
        cumret,
        alpha,
        beta,
        sharpe,
        sortino,
        volatility
    )
     select p.user_id,
            p.date,
            p.value, 
            coalesce(p.ret, 0) as ret,
            coalesce(p.cumret, 0) as cumret,
            coalesce(p.alpha, 0) as alpha,
            p.beta,
            case when array_stddev(p.daily_returns) <> 0 then
                    array_mean(p.daily_returns) / array_stddev(p.daily_returns) * sqrt(252)
                else
                    0
                end as sharpe,
            case when  array_stddev(p.neg_daily_returns) <> 0 then
                    array_mean(p.daily_returns) / array_stddev(p.neg_daily_returns) * sqrt(252)
                else
                    0
                end as sortino,
            coalesce(array_stddev(p.daily_returns) * sqrt(252), 0) as volatility
    from (
        select p.user_id,
            p.date,
            p.value, 
            p.ret,
            p.cumret,
            sum(h.value / p.value * m.beta) as beta,
            p.cumret - sum(h.value / p.value * m.beta) * (cumprod(((1)::double precision +
                CASE
                    WHEN (p.ret = (0)::double precision) THEN (0)::double precision
                    ELSE dsi.sprtrn
                END)) OVER (PARTITION BY p.user_id ORDER BY p.date) - (1)::double precision) as alpha,
            array_accum(p.ret) over (PARTITION BY p.user_id ORDER BY p.date) as daily_returns,
            array_accum(case when p.ret < 0 then p.ret end) over (PARTITION BY p.user_id ORDER BY p.date) as neg_daily_returns
        
        from (
            select q4.user_id,
                q4.date,
                q4.value,
                q4.ret,
                ((cumprod(1+q4.ret) over (partition by q4.user_id order by q4.date)) -1) as cumret
            from (
                select q3.user_id, 
                    q3.date, 
                    value, 
                    last_value,
                    (value - last_value)/last_value as ret
                from (
                    select q2.user_id, 
                        q2.date, 
                        q2.value,
                        lag(q2.value, 1) over (partition by q2.user_id order by q2.date) as last_value
                    from (
                        select q.user_id, 
                            q.date, 
                            sum(value) as value
                        from (
                            select h.user_id,
                                h.permno,
                                h.date,
                                h.value
                            from holdings h
                            where user_id = p_userid
                        ) q
                        group by q.user_id, q.date
                        order by q.user_id, q.date
                    ) q2
                    order by q2.user_id, q2.date
                ) q3
            ) q4
        ) p
        inner join holdings h on p.user_id = h.user_id and p.date = h.date
        inner join metrics m on m.permno = h.permno 
            and m.date = h.date
        inner join dsi ON p.date = dsi.date
        group by p.user_id,
            p.date,
            p.value, 
            p.ret,
            p.cumret,
            dsi.sprtrn
        order by p.user_id, p.date
    ) p
    order by p.user_id, p.date
    on conflict (user_id, date)
    do update set value = EXCLUDED.value, 
        ret = EXCLUDED.ret, 
        cumret = EXCLUDED.cumret,
        alpha = EXCLUDED.alpha,
        beta = EXCLUDED.beta,
        sharpe = EXCLUDED.sharpe,
        sortino = EXCLUDED.sortino,
        volatility = EXCLUDED.volatility;
end
$$;


ALTER FUNCTION public.refreshportfolio(p_userid integer) OWNER TO crsp;

--
-- Name: sharpe_metrics_annualized(integer, timestamp without time zone, integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.sharpe_metrics_annualized(p_permno integer, p_date timestamp without time zone, p_days integer DEFAULT 252) RETURNS double precision
    LANGUAGE sql IMMUTABLE
    AS $_$

    select case when min(q.ret) <> max(q.ret) then avg(q.ret) / stddev(q.ret) * sqrt($3) end as sharpe
    from (
        select m.permno,
            ed.date,
            m.ret
        from market_tradedays ed
        inner join market_tradedays bd 
        on bd.idxdate=ed.idxdate - $3
        inner join metrics m 
            on m.date between bd.date 
                and ed.date
        where m.permno = $1
            and ed.date = $2
        order by bd.date
        offset 1
    ) q;

$_$;


ALTER FUNCTION public.sharpe_metrics_annualized(p_permno integer, p_date timestamp without time zone, p_days integer) OWNER TO crsp;

--
-- Name: sortino_metrics_annualized(integer, timestamp without time zone, integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.sortino_metrics_annualized(p_permno integer, p_date timestamp without time zone, p_days integer DEFAULT 252) RETURNS double precision
    LANGUAGE sql IMMUTABLE
    AS $_$

    select case when min(q.ret) <> max(q.ret) then avg(q.ret) / stddev(case when q.ret < 0 then q.ret end) * sqrt($3) end as sortino
    from (
        select m.permno,
            ed.date,
            m.ret
        from market_tradedays ed
        inner join market_tradedays bd 
        on bd.idxdate=ed.idxdate - $3
        inner join metrics m 
            on m.date between bd.date 
                and ed.date
        where m.permno = $1
            and ed.date = $2
        order by bd.date
        offset 1
    ) q;

$_$;


ALTER FUNCTION public.sortino_metrics_annualized(p_permno integer, p_date timestamp without time zone, p_days integer) OWNER TO crsp;

--
-- Name: tickerfrompermno(integer, timestamp without time zone); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.tickerfrompermno(p_permno integer, p_date timestamp without time zone DEFAULT '2018-12-31 00:00:00'::timestamp without time zone) RETURNS text
    LANGUAGE sql STABLE
    AS $_$
    select ticker 
    from stocknames
    where permno = $1
        and $2 <@ tsrange(namedt, nameenddt, '[]')
        and $2 <@ tsrange(st_date, end_date, '[]');
$_$;


ALTER FUNCTION public.tickerfrompermno(p_permno integer, p_date timestamp without time zone) OWNER TO crsp;

--
-- Name: transactions_manage_cash(); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.transactions_manage_cash() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
declare
    v_cash double precision;
    v_cashcode text;
    v_value double precision;
begin
    if TG_OP = 'INSERT' then
    
        select sum(case when code ='B' then value else -value end) as value
        into v_cash
        from transactions
        where user_id = NEW.user_id
            and date < NEW.date
            and permno = 0;
    
        if NEW.permno <> 0 then
        
            -- for buys we need to use cash on hand before having a portfolio contribution
            if NEW.code = 'B' then 
                -- we already have cash so well add to it
                if v_cash > 0 then 
                
                    if v_cash > NEW.value then
                    
                        v_cash := NEW.value;
                        
                    end if;
                
                    insert into transactions(user_id, date, code, permno, value)
                    values(NEW.user_id, NEW.date, 'S', 0, v_cash);
            
                end if;
                -- no cash as all, insert cash and then draw it down
                if v_cash is null then
                
                    insert into transactions(user_id, date, code, permno, value)
                    values(NEW.user_id, NEW.date, 'B', 0, NEW.value);
                    
                    insert into transactions(user_id, date, code, permno, value)
                    values(NEW.user_id, NEW.date, 'S', 0, NEW.value);
                    
                end if;
           else
                -- for sells we just need to sweep into cash
                select value
                into v_value
                from holdings
                where user_id = NEW.user_id
                    and permno = NEW.permno
                    and date = getmarketdate(NEW.date);
                    
                if found then
                
                    if v_value <= NEW.value then
                        NEW.value = v_value;
                    end if;
                end if;
                    
                insert into transactions(user_id, date, code, permno, value)
                values(NEW.user_id, NEW.date, 'B', 0, NEW.value);
            end if;
        end if;
        return NEW;
    end if;
    if TG_OP = 'DELETE' then
    
        if OLD.permno <> 0 then
    
            if OLD.code = 'B' then
            
                v_cashcode = 'S';
                
            else
            
                v_cashcode = 'B';
                
            end if;
            
            select value 
            into v_cash
            from transactions 
            where user_id = OLD.user_id
                and date = OLD.date
                and permno = 0
                and code = v_cashcode;
                
            if v_cash <= OLD.value then
        
                -- we just need to reverse the cash positions from the delete back out
                delete from transactions
                where user_id = OLD.user_id
                    and date = OLD.date
                    and permno = 0
                   and code = v_cashcode;
                   
            else
                -- we need to reduce the amount of cash by the delete
                v_cash:= v_cash - OLD.value;
                
                update transactions
                set value = v_cash
                where user_id = OLD.user_id
                    and date = OLD.date
                    and permno = 0
                    and code = v_cashcode;
            end if;
        end if;
        return OLD;
    end if;
end
$$;


ALTER FUNCTION public.transactions_manage_cash() OWNER TO crsp;

--
-- Name: update_metrics(integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.update_metrics(p_permno integer DEFAULT NULL::integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare
    v_rec record;
begin
    delete from metrics;
        
    insert into metrics(permno, date, ret, beta)
    select 
        dsf.permno,
        dsf.date,
        (
            dsf.prc / dsf.cfacshr + coalesce(d.divamt, 0) 
            - coalesce(lag(dsf.prc / dsf.cfacshr + coalesce(d.divamt, 0), 1)  over (partition by dsf.permno order by dsf.date), dsf.prc / dsf.cfacshr)
        )
        / coalesce(lag(dsf.prc / dsf.cfacshr + coalesce(d.divamt, 0), 1)  over (partition by dsf.permno order by dsf.date), dsf.prc / dsf.cfacshr) as ret,
        beta_dsf_monthly(dsf.permno::integer, dsf.date) as beta
    from dsf 
    inner join market_tradedays nd
        on nd.date = dsf.date
    inner join market_tradedays md
        on nd.idxdate - 1 = md.idxdate
    left join dsf nxt 
        on nxt.permno = dsf.permno
            and nxt.date = nd.date
    left join  (
        select d.permno,
            d.exdt,
            d.divamt
        from dsedist d 
        group by d.permno, d.exdt, d.divamt
    ) d on d.permno = dsf.permno
        and d.exdt = dsf.date
    where nxt.date is not null 
        and dsf.date between '2007-01-03' and '2018-12-31'
    and case when p_permno is not null then
            dsf.permno = p_permno
        else
            1 = 1
        end
    group by
        dsf.permno, 
        dsf.date, 
        dsf.prc, 
        dsf.cfacshr, 
        d.divamt
    order by dsf.permno, dsf.date;
end
$$;


ALTER FUNCTION public.update_metrics(p_permno integer) OWNER TO crsp;

--
-- Name: update_metrics_alpha(integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.update_metrics_alpha(p_permno integer) RETURNS void
    LANGUAGE sql
    AS $_$

    update metrics
    set alpha = alpha_metrics_annualized(permno::integer, date)
    where case when permno is not null then
            permno = $1
        else
            1 = 1
        end;
   
$_$;


ALTER FUNCTION public.update_metrics_alpha(p_permno integer) OWNER TO crsp;

--
-- Name: update_metrics_beta(integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.update_metrics_beta(p_permno integer DEFAULT NULL::integer) RETURNS void
    LANGUAGE sql
    AS $$

    update metrics
    set beta = beta_metrics_daily(permno, date)
    where case when p_permno is not null then
            permno = p_permno
        else
            1 = 1
        end
        and date between '2007-01-03' and '2018-12-31';
$$;


ALTER FUNCTION public.update_metrics_beta(p_permno integer) OWNER TO crsp;

--
-- Name: update_metrics_daily_ret(integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.update_metrics_daily_ret(p_permno integer DEFAULT NULL::integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare
    v_rec record;
begin
    update metrics m
        set ret = upd.ret,
        ret_sp500 = upd.ret_sp500
    from (
        select 
            dsf.permno,
            dsf.date,
            (
                dsf.prc / dsf.cfacshr + coalesce(d.divamt, 0) 
                - coalesce(lag(dsf.prc / dsf.cfacshr + coalesce(d.divamt, 0), 1)  over (partition by dsf.permno order by dsf.date), dsf.prc / dsf.cfacshr)
            )
            / coalesce(lag(dsf.prc / dsf.cfacshr + coalesce(d.divamt, 0), 1)  over (partition by dsf.permno order by dsf.date), dsf.prc / dsf.cfacshr) as ret,
            coalesce((
                    dsi.spindx - lag(dsi.spindx, 1) over (partition by dsf.permno  order by dsf.date)
                ) / lag(dsi.spindx, 1) over (partition by dsf.permno  order by dsf.date), 0) as ret_sp500
        from dsf 
        inner join market_tradedays nd
            on nd.date = dsf.date
        inner join market_tradedays md
            on nd.idxdate - 1 = md.idxdate
        left join dsf nxt 
            on nxt.permno = dsf.permno
                and nxt.date = nd.date
        left join  (
            select d.permno,
                d.exdt,
                sum(d.divamt) as divamt
            from dsedist d 
            group by d.permno, d.exdt
        ) d on d.permno = dsf.permno
            and d.exdt = dsf.date
        inner join dsi on 
            dsf.date = dsi.date
        where nxt.date is not null 
            and dsf.date between '2003-12-31' and '2018-12-31'
        and case when p_permno is not null then
                dsf.permno = p_permno
            else
                1 = 1
            end
        group by
            dsf.permno, 
            dsf.date, 
            dsf.prc, 
            dsf.cfacshr, 
            d.divamt,
            dsi.spindx
        order by dsf.permno, dsf.date
    ) upd 
    where upd.permno = m.permno 
        and upd.date = m.date;
end
$$;


ALTER FUNCTION public.update_metrics_daily_ret(p_permno integer) OWNER TO crsp;

--
-- Name: update_metrics_sharpe(integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.update_metrics_sharpe(p_permno integer DEFAULT NULL::integer) RETURNS void
    LANGUAGE sql
    AS $$

    update metrics
    set sharpe = sharpe_metrics_annualized(permno, date)
    where case when p_permno is not null then
            permno = p_permno
        else
            1 = 1
        end
        and date between '2007-01-03' and '2018-12-31';
$$;


ALTER FUNCTION public.update_metrics_sharpe(p_permno integer) OWNER TO crsp;

--
-- Name: update_metrics_sortino(integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.update_metrics_sortino(p_permno integer DEFAULT NULL::integer) RETURNS void
    LANGUAGE sql
    AS $$

    update metrics
    set sortino = sortino_metrics_annualized(permno, date)
    where case when p_permno is not null then
            permno = p_permno
        else
            1 = 1
        end
        and date between '2007-01-03' and '2018-12-31';
$$;


ALTER FUNCTION public.update_metrics_sortino(p_permno integer) OWNER TO crsp;

--
-- Name: update_metrics_volatility(integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.update_metrics_volatility(p_permno integer DEFAULT NULL::integer) RETURNS void
    LANGUAGE sql
    AS $$

    update metrics
    set volatility = volatility_metrics_annualized(permno, date)
    where case when p_permno is not null then
            permno = p_permno
        else
            1 = 1
        end
        and date between '2007-01-03' and '2018-12-31';
$$;


ALTER FUNCTION public.update_metrics_volatility(p_permno integer) OWNER TO crsp;

--
-- Name: updateholdings(integer, integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.updateholdings(p_userid integer, p_permno integer DEFAULT NULL::integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare
    v_last record;
    v_rec record;
    v_n integer;
    v_xsum double precision;
    v_x2sum double precision;
    v_mean double precision;
    v_var double precision;
    v_std double precision;
    v_negn integer;
    v_negxsum double precision;
    v_negx2sum double precision;
    v_negmean double precision;
    v_negvar double precision;
    v_negstd double precision;
    v_sharpe double precision;
    v_sortino double precision;
    v_volatility double precision;
begin
    -- update holdings function that dynamically calculates statistics as each row is calculated
    -- based on my earlier c++ careeer work @ https://github.com/rla3rd/RollingStats
    delete from holdings 
    where user_id = p_userid
        and permno in (
            select h.permno 
            from holdings h
            left join transactions t 
                on t.user_id = h.user_id
                    and t.permno = h.permno
                    and t.code = 'B'
            where t.user_id is null
                and h.user_id = p_userid
            group by h.permno
        );

    for v_rec in 
    
        select q.user_id,
            q.permno,
            q.date,
            q.prc,
            round(q.value::numeric, 2)::double precision as value,
            q.ret,
            q.cumret,
            q.cumret - (q.beta * q.cumret_sp500) as alpha,
            q.beta
        from (
            select q.user_id,
                q.permno,
                q.date,
                q.prc,
                q.divamt,
                q.value,
                q.ret,
                q.beta,
                (cumprod(1+q.ret) over (partition by q.user_id, q.permno order by q.date) -1) as cumret,
                (cumprod(1+q.ret_sp500) over (partition by q.user_id, q.permno order by q.date) -1) as cumret_sp500
            from (
               select t.user_id,
                    t.permno,
                    dsf.date,
                    dsf.prc,
                    coalesce(d.divamt, 0) as divamt,
                    sum(case when code = 'B' then shares else -shares end) as shares,
                    greatest(sum(case when code = 'B' then shares else -shares end) * dsf.prc / dsf.cfacpr, 0) as value,
                    case when sum(case when code = 'B' then shares else -shares end) * dsf.prc / dsf.cfacpr > 0 then 
                            (
                                dsf.prc / dsf.cfacpr + coalesce(d.divamt, 0) 
                                - coalesce(lag(dsf.prc / dsf.cfacpr + coalesce(d.divamt, 0), 1)  over (partition by t.user_id, t.permno order by dsf.date), dsf.prc / dsf.cfacpr)
                            )
                            / coalesce(lag(dsf.prc / dsf.cfacpr + coalesce(d.divamt, 0), 1)  over (partition by t.user_id, t.permno order by dsf.date), dsf.prc / dsf.cfacpr) 
                        else
                            0
                        end as ret,
                    dsi.sprtrn as ret_sp500,
                    m.beta
                from transactions t
                inner join dsf 
                    on dsf.permno = t.permno
                        and dsf.date >= t.date
                inner join market_tradedays nd
                    on nd.date = dsf.date
                inner join market_tradedays md
                    on nd.idxdate - 1 = md.idxdate
                left join dsf nxt 
                    on nxt.permno = t.permno
                        and nxt.date = nd.date
                left join dsi ON dsi.date = nd.date
                left join metrics m on m.permno = t.permno 
                    and m.date = nd.date
                left join  (
                    select d.permno,
                        d.exdt,
                        d.divamt
                    from dsedist d 
                    group by d.permno, d.exdt, d.divamt
                ) d on d.permno = dsf.permno
                    and d.exdt = dsf.date
                where nxt.date is not null 
                    and t.user_id = p_userid
                    and case when p_permno is not null then
                            t.permno = p_permno
                        else
                            1 = 1
                        end
                group by t.user_id, 
                    t.permno, 
                    dsf.date, 
                    dsf.prc, 
                    dsf.cfacpr, 
                    d.divamt,
                    m.beta,
                    dsi.sprtrn
                order by dsf.date
            ) q
            group by q.user_id, 
                q.permno, 
                q.date, 
                q.prc, 
                q.divamt, 
                q.value,
                q.ret,
                q.ret_sp500,
                q.beta
        )q
        
    loop
    
        if v_last is null then
        
            v_n := 0;
            v_xsum := 0;
            v_x2sum := 0;
            v_negn := 0;
            v_negxsum := 0;
            v_negx2sum := 0;
            
        else
        
            if v_last.permno is distinct from v_rec.permno then
            
                v_n := 0;
                v_xsum := 0;
                v_x2sum := 0;
                v_negn := 0;
                v_negxsum := 0;
                v_negx2sum := 0;
            
            end if;
        end if;
            
        v_n := v_n + 1;
        v_xsum := v_xsum + v_rec.ret;
        v_x2sum := v_x2sum + pow(v_rec.ret, 2);
        v_mean := v_xsum / v_n;
        v_var := (v_x2sum - pow(v_xsum, 2) / v_n) / v_n;
        v_std = sqrt(v_var);
        
        if v_rec.ret < 0 then
        
            v_negn := v_negn + 1;
            v_negxsum:= v_negxsum + v_rec.ret;
            v_negx2sum := v_negx2sum + pow(v_rec.ret, 2);
            v_negmean = v_negxsum / v_negn;
            v_negvar := ( v_negx2sum - pow(v_negxsum, 2) / v_negn) / v_negn;
            v_negstd := sqrt(v_negvar);
            
        end if;
        
        if v_std <> 0 then 
            v_sharpe := v_mean / v_std * sqrt(252);
            v_volatility := v_std * sqrt(252);
        else
            v_sharpe := 0;
            v_volatility := 0;
        end if;
        
        if v_negstd <> 0 then 
            v_sortino := v_mean / v_negstd * sqrt(252);
        else
            v_sortino := 0;
        end if;
    
        insert into holdings (
            user_id, 
            permno,
            date,
            price,
            value,
            ret,
            cumret,
            alpha,
            beta,
            sharpe,
            sortino,
            volatility
        ) 
        values(
            v_rec.user_id, 
            v_rec.permno,
            v_rec.date,
            v_rec.prc,
            v_rec.value,
            v_rec.ret,
            v_rec.cumret,
            v_rec.alpha,
            v_rec.beta,
            v_sharpe,
            v_sortino,
            v_volatility
        )
        on conflict(user_id, permno, date)
        do update set price = EXCLUDED.price,
            value = EXCLUDED.value,
            ret = EXCLUDED.ret,
            cumret = EXCLUDED.cumret;
            
        v_last = v_rec;
    end loop;
end     
$$;


ALTER FUNCTION public.updateholdings(p_userid integer, p_permno integer) OWNER TO crsp;

--
-- Name: updateholdings_old(integer, integer); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.updateholdings_old(p_userid integer, p_permno integer DEFAULT NULL::integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
declare
begin
    -- original update holdings function that runs too slow, the new one
    -- is optimized so not every row needs a complete set of data
    delete from holdings 
    where user_id = p_userid
        and permno in (
            select h.permno 
            from holdings h
            left join transactions t 
                on t.permno = h.permno
                    and t.code = 'B'
            where t.user_id is null
                and h.user_id = p_userid
            group by h.permno
        );

    insert into holdings (
        user_id, 
        permno,
        date,
        price,
        value,
        ret,
        cumret,
        alpha,
        beta,
        sharpe,
        sortino,
        volatility
    ) 
    select q.user_id,
        q.permno,
        q.date,
        q.prc,
        round(q.value::numeric, 2)::double precision as value,
        q.ret,
        q.cumret,
        q.cumret - (q.beta * q.cumret_sp500) as alpha,
        q.beta,
        case when array_stddev(q.daily_returns) <> 0 then
                array_mean(q.daily_returns) / array_stddev(q.daily_returns) * sqrt(252)
            else
                0
            end as sharpe,
        case when  array_stddev(q.neg_daily_returns) <> 0 then
                array_mean(q.daily_returns) / array_stddev(q.neg_daily_returns) * sqrt(252)
            else
                0
            end as sortino,
        coalesce(array_stddev(q.daily_returns) * sqrt(252), 0) as volatility
    from (
        select q.user_id,
            q.permno,
            q.date,
            q.prc,
            q.divamt,
            q.value,
            q.ret,
            q.beta,
            (cumprod(1+q.ret) over (partition by q.user_id, q.permno order by q.date) -1) as cumret,
            (cumprod(1+q.ret_sp500) over (partition by q.user_id, q.permno order by q.date) -1) as cumret_sp500,
            array_accum(q.ret) over (PARTITION BY q.user_id, q.permno ORDER BY q.date) as daily_returns,
            array_accum(case when q.ret < 0 then q.ret end) over (PARTITION BY q.user_id, q.permno ORDER BY q.date) as neg_daily_returns
        from (
           select t.user_id,
                t.permno,
                dsf.date,
                dsf.prc,
                coalesce(d.divamt, 0) as divamt,
                sum(case when code = 'B' then shares else -shares end) as shares,
                greatest(sum(case when code = 'B' then shares else -shares end) * dsf.prc / dsf.cfacpr, 0) as value,
                case when sum(case when code = 'B' then shares else -shares end) * dsf.prc / dsf.cfacpr > 0 then 
                        (
                            dsf.prc / dsf.cfacpr + coalesce(d.divamt, 0) 
                            - coalesce(lag(dsf.prc / dsf.cfacpr + coalesce(d.divamt, 0), 1)  over (partition by t.user_id, t.permno order by dsf.date), dsf.prc / dsf.cfacpr)
                        )
                        / coalesce(lag(dsf.prc / dsf.cfacpr + coalesce(d.divamt, 0), 1)  over (partition by t.user_id, t.permno order by dsf.date), dsf.prc / dsf.cfacpr) 
                    else
                        0
                    end as ret,
                dsi.sprtrn as ret_sp500,
                m.beta
            from transactions t
            inner join dsf 
                on dsf.permno = t.permno
                    and dsf.date >= t.date
            inner join market_tradedays nd
                on nd.date = dsf.date
            inner join market_tradedays md
                on nd.idxdate - 1 = md.idxdate
            left join dsf nxt 
                on nxt.permno = t.permno
                    and nxt.date = nd.date
            left join dsi ON dsi.date = nd.date
            left join metrics m on m.permno = t.permno 
                and m.date = nd.date
            left join  (
                select d.permno,
                    d.exdt,
                    d.divamt
                from dsedist d 
                group by d.permno, d.exdt, d.divamt
            ) d on d.permno = dsf.permno
                and d.exdt = dsf.date
            where nxt.date is not null 
                and t.user_id = p_userid
                and case when p_permno is not null then
                        t.permno = p_permno
                    else
                        1 = 1
                    end
            group by t.user_id, 
                t.permno, 
                dsf.date, 
                dsf.prc, 
                dsf.cfacpr, 
                d.divamt,
                m.beta,
                dsi.sprtrn
            order by dsf.date
        ) q
        group by q.user_id, 
            q.permno, 
            q.date, 
            q.prc, 
            q.divamt, 
            q.value,
            q.ret,
            q.ret_sp500,
            q.beta
    )q
    on conflict(user_id, permno, date)
    do update set price = EXCLUDED.price,
        value = EXCLUDED.value,
        ret = EXCLUDED.ret,
        cumret = EXCLUDED.cumret;
end     
$$;


ALTER FUNCTION public.updateholdings_old(p_userid integer, p_permno integer) OWNER TO crsp;

--
-- Name: volatility_metrics_annualized(integer, timestamp without time zone); Type: FUNCTION; Schema: public; Owner: crsp
--

CREATE FUNCTION public.volatility_metrics_annualized(p_permno integer, p_date timestamp without time zone) RETURNS double precision
    LANGUAGE sql IMMUTABLE
    AS $_$

    select stddev(q.ret) * sqrt(252) as volatility
    from (
        select m.permno,
            ed.date,
            m.ret
        from market_tradedays ed
        inner join market_tradedays bd 
        on bd.idxdate=ed.idxdate - 252
        inner join metrics m 
            on m.date between bd.date 
                and ed.date
        where m.permno = $1
            and ed.date = $2
        order by bd.date
        offset 1
    ) q;

$_$;


ALTER FUNCTION public.volatility_metrics_annualized(p_permno integer, p_date timestamp without time zone) OWNER TO crsp;

--
-- Name: array_accum(anyelement); Type: AGGREGATE; Schema: public; Owner: crsp
--

CREATE AGGREGATE public.array_accum(anyelement) (
    SFUNC = array_append,
    STYPE = anyarray,
    INITCOND = '{}'
);


ALTER AGGREGATE public.array_accum(anyelement) OWNER TO crsp;

--
-- Name: cumprod(double precision); Type: AGGREGATE; Schema: public; Owner: crsp
--

CREATE AGGREGATE public.cumprod(double precision) (
    SFUNC = float8mul,
    STYPE = double precision
);


ALTER AGGREGATE public.cumprod(double precision) OWNER TO crsp;

--
-- Name: cumprod(numeric); Type: AGGREGATE; Schema: public; Owner: crsp
--

CREATE AGGREGATE public.cumprod(numeric) (
    SFUNC = numeric_mul,
    STYPE = numeric
);


ALTER AGGREGATE public.cumprod(numeric) OWNER TO crsp;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: dse; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.dse (
    event text,
    date timestamp without time zone,
    hsicmg double precision,
    hsicig double precision,
    comnam text,
    cusip text,
    dclrdt timestamp without time zone,
    dlamt double precision,
    dlpdt timestamp without time zone,
    dlstcd double precision,
    hsiccd double precision,
    issuno double precision,
    ncusip text,
    nextdt timestamp without time zone,
    paydt timestamp without time zone,
    rcrddt timestamp without time zone,
    shrcls text,
    shrflg double precision,
    ticker text,
    permno double precision,
    nameendt timestamp without time zone,
    shrcd double precision,
    exchcd double precision,
    siccd double precision,
    tsymbol text,
    naics text,
    primexch text,
    trdstat text,
    secstat text,
    permco double precision,
    compno double precision,
    hexcd double precision,
    distcd double precision,
    divamt double precision,
    facpr double precision,
    facshr double precision,
    acperm double precision,
    accomp double precision,
    nwperm double precision,
    nwcomp double precision,
    dlretx double precision,
    dlprc double precision,
    dlret double precision,
    shrout double precision,
    shrenddt timestamp without time zone,
    trtscd double precision,
    trtsendt timestamp without time zone,
    nmsind double precision,
    mmcnt double precision,
    nsdinx double precision,
    id integer NOT NULL
);


ALTER TABLE public.dse OWNER TO crsp;

--
-- Name: dse_id_seq; Type: SEQUENCE; Schema: public; Owner: crsp
--

CREATE SEQUENCE public.dse_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dse_id_seq OWNER TO crsp;

--
-- Name: dse_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crsp
--

ALTER SEQUENCE public.dse_id_seq OWNED BY public.dse.id;


--
-- Name: sp500; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.sp500 (
    gvkey bigint NOT NULL,
    iid bigint NOT NULL,
    gvkeyx bigint,
    "from" timestamp without time zone NOT NULL,
    thru timestamp without time zone,
    conm text,
    indextype text,
    tic text,
    spii double precision,
    spmi bigint,
    indexcat text,
    co_conm text,
    co_tic text,
    co_cusip text,
    co_cik double precision,
    co_sic double precision,
    co_naics double precision,
    crsp_cusip text
);


ALTER TABLE public.sp500 OWNER TO crsp;

--
-- Name: stocknames; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.stocknames (
    permno double precision NOT NULL,
    permco double precision NOT NULL,
    namedt timestamp without time zone NOT NULL,
    nameenddt timestamp without time zone NOT NULL,
    cusip text,
    ncusip text,
    ticker text,
    comnam text,
    hexcd double precision,
    exchcd double precision,
    siccd double precision,
    shrcd double precision,
    shrcls text,
    st_date timestamp without time zone,
    end_date timestamp without time zone,
    namedum double precision
);


ALTER TABLE public.stocknames OWNER TO crsp;

--
-- Name: stocknames_sp500; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.stocknames_sp500 AS
 SELECT s.permno,
    s.permco,
    s.namedt,
    s.nameenddt,
    s.cusip,
    s.ncusip,
    s.ticker,
    s.comnam,
    s.hexcd,
    s.exchcd,
    s.siccd,
    s.shrcd,
    s.shrcls,
    s.st_date,
    s.end_date,
    s.namedum
   FROM (public.sp500 idx
     JOIN public.stocknames s ON ((s.ncusip = idx.crsp_cusip)));


ALTER TABLE public.stocknames_sp500 OWNER TO crsp;

--
-- Name: dse_sp500; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.dse_sp500 AS
 SELECT d.event,
    d.date,
    d.hsicmg,
    d.hsicig,
    d.comnam,
    d.cusip,
    d.dclrdt,
    d.dlamt,
    d.dlpdt,
    d.dlstcd,
    d.hsiccd,
    d.issuno,
    d.ncusip,
    d.nextdt,
    d.paydt,
    d.rcrddt,
    d.shrcls,
    d.shrflg,
    d.ticker,
    d.permno,
    d.nameendt,
    d.shrcd,
    d.exchcd,
    d.siccd,
    d.tsymbol,
    d.naics,
    d.primexch,
    d.trdstat,
    d.secstat,
    d.permco,
    d.compno,
    d.hexcd,
    d.distcd,
    d.divamt,
    d.facpr,
    d.facshr,
    d.acperm,
    d.accomp,
    d.nwperm,
    d.nwcomp,
    d.dlretx,
    d.dlprc,
    d.dlret,
    d.shrout,
    d.shrenddt,
    d.trtscd,
    d.trtsendt,
    d.nmsind,
    d.mmcnt,
    d.nsdinx,
    d.id
   FROM public.dse d
  WHERE ((d.date >= '2007-01-01 00:00:00'::timestamp without time zone) AND (d.date <= '2018-12-31 00:00:00'::timestamp without time zone) AND (d.permno IN ( SELECT DISTINCT stocknames_sp500.permno
           FROM public.stocknames_sp500)));


ALTER TABLE public.dse_sp500 OWNER TO crsp;

--
-- Name: dseall; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.dseall (
    date timestamp without time zone,
    comnam text,
    cusip text,
    dclrdt text,
    dlamt double precision,
    dlpdt text,
    dlstcd double precision,
    hsiccd double precision,
    issuno double precision,
    ncusip text,
    nextdt text,
    paydt text,
    rcrddt text,
    shrcls text,
    shrflg double precision,
    ticker text,
    permno double precision,
    permco double precision,
    hexcd double precision,
    hsicmg double precision,
    hsicig double precision,
    nameendt text,
    shrcd double precision,
    exchcd double precision,
    siccd double precision,
    tsymbol text,
    naics text,
    primexch text,
    trdstat text,
    secstat text,
    distcd double precision,
    divamt double precision,
    facpr double precision,
    facshr double precision,
    acperm double precision,
    accomp double precision,
    shrout double precision,
    shrenddt timestamp without time zone,
    nwperm double precision,
    nwcomp double precision,
    dlretx double precision,
    dlprc double precision,
    dlret double precision,
    trtscd double precision,
    trtsendt timestamp without time zone,
    nmsind double precision,
    mmcnt double precision,
    nsdinx double precision,
    id integer NOT NULL
);


ALTER TABLE public.dseall OWNER TO crsp;

--
-- Name: dseall_id_seq; Type: SEQUENCE; Schema: public; Owner: crsp
--

CREATE SEQUENCE public.dseall_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dseall_id_seq OWNER TO crsp;

--
-- Name: dseall_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crsp
--

ALTER SEQUENCE public.dseall_id_seq OWNED BY public.dseall.id;


--
-- Name: dseall_sp500; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.dseall_sp500 AS
 SELECT d.date,
    d.comnam,
    d.cusip,
    d.dclrdt,
    d.dlamt,
    d.dlpdt,
    d.dlstcd,
    d.hsiccd,
    d.issuno,
    d.ncusip,
    d.nextdt,
    d.paydt,
    d.rcrddt,
    d.shrcls,
    d.shrflg,
    d.ticker,
    d.permno,
    d.permco,
    d.hexcd,
    d.hsicmg,
    d.hsicig,
    d.nameendt,
    d.shrcd,
    d.exchcd,
    d.siccd,
    d.tsymbol,
    d.naics,
    d.primexch,
    d.trdstat,
    d.secstat,
    d.distcd,
    d.divamt,
    d.facpr,
    d.facshr,
    d.acperm,
    d.accomp,
    d.shrout,
    d.shrenddt,
    d.nwperm,
    d.nwcomp,
    d.dlretx,
    d.dlprc,
    d.dlret,
    d.trtscd,
    d.trtsendt,
    d.nmsind,
    d.mmcnt,
    d.nsdinx,
    d.id
   FROM public.dseall d
  WHERE ((d.date >= '2007-01-01 00:00:00'::timestamp without time zone) AND (d.date <= '2018-12-31 00:00:00'::timestamp without time zone) AND (d.permno IN ( SELECT DISTINCT stocknames_sp500.permno
           FROM public.stocknames_sp500)));


ALTER TABLE public.dseall_sp500 OWNER TO crsp;

--
-- Name: dsedelist; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.dsedelist (
    permno double precision,
    dlstdt timestamp without time zone,
    dlstcd double precision,
    nwperm double precision,
    nwcomp double precision,
    nextdt timestamp without time zone,
    dlamt double precision,
    dlretx double precision,
    dlprc double precision,
    dlpdt timestamp without time zone,
    dlret double precision,
    permco double precision,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    cusip text,
    acperm text,
    accomp text,
    id integer NOT NULL
);


ALTER TABLE public.dsedelist OWNER TO crsp;

--
-- Name: dsedelist_id_seq; Type: SEQUENCE; Schema: public; Owner: crsp
--

CREATE SEQUENCE public.dsedelist_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dsedelist_id_seq OWNER TO crsp;

--
-- Name: dsedelist_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crsp
--

ALTER SEQUENCE public.dsedelist_id_seq OWNED BY public.dsedelist.id;


--
-- Name: dsedelist_sp500; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.dsedelist_sp500 AS
 SELECT d.permno,
    d.dlstdt,
    d.dlstcd,
    d.nwperm,
    d.nwcomp,
    d.nextdt,
    d.dlamt,
    d.dlretx,
    d.dlprc,
    d.dlpdt,
    d.dlret,
    d.permco,
    d.compno,
    d.issuno,
    d.hexcd,
    d.hsiccd,
    d.cusip,
    d.acperm,
    d.accomp,
    d.id
   FROM public.dsedelist d
  WHERE ((d.dlstdt >= '2007-01-01 00:00:00'::timestamp without time zone) AND (d.dlstdt <= '2018-12-31 00:00:00'::timestamp without time zone) AND (d.permno IN ( SELECT DISTINCT stocknames_sp500.permno
           FROM public.stocknames_sp500)));


ALTER TABLE public.dsedelist_sp500 OWNER TO crsp;

--
-- Name: dsedist; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.dsedist (
    permno double precision,
    distcd double precision,
    divamt double precision,
    facpr double precision,
    facshr double precision,
    dclrdt timestamp without time zone,
    exdt timestamp without time zone,
    rcrddt timestamp without time zone,
    paydt timestamp without time zone,
    acperm double precision,
    accomp double precision,
    permco double precision,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    cusip text
);


ALTER TABLE public.dsedist OWNER TO crsp;

--
-- Name: dsedist_sp500; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.dsedist_sp500 AS
 SELECT d.permno,
    d.distcd,
    d.divamt,
    d.facpr,
    d.facshr,
    d.dclrdt,
    d.exdt,
    d.rcrddt,
    d.paydt,
    d.acperm,
    d.accomp,
    d.permco,
    d.compno,
    d.issuno,
    d.hexcd,
    d.hsiccd,
    d.cusip
   FROM ((public.dsedist d
     JOIN public.stocknames s ON (((s.permco = d.permco) AND (d.exdt <@ tsrange(s.namedt, s.nameenddt, '[]'::text)) AND (d.exdt <@ tsrange(s.st_date, s.end_date, '[]'::text)))))
     JOIN public.sp500 i ON ((i.crsp_cusip = s.ncusip)))
  WHERE ((d.exdt >= '2003-12-31 00:00:00'::timestamp without time zone) AND (d.exdt <= '2018-12-31 00:00:00'::timestamp without time zone));


ALTER TABLE public.dsedist_sp500 OWNER TO crsp;

--
-- Name: dseexchdates; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.dseexchdates (
    permno double precision,
    namedt timestamp without time zone,
    nameendt timestamp without time zone,
    shrcd double precision,
    exchcd double precision,
    siccd double precision,
    ncusip text,
    ticker text,
    comnam text,
    shrcls text,
    tsymbol text,
    naics text,
    primexch text,
    trdstat text,
    secstat text,
    permco double precision,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    cusip text,
    begexchdate timestamp without time zone,
    endexchdate timestamp without time zone,
    dlstdt timestamp without time zone,
    dlstcd double precision,
    id integer NOT NULL
);


ALTER TABLE public.dseexchdates OWNER TO crsp;

--
-- Name: dseexchdates_id_seq; Type: SEQUENCE; Schema: public; Owner: crsp
--

CREATE SEQUENCE public.dseexchdates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dseexchdates_id_seq OWNER TO crsp;

--
-- Name: dseexchdates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crsp
--

ALTER SEQUENCE public.dseexchdates_id_seq OWNED BY public.dseexchdates.id;


--
-- Name: dseexchdates_sp500; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.dseexchdates_sp500 AS
 SELECT d.permno,
    d.namedt,
    d.nameendt,
    d.shrcd,
    d.exchcd,
    d.siccd,
    d.ncusip,
    d.ticker,
    d.comnam,
    d.shrcls,
    d.tsymbol,
    d.naics,
    d.primexch,
    d.trdstat,
    d.secstat,
    d.permco,
    d.compno,
    d.issuno,
    d.hexcd,
    d.hsiccd,
    d.cusip,
    d.begexchdate,
    d.endexchdate,
    d.dlstdt,
    d.dlstcd,
    d.id
   FROM public.dseexchdates d
  WHERE ((d.begexchdate >= '2007-01-01 00:00:00'::timestamp without time zone) AND (d.endexchdate <= '2018-12-31 00:00:00'::timestamp without time zone) AND (d.permno IN ( SELECT DISTINCT stocknames_sp500.permno
           FROM public.stocknames_sp500)));


ALTER TABLE public.dseexchdates_sp500 OWNER TO crsp;

--
-- Name: dsenames; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.dsenames (
    permno double precision,
    namedt timestamp without time zone,
    nameendt timestamp without time zone,
    shrcd double precision,
    exchcd double precision,
    siccd double precision,
    ncusip text,
    ticker text,
    comnam text,
    shrcls text,
    tsymbol text,
    naics text,
    primexch text,
    trdstat text,
    secstat text,
    permco double precision,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    cusip text,
    id integer NOT NULL
);


ALTER TABLE public.dsenames OWNER TO crsp;

--
-- Name: dsenames_id_seq; Type: SEQUENCE; Schema: public; Owner: crsp
--

CREATE SEQUENCE public.dsenames_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dsenames_id_seq OWNER TO crsp;

--
-- Name: dsenames_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crsp
--

ALTER SEQUENCE public.dsenames_id_seq OWNED BY public.dsenames.id;


--
-- Name: dsenames_sp500; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.dsenames_sp500 AS
 SELECT d.permno,
    d.namedt,
    d.nameendt,
    d.shrcd,
    d.exchcd,
    d.siccd,
    d.ncusip,
    d.ticker,
    d.comnam,
    d.shrcls,
    d.tsymbol,
    d.naics,
    d.primexch,
    d.trdstat,
    d.secstat,
    d.permco,
    d.compno,
    d.issuno,
    d.hexcd,
    d.hsiccd,
    d.cusip,
    d.id
   FROM public.dsenames d
  WHERE ((d.namedt >= '2007-01-01 00:00:00'::timestamp without time zone) AND (d.nameendt <= '2018-12-31 00:00:00'::timestamp without time zone) AND (d.permno IN ( SELECT DISTINCT stocknames_sp500.permno
           FROM public.stocknames_sp500)));


ALTER TABLE public.dsenames_sp500 OWNER TO crsp;

--
-- Name: dsenasdin; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.dsenasdin (
    permno double precision,
    trtscd double precision,
    trtsdt timestamp without time zone,
    trtsendt timestamp without time zone,
    nmsind double precision,
    mmcnt double precision,
    nsdinx double precision,
    permco double precision,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    cusip text,
    id integer NOT NULL
);


ALTER TABLE public.dsenasdin OWNER TO crsp;

--
-- Name: dsenasdin_id_seq; Type: SEQUENCE; Schema: public; Owner: crsp
--

CREATE SEQUENCE public.dsenasdin_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dsenasdin_id_seq OWNER TO crsp;

--
-- Name: dsenasdin_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crsp
--

ALTER SEQUENCE public.dsenasdin_id_seq OWNED BY public.dsenasdin.id;


--
-- Name: dsenasdin_sp500; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.dsenasdin_sp500 AS
 SELECT d.permno,
    d.trtscd,
    d.trtsdt,
    d.trtsendt,
    d.nmsind,
    d.mmcnt,
    d.nsdinx,
    d.permco,
    d.compno,
    d.issuno,
    d.hexcd,
    d.hsiccd,
    d.cusip,
    d.id
   FROM public.dsenasdin d
  WHERE ((d.trtsdt >= '2007-01-01 00:00:00'::timestamp without time zone) AND (d.trtsendt <= '2018-12-31 00:00:00'::timestamp without time zone) AND (d.permno IN ( SELECT DISTINCT stocknames_sp500.permno
           FROM public.stocknames_sp500)));


ALTER TABLE public.dsenasdin_sp500 OWNER TO crsp;

--
-- Name: dseshares; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.dseshares (
    permno double precision,
    shrout double precision,
    shrsdt timestamp without time zone,
    shrenddt timestamp without time zone,
    shrflg double precision,
    permco double precision,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    cusip text,
    id integer NOT NULL
);


ALTER TABLE public.dseshares OWNER TO crsp;

--
-- Name: dseshares_id_seq; Type: SEQUENCE; Schema: public; Owner: crsp
--

CREATE SEQUENCE public.dseshares_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dseshares_id_seq OWNER TO crsp;

--
-- Name: dseshares_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crsp
--

ALTER SEQUENCE public.dseshares_id_seq OWNED BY public.dseshares.id;


--
-- Name: dseshares_sp500; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.dseshares_sp500 AS
 SELECT d.permno,
    d.shrout,
    d.shrsdt,
    d.shrenddt,
    d.shrflg,
    d.permco,
    d.compno,
    d.issuno,
    d.hexcd,
    d.hsiccd,
    d.cusip,
    d.id
   FROM public.dseshares d
  WHERE ((d.shrsdt >= '2007-01-01 00:00:00'::timestamp without time zone) AND (d.shrenddt <= '2018-12-31 00:00:00'::timestamp without time zone) AND (d.permno IN ( SELECT DISTINCT stocknames_sp500.permno
           FROM public.stocknames_sp500)));


ALTER TABLE public.dseshares_sp500 OWNER TO crsp;

--
-- Name: dsf; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.dsf (
    cusip text,
    permno double precision NOT NULL,
    permco double precision NOT NULL,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    date timestamp without time zone NOT NULL,
    bidlo double precision,
    askhi double precision,
    prc double precision,
    vol double precision,
    ret double precision,
    bid double precision,
    ask double precision,
    shrout double precision,
    cfacpr double precision,
    cfacshr double precision,
    openprc double precision,
    numtrd double precision,
    retx double precision
);


ALTER TABLE public.dsf OWNER TO crsp;

--
-- Name: dsf_sp500; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.dsf_sp500 AS
 SELECT d.cusip,
    d.permno,
    d.permco,
    d.issuno,
    d.hexcd,
    d.hsiccd,
    d.date,
    d.bidlo,
    d.askhi,
    d.prc,
    d.vol,
    d.ret,
    d.bid,
    d.ask,
    d.shrout,
    d.cfacpr,
    d.cfacshr,
    d.openprc,
    d.numtrd,
    d.retx
   FROM public.dsf d
  WHERE ((d.date >= '2003-12-31 00:00:00'::timestamp without time zone) AND (d.date <= '2018-12-31 00:00:00'::timestamp without time zone) AND (d.permno IN ( SELECT DISTINCT stocknames_sp500.permno
           FROM public.stocknames_sp500)))
  ORDER BY d.permco, d.permno, d.date;


ALTER TABLE public.dsf_sp500 OWNER TO crsp;

--
-- Name: dsfhdr; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.dsfhdr (
    permno double precision,
    permco double precision,
    hshrcd double precision,
    dlstcd double precision,
    hcusip text,
    htick text,
    hcomnam text,
    htsymbol text,
    hnaics text,
    hprimexc text,
    htrdstat text,
    hsecstat text,
    cusip text,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    numnam double precision,
    numdis double precision,
    numshr double precision,
    numdel double precision,
    numndi double precision,
    begdat timestamp without time zone,
    enddat timestamp without time zone,
    begprc timestamp without time zone,
    endprc timestamp without time zone,
    begret timestamp without time zone,
    endret timestamp without time zone,
    begrtx timestamp without time zone,
    endrtx timestamp without time zone,
    begbidlo timestamp without time zone,
    endbidlo timestamp without time zone,
    begaskhi timestamp without time zone,
    endaskhi timestamp without time zone,
    begvol timestamp without time zone,
    endvol timestamp without time zone,
    begbid timestamp without time zone,
    endbid timestamp without time zone,
    begask timestamp without time zone,
    endask timestamp without time zone,
    begopr timestamp without time zone,
    endopr timestamp without time zone,
    hsicmg double precision,
    hsicig double precision
);


ALTER TABLE public.dsfhdr OWNER TO crsp;

--
-- Name: dsfhdr_sp500; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.dsfhdr_sp500 AS
 SELECT d.permno,
    d.permco,
    d.hshrcd,
    d.dlstcd,
    d.hcusip,
    d.htick,
    d.hcomnam,
    d.htsymbol,
    d.hnaics,
    d.hprimexc,
    d.htrdstat,
    d.hsecstat,
    d.cusip,
    d.compno,
    d.issuno,
    d.hexcd,
    d.hsiccd,
    d.numnam,
    d.numdis,
    d.numshr,
    d.numdel,
    d.numndi,
    d.begdat,
    d.enddat,
    d.begprc,
    d.endprc,
    d.begret,
    d.endret,
    d.begrtx,
    d.endrtx,
    d.begbidlo,
    d.endbidlo,
    d.begaskhi,
    d.endaskhi,
    d.begvol,
    d.endvol,
    d.begbid,
    d.endbid,
    d.begask,
    d.endask,
    d.begopr,
    d.endopr,
    d.hsicmg,
    d.hsicig
   FROM public.dsfhdr d
  WHERE ((d.begdat >= '2007-01-01 00:00:00'::timestamp without time zone) AND (d.enddat <= '2018-12-31 00:00:00'::timestamp without time zone) AND (d.permno IN ( SELECT DISTINCT stocknames_sp500.permno
           FROM public.stocknames_sp500)));


ALTER TABLE public.dsfhdr_sp500 OWNER TO crsp;

--
-- Name: dsi; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.dsi (
    date timestamp without time zone NOT NULL,
    vwretd double precision,
    vwretx double precision,
    ewretd double precision,
    ewretx double precision,
    sprtrn double precision,
    spindx double precision,
    totval double precision,
    totcnt double precision,
    usdval double precision,
    usdcnt double precision
);


ALTER TABLE public.dsi OWNER TO crsp;

--
-- Name: dsi_sp500; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.dsi_sp500 AS
 SELECT d.date,
    d.vwretd,
    d.vwretx,
    d.ewretd,
    d.ewretx,
    d.sprtrn,
    d.spindx,
    d.totval,
    d.totcnt,
    d.usdval,
    d.usdcnt
   FROM public.dsi d
  WHERE ((d.date >= '2003-12-31 00:00:00'::timestamp without time zone) AND (d.date <= '2018-12-31 00:00:00'::timestamp without time zone));


ALTER TABLE public.dsi_sp500 OWNER TO crsp;

--
-- Name: dsiy; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.dsiy (
    caldt timestamp without time zone NOT NULL,
    vwretd double precision,
    vwretx double precision,
    ewretd double precision,
    ewretx double precision,
    sprtrn double precision,
    spindx double precision,
    totval double precision,
    totcnt double precision,
    usdval double precision,
    usdcnt double precision
);


ALTER TABLE public.dsiy OWNER TO crsp;

--
-- Name: dsiy_sp500; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.dsiy_sp500 AS
 SELECT d.caldt,
    d.vwretd,
    d.vwretx,
    d.ewretd,
    d.ewretx,
    d.sprtrn,
    d.spindx,
    d.totval,
    d.totcnt,
    d.usdval,
    d.usdcnt
   FROM public.dsiy d
  WHERE ((d.caldt >= '2007-01-01 00:00:00'::timestamp without time zone) AND (d.caldt <= '2018-12-31 00:00:00'::timestamp without time zone));


ALTER TABLE public.dsiy_sp500 OWNER TO crsp;

--
-- Name: holdings; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.holdings (
    user_id integer NOT NULL,
    permno integer NOT NULL,
    date date NOT NULL,
    price double precision,
    value double precision,
    ret double precision,
    cumret double precision,
    alpha double precision,
    beta double precision,
    sharpe double precision,
    sortino double precision,
    volatility double precision
);


ALTER TABLE public.holdings OWNER TO crsp;

--
-- Name: holdingsgain; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.holdingsgain AS
 SELECT h.user_id,
    h.permno,
    h.date,
    h.price,
    h.value,
    h.ret,
    h.cumret,
    h.alpha,
    h.beta,
    h.sharpe,
    h.sortino,
    h.volatility,
        CASE
            WHEN (h.ret = (0)::double precision) THEN (0)::double precision
            ELSE dsi.sprtrn
        END AS ret_sp500,
    (public.cumprod(((1)::double precision +
        CASE
            WHEN (h.ret = (0)::double precision) THEN (0)::double precision
            ELSE dsi.sprtrn
        END)) OVER (PARTITION BY h.user_id, h.permno ORDER BY h.date) - (1)::double precision) AS cumret_sp500
   FROM (public.holdings h
     JOIN public.dsi ON ((h.date = dsi.date)))
  ORDER BY h.user_id, h.permno, h.date;


ALTER TABLE public.holdingsgain OWNER TO crsp;

--
-- Name: market_holidays; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.market_holidays (
    date date NOT NULL,
    marketclosed boolean
);


ALTER TABLE public.market_holidays OWNER TO crsp;

--
-- Name: market_tradedays; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.market_tradedays (
    date timestamp without time zone NOT NULL,
    idxdate integer NOT NULL,
    year integer,
    quarter integer,
    quarterlabel text,
    quarterstart timestamp without time zone,
    quarterend timestamp without time zone
);


ALTER TABLE public.market_tradedays OWNER TO crsp;

--
-- Name: metrics; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.metrics (
    permno integer NOT NULL,
    date date NOT NULL,
    ret double precision,
    ret_sp500 double precision,
    alpha double precision,
    beta double precision,
    sharpe double precision,
    sortino double precision,
    volatility double precision
);


ALTER TABLE public.metrics OWNER TO crsp;

--
-- Name: mse; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.mse (
    event text,
    date timestamp without time zone,
    hsicmg double precision,
    hsicig double precision,
    comnam text,
    cusip text,
    dclrdt timestamp without time zone,
    dlamt double precision,
    dlpdt timestamp without time zone,
    dlstcd double precision,
    hsiccd double precision,
    issuno double precision,
    ncusip text,
    nextdt timestamp without time zone,
    paydt timestamp without time zone,
    rcrddt timestamp without time zone,
    shrcls text,
    shrflg double precision,
    ticker text,
    permno double precision,
    nameendt timestamp without time zone,
    shrcd double precision,
    exchcd double precision,
    siccd double precision,
    tsymbol text,
    naics text,
    primexch text,
    trdstat text,
    secstat text,
    permco double precision,
    compno double precision,
    hexcd double precision,
    distcd double precision,
    divamt double precision,
    facpr double precision,
    facshr double precision,
    acperm double precision,
    accomp double precision,
    nwperm double precision,
    nwcomp double precision,
    dlretx double precision,
    dlprc double precision,
    dlret double precision,
    shrout double precision,
    shrenddt timestamp without time zone,
    trtscd double precision,
    trtsendt timestamp without time zone,
    nmsind double precision,
    mmcnt double precision,
    nsdinx double precision
);


ALTER TABLE public.mse OWNER TO crsp;

--
-- Name: mseall; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.mseall (
    date timestamp without time zone,
    comnam text,
    cusip text,
    dclrdt timestamp without time zone,
    dlamt double precision,
    dlpdt timestamp without time zone,
    dlstcd double precision,
    hsiccd double precision,
    issuno double precision,
    ncusip text,
    nextdt timestamp without time zone,
    paydt timestamp without time zone,
    rcrddt timestamp without time zone,
    shrcls text,
    shrflg double precision,
    ticker text,
    permno double precision,
    permco double precision,
    hexcd double precision,
    hsicmg double precision,
    hsicig double precision,
    nameendt timestamp without time zone,
    shrcd double precision,
    exchcd double precision,
    siccd double precision,
    tsymbol text,
    naics text,
    primexch text,
    trdstat text,
    secstat text,
    distcd double precision,
    divamt double precision,
    facpr double precision,
    facshr double precision,
    acperm double precision,
    accomp double precision,
    shrout double precision,
    shrenddt timestamp without time zone,
    nwperm double precision,
    nwcomp double precision,
    dlretx double precision,
    dlprc double precision,
    dlret double precision,
    trtscd double precision,
    trtsendt timestamp without time zone,
    nmsind double precision,
    mmcnt double precision,
    nsdinx double precision,
    year double precision,
    month double precision
);


ALTER TABLE public.mseall OWNER TO crsp;

--
-- Name: msedelist; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.msedelist (
    permno double precision,
    dlstdt timestamp without time zone,
    dlstcd double precision,
    nwperm double precision,
    nwcomp double precision,
    nextdt timestamp without time zone,
    dlamt double precision,
    dlretx double precision,
    dlprc double precision,
    dlpdt timestamp without time zone,
    dlret double precision,
    permco double precision,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    cusip text,
    acperm text,
    accomp text
);


ALTER TABLE public.msedelist OWNER TO crsp;

--
-- Name: msedist; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.msedist (
    permno double precision,
    distcd double precision,
    divamt double precision,
    facpr double precision,
    facshr double precision,
    dclrdt timestamp without time zone,
    exdt timestamp without time zone,
    rcrddt timestamp without time zone,
    paydt timestamp without time zone,
    acperm double precision,
    accomp double precision,
    permco double precision,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    cusip text
);


ALTER TABLE public.msedist OWNER TO crsp;

--
-- Name: mseexchdates; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.mseexchdates (
    permno double precision,
    namedt timestamp without time zone,
    nameendt timestamp without time zone,
    shrcd double precision,
    exchcd double precision,
    siccd double precision,
    ncusip text,
    ticker text,
    comnam text,
    shrcls text,
    tsymbol text,
    naics text,
    primexch text,
    trdstat text,
    secstat text,
    permco double precision,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    cusip text,
    begexchdate timestamp without time zone,
    endexchdate timestamp without time zone,
    dlstdt text,
    dlstcd double precision
);


ALTER TABLE public.mseexchdates OWNER TO crsp;

--
-- Name: msenames; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.msenames (
    permno double precision,
    namedt timestamp without time zone,
    nameendt timestamp without time zone,
    shrcd double precision,
    exchcd double precision,
    siccd double precision,
    ncusip text,
    ticker text,
    comnam text,
    shrcls text,
    tsymbol text,
    naics text,
    primexch text,
    trdstat text,
    secstat text,
    permco double precision,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    cusip text
);


ALTER TABLE public.msenames OWNER TO crsp;

--
-- Name: msenasdin; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.msenasdin (
    permno double precision,
    trtscd double precision,
    trtsdt timestamp without time zone,
    trtsendt timestamp without time zone,
    nmsind double precision,
    mmcnt double precision,
    nsdinx double precision,
    permco double precision,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    cusip text
);


ALTER TABLE public.msenasdin OWNER TO crsp;

--
-- Name: mseshares; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.mseshares (
    permno double precision,
    shrout double precision,
    shrsdt timestamp without time zone,
    shrenddt timestamp without time zone,
    shrflg double precision,
    permco double precision,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    cusip text
);


ALTER TABLE public.mseshares OWNER TO crsp;

--
-- Name: msf; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.msf (
    cusip text,
    permno double precision,
    permco double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    date timestamp without time zone,
    bidlo double precision,
    askhi double precision,
    prc double precision,
    vol double precision,
    ret double precision,
    bid double precision,
    ask double precision,
    shrout double precision,
    cfacpr double precision,
    cfacshr double precision,
    altprc double precision,
    spread double precision,
    altprcdt timestamp without time zone,
    retx double precision
);


ALTER TABLE public.msf OWNER TO crsp;

--
-- Name: msfhdr; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.msfhdr (
    permno double precision,
    permco double precision,
    hshrcd double precision,
    dlstcd double precision,
    hcusip text,
    htick text,
    hcomnam text,
    htsymbol text,
    hnaics text,
    hprimexc text,
    htrdstat text,
    hsecstat text,
    cusip text,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    numnam double precision,
    numdis double precision,
    numshr double precision,
    numdel double precision,
    numndi double precision,
    begdat timestamp without time zone,
    enddat timestamp without time zone,
    begprc timestamp without time zone,
    endprc timestamp without time zone,
    begret timestamp without time zone,
    endret timestamp without time zone,
    begrtx timestamp without time zone,
    endrtx timestamp without time zone,
    begbidlo timestamp without time zone,
    endbidlo timestamp without time zone,
    begaskhi timestamp without time zone,
    endaskhi timestamp without time zone,
    begvol timestamp without time zone,
    endvol timestamp without time zone,
    begbid timestamp without time zone,
    endbid timestamp without time zone,
    begask timestamp without time zone,
    endask timestamp without time zone,
    begpr2 timestamp without time zone,
    endpr2 timestamp without time zone,
    begsprd timestamp without time zone,
    endsprd timestamp without time zone,
    hsicmg double precision,
    hsicig double precision
);


ALTER TABLE public.msfhdr OWNER TO crsp;

--
-- Name: msi; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.msi (
    date timestamp without time zone,
    vwretd double precision,
    vwretx double precision,
    ewretd double precision,
    ewretx double precision,
    sprtrn double precision,
    spindx double precision,
    totval double precision,
    totcnt double precision,
    usdval double precision,
    usdcnt double precision
);


ALTER TABLE public.msi OWNER TO crsp;

--
-- Name: msiy; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.msiy (
    caldt timestamp without time zone,
    vwretd double precision,
    vwretx double precision,
    ewretd double precision,
    ewretx double precision,
    sprtrn double precision,
    spindx double precision,
    totval double precision,
    totcnt double precision,
    usdval double precision,
    usdcnt double precision
);


ALTER TABLE public.msiy OWNER TO crsp;

--
-- Name: portfolio; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.portfolio (
    user_id integer NOT NULL,
    date date NOT NULL,
    value double precision,
    ret double precision,
    cumret double precision,
    alpha double precision,
    beta double precision,
    sharpe double precision,
    sortino double precision,
    volatility double precision
);


ALTER TABLE public.portfolio OWNER TO crsp;

--
-- Name: portfoliogain; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.portfoliogain AS
 SELECT p.user_id,
    p.date,
    p.value,
    p.ret,
    p.cumret,
    p.ret_sp500,
    p.cumret_sp500,
    p.alpha,
    p.beta,
    p.sharpe,
    p.sortino,
    p.volatility,
    COALESCE((public.array_stddev(p.daily_sp500_returns) * sqrt((252)::double precision)), (0)::double precision) AS volatility_sp500
   FROM ( SELECT p_1.user_id,
            p_1.date,
            p_1.value,
            p_1.ret,
            p_1.cumret,
                CASE
                    WHEN (p_1.ret = (0)::double precision) THEN (0)::double precision
                    ELSE dsi.sprtrn
                END AS ret_sp500,
            (public.cumprod(((1)::double precision +
                CASE
                    WHEN (p_1.ret = (0)::double precision) THEN (0)::double precision
                    ELSE dsi.sprtrn
                END)) OVER (PARTITION BY p_1.user_id ORDER BY p_1.date) - (1)::double precision) AS cumret_sp500,
            p_1.alpha,
            p_1.beta,
            p_1.sharpe,
            p_1.sortino,
            p_1.volatility,
            public.array_accum(dsi.sprtrn) OVER (PARTITION BY p_1.user_id ORDER BY p_1.date) AS daily_sp500_returns
           FROM (public.portfolio p_1
             JOIN public.dsi ON ((p_1.date = dsi.date)))
          ORDER BY p_1.user_id, p_1.date) p;


ALTER TABLE public.portfoliogain OWNER TO crsp;

--
-- Name: quarterdates; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.quarterdates (
    startts timestamp without time zone,
    endts timestamp without time zone,
    quarter text,
    startepoch bigint,
    endepoch bigint,
    qtridx integer NOT NULL
);


ALTER TABLE public.quarterdates OWNER TO crsp;

--
-- Name: saz_del; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.saz_del (
    kypermno double precision,
    dlstdt timestamp without time zone,
    dlstcd double precision,
    nwperm double precision,
    nwcomp double precision,
    nextdt text,
    dlprc double precision,
    dlpdt timestamp without time zone,
    dlamt double precision,
    dlret double precision,
    dlretx double precision
);


ALTER TABLE public.saz_del OWNER TO crsp;

--
-- Name: saz_dind; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.saz_dind (
    kyindno double precision NOT NULL,
    caldt timestamp without time zone NOT NULL,
    tret double precision,
    tind double precision,
    aret double precision,
    aind double precision,
    iret double precision,
    iind double precision,
    usdcnt double precision,
    usdval double precision,
    totcnt double precision,
    totval double precision
);


ALTER TABLE public.saz_dind OWNER TO crsp;

--
-- Name: saz_dis; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.saz_dis (
    kypermno double precision,
    distcd double precision,
    divamt double precision,
    facpr double precision,
    facshr double precision,
    dclrdt timestamp without time zone,
    exdt timestamp without time zone,
    rcrddt timestamp without time zone,
    paydt timestamp without time zone,
    acperm double precision,
    accomp double precision
);


ALTER TABLE public.saz_dis OWNER TO crsp;

--
-- Name: saz_dp_dly; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.saz_dp_dly (
    kypermno double precision,
    caldt timestamp without time zone,
    prc double precision,
    ret double precision,
    retx double precision,
    tcap double precision,
    vol double precision
);


ALTER TABLE public.saz_dp_dly OWNER TO crsp;

--
-- Name: saz_ds_dly; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.saz_ds_dly (
    kypermno double precision,
    caldt timestamp without time zone,
    bidlo double precision,
    askhi double precision,
    bid double precision,
    ask double precision,
    numtrd double precision,
    openprc double precision
);


ALTER TABLE public.saz_ds_dly OWNER TO crsp;

--
-- Name: saz_hdr; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.saz_hdr (
    kypermno double precision,
    cusip text,
    cusip9 text,
    htick text,
    permco double precision,
    compno double precision,
    issuno double precision,
    hexcd double precision,
    hsiccd double precision,
    begdt timestamp without time zone,
    enddt timestamp without time zone,
    hdlstcd double precision,
    hcomnam text,
    htsymbol text,
    hsnaics text,
    hshrcd double precision,
    hprimexch text,
    htrdstat text,
    hsecstat text
);


ALTER TABLE public.saz_hdr OWNER TO crsp;

--
-- Name: saz_indhdr; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.saz_indhdr (
    kyindno double precision NOT NULL,
    indname text,
    indbegdt timestamp without time zone,
    indenddt timestamp without time zone,
    indfam double precision,
    portnum double precision,
    baselvl double precision,
    basedt timestamp without time zone,
    availability text,
    calcrule text,
    listrule double precision,
    method double precision,
    rebalrule text,
    puniverse text,
    universe double precision
);


ALTER TABLE public.saz_indhdr OWNER TO crsp;

--
-- Name: saz_mdel; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.saz_mdel (
    kypermno double precision,
    mdlstdt timestamp without time zone,
    mdlstcd double precision,
    mnwperm double precision,
    mnwcomp double precision,
    mnextdt timestamp without time zone,
    mdlprc double precision,
    mdlpdt timestamp without time zone,
    mdlamt double precision,
    mdlret double precision,
    mdlretx double precision
);


ALTER TABLE public.saz_mdel OWNER TO crsp;

--
-- Name: saz_mind; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.saz_mind (
    kyindno double precision,
    mcaldt timestamp without time zone,
    mtret double precision,
    mtind double precision,
    maret double precision,
    maind double precision,
    miret double precision,
    miind double precision,
    musdcnt double precision,
    musdval double precision,
    mtotcnt double precision,
    mtotval double precision
);


ALTER TABLE public.saz_mind OWNER TO crsp;

--
-- Name: saz_mth; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.saz_mth (
    kypermno double precision,
    mcaldt timestamp without time zone,
    mprc double precision,
    mret double precision,
    mretx double precision,
    mtcap double precision,
    mvol double precision,
    mbidlo double precision,
    maskhi double precision,
    mbid double precision,
    mask double precision,
    mspread double precision,
    maltprc double precision,
    maltprcdt timestamp without time zone
);


ALTER TABLE public.saz_mth OWNER TO crsp;

--
-- Name: saz_nam; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.saz_nam (
    kypermno double precision,
    namedt timestamp without time zone,
    nameenddt timestamp without time zone,
    ncusip text,
    ncusip9 text,
    ticker text,
    comnam text,
    shrcls text,
    shrcd double precision,
    exchcd double precision,
    siccd double precision,
    tsymbol text,
    snaics text,
    primexch text,
    trdstat text,
    secstat text
);


ALTER TABLE public.saz_nam OWNER TO crsp;

--
-- Name: saz_ndi; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.saz_ndi (
    kypermno double precision,
    trtsdt timestamp without time zone,
    trtsenddt timestamp without time zone,
    nsdinx double precision,
    nmsind double precision,
    mmcnt double precision,
    trtscd double precision
);


ALTER TABLE public.saz_ndi OWNER TO crsp;

--
-- Name: saz_shr; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.saz_shr (
    kypermno double precision,
    shrsdt timestamp without time zone,
    shrsenddt timestamp without time zone,
    shrout double precision,
    shrflg double precision
);


ALTER TABLE public.saz_shr OWNER TO crsp;

--
-- Name: stock_qvards; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.stock_qvards (
    event text,
    date timestamp without time zone,
    hsicmg text,
    hsicig text,
    comnam text,
    cusip text,
    dclrdt timestamp without time zone,
    dlamt text,
    dlpdt timestamp without time zone,
    dlstcd text,
    hsiccd text,
    issuno text,
    ncusip text,
    nextdt timestamp without time zone,
    paydt timestamp without time zone,
    rcrddt timestamp without time zone,
    shrcls text,
    shrflg text,
    ticker text,
    permno text,
    nameendt timestamp without time zone,
    shrcd text,
    exchcd text,
    siccd text,
    tsymbol text,
    naics text,
    primexch text,
    trdstat text,
    secstat text,
    permco text,
    compno text,
    hexcd text,
    distcd text,
    divamt text,
    facpr text,
    facshr text,
    acperm text,
    accomp text,
    nwperm text,
    nwcomp text,
    dlretx text,
    dlprc text,
    dlret text,
    shrout text,
    shrenddt text,
    trtscd text,
    trtsendt timestamp without time zone,
    nmsind text,
    mmcnt text,
    nsdinx text,
    jlkey text
);


ALTER TABLE public.stock_qvards OWNER TO crsp;

--
-- Name: stockmaster; Type: VIEW; Schema: public; Owner: crsp
--

CREATE VIEW public.stockmaster AS
 SELECT DISTINCT ON (stocknames.permno, stocknames.end_date, stocknames.st_date) stocknames.permno,
    stocknames.ticker,
    stocknames.comnam,
    stocknames.st_date,
    stocknames.end_date
   FROM public.stocknames
  ORDER BY stocknames.permno, stocknames.end_date DESC, stocknames.st_date, stocknames.nameenddt DESC, stocknames.namedt DESC, stocknames.ticker, stocknames.comnam;


ALTER TABLE public.stockmaster OWNER TO crsp;

--
-- Name: transactions; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public.transactions (
    user_id integer NOT NULL,
    date date NOT NULL,
    permno integer NOT NULL,
    code text NOT NULL,
    value double precision NOT NULL,
    shares double precision,
    price double precision,
    id integer NOT NULL,
    auto boolean DEFAULT false,
    contra integer
);


ALTER TABLE public.transactions OWNER TO crsp;

--
-- Name: transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: crsp
--

CREATE SEQUENCE public.transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.transactions_id_seq OWNER TO crsp;

--
-- Name: transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crsp
--

ALTER SEQUENCE public.transactions_id_seq OWNED BY public.transactions.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: crsp
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    username character varying(64),
    email character varying(120),
    password_hash character varying(128),
    admin boolean DEFAULT false NOT NULL
);


ALTER TABLE public."user" OWNER TO crsp;

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: crsp
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_id_seq OWNER TO crsp;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: crsp
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: dse id; Type: DEFAULT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dse ALTER COLUMN id SET DEFAULT nextval('public.dse_id_seq'::regclass);


--
-- Name: dseall id; Type: DEFAULT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dseall ALTER COLUMN id SET DEFAULT nextval('public.dseall_id_seq'::regclass);


--
-- Name: dsedelist id; Type: DEFAULT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dsedelist ALTER COLUMN id SET DEFAULT nextval('public.dsedelist_id_seq'::regclass);


--
-- Name: dseexchdates id; Type: DEFAULT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dseexchdates ALTER COLUMN id SET DEFAULT nextval('public.dseexchdates_id_seq'::regclass);


--
-- Name: dsenames id; Type: DEFAULT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dsenames ALTER COLUMN id SET DEFAULT nextval('public.dsenames_id_seq'::regclass);


--
-- Name: dsenasdin id; Type: DEFAULT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dsenasdin ALTER COLUMN id SET DEFAULT nextval('public.dsenasdin_id_seq'::regclass);


--
-- Name: dseshares id; Type: DEFAULT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dseshares ALTER COLUMN id SET DEFAULT nextval('public.dseshares_id_seq'::regclass);


--
-- Name: transactions id; Type: DEFAULT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.transactions ALTER COLUMN id SET DEFAULT nextval('public.transactions_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: dse dse_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dse
    ADD CONSTRAINT dse_pk PRIMARY KEY (id);


--
-- Name: dseall dseall_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dseall
    ADD CONSTRAINT dseall_pk PRIMARY KEY (id);


--
-- Name: dsedelist dsedelist_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dsedelist
    ADD CONSTRAINT dsedelist_pk PRIMARY KEY (id);


--
-- Name: dseexchdates dseexchdates_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dseexchdates
    ADD CONSTRAINT dseexchdates_pk PRIMARY KEY (id);


--
-- Name: dsenames dsenames_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dsenames
    ADD CONSTRAINT dsenames_pk PRIMARY KEY (id);


--
-- Name: dsenasdin dsenasdin_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dsenasdin
    ADD CONSTRAINT dsenasdin_pk PRIMARY KEY (id);


--
-- Name: dseshares dseshares_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dseshares
    ADD CONSTRAINT dseshares_pk PRIMARY KEY (id);


--
-- Name: dsf dsf_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dsf
    ADD CONSTRAINT dsf_pk PRIMARY KEY (permno, date);


--
-- Name: dsi dsi_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dsi
    ADD CONSTRAINT dsi_pk PRIMARY KEY (date);


--
-- Name: dsiy dsiy_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.dsiy
    ADD CONSTRAINT dsiy_pk PRIMARY KEY (caldt);


--
-- Name: holdings holdings_pkey; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.holdings
    ADD CONSTRAINT holdings_pkey PRIMARY KEY (user_id, permno, date);


--
-- Name: market_tradedays market_tradedays_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.market_tradedays
    ADD CONSTRAINT market_tradedays_pk PRIMARY KEY (date);


--
-- Name: metrics metrics_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.metrics
    ADD CONSTRAINT metrics_pk PRIMARY KEY (permno, date);


--
-- Name: portfolio portfolio_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.portfolio
    ADD CONSTRAINT portfolio_pk PRIMARY KEY (user_id, date);


--
-- Name: saz_dind saz_dind_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.saz_dind
    ADD CONSTRAINT saz_dind_pk PRIMARY KEY (kyindno, caldt);


--
-- Name: saz_indhdr saz_indhdr_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.saz_indhdr
    ADD CONSTRAINT saz_indhdr_pk PRIMARY KEY (kyindno);


--
-- Name: sp500 sp500_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.sp500
    ADD CONSTRAINT sp500_pk PRIMARY KEY (gvkey, iid, "from");


--
-- Name: stocknames stocknames_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.stocknames
    ADD CONSTRAINT stocknames_pk PRIMARY KEY (permco, permno, namedt, nameenddt);


--
-- Name: transactions transactions_pk; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pk PRIMARY KEY (user_id, date, code, permno);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: crsp
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: dse_date_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX dse_date_idx ON public.dse USING btree (date);


--
-- Name: dse_permco_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX dse_permco_idx ON public.dse USING btree (permco);


--
-- Name: dse_permno_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX dse_permno_idx ON public.dse USING btree (permno);


--
-- Name: dsf_date_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX dsf_date_idx ON public.dsf USING btree (date);


--
-- Name: dsf_permco_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX dsf_permco_idx ON public.dsf USING btree (permco);


--
-- Name: dsf_permno_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX dsf_permno_idx ON public.dsf USING btree (permno);


--
-- Name: holdings_permno_date_value_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX holdings_permno_date_value_idx ON public.holdings USING btree (permno, date, value);


--
-- Name: holdings_userid_permno_date_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX holdings_userid_permno_date_idx ON public.holdings USING btree (user_id, permno, date);


--
-- Name: ix_user_email; Type: INDEX; Schema: public; Owner: crsp
--

CREATE UNIQUE INDEX ix_user_email ON public."user" USING btree (email);


--
-- Name: ix_user_username; Type: INDEX; Schema: public; Owner: crsp
--

CREATE UNIQUE INDEX ix_user_username ON public."user" USING btree (username);


--
-- Name: market_tradedays_date_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX market_tradedays_date_idx ON public.market_tradedays USING btree (date);


--
-- Name: market_tradedays_idxdate_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX market_tradedays_idxdate_idx ON public.market_tradedays USING btree (idxdate);


--
-- Name: metrics_date_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX metrics_date_idx ON public.metrics USING btree (date);


--
-- Name: metrics_permno_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX metrics_permno_idx ON public.metrics USING btree (permno);


--
-- Name: saz_dind_caldt_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX saz_dind_caldt_idx ON public.saz_dind USING btree (caldt);


--
-- Name: saz_dind_kyindno_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX saz_dind_kyindno_idx ON public.saz_dind USING btree (kyindno);


--
-- Name: sp500_co_cusip_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX sp500_co_cusip_idx ON public.sp500 USING btree (co_cusip);


--
-- Name: sp500_crsp_cusip_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX sp500_crsp_cusip_idx ON public.sp500 USING btree (crsp_cusip);


--
-- Name: stocknames_cusip_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX stocknames_cusip_idx ON public.stocknames USING btree (cusip);


--
-- Name: stocknames_ncusip_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX stocknames_ncusip_idx ON public.stocknames USING btree (ncusip);


--
-- Name: stocknames_ticker_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX stocknames_ticker_idx ON public.stocknames USING btree (ticker);


--
-- Name: transactions_date_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX transactions_date_idx ON public.transactions USING btree (date);


--
-- Name: transactions_permno_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX transactions_permno_idx ON public.transactions USING btree (permno);


--
-- Name: transactions_user_id_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX transactions_user_id_idx ON public.transactions USING btree (user_id);


--
-- Name: transactions_userid_permno_date_idx; Type: INDEX; Schema: public; Owner: crsp
--

CREATE INDEX transactions_userid_permno_date_idx ON public.transactions USING btree (user_id, permno, date);


--
-- Name: transactions b_transactions_manage_cash; Type: TRIGGER; Schema: public; Owner: crsp
--

CREATE TRIGGER b_transactions_manage_cash AFTER INSERT OR DELETE ON public.transactions FOR EACH ROW EXECUTE PROCEDURE public.transactions_manage_cash();

ALTER TABLE public.transactions DISABLE TRIGGER b_transactions_manage_cash;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM rdsadmin;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

