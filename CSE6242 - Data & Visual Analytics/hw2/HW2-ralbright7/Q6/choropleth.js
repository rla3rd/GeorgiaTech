function load_chart() {

    var states = d3.map();
    var earthquakes = d3.map();

    var promises = [
        d3.json("states-10m.json"),
        d3.csv("state-earthquakes.csv", function(d) {
            earthquakes.set(d.States, [d.States, d.Region, +d["Total Earthquakes"]])
        })
    ]
    
    Promise.all(promises).then(ready)

    function ready([us]) {
        console.log("in ready", topojson.feature(us, us.objects.states).features);

        var geo = us.objects.states.geometries;
        var keys = geo.map(d => d.id);
        var values = geo.map(d => d.properties.name)
        var states = {};
        keys.forEach((key, i) => states[key] = values[i]);

        var tip = d3.tip()
        .attr('class', 'd3-tip')
        .offset([5, 5])
        .html(function(d) {
            var row = earthquakes.get(d.properties.name);
            row;
            if (row) {
                return "State: "+row[0]+"<br>Region: "+row[1]+"<br>Earthquakes: " + row[2];
            } else {
                return d.properties.name + ": No data.";
            }
        });

        var svg = d3.select("svg"),
            width = +svg.attr("width"),
            height = +svg.attr("height");
        
        svg.call(tip);

        // D3 Projection
        var projection = d3.geoAlbersUsa()
        .translate([width/2, height/2])    // translate to center of screen
        .scale([1000]);          // scale things down so see entire US

        var path = d3.geoPath().projection(projection);

        var x = d3.scaleLinear()
            .domain([1, 10])
            .rangeRound([600, 860]);

        // this is equi-distant looping thru 10^x at specific steps
        // this breaks up our color groups on a log scale
        var eMax = 3.4
        var eStep = eMax/8;
        var thresholds = [];
        i=0;
        while(i < eMax)
        {
            thresholds.push(Math.ceil(Math.pow(10, i)));
            i += eStep;
        }

        // red color scheme
        var colorScheme = d3.schemeReds[9];

        var color = d3.scaleThreshold()
            .domain(thresholds)
            .range(colorScheme);

        // legend setup
        // push 0 on the front for the first color group
        legend = svg.append("g")
            .attr("class", "legend"); 

        legItemHt = 15;
        legendText = [...thresholds];
        legendText = [0].concat(legendText);
        legendText.pop();

        // legend colors
        legend.selectAll("g")
            .data(
                colorScheme
                )
            .enter()
            .append("rect")
                .attr("class", "chart")
                .attr("y", function(d,i){ return 400 + i*legItemHt;})
                .attr("x", 800)
                .attr("width", 20)
                .attr("height", legItemHt)
                .style('fill', function(d) {return d; })
                .style("stroke-width", 4)
                .style("stroke", "none")
                .style("opacity", 0.8);

        // legend text
        legend.selectAll("g")
            .data(legendText)
            .enter()
            .append("text")
                .attr("class", "chart")
                .attr("y", function(d,i){ return 410 + i*legItemHt}) 
                .attr("x", 825)
                .text(function(d){ return d})
                .attr("text-anchor", "left")
                .style("alignment-baseline", "middle");

        // legend title
        legend.append("text")
            .attr("class", "caption")
            .attr("x", 750)
            .attr("y", 390)
            .attr("fill", "#000")
            .attr("text-anchor", "start")
            .attr("font-weight", "bold")
            .text("Earthquake Frequency");

        // the states
        svg.append("g")
            .attr("class", "counties")
            .selectAll("path")
            .data(topojson.feature(us, us.objects.states).features)
            .enter().append("path")
            .on('mouseover', tip.show)
            .on('mouseout', tip.hide)
            .attr("fill", function(d) { 
                var sn = states[d.id];
                var eq = earthquakes.get(sn) || [d.properties.name, '', 0];
                d.count = eq[2];
                var col =  color(d.count); 
                if (col) {
                    return col;
                } else {
                    return '#ffffff';
                }
            })
            .attr("d", path);

        svg.append("path")
            .datum(topojson.mesh(us, us.objects.states, function(a, b) { return a !== b; }))
            .attr("class", "states")
            .attr("d", path);
    }
}