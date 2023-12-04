function load_heatmap() {
    var margin = {top: 80, right: 25, bottom: 100, left: 40},
        width = 800 - margin.left - margin.right,
        height = 400 - margin.top - margin.bottom;
    // append the svg object to the body of the page
    var svg = d3.select("#heatmap")
        .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
        .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    d3.dsv(",", "earthquakes.csv", function(d) {
        return {
            states: d.States,
            '2010': +d['2010'],
            '2011': +d['2011'],
            '2012': +d['2012'],
            '2013': +d['2013'],
            '2014': +d['2014'],
            '2015': +d['2015'],
            'category': d.Category      
        };
    }).then(
        (data) => {
            var categories = {};
            var states = {};
            var years = {};
            data.forEach( function(row) {
                // Loop through all of the columns, and for each column
                // make a new row
                Object.keys(row).forEach( function(colname) {
                    // Ignore 'State' and 'Value' columns
                    if(colname == "states" || colname == "category") {
                        return
                    }
                    if(!(row['category'] in categories)) {
                        categories[row['category']] = [];
                        states[row['category']] = []
                        years[row['category']] = []
                    }
                    categories[row['category']].push({"States": row["states"], "Value": row[colname], "Year": colname});
                    if(!states[row['category']].includes(row['states'])) {
                        states[row['category']].push(row['states']);
                    }
                    if(!years[row['category']].includes(colname)) {
                        years[row['category']].push(colname);
                    }
                });
            })
            data = categories
    
            var svgPos = document.getElementById("heatmap");

            // create location dropdown menu
            var categoryMenu = d3.select("#heatmap");
            categoryMenu
            .append("div")
            .attr("class", "select")
                .style("left", svgPos.offsetLeft + 200 + "px")
                .style("top", svgPos.offsetTop + 40 + "px")
            .append("select")
            .attr("id", "categoryMenu")
            .on('change',onchange)
            .selectAll("option")
                .data(Object.keys(categories).sort())
                .enter()
                .append("option")
                .attr("value", function(d) { return d; })
                .text(function(d) { return d; });

            function onchange() {
                categoryValue = d3.select('select').property('value')
                console.log('Category: ' + categoryValue)
                d3.selectAll(".chart").remove();
                drawCategory(categoryValue)
            }

            var tooltip = d3.select("#heatmap")
                .append("div")
                .style("opacity", 0)
                .attr("class", "tooltip")
                .style("background-color", "white")
                .style("padding", "5px")
                .style("left", svgPos.offsetLeft + 350 + "px")
                .style("top", svgPos.offsetTop + 40 + "px")
            
              // Three function that change the tooltip when user hover / move / leave a cell
            var mouseover = function(d) {
                tooltip
                    .style("opacity", 1)
                d3.select(this)
                    .style("stroke", "black")
                    .style("opacity", 1)
            }
            var mousemove = function(d) {
                tooltip
                    .html(d.States + " " +d.Year +": " + d.Value)
            }
            var mouseleave = function(d) {
                tooltip
                    .style("opacity", 0)
                d3.select(this)
                    .style("stroke", "none")
                    .style("opacity", 0.8)
            }

            var colorScheme = d3.schemeReds[9]
            // initialize the chart on 1st load
            drawCategory("0 to 9")

            function drawCategory(category) {

                // Build color scale
                var values = data[category].map(d => d.Value)
                var min = Math.min(...values);
                var max = Math.max(...values);
                
                var ranges = d3.scaleQuantile()
                    .domain([min, max])
                    .range([0,1,2,3,4,5,6,7,8]);

                var rangeValues = [Math.floor(min)].concat(ranges.quantiles().map(i => Math.ceil(i)));
            
                var myColor = d3.scaleQuantile()
                    .domain([min, max])
                    .range(colorScheme);

                // Add title to graph
                svg.append("text")
                    .attr("x", 80)
                    .attr("y", -50)
                    .attr("text-anchor", "left")
                    .style("font-size", "22px")
                    .text("Visualizing Earthquake Counts by State 2010-2015 (M3+)");

                // add name to legend
                svg.append("text")
                    .attr("x", 0)
                    .attr("y", 270)
                    .attr("text-anchor", "left")
                    .style("font-size", "12px")
                    .text("Count");
                    
                // Labels of row and columns
                var myGroups = states[category].sort();
                var myVars = years[category];
                // Build X scales and axis:
                var x = d3.scaleBand()
                    .range([0, width])
                    .domain(myGroups)
                    .padding(0.01);

                svg.append("g")
                    .attr("class", "chart")
                    .attr("transform", "translate(0," + height + ")")
                    .call(d3.axisBottom(x));

                // Build Y scales and axis:
                var y = d3.scaleBand()
                    .range([0, height])
                    .domain(myVars)
                    .padding(0.01);
                svg.append("g")
                    .attr("class", "chart")
                    .call(d3.axisLeft(y));
                
            
                // add the squares
                svg.selectAll()
                .data(data[category], function (d) {
                    return d.States + ':' + d.Year; 
                })
                .enter()
                .append("rect")
                    .attr("class", "chart")
                    .attr("x", function (d) { return x(d.States); })
                    .attr("y", function (d) { return y(d.Year); })
                    .attr("rx", 4)
                    .attr("ry", 4)
                    .attr("width", x.bandwidth())
                    .attr("height", y.bandwidth())
                    .style("fill", function (d) { return myColor(d.Value); })
                    .style("stroke-width", 4)
                    .style("stroke", "none")
                    .style("opacity", 0.8)
                .on("mouseover", mouseover)
                .on("mousemove", mousemove)
                .on("mouseleave", mouseleave);

                // add the legend
                // use ranges.invertExtent(x)[0] to get lower bound for myColors
                legend = svg.append("g")
                    .attr("class", "legend");
                    

                legend.selectAll("g")
                    .data(
                        colorScheme
                        )
                    .enter()
                    .append("rect")
                        .attr("class", "chart")
                        .attr("x", function(d,i){ return 0 + i*60;}) // 60 is the width of rects
                        .attr("y", 280)
                        .attr("width", 60)
                        .attr("height", 30)
                        .style('fill', function(d) {return d; })
                        .style("stroke-width", 4)
                        .style("stroke", "none")
                        .style("opacity", 0.8);

                // Add one dot in the legend for each name.
                legend.selectAll("g")
                    .data(rangeValues)
                    .enter()
                    .append("text")
                        .attr("class", "chart")
                        .attr("x", function(d,i){ return 0 + i*60}) // 100 is where the first dot appears. 25 is the distance between dots)
                        .attr("y", 320)
                        .text(function(d){ return d})
                        .attr("text-anchor", "left")
                        .style("alignment-baseline", "middle");
                
            }
        }
    );
}