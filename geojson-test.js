// main.js – Tony Cannistra CSE512 Sp18


mapboxgl.accessToken = "pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4M29iazA2Z2gycXA4N2pmbDZmangifQ.-g_vE53SD2WrJ6tFX7QHmA";

var map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v9', 
});




map.on('load', function(x){
	map.fitBounds(new mapboxgl.LngLatBounds([-110.63,36.43],[-100.747,42.1094987784]));
	map.addSource('temp', {
	        "type": "geojson",
	        "data": "/notebooks/hour.geojson"
	});
	map.addLayer({
	  id: 'temp-heat',
	  type: 'heatmap',
	  source: 'temp',
	  maxzoom: 15,
	  paint: {
	    // increase weight as diameter breast height increases
	    'heatmap-weight': {
	      'property': 'To_Lizard',
	      'type': 'exponential', 
	      'stops' : [
	      	[-20, 8], 
	      	[-10, 6],
	      	[0, 3],
	      	[5, 0.1]
	      ]
	  	}
	  }
	})
});







