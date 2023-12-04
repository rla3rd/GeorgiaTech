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
        .text("Worldwide Earthquake stats 2000-2015");

    var parseYear = d3.timeParse("%Y");
    var formatYear = d3.timeFormat("%Y");

    var line = d3.line()
    .x(function(d) { return xScale(d.year); })
    .y(function(d) { return yScale(d.value); })
    .curve(d3.curveMonotoneX);

    d3.dsv(",", "earthquakes.csv", function(d) {
        return {
            'year': parseYear(+d.year),
            'nextYearTick': parseYear(+d.year + 2),
            '5_5.9': +d['5_5.9'],
            '6_6.9': +d['6_6.9'],
            '7_7.9': +d['7_7.9'],
            '8.0+': +d['8.0+'],
            'deaths': +d['Estimated Deaths']         
        };
    }).then((data) => {
        var keys = d3.keys(data[0]).filter(function(key) {
            return key !== "year" && key !== "deaths" && key !== "nextYearTick"});

        var colors = {'5_5.9': '#FFC300', '6_6.9': '#FF5733', '7_7.9': '#C70039', '8.0+': '#900C3F'};

        var quakes = keys.map(function(name) {
            return {
                name: name,
                values: data.map(function(d) {
                    return {
                        year: d['year'],
                        value: d[name]
                    };
                })
            };
        });
        
        var xmin = data[0].year;
        var xmax = data[data.length - 1].nextYearTick;
        var ticks = d3.timeYear.range(xmin, xmax, 2)
        xScale.domain([ticks[0], ticks[ticks.length-1]]);
        var ymax = d3.max(data, function(d) {
            return Math.max(d['5_5.9'], d['6_6.9'], d['7_7.9'], d['8.0+']); });
        yScale.domain([0, ymax]);

        var quake = g.selectAll(".quake")
        .data(quakes)
        .enter().append("g")
        .attr("class", "quake");

        quake.append("path")
        .attr("class", "line")
        .attr("d", function(d) {
            return line(d.values);
        })
        .style("stroke", function(d) {
            return colors[d.name];
        });

        g.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(d3.axisBottom(xScale)
                .tickValues(ticks)
                .tickFormat(function(n) { return formatYear(n); })) ;

        g.append("g")
            .attr("class", "y axis")
            .call(d3.axisLeft(yScale));

        legend = g.append("g")
            .attr("class", "legend");

        legend.selectAll("g")
            .data(keys)
            .enter()
            .append("circle")
                .attr("cx", 720)
                .attr("cy", function(d,i){ return 0 + i*25}) // 100 is where the first dot appears. 25 is the distance between dots
                .attr("r", 7)
                .style('fill', function(d) { return colors[d]; });
        
            // Add one dot in the legend for each name.
        legend.selectAll("g")
            .data(keys)
            .enter()
            .append("text")
                .attr("x", 735)
                .attr("y", function(d,i){ return 5 + i*25}) // 100 is where the first dot appears. 25 is the distance between dots
                .text(function(d){ return d})
                .attr("text-anchor", "left")
                .style("alignment-baseline", "middle");

    })
    .catch((error) => {
        throw error;
    });
};

