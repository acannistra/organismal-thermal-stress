// main.js – Tony Cannistra CSE512 Sp18


mapboxgl.accessToken = "pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4M29iazA2Z2gycXA4N2pmbDZmangifQ.-g_vE53SD2WrJ6tFX7QHmA";

var map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v9', 
});




map.on('load', function(x){
	map.fitBounds(new mapboxgl.LngLatBounds([-110.63,36.43],[-100.747,42.1094987784]));
	var img = d3.csv('../notebooks/piltest.ref', function(d) {
		console.log(d)
		d = d.columns

		map.addLayer({
			"id" : "temps",
			"type" : 'raster',
			'source' : {
				"type" : 'image', 
				"url"  : "../notebooks/" + d[0],

				'coordinates' : [
					[parseFloat(d[1]), parseFloat(d[4])], // [top, left]
					[parseFloat(d[2]), parseFloat(d[4])], // [top, right]
					[parseFloat(d[2]), parseFloat(d[3])], // [bottom, right]
					[parseFloat(d[1]), parseFloat(d[3])]  // [bottom, left]
				]
			}, 
			'attribution' : "Buckley Lab",
			"style" : {
				'raster-opacity' : 0.85,
			}
		});

		d3.select("#opacity").on('input', function(){
			d3.select("#opacity-value").text(+this.value);
			map.setPaintProperty('temps', 'raster-opacity', +this.value / 100);

		})

	})

})






