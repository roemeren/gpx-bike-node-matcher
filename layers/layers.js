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
var format_TrackBuffer20m_2 = new ol.format.GeoJSON();
var features_TrackBuffer20m_2 = format_TrackBuffer20m_2.readFeatures(json_TrackBuffer20m_2, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_TrackBuffer20m_2 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_TrackBuffer20m_2.addFeatures(features_TrackBuffer20m_2);
var lyr_TrackBuffer20m_2 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_TrackBuffer20m_2, 
                style: style_TrackBuffer20m_2,
                popuplayertitle: 'Track Buffer (20 m)',
                interactive: false,
                title: '<img src="styles/legend/TrackBuffer20m_2.png" /> Track Buffer (20 m)'
            });
var format_GPSTrack_3 = new ol.format.GeoJSON();
var features_GPSTrack_3 = format_GPSTrack_3.readFeatures(json_GPSTrack_3, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_GPSTrack_3 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_GPSTrack_3.addFeatures(features_GPSTrack_3);
var lyr_GPSTrack_3 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_GPSTrack_3, 
                style: style_GPSTrack_3,
                popuplayertitle: 'GPS Track',
                interactive: true,
                title: '<img src="styles/legend/GPSTrack_3.png" /> GPS Track'
            });
var format_NetworkLines_4 = new ol.format.GeoJSON();
var features_NetworkLines_4 = format_NetworkLines_4.readFeatures(json_NetworkLines_4, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_NetworkLines_4 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_NetworkLines_4.addFeatures(features_NetworkLines_4);
var lyr_NetworkLines_4 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_NetworkLines_4, 
                style: style_NetworkLines_4,
                popuplayertitle: 'Network Lines',
                interactive: true,
                title: '<img src="styles/legend/NetworkLines_4.png" /> Network Lines'
            });
var format_NetworkNodes_5 = new ol.format.GeoJSON();
var features_NetworkNodes_5 = format_NetworkNodes_5.readFeatures(json_NetworkNodes_5, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_NetworkNodes_5 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_NetworkNodes_5.addFeatures(features_NetworkNodes_5);
var lyr_NetworkNodes_5 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_NetworkNodes_5,
maxResolution:70.0111653806549,
 
                style: style_NetworkNodes_5,
                popuplayertitle: 'Network Nodes',
                interactive: true,
                title: '<img src="styles/legend/NetworkNodes_5.png" /> Network Nodes'
            });
var format_Intersections_6 = new ol.format.GeoJSON();
var features_Intersections_6 = format_Intersections_6.readFeatures(json_Intersections_6, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_Intersections_6 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_Intersections_6.addFeatures(features_Intersections_6);
var lyr_Intersections_6 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_Intersections_6, 
                style: style_Intersections_6,
                popuplayertitle: 'Intersections',
                interactive: false,
                title: '<img src="styles/legend/Intersections_6.png" /> Intersections'
            });
var format_SegmentMatching_7 = new ol.format.GeoJSON();
var features_SegmentMatching_7 = format_SegmentMatching_7.readFeatures(json_SegmentMatching_7, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_SegmentMatching_7 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_SegmentMatching_7.addFeatures(features_SegmentMatching_7);
var lyr_SegmentMatching_7 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_SegmentMatching_7, 
                style: style_SegmentMatching_7,
                popuplayertitle: 'Segment Matching',
                interactive: true,
    title: 'Segment Matching<br />\
    <img src="styles/legend/SegmentMatching_7_0.png" /> Not Matched<br />\
    <img src="styles/legend/SegmentMatching_7_1.png" /> Matched<br />' });
var format_MatchedSegments_8 = new ol.format.GeoJSON();
var features_MatchedSegments_8 = format_MatchedSegments_8.readFeatures(json_MatchedSegments_8, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_MatchedSegments_8 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_MatchedSegments_8.addFeatures(features_MatchedSegments_8);
var lyr_MatchedSegments_8 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_MatchedSegments_8, 
                style: style_MatchedSegments_8,
                popuplayertitle: 'Matched Segments',
                interactive: true,
                title: '<img src="styles/legend/MatchedSegments_8.png" /> Matched Segments'
            });