function load_chart2() {
    var svg = d3.select("#chart2");
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
        .text("Worldwide Earthquake stats 2000-2015 with symbols");

    var parseYear = d3.timeParse("%Y");
    var formatYear = d3.timeFormat("%Y");

    var line = d3.line()
    .x(function(d) { return xScale(d.year); })
    .y(function(d) { return yScale(d.value); })
    .curve(d3.curveMonotoneX);

    d3.dsv(",", "earthquakes.csv", function(d) {
        return {
            'year': parseYear(+d.year),
            'nextYearTick': parseYear(+d.year + 2),
            '5_5.9': +d['5_5.9'],
            '6_6.9': +d['6_6.9'],
            '7_7.9': +d['7_7.9'],
            '8.0+': +d['8.0+'],
            'deaths': +d['Estimated Deaths']         
        };
    }).then((data) => {

        var deaths = data.map( function(d) { return d.deaths });
        var radius = d3.scaleSqrt().domain([0, Math.max(...deaths)]).range([3, 15]);
        var keys = d3.keys(data[0]).filter(function(key) {
            return key !== "year" && key !== "deaths" && key !== "nextYearTick"});

        var colors = {'5_5.9': '#FFC300', '6_6.9': '#FF5733', '7_7.9': '#C70039', '8.0+': '#900C3F'};

        var quakes = keys.map(function(name) {
            return {
                name: name,
                values: data.map(function(d) {
                    return {
                        year: d.year,
                        value: d[name],
                        deaths: d.deaths
                    };
                })
            };
        });
        
        var xmin = data[0].year;
        var xmax = data[data.length - 1].nextYearTick;
        var ticks = d3.timeYear.range(xmin, xmax, 2)
        xScale.domain([ticks[0], ticks[ticks.length-1]]);
        var ymax = d3.max(data, function(d) {
            return Math.max(d['5_5.9'], d['6_6.9'], d['7_7.9'], d['8.0+']); });
        yScale.domain([0, ymax]);

        var quake = g.selectAll(".quake")
        .data(quakes)
        .enter().append("g")
        .attr("class", "quake");

        quake.append("path")
        .attr("class", "line")
        .attr("d", function(d) {
            return line(d.values);
        })
        .style("stroke", function(d) {
            return colors[d.name];
        });

        quake.append("g").selectAll("circle")
        .data(function(d){return d.values})
        .enter()
        .append("circle")
        .attr("r", function(dd){return radius(dd.deaths)})
        .attr("cx", function(dd){return xScale(dd.year)})
        .attr("cy", function(dd){return yScale(dd.value)})
        .attr("fill", function(d){return colors[this.parentNode.__data__.name]})
        .attr("stroke", function(d){return colors[this.parentNode.__data__.name]});

        g.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(d3.axisBottom(xScale)
                .tickValues(ticks)
                .tickFormat(function(n) { return formatYear(n); })) ;

        g.append("g")
            .attr("class", "y axis")
            .call(d3.axisLeft(yScale));

        legend = g.append("g")
            .attr("class", "legend");

        legend.selectAll("g")
            .data(keys)
            .enter()
            .append("circle")
                .attr("cx", 720)
                .attr("cy", function(d,i){ return 0 + i*25}) // 100 is where the first dot appears. 25 is the distance between dots
                .attr("r", 7)
                .style('fill', function(d) { return colors[d]; });
        
            // Add one dot in the legend for each name.
        legend.selectAll("g")
            .data(keys)
            .enter()
            .append("text")
                .attr("x", 735)
                .attr("y", function(d,i){ return 5 + i*25}) // 100 is where the first dot appears. 25 is the distance between dots
                .text(function(d){ return d})
                .attr("text-anchor", "left")
                .style("alignment-baseline", "middle");

    })
    .catch((error) => {
        throw error;
    });
};

function load_chart3() {
    var svg = d3.select("#chart3");
    margin = {top: 20, right: 20, bottom: 30, left: 40},
    width = +svg.attr("width") - margin.left - margin.right,
    height = +svg.attr("height") - margin.top - margin.bottom;

    var xScale = d3.scaleTime().rangeRound([0, width]),
        yScale = d3.scaleSqrt().rangeRound([height, 0]);

    var g = svg.append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    g.append("text")
        .attr("x", (width / 2))             
        .attr("y", 0 - (margin.top / 2))
        .attr("text-anchor", "middle")  
        .style("font-size", "12px") 
        .text("Worldwide Earthquake stats 2000-2015 square root scale");

    var parseYear = d3.timeParse("%Y");
    var formatYear = d3.timeFormat("%Y");

    var line = d3.line()
    .x(function(d) { return xScale(d.year); })
    .y(function(d) { return yScale(d.value); })
    .curve(d3.curveMonotoneX);

    d3.dsv(",", "earthquakes.csv", function(d) {
        return {
            'year': parseYear(+d.year),
            'nextYearTick': parseYear(+d.year + 2),
            '5_5.9': +d['5_5.9'],
            '6_6.9': +d['6_6.9'],
            '7_7.9': +d['7_7.9'],
            '8.0+': +d['8.0+'],
            'deaths': +d['Estimated Deaths']         
        };
    }).then((data) => {

        var deaths = data.map( function(d) { return d.deaths });
        var radius = d3.scaleSqrt().domain([0, Math.max(...deaths)]).range([3, 15]);
        var keys = d3.keys(data[0]).filter(function(key) {
            return key !== "year" && key !== "deaths" && key !== "nextYearTick"});

        var colors = {'5_5.9': '#FFC300', '6_6.9': '#FF5733', '7_7.9': '#C70039', '8.0+': '#900C3F'};

        var quakes = keys.map(function(name) {
            return {
                name: name,
                values: data.map(function(d) {
                    return {
                        year: d.year,
                        value: d[name],
                        deaths: d.deaths
                    };
                })
            };
        });
        
        var xmin = data[0].year;
        var xmax = data[data.length - 1].nextYearTick;
        var ticks = d3.timeYear.range(xmin, xmax, 2)
        xScale.domain([ticks[0], ticks[ticks.length-1]]);
        var ymax = d3.max(data, function(d) {
            return Math.max(d['5_5.9'], d['6_6.9'], d['7_7.9'], d['8.0+']); });
        yScale.domain([0, ymax]);

        var quake = g.selectAll(".quake")
        .data(quakes)
        .enter().append("g")
        .attr("class", "quake");

        quake.append("path")
        .attr("class", "line")
        .attr("d", function(d) {
            return line(d.values);
        })
        .style("stroke", function(d) {
            return colors[d.name];
        });

        quake.append("g").selectAll("circle")
        .data(function(d){return d.values})
        .enter()
        .append("circle")
        .attr("r", function(dd){return radius(dd.deaths)})
        .attr("cx", function(dd){return xScale(dd.year)})
        .attr("cy", function(dd){return yScale(dd.value)})
        .attr("fill", function(d){return colors[this.parentNode.__data__.name]})
        .attr("stroke", function(d){return colors[this.parentNode.__data__.name]});

        g.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(d3.axisBottom(xScale)
                .tickValues(ticks)
                .tickFormat(function(n) { return formatYear(n); })) ;

        g.append("g")
            .attr("class", "y axis")
            .call(d3.axisLeft(yScale));

        legend = g.append("g")
            .attr("class", "legend");

        legend.selectAll("g")
            .data(keys)
            .enter()
            .append("circle")
                .attr("cx", 720)
                .attr("cy", function(d,i){ return 0 + i*25}) // 100 is where the first dot appears. 25 is the distance between dots
                .attr("r", 7)
                .style('fill', function(d) { return colors[d]; });
        
            // Add one dot in the legend for each name.
        legend.selectAll("g")
            .data(keys)
            .enter()
            .append("text")
                .attr("x", 735)
                .attr("y", function(d,i){ return 5 + i*25}) // 100 is where the first dot appears. 25 is the distance between dots
                .text(function(d){ return d})
                .attr("text-anchor", "left")
                .style("alignment-baseline", "middle");

    })
    .catch((error) => {
        throw error;
    });
};

function load_chart4() {
    var svg = d3.select("#chart4");
    margin = {top: 20, right: 20, bottom: 30, left: 40},
    width = +svg.attr("width") - margin.left - margin.right,
    height = +svg.attr("height") - margin.top - margin.bottom;

    var xScale = d3.scaleTime().rangeRound([0, width]),
        yScale = d3.scaleLog().clamp(true).rangeRound([height, 0]);

    var g = svg.append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    g.append("text")
        .attr("x", (width / 2))             
        .attr("y", 0 - (margin.top / 2))
        .attr("text-anchor", "middle")  
        .style("font-size", "12px") 
        .text("Worldwide Earthquake stats 2000-2015 log scale");

    var parseYear = d3.timeParse("%Y");
    var formatYear = d3.timeFormat("%Y");

    var line = d3.line()
    .x(function(d) { return xScale(d.year); })
    .y(function(d) { return yScale(d.value); })
    .curve(d3.curveMonotoneX);

    d3.dsv(",", "earthquakes.csv", function(d) {
        return {
            'year': parseYear(+d.year),
            'nextYearTick': parseYear(+d.year + 2),
            '5_5.9': +d['5_5.9'],
            '6_6.9': +d['6_6.9'],
            '7_7.9': +d['7_7.9'],
            '8.0+': +d['8.0+'],
            'deaths': +d['Estimated Deaths']         
        };
    }).then((data) => {

        var deaths = data.map( function(d) { return d.deaths });
        var radius = d3.scaleSqrt().domain([0, Math.max(...deaths)]).range([3, 15]);
        var keys = d3.keys(data[0]).filter(function(key) {
            return key !== "year" && key !== "deaths" && key !== "nextYearTick"});

        var colors = {'5_5.9': '#FFC300', '6_6.9': '#FF5733', '7_7.9': '#C70039', '8.0+': '#900C3F'};

        var quakes = keys.map(function(name) {
            return {
                name: name,
                values: data.map(function(d) {
                    return {
                        year: d.year,
                        value: d[name],
                        deaths: d.deaths
                    };
                })
            };
        });
        
        var xmin = data[0].year;
        var xmax = data[data.length - 1].nextYearTick;
        var ticks = d3.timeYear.range(xmin, xmax, 2)
        xScale.domain([ticks[0], ticks[ticks.length-1]]);
        var ymax = d3.max(data, function(d) {
            return Math.max(d['5_5.9'], d['6_6.9'], d['7_7.9'], d['8.0+']); });
        yScale.domain([0.5, ymax]).nice();

        var quake = g.selectAll(".quake")
        .data(quakes)
        .enter().append("g")
        .attr("class", "quake");

        quake.append("path")
        .attr("class", "line")
        .attr("d", function(d) {
            return line(d.values);
        })
        .style("stroke", function(d) {
            return colors[d.name];
        });

        quake.append("g").selectAll("circle")
        .data(function(d){return d.values})
        .enter()
        .append("circle")
        .attr("r", function(dd){return radius(dd.deaths)})
        .attr("cx", function(dd){return xScale(dd.year)})
        .attr("cy", function(dd){return yScale(dd.value)})
        .attr("fill", function(d){return colors[this.parentNode.__data__.name]})
        .attr("stroke", function(d){return colors[this.parentNode.__data__.name]});

        g.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(d3.axisBottom(xScale)
                .tickValues(ticks)
                .tickFormat(function(n) { return formatYear(n); })) ;

        g.append("g")
            .attr("class", "y axis")
            .call(d3.axisLeft(yScale));

        legend = g.append("g")
            .attr("class", "legend");

        legend.selectAll("g")
            .data(keys)
            .enter()
            .append("circle")
                .attr("cx", 720)
                .attr("cy", function(d,i){ return 0 + i*25}) // 100 is where the first dot appears. 25 is the distance between dots
                .attr("r", 7)
                .style('fill', function(d) { return colors[d]; });
        
            // Add one dot in the legend for each name.
        legend.selectAll("g")
            .data(keys)
            .enter()
            .append("text")
                .attr("x", 735)
                .attr("y", function(d,i){ return 5 + i*25}) // 100 is where the first dot appears. 25 is the distance between dots
                .text(function(d){ return d})
                .attr("text-anchor", "left")
                .style("alignment-baseline", "middle");

    })
    .catch((error) => {
        throw error;
    });
};