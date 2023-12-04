function load_chart1() {

    var svg = d3.select("#chart1");
    margin = {top: 20, right: 20, bottom: 30, left: 40},
    width = +svg.attr("width") - margin.left - margin.right,
    height = +svg.attr("height") - margin.top - margin.bottom;

    var xScale = d3.scaleTime().rangeRound([0, width]),
        yScale = d3.scaleLinear().rangeRound([height, 0]);

    var g = svg.append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    g.append("text")
        .attr("x", (width / 2))             
        .attr("y", 0 - (margin.top / 2))
        .attr("text-anchor", "middle")  
        .style("font-size", "12px") 
        .text("US Earthquakes by Region 2010-2015");

    var parseYear = d3.timeParse("%Y");
    var formatYear = d3.timeFormat("%Y");

    var line = d3.line()
    .x(function(d) { return xScale(
        parseYear(+d.key)
        ); })
    .y(function(d) { return yScale(
        d.value
        ); });

    subchart = load_chart2;

      // Three function that change the tooltip when user hover / move / leave a circle
    var mouseover = function(d) {
        d3.selectAll(".subchart").remove();
        d3.select("#chart2").attr("visibility", "visible");
        subchart(this.parentElement.__data__.key, this.__data__.key);
        
    }
    var mouseleave = function(d) {
        d3.select("#chart2").attr("visibility", "hidden");   
    }

    d3.dsv(",", "state-year-earthquakes.csv", function(d) {
        return {
            state: d.state,
            region: d.region,
            year: +d.year,
            count: +d.count
        };
    }).then((data) => {

        var regions = 
            d3.nest()
            .key(function(d) { return d.region })
            .key(function(d) { return d.year })
            .sortKeys(d3.ascending)
            .rollup(function(v) { return d3.sum(v, function(d) { return d.count; }); })
            .entries(data);

        var colors = d3.scaleOrdinal(d3.schemeCategory10);
        var regionKeys = regions.map(function(d){return d.key;}).sort();
        
        yScale.domain([0 ,d3.max(regions.map(d => d3.max(d.values.map(n => n.value))))]);
        xScale.domain([d3.min((regions[0]).values.map(function(d) { return parseYear(+d.key); })),
            d3.max((regions[0]).values.map(function(d) { return parseYear(+d.key); }))]);

        var region = g.selectAll(".region")
        .data(regions)
        .enter().append("g")
        .attr("class", "region");

        region.append("path")
        .attr("class", "line")
        .attr("d", function(d) {
            return line(
                d.values
            );
        })
        .style("stroke", function(d) {
            return colors(regionKeys.indexOf(d.key));
        });

        region.append("g").selectAll("circle")
        .data(function(d){return d.values})
        .enter()
        .append("circle")
            .attr("r", 3)
            .attr("cx", function(dd){return xScale(parseYear(+dd.key))})
            .attr("cy", function(dd){return yScale(dd.value)})
            .attr("fill", function(d){return colors(regionKeys.indexOf(this.parentNode.__data__.key))})
            .attr("stroke", function(d){return colors(regionKeys.indexOf(this.parentNode.__data__.key))})
        .on("mouseover", mouseover)
        .on("mouseleave", mouseleave);;

        g.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(d3.axisBottom(xScale)
                .tickFormat(function(n) { return formatYear(n); })) ;

        g.append("g")
            .attr("class", "y axis")
            .call(d3.axisLeft(yScale));

            legend = g.append("g")
            .attr("class", "legend");

        legend.selectAll("g")
            .data(regionKeys)
            .enter()
            .append("circle")
                .attr("cx", 700)
                .attr("cy", function(d,i){ return 0 + i*15}) // 100 is where the first dot appears. 25 is the distance between dots
                .attr("r", 5)
                .style('fill', function(d) { return colors(regionKeys.indexOf(d)); });
        
            // Add one dot in the legend for each name.
        legend.selectAll("g")
            .data(regionKeys)
            .enter()
            .append("text")
                .attr("x", 710)
                .attr("y", function(d,i){ return 3 + i*15}) // 100 is where the first dot appears. 25 is the distance between dots
                .text(function(d){ return d})
                .attr("text-anchor", "left")
                .style("alignment-baseline", "middle");
                
        d3.select("#chart2").attr("visibility", "hidden");

    })
    .catch((error) => {
        throw error;
    });
};

function load_chart2(region, year) {
    var svg = d3.select("#chart2");
    margin = {top: 20, right: 20, bottom: 30, left: 80},
    width = +svg.attr("width") - margin.left - margin.right,
    height = +svg.attr("height") - margin.top - margin.bottom;

    var yScale = d3.scaleBand().rangeRound([0, height]),
        xScale = d3.scaleLinear().rangeRound([0, width]);

    var yAxis = d3.axisLeft(yScale);

    var g = svg.append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    g.append("text")
        .attr("x", (width / 2))             
        .attr("y", 0 - (margin.top / 2))
        .attr("text-anchor", "middle")  
        .style("font-size", "12px") 
        .attr("class", "subchart")
        .text(region + " Region Earthquakes " + year);

    var parseYear = d3.timeParse("%Y");
    var formatYear = d3.timeFormat("%Y");

    d3.dsv(",", "state-year-earthquakes.csv", function(d) {
        return {
            state: d.state,
            region: d.region,
            year: +d.year,
            count: +d.count
        };
    }).then((data) => {
        var filter = data.filter((function(d) { return d.region == region && d.year == year }));
        
        var regions = d3.nest()
            .key(function(d) { return d.state })
            .sortKeys(d3.descending)
            .rollup(function(v) { return d3.sum(v, function(d) { return d.count; }); })
            .entries(filter)
            .sort(function(a, b){ return d3.descending(a.value, b.value)});

        xScale.domain([0, d3.max(regions, function(d) { 
            return d.value; 
        })]);

        yScale.domain(regions.map(function(d) { 
            return d.key; 
        }))
        .paddingInner(0.1);

        var xAxisTicks = xScale.ticks()
            .filter(tick => Number.isInteger(tick));

        var xAxis = d3.axisBottom(xScale)
            .tickValues(xAxisTicks)
            .tickFormat(d3.format('d'));

        // grid lines in x axis function
        function xAxisLines() {		
            return d3.axisBottom(xScale)
            .tickValues(xAxisTicks);
        }
      
        g.append("g")
            .attr("class", "axis axis--x subchart")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxisLines()
                .tickSize(-height)
                .tickFormat(""));
            
            
        g.append("g")
            .attr("class", "axis axis--x subchart")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis);

        g.append("g")
            .attr("class", "axis axis--y subchart")
            .call(d3.axisLeft(yScale).ticks());
      
            g.selectAll(".bar")
                .data(regions)
              .enter().append("rect")
                .attr("class", "bar subchart")
                .attr("x", 0)
                .attr("y", function(d) { return yScale(d.key); })
                .attr("width", function(d) { return xScale(d.value); })
                .attr("height", function (d) {return height/regions.length/1.5})

    });

};