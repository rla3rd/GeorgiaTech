function load_chart() {
    var svg = d3.select("svg"),
        margin = {top: 20, right: 20, bottom: 30, left: 40},
        width = +svg.attr("width") - margin.left - margin.right,
        height = +svg.attr("height") - margin.top - margin.bottom;

    var x = d3.scaleTime().rangeRound([0, width]),
        y = d3.scaleLinear().rangeRound([height, 0]);

    var g = svg.append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    g.append("text")
        .attr("x", (width / 2))             
        .attr("y", 0 - (margin.top / 2))
        .attr("text-anchor", "middle")  
        .style("font-size", "12px") 
        .text("Lego Sets by Year from Rebrickable");

        g.append("text")
        .attr("x", (width - 30))             
        .attr("y", (height + 25))
        .attr("text-anchor", "right")  
        .style("font-size", "10px") 
        .text("ralbright7");

    var parseYear = d3.timeParse("%Y");
    var formatYear = d3.timeFormat("%Y");

    d3.dsv(",", "Q3.csv", function(d) {
        return {
            year: parseYear(+d.year),
            nextYearTick: parseYear(+d.year + 3),
            running_total: +d.running_total 
        };
    }).then((data) => {
        var xmin = data[0].year;
        var xmax = data[data.length - 1].nextYearTick;
        var ticks = d3.timeYear.range(xmin, xmax, 3)
        x.domain([ticks[0], ticks[ticks.length-1]]);
        y.domain([0, d3.max(data, function(d) { return d.running_total; })]);
       
        g.append("g")
            .attr("class", "axis axis--x")
            .attr("transform", "translate(0," + height + ")")
            .call(d3.axisBottom(x)
                .tickValues(ticks)
                .tickFormat(function(n) { return formatYear(n); })) ;

        g.append("g")
            .attr("class", "axis axis--y")
            .call(d3.axisLeft(y).ticks());
            
        g.selectAll(".bar")
            .data(data)
            .enter().append("rect")
                .attr("class", "bar")
                .attr("x", function(d) { return x(d.year); })
                .attr("y", function(d) { return y(d.running_total); })
                .attr("width", width/data.length/1.5)
                .attr("height", function(d) { return height - y(d.running_total); });
        })
        .catch((error) => {
                throw error;
        });
    
};