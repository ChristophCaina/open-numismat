import json
import urllib.request

from OpenNumismat import version
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from .MapWidget import BaseMapWidget

mapboxAvailable = True

try:
    from OpenNumismat.private_keys import MAPBOX_ACCESS_TOKEN
except ImportError:
    mapboxAvailable = False


class MapboxWidget(BaseMapWidget):
    HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no"/>
    <link href="https://api.mapbox.com/mapbox-gl-js/v3.9.3/mapbox-gl.css" rel="stylesheet">
    <script src="https://api.mapbox.com/mapbox-gl-js/v3.9.3/mapbox-gl.js"></script>
    <script src='https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-language/v1.0.0/mapbox-gl-language.js'></script>
    <style type="text/css">
        html {
            height: 100%;
        }
        body {
            height: 100%;
            margin: 0;
            padding: 0
        }
        #map {
            height: 100%
        }
        .marker {
            display: block;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            padding: 0;
        }
        .mapboxgl-marker {
            cursor: pointer;
        }
    </style>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
var map;
var marker = null;
var markers = [];

function onload() {
  if (typeof qtWidget !== 'undefined') {
    initialize();
  }
  else {
    new QWebChannel(qt.webChannelTransport, function(channel) {
      window.qtWidget = channel.objects.qtWidget;
      initialize();
    });
  }
}

function initialize() {
  mapboxgl.accessToken = 'ACCESS_TOKEN';
  map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v12',
    center: [LONGITUDE, LATITUDE],
    minZoom: 1,
    zoom: ZOOM
  });
  const nav = new mapboxgl.NavigationControl({showCompass: false});
  map.addControl(nav);
  map.addControl(new MapboxLanguage());

  map.on('moveend', function (e) {
    var center = map.getCenter();
    qtWidget.mapIsMoved(center.lat, center.lng);
  });
  map.on('zoomend', function() {
    zoom = map.getZoom();
    qtWidget.mapIsZoomed(zoom);
  });
  map.on('click', function (ev) {
    if (marker === null) {
      lat = ev.lngLat.lat;
      lng = ev.lngLat.lng;
      qtWidget.mapIsClicked(lat, lng)
    }
  });

  qtWidget.mapIsReady();
}

function gmap_addMarker(lat, lng) {
  marker = new mapboxgl.Marker({draggable: DRAGGABLE}).setLngLat([lng, lat]).addTo(map);

  marker.on('dragend', function () {
    position = marker.getLngLat();
    qtWidget.markerIsMoved(position.lat, position.lng, true);
  });
  marker.getElement().addEventListener('click', () => {
    position = marker.getLngLat();
    qtWidget.markerIsMoved(position.lat, position.lng, true);
  });
  marker.getElement().addEventListener('contextmenu', () => {
    qtWidget.markerIsRemoved();
    gmap_deleteMarker();
  });
}
function gmap_deleteMarker() {
  marker.remove();
  delete marker;
  marker = null;
}
function gmap_moveMarker(lat, lng) {
  if (marker === null) {
    gmap_addMarker(lat, lng);
  }
  else {
    marker.setLngLat([lng, lat]);
  }
  map.panTo([lng, lat]);
}
function gmap_addStaticMarker(lat, lng, coin_id, status) {
  const el = document.createElement('div');
  el.className = 'marker';
  el.style.backgroundImage = `url(qrc:/${status}.png)`;
  el.style.width = '16px';
  el.style.height = '16px';
  el.style.backgroundSize = '100%';
  el.addEventListener('click', () => {
    qtWidget.markerIsClicked(marker.coin_id);
  });

  var marker = new mapboxgl.Marker(el).setLngLat([lng, lat]).addTo(map);
  marker.coin_id = coin_id;

  markers.push(marker);
}
function gmap_clearStaticMarkers() {
  for (var i = 0; i < markers.length; i++ ) {
    markers[i].remove();
  }
  markers.length = 0;
}
function gmap_fitBounds() {
  var bounds = new mapboxgl.LngLatBounds();
  for (var i = 0; i < markers.length; i++) {
    bounds.extend(markers[i].getLngLat());
  }
  map.fitBounds(bounds, {maxZoom: 15, padding: 50});
}
function gmap_geocode(address) {
  url = "https://api.mapbox.com/search/geocode/v6/forward?q=" + address + "&access_token=ACCESS_TOKEN";
  var xmlHttp = new XMLHttpRequest();
  xmlHttp.open("GET", url, false);
  xmlHttp.send(null);
  if (xmlHttp.status == 200) {
      results = JSON.parse(xmlHttp.responseText);
      if (results['features'].length > 0) {
        coordinates = results['features'][0]['geometry']['coordinates']
        lat = parseFloat(coordinates[1]);
        lng = parseFloat(coordinates[0]);
        gmap_moveMarker(lat, lng);
        qtWidget.markerIsMoved(lat, lng, false);
      }
  }
}
    </script>
</head>
<body onload="onload()">
<div id="map"></div>
</body>
</html>
'''

    def _getParams(self):
        params = super()._getParams()
        params['ACCESS_TOKEN'] = MAPBOX_ACCESS_TOKEN
        return params

    @waitCursorDecorator
    def reverseGeocode(self, lat, lng):
        url = "https://api.mapbox.com/search/geocode/v6/reverse?longitude=%f&latitude=%f&access_token=%s&language=%s&types=country,region,district,place,address" % (lng, lat, MAPBOX_ACCESS_TOKEN, self.language)

        try:
            req = urllib.request.Request(url,
                                         headers={'User-Agent': version.AppName})
            data = urllib.request.urlopen(req, timeout=10).read()
            json_data = json.loads(data.decode())
            return json_data['features'][0]['properties']['full_address']
        except:
            return ''