var format_MatchedNodes_9 = new ol.format.GeoJSON();
var features_MatchedNodes_9 = format_MatchedNodes_9.readFeatures(json_MatchedNodes_9, 
            {dataProjection: 'EPSG:4326', featureProjection: 'EPSG:3857'});
var jsonSource_MatchedNodes_9 = new ol.source.Vector({
    attributions: ' ',
});
jsonSource_MatchedNodes_9.addFeatures(features_MatchedNodes_9);
var lyr_MatchedNodes_9 = new ol.layer.Vector({
                declutter: false,
                source:jsonSource_MatchedNodes_9, 
                style: style_MatchedNodes_9,
                popuplayertitle: 'Matched Nodes',
                interactive: true,
                title: '<img src="styles/legend/MatchedNodes_9.png" /> Matched Nodes'
            });
var group_Match = new ol.layer.Group({
                                layers: [lyr_MatchedSegments_8,lyr_MatchedNodes_9,],
                                fold: 'open',
                                title: 'Match'});
var group_Network = new ol.layer.Group({
                                layers: [lyr_NetworkLines_4,lyr_NetworkNodes_5,],
                                fold: 'open',
                                title: 'Network'});

lyr_Voyagerretina_0.setVisible(false);lyr_Positronretina_1.setVisible(true);lyr_TrackBuffer20m_2.setVisible(false);lyr_GPSTrack_3.setVisible(true);lyr_NetworkLines_4.setVisible(false);lyr_NetworkNodes_5.setVisible(false);lyr_Intersections_6.setVisible(false);lyr_SegmentMatching_7.setVisible(false);lyr_MatchedSegments_8.setVisible(false);lyr_MatchedNodes_9.setVisible(false);
var layersList = [lyr_Voyagerretina_0,lyr_Positronretina_1,lyr_TrackBuffer20m_2,lyr_GPSTrack_3,group_Network,lyr_Intersections_6,lyr_SegmentMatching_7,group_Match];
lyr_TrackBuffer20m_2.set('fieldAliases', {'name': 'name', 'cmt': 'cmt', 'desc': 'desc', 'src': 'src', 'link1_href': 'link1_href', 'link1_text': 'link1_text', 'link1_type': 'link1_type', 'link2_href': 'link2_href', 'link2_text': 'link2_text', 'link2_type': 'link2_type', 'number': 'number', 'type': 'type', });
lyr_GPSTrack_3.set('fieldAliases', {'name': 'name', 'cmt': 'cmt', 'desc': 'desc', 'src': 'src', 'link1_href': 'link1_href', 'link1_text': 'link1_text', 'link1_type': 'link1_type', 'link2_href': 'link2_href', 'link2_text': 'link2_text', 'link2_type': 'link2_type', 'number': 'number', 'type': 'type', 'track_length': 'track_length', });
lyr_NetworkLines_4.set('fieldAliases', {'fid': 'fid', 'osm_id': 'osm_id', 'name': 'name', 'type': 'type', 'other_tags': 'other_tags', 'segment': 'segment', });
lyr_NetworkNodes_5.set('fieldAliases', {'fid': 'fid', 'osm_id': 'osm_id', 'name': 'name', 'barrier': 'barrier', 'highway': 'highway', 'ref': 'ref', 'address': 'address', 'is_in': 'is_in', 'place': 'place', 'man_made': 'man_made', 'other_tags': 'other_tags', 'node': 'node', });
lyr_Intersections_6.set('fieldAliases', {'osm_id': 'osm_id', 'segment_length': 'segment_length', 'name': 'name', 'intersection_length': 'intersection_length', 'intersection_percentage': 'intersection_percentage', 'flag_match': 'flag_match', });
lyr_SegmentMatching_7.set('fieldAliases', {'fid': 'fid', 'osm_id': 'osm_id', 'name': 'name', 'type': 'type', 'other_tags': 'other_tags', 'segment': 'segment', 'segment_length': 'segment_length', 'intersection_length': 'intersection_length', 'intersection_percentage': 'intersection_percentage', 'flag_match': 'flag_match', });
lyr_MatchedSegments_8.set('fieldAliases', {'fid': 'fid', 'osm_id': 'osm_id', 'name': 'name', 'type': 'type', 'other_tags': 'other_tags', 'segment': 'segment', 'segment_length': 'segment_length', 'intersection_length': 'intersection_length', 'intersection_percentage': 'intersection_percentage', 'flag_match': 'flag_match', });
lyr_MatchedNodes_9.set('fieldAliases', {'fid': 'fid', 'osm_id': 'osm_id', 'name': 'name', 'barrier': 'barrier', 'highway': 'highway', 'ref': 'ref', 'address': 'address', 'is_in': 'is_in', 'place': 'place', 'man_made': 'man_made', 'other_tags': 'other_tags', 'node': 'node', 'osm_id_2': 'osm_id_2', });
lyr_TrackBuffer20m_2.set('fieldImages', {'name': 'TextEdit', 'cmt': 'TextEdit', 'desc': 'TextEdit', 'src': 'TextEdit', 'link1_href': 'TextEdit', 'link1_text': 'TextEdit', 'link1_type': 'TextEdit', 'link2_href': 'TextEdit', 'link2_text': 'TextEdit', 'link2_type': 'TextEdit', 'number': 'TextEdit', 'type': 'TextEdit', });
lyr_GPSTrack_3.set('fieldImages', {'name': 'TextEdit', 'cmt': 'TextEdit', 'desc': 'TextEdit', 'src': 'TextEdit', 'link1_href': 'TextEdit', 'link1_text': 'TextEdit', 'link1_type': 'TextEdit', 'link2_href': 'TextEdit', 'link2_text': 'TextEdit', 'link2_type': 'TextEdit', 'number': 'TextEdit', 'type': 'TextEdit', 'track_length': '', });
lyr_NetworkLines_4.set('fieldImages', {'fid': 'Range', 'osm_id': 'TextEdit', 'name': 'TextEdit', 'type': 'TextEdit', 'other_tags': 'TextEdit', 'segment': 'TextEdit', });
lyr_NetworkNodes_5.set('fieldImages', {'fid': 'Range', 'osm_id': 'TextEdit', 'name': 'TextEdit', 'barrier': 'TextEdit', 'highway': 'TextEdit', 'ref': 'TextEdit', 'address': 'TextEdit', 'is_in': 'TextEdit', 'place': 'TextEdit', 'man_made': 'TextEdit', 'other_tags': 'TextEdit', 'node': 'Range', });
lyr_Intersections_6.set('fieldImages', {'osm_id': 'TextEdit', 'segment_length': 'TextEdit', 'name': 'TextEdit', 'intersection_length': 'TextEdit', 'intersection_percentage': 'TextEdit', 'flag_match': 'Range', });
lyr_SegmentMatching_7.set('fieldImages', {'fid': 'Range', 'osm_id': 'TextEdit', 'name': 'TextEdit', 'type': 'TextEdit', 'other_tags': 'TextEdit', 'segment': 'TextEdit', 'segment_length': 'TextEdit', 'intersection_length': 'TextEdit', 'intersection_percentage': 'TextEdit', 'flag_match': 'Range', });
lyr_MatchedSegments_8.set('fieldImages', {'fid': 'Range', 'osm_id': 'TextEdit', 'name': 'TextEdit', 'type': 'TextEdit', 'other_tags': 'TextEdit', 'segment': 'TextEdit', 'segment_length': 'TextEdit', 'intersection_length': 'TextEdit', 'intersection_percentage': 'TextEdit', 'flag_match': 'Range', });
lyr_MatchedNodes_9.set('fieldImages', {'fid': 'Range', 'osm_id': 'TextEdit', 'name': 'TextEdit', 'barrier': 'TextEdit', 'highway': 'TextEdit', 'ref': 'TextEdit', 'address': 'TextEdit', 'is_in': 'TextEdit', 'place': 'TextEdit', 'man_made': 'TextEdit', 'other_tags': 'TextEdit', 'node': 'Range', 'osm_id_2': 'TextEdit', });
lyr_TrackBuffer20m_2.set('fieldLabels', {'name': 'hidden field', 'cmt': 'hidden field', 'desc': 'hidden field', 'src': 'hidden field', 'link1_href': 'hidden field', 'link1_text': 'hidden field', 'link1_type': 'hidden field', 'link2_href': 'hidden field', 'link2_text': 'hidden field', 'link2_type': 'hidden field', 'number': 'hidden field', 'type': 'hidden field', });
lyr_GPSTrack_3.set('fieldLabels', {'name': 'inline label - always visible', 'cmt': 'hidden field', 'desc': 'hidden field', 'src': 'hidden field', 'link1_href': 'hidden field', 'link1_text': 'hidden field', 'link1_type': 'hidden field', 'link2_href': 'hidden field', 'link2_text': 'hidden field', 'link2_type': 'hidden field', 'number': 'hidden field', 'type': 'hidden field', 'track_length': 'inline label - always visible', });
lyr_NetworkLines_4.set('fieldLabels', {'fid': 'hidden field', 'osm_id': 'hidden field', 'name': 'hidden field', 'type': 'hidden field', 'other_tags': 'hidden field', 'segment': 'inline label - always visible', });
lyr_NetworkNodes_5.set('fieldLabels', {'fid': 'hidden field', 'osm_id': 'hidden field', 'name': 'hidden field', 'barrier': 'hidden field', 'highway': 'hidden field', 'ref': 'hidden field', 'address': 'hidden field', 'is_in': 'hidden field', 'place': 'hidden field', 'man_made': 'hidden field', 'other_tags': 'hidden field', 'node': 'inline label - always visible', });
lyr_Intersections_6.set('fieldLabels', {'osm_id': 'hidden field', 'segment_length': 'hidden field', 'name': 'hidden field', 'intersection_length': 'hidden field', 'intersection_percentage': 'hidden field', 'flag_match': 'hidden field', });
lyr_SegmentMatching_7.set('fieldLabels', {'fid': 'hidden field', 'osm_id': 'hidden field', 'name': 'hidden field', 'type': 'hidden field', 'other_tags': 'hidden field', 'segment': 'inline label - always visible', 'segment_length': 'inline label - always visible', 'intersection_length': 'inline label - always visible', 'intersection_percentage': 'inline label - always visible', 'flag_match': 'inline label - always visible', });
lyr_MatchedSegments_8.set('fieldLabels', {'fid': 'hidden field', 'osm_id': 'hidden field', 'name': 'hidden field', 'type': 'hidden field', 'other_tags': 'hidden field', 'segment': 'inline label - always visible', 'segment_length': 'inline label - always visible', 'intersection_length': 'inline label - always visible', 'intersection_percentage': 'inline label - always visible', 'flag_match': 'hidden field', });
lyr_MatchedNodes_9.set('fieldLabels', {'fid': 'hidden field', 'osm_id': 'hidden field', 'name': 'hidden field', 'barrier': 'hidden field', 'highway': 'hidden field', 'ref': 'hidden field', 'address': 'hidden field', 'is_in': 'hidden field', 'place': 'hidden field', 'man_made': 'hidden field', 'other_tags': 'hidden field', 'node': 'inline label - visible with data', 'osm_id_2': 'hidden field', });
lyr_MatchedNodes_9.on('precompose', function(evt) {
    evt.context.globalCompositeOperation = 'normal';
});