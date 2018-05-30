// main.js – Tony Cannistra CSE512 Sp18


mapboxgl.accessToken = "pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4M29iazA2Z2gycXA4N2pmbDZmangifQ.-g_vE53SD2WrJ6tFX7QHmA";

var colorado_bounds = [
	[-110.63 , 36.43],
 	[-100.747, 42.1094987784]
];

var map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v9', 
    maxBounds: colorado_bounds
});



var timebrush_svgWidth = 900, timebrush_svgHeight = 100;
var timebrush_margin = { top: 10, right: 10, bottom: 20, left: 20 };
var timebrush_width = timebrush_svgWidth - timebrush_margin.left - timebrush_margin.right;
var timebrush_height = timebrush_svgHeight - timebrush_margin.top - timebrush_margin.bottom;

var timebrush = d3.select('#timebrush').append('svg')
     .attr("width", timebrush_svgWidth)
     .attr("height", timebrush_svgHeight);

var comma_formatter = d3.format(",.1f")

map.on('load', function(x){
	var img = d3.csv('notebooks/piltest.ref', function(d) {
		d = d.columns

		d3.json("notebooks/piltest.gif.geojson", (d) => d3.select(".large").select('tspan').text(comma_formatter(turf.area(d)/ 2589988.110336))) // square miles

		map.addSource('stress-poly-src', { type: 'geojson', data: "notebooks/piltest.gif.geojson" });

		
		map.addLayer({
			"id" : "stress-poly", 
			"type" : "fill", 
			"source": 'stress-poly-src',
			'paint': {
            'fill-color': 'red',
            'fill-opacity': 0.6}
		});

		map.addLayer({
			"id" : "temps",
			"type" : 'raster',
			'source' : {
				"type" : 'image', 
				"url"  : "notebooks/" + d[0],

				'coordinates' : [
					[parseFloat(d[1]), parseFloat(d[3])], // [top, left]
					[parseFloat(d[2]), parseFloat(d[3])], // [top, right]
					[parseFloat(d[2]), parseFloat(d[4])], // [bottom, right]
					[parseFloat(d[1]), parseFloat(d[4])]  // [bottom, left]
				]
			}, 
			'attribution' : "Buckley Lab",
			'paint' : {
				'raster-opacity' : 0.0
			}

		});

		// Adjustable Opacity

		d3.select("#opacity").on('input', function(){
			d3.select("#opacity-value").text(+this.value);
			map.setPaintProperty('temps', 'raster-opacity', +this.value / 100);

		})

		
		var parseDate = d3.timeParse("%b-%y");

		function datatype(d) {
		  console.log(d)
		  d.date = parseDate(d.date);
		  d.area = +d.area;
		  return d;
		}

		queue()
		    .defer(d3.csv, "data/fakearea.csv", datatype)
		    .await(drawTimeSlider);
		

	})

})


function loadNewData(dateString){
	var urlroot = "https://s3-us-west-2.amazonaws.com/stressviz/CO_all_273/"+dateString
	d3.csv(urlroot+".ref", function(d){
		d = d.columns
		d3.json(urlroot + ".geojson", function(geodata){
			d3.select(".large").select('tspan').text(comma_formatter(turf.area(geodata)/ 2589988.110336))
			map.getSource('stress-poly-src').setData(geodata)
		})

		map.removeLayer('temps');
		map.removeSource('temps');

		map.addLayer({
				"id" : "temps",
				"type" : 'raster',
				'source' : {
					"type" : 'image', 
					"url"  : urlroot + ".gif",

					'coordinates' : [
						[parseFloat(d[1]), parseFloat(d[3])], // [top, left]
						[parseFloat(d[2]), parseFloat(d[3])], // [top, right]
						[parseFloat(d[2]), parseFloat(d[4])], // [bottom, right]
						[parseFloat(d[1]), parseFloat(d[4])]  // [bottom, left]
					]
				}, 
				'attribution' : "Buckley Lab",
				'paint' : {
					'raster-opacity' : 0.0
				}

			});
	})

	
}


function drawTimeSlider(err, data){
	// inspration: https://bl.ocks.org/mbostock/3883245

	function brushed() {
	  if (d3.event.sourceEvent.type === "brush") return;
	  var d0 = d3.event.selection.map(x.invert),
	      d1 = d0.map(d3.timeDay.round);

	  function pad(n){return n<10 ? '0'+n : n}

	  var start = d1[0]
	  var dateString = pad(start.getFullYear()).toString() + pad(start.getMonth()).toString() + pad(start.getDate()).toString()
	  loadNewData(dateString)
	  // d3.select(this).call(d3.event.target.move, d1.map(x));

	}



	if (err) throw err; 



	var g = timebrush.append("g").attr("transform", 
      "translate(" + timebrush_margin.left + "," + timebrush_margin.top + ")"
   	);

   	var x = d3.scaleTime().rangeRound([0, timebrush_width]);
		x.domain(d3.extent(data, function(d) { return d.date; }));
	var y = d3.scaleLinear().rangeRound([timebrush_height, 0]);
	  	y.domain([0, d3.max(data, function(d) { return d.area; })]);



	// brushing code
	var brush = d3.brushX()
	    .extent([[0, 0], [timebrush_width, timebrush_height]])
	    .on("brush", brushed)


	var gb = timebrush.append("g")
	    .attr("class", "brush")
	    .call(brush)
	    .selectAll("rect")
	      .attr("y", -6)
    	  .attr("height", timebrush_height + 7);




	g.append("g")
	   .attr("transform", "translate(0," + timebrush_height + ")")
	   .call(d3.axisBottom(x))
	   .select(".domain")
	   .remove();

	var line = d3.line()
		.x(function(d) { return x(d.date); })
		.y(function(d) { return y(d.area); });

	g.append("path")
	.datum(data)
	.attr("fill", "none")
	.attr("stroke", "steelblue")
	.attr("stroke-linejoin", "round")
	.attr("stroke-linecap", "round")
	.attr("stroke-width", 1.5)
	.attr("d", line);

	g.append("g")
	  	.append("text")
	    .attr("fill", "#000")
	    .attr("transform", "rotate(-90)")
	    .attr("y", 9)
	    .attr("dy", "0.71em")
	    .attr("x", 0)
	    .attr("text-anchor", "end")
	    .attr("font-size", "10")
	    .text("Area (sq. mi)");




	// var line = d3.line()
	//    .x(function(d) { return x(d.date)})
	//    .y(function(d) { return y(d.value)})


}





