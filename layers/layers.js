var wms_layers = [];


        var lyr_Voyagerretina_0 = new ol.layer.Tile({
            'title': 'Voyager (retina)',
            'type':'base',
            'opacity': 1.000000,
            
            
            source: new ol.source.XYZ({
            attributions: '&nbsp;&middot; <a href="https://cartodb.com/basemaps/">Map tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.</a>',
                url: 'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png'
            })
        });

        var lyr_Positronretina_1 = new ol.layer.Tile({
            'title': 'Positron (retina)',
            'type':'base',
            'opacity': 1.000000,
            
            
            source: new ol.source.XYZ({
            attributions: '&nbsp;&middot; <a href="https://cartodb.com/basemaps/">Map tiles by CartoDB, under CC BY 3.0. Data by OpenStreetMap, under ODbL.</a>',
                url: 'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png'
            })
        });
var format_SampleRide_2 = new ol.format.GeoJSON();
var features_SampleRide_2 = format_SampleRide_2.readFeatures(json_SampleRide_2, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_SampleRide_2 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_SampleRide_2.addFeatures(features_SampleRide_2);
var lyr_SampleRide_2 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_SampleRide_2, 
                style: style_SampleRide_2,
                popuplayertitle: 'Sample Ride',
                interactive: false,
                title: '<img src="styles/legend/SampleRide_2.png" /> Sample Ride'
            });
var format_SampleRideBuffer_3 = new ol.format.GeoJSON();
var features_SampleRideBuffer_3 = format_SampleRideBuffer_3.readFeatures(json_SampleRideBuffer_3, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_SampleRideBuffer_3 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_SampleRideBuffer_3.addFeatures(features_SampleRideBuffer_3);
var lyr_SampleRideBuffer_3 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_SampleRideBuffer_3, 
                style: style_SampleRideBuffer_3,
                popuplayertitle: 'Sample Ride Buffer',
                interactive: true,
                title: '<img src="styles/legend/SampleRideBuffer_3.png" /> Sample Ride Buffer'
            });
var format_MatchedSegments_4 = new ol.format.GeoJSON();
var features_MatchedSegments_4 = format_MatchedSegments_4.readFeatures(json_MatchedSegments_4, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_MatchedSegments_4 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_MatchedSegments_4.addFeatures(features_MatchedSegments_4);
var lyr_MatchedSegments_4 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_MatchedSegments_4, 
                style: style_MatchedSegments_4,
                popuplayertitle: 'Matched Segments',
                interactive: true,
                title: '<img src="styles/legend/MatchedSegments_4.png" /> Matched Segments'
            });
var format_MatchedNodes_5 = new ol.format.GeoJSON();
var features_MatchedNodes_5 = format_MatchedNodes_5.readFeatures(json_MatchedNodes_5, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_MatchedNodes_5 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_MatchedNodes_5.addFeatures(features_MatchedNodes_5);
var lyr_MatchedNodes_5 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_MatchedNodes_5, 
                style: style_MatchedNodes_5,
                popuplayertitle: 'Matched Nodes',
                interactive: true,
                title: '<img src="styles/legend/MatchedNodes_5.png" /> Matched Nodes'
            });
var format_ExampleSegments_6 = new ol.format.GeoJSON();
var features_ExampleSegments_6 = format_ExampleSegments_6.readFeatures(json_ExampleSegments_6, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_ExampleSegments_6 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_ExampleSegments_6.addFeatures(features_ExampleSegments_6);
var lyr_ExampleSegments_6 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_ExampleSegments_6, 
                style: style_ExampleSegments_6,
                popuplayertitle: 'Example Segments',
                interactive: true,
                title: '<img src="styles/legend/ExampleSegments_6.png" /> Example Segments'
            });
var format_ExampleIntersections_7 = new ol.format.GeoJSON();
var features_ExampleIntersections_7 = format_ExampleIntersections_7.readFeatures(json_ExampleIntersections_7, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_ExampleIntersections_7 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_ExampleIntersections_7.addFeatures(features_ExampleIntersections_7);
var lyr_ExampleIntersections_7 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_ExampleIntersections_7, 
                style: style_ExampleIntersections_7,
                popuplayertitle: 'Example Intersections',
                interactive: true,
                title: '<img src="styles/legend/ExampleIntersections_7.png" /> Example Intersections'
            });
var group_Example = new ol.layer.Group({
                                layers: [lyr_ExampleSegments_6,lyr_ExampleIntersections_7,],
                                fold: 'open',
                                title: 'Example'});
var group_OutputLayers = new ol.layer.Group({
                                layers: [lyr_MatchedSegments_4,lyr_MatchedNodes_5,],
                                fold: 'open',
                                title: 'Output Layers'});
var group_IntermediateResults = new ol.layer.Group({
                                layers: [lyr_SampleRideBuffer_3,],
                                fold: 'open',
                                title: 'Intermediate Results'});
var group_InputLayers = new ol.layer.Group({
                                layers: [lyr_SampleRide_2,],
                                fold: 'open',
                                title: 'Input Layers'});

lyr_Voyagerretina_0.setVisible(false);lyr_Positronretina_1.setVisible(true);lyr_SampleRide_2.setVisible(true);lyr_SampleRideBuffer_3.setVisible(false);lyr_MatchedSegments_4.setVisible(true);lyr_MatchedNodes_5.setVisible(true);lyr_ExampleSegments_6.setVisible(true);lyr_ExampleIntersections_7.setVisible(true);
var layersList = [lyr_Voyagerretina_0,lyr_Positronretina_1,group_InputLayers,group_IntermediateResults,group_OutputLayers,group_Example];
lyr_SampleRide_2.set('fieldAliases', {'name': 'name', 'cmt': 'cmt', 'desc': 'desc', 'src': 'src', 'link1_href': 'link1_href', 'link1_text': 'link1_text', 'link1_type': 'link1_type', 'link2_href': 'link2_href', 'link2_text': 'link2_text', 'link2_type': 'link2_type', 'number': 'number', 'type': 'type', });
lyr_SampleRideBuffer_3.set('fieldAliases', {'name': 'name', 'cmt': 'cmt', 'desc': 'desc', 'src': 'src', 'link1_href': 'link1_href', 'link1_text': 'link1_text', 'link1_type': 'link1_type', 'link2_href': 'link2_href', 'link2_text': 'link2_text', 'link2_type': 'link2_type', 'number': 'number', 'type': 'type', });
lyr_MatchedSegments_4.set('fieldAliases', {'fid': 'fid', 'osm_id': 'osm_id', 'name': 'name', 'type': 'type', 'other_tags': 'other_tags', 'segment': 'segment', 'segment_length': 'segment_length', 'intersection_length': 'intersection_length', 'intersection_percentage': 'intersection_percentage', });
lyr_MatchedNodes_5.set('fieldAliases', {'fid': 'fid', 'osm_id': 'osm_id', 'name': 'name', 'barrier': 'barrier', 'highway': 'highway', 'ref': 'ref', 'address': 'address', 'is_in': 'is_in', 'place': 'place', 'man_made': 'man_made', 'other_tags': 'other_tags', 'node': 'node', 'osm_id_2': 'osm_id_2', });
lyr_ExampleSegments_6.set('fieldAliases', {'fid': 'fid', 'osm_id': 'osm_id', 'name': 'name', 'type': 'type', 'other_tags': 'other_tags', 'segment': 'segment', 'segment_length': 'segment_length', });
lyr_ExampleIntersections_7.set('fieldAliases', {'osm_id': 'osm_id', 'segment_length': 'segment_length', 'name': 'name', 'intersection_length': 'intersection_length', 'intersection_percentage': 'intersection_percentage', 'flag_match': 'flag_match', });
lyr_SampleRide_2.set('fieldImages', {'name': 'TextEdit', 'cmt': 'TextEdit', 'desc': 'TextEdit', 'src': 'TextEdit', 'link1_href': 'TextEdit', 'link1_text': 'TextEdit', 'link1_type': 'TextEdit', 'link2_href': 'TextEdit', 'link2_text': 'TextEdit', 'link2_type': 'TextEdit', 'number': 'TextEdit', 'type': 'TextEdit', });
lyr_SampleRideBuffer_3.set('fieldImages', {'name': 'TextEdit', 'cmt': 'TextEdit', 'desc': 'TextEdit', 'src': 'TextEdit', 'link1_href': 'TextEdit', 'link1_text': 'TextEdit', 'link1_type': 'TextEdit', 'link2_href': 'TextEdit', 'link2_text': 'TextEdit', 'link2_type': 'TextEdit', 'number': 'TextEdit', 'type': 'TextEdit', });
lyr_MatchedSegments_4.set('fieldImages', {'fid': 'Range', 'osm_id': 'TextEdit', 'name': 'TextEdit', 'type': 'TextEdit', 'other_tags': 'TextEdit', 'segment': 'TextEdit', 'segment_length': 'TextEdit', 'intersection_length': 'TextEdit', 'intersection_percentage': 'TextEdit', });
lyr_MatchedNodes_5.set('fieldImages', {'fid': 'Range', 'osm_id': 'TextEdit', 'name': 'TextEdit', 'barrier': 'TextEdit', 'highway': 'TextEdit', 'ref': 'TextEdit', 'address': 'TextEdit', 'is_in': 'TextEdit', 'place': 'TextEdit', 'man_made': 'TextEdit', 'other_tags': 'TextEdit', 'node': 'Range', 'osm_id_2': 'TextEdit', });
lyr_ExampleSegments_6.set('fieldImages', {'fid': 'Range', 'osm_id': 'TextEdit', 'name': 'TextEdit', 'type': 'TextEdit', 'other_tags': 'TextEdit', 'segment': 'TextEdit', 'segment_length': 'TextEdit', });
lyr_ExampleIntersections_7.set('fieldImages', {'osm_id': 'TextEdit', 'segment_length': 'TextEdit', 'name': 'TextEdit', 'intersection_length': 'TextEdit', 'intersection_percentage': 'TextEdit', 'flag_match': 'Range', });
lyr_SampleRide_2.set('fieldLabels', {'name': 'hidden field', 'cmt': 'hidden field', 'desc': 'hidden field', 'src': 'hidden field', 'link1_href': 'hidden field', 'link1_text': 'hidden field', 'link1_type': 'hidden field', 'link2_href': 'hidden field', 'link2_text': 'hidden field', 'link2_type': 'hidden field', 'number': 'hidden field', 'type': 'hidden field', });
lyr_SampleRideBuffer_3.set('fieldLabels', {'name': 'no label', 'cmt': 'no label', 'desc': 'no label', 'src': 'no label', 'link1_href': 'no label', 'link1_text': 'no label', 'link1_type': 'no label', 'link2_href': 'no label', 'link2_text': 'no label', 'link2_type': 'no label', 'number': 'no label', 'type': 'no label', });
lyr_MatchedSegments_4.set('fieldLabels', {'fid': 'hidden field', 'osm_id': 'hidden field', 'name': 'hidden field', 'type': 'hidden field', 'other_tags': 'hidden field', 'segment': 'inline label - always visible', 'segment_length': 'inline label - always visible', 'intersection_length': 'inline label - always visible', 'intersection_percentage': 'inline label - always visible', });
lyr_MatchedNodes_5.set('fieldLabels', {'fid': 'hidden field', 'osm_id': 'hidden field', 'name': 'hidden field', 'barrier': 'hidden field', 'highway': 'hidden field', 'ref': 'hidden field', 'address': 'hidden field', 'is_in': 'hidden field', 'place': 'hidden field', 'man_made': 'hidden field', 'other_tags': 'hidden field', 'node': 'inline label - visible with data', 'osm_id_2': 'hidden field', });
lyr_ExampleSegments_6.set('fieldLabels', {'fid': 'hidden field', 'osm_id': 'inline label - always visible', 'name': 'hidden field', 'type': 'hidden field', 'other_tags': 'hidden field', 'segment': 'inline label - always visible', 'segment_length': 'inline label - visible with data', });
lyr_ExampleIntersections_7.set('fieldLabels', {'osm_id': 'inline label - always visible', 'segment_length': 'inline label - always visible', 'name': 'hidden field', 'intersection_length': 'inline label - always visible', 'intersection_percentage': 'inline label - always visible', 'flag_match': 'hidden field', });
lyr_ExampleIntersections_7.on('precompose', function(evt) {
    evt.context.globalCompositeOperation = 'normal';
});