"""
Model exported as python.
Name : GPX Matching
Group : 
With QGIS : 34012
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class GpxMatching(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('nodes', 'Nodes', types=[QgsProcessing.TypeVectorPoint], defaultValue='nodes'))
        self.addParameter(QgsProcessingParameterVectorLayer('segments', 'Segments', types=[QgsProcessing.TypeVectorLine], defaultValue='segments'))
        self.addParameter(QgsProcessingParameterVectorLayer('tracks', 'Tracks', types=[QgsProcessing.TypeVectorLine], defaultValue='tracks'))
        self.addParameter(QgsProcessingParameterFeatureSink('MatchedSegmentsStats', 'Matched Segments Stats', optional=True, type=QgsProcessing.TypeVector, createByDefault=True, defaultValue='./output/segments_matched_stats.csv'))
        self.addParameter(QgsProcessingParameterFeatureSink('MatchedNodesStats', 'Matched Nodes Stats', optional=True, type=QgsProcessing.TypeVector, createByDefault=True, defaultValue='./output/nodes_matched_stats.csv'))
        self.addParameter(QgsProcessingParameterFeatureSink('TrackBuffer20M', 'Track Buffer (20 m)', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, supportsAppend=True, defaultValue='./intermediate/tracks_reprojected_buffer.geojson'))
        self.addParameter(QgsProcessingParameterFeatureSink('MatchedSegments', 'Matched Segments', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='./output/segments_matched.geojson'))
        self.addParameter(QgsProcessingParameterFeatureSink('NetworkNodes', 'Network Nodes', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue='./intermediate/nodes_clipped_reprojected.geojson'))
        self.addParameter(QgsProcessingParameterFeatureSink('NetworkLines', 'Network Lines', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue='./intermediate/segments_clipped_reprojected.geojson'))
        self.addParameter(QgsProcessingParameterFeatureSink('GpsTrack', 'GPS Track', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue='C:/Users/remerencia/OneDrive - Business & Decision Europe/Desktop/QGIS Demo/intermediate/tracks_reprojected.geojson'))
        self.addParameter(QgsProcessingParameterFeatureSink('Intersections', 'Intersections', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='./intermediate/segments_clipped_reprojected_intersection.geojson'))
        self.addParameter(QgsProcessingParameterFeatureSink('SegmentMatching', 'Segment Matching', optional=True, type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='./intermediate/segments_clipped_reprojected_joined.geojson'))
        self.addParameter(QgsProcessingParameterFeatureSink('MatchedNodes', 'Matched Nodes', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='./output/nodes_matched.geojson'))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(23, model_feedback)
        results = {}
        outputs = {}

        # Clip segments
        alg_params = {
            'CLIP': False,
            'EXTENT': '4.545055000,5.294535000,50.492793000,50.904264000 [EPSG:4326]',
            'INPUT': parameters['segments'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ClipSegments'] = processing.run('native:extractbyextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Clip nodes
        alg_params = {
            'CLIP': False,
            'EXTENT': '4.545055000,5.294535000,50.492793000,50.904264000 [EPSG:4326]',
            'INPUT': parameters['nodes'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ClipNodes'] = processing.run('native:extractbyextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Reproject tracks
        alg_params = {
            'CONVERT_CURVED_GEOMETRIES': False,
            'INPUT': parameters['tracks'],
            'OPERATION': None,
            'TARGET_CRS': 'ProjectCrs',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectTracks'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Calculate node
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'node',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'regexp_substr("other_tags", \'"rcn_ref"=>"([^"]+)"\')',
            'INPUT': outputs['ClipNodes']['OUTPUT'],
            'OUTPUT': parameters['NetworkNodes']
        }
        outputs['CalculateNode'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['NetworkNodes'] = outputs['CalculateNode']['OUTPUT']

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Calculate track length
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'track_length',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimal (double)
            'FORMULA': '$length',
            'INPUT': outputs['ReprojectTracks']['OUTPUT'],
            'OUTPUT': parameters['GpsTrack']
        }
        outputs['CalculateTrackLength'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['GpsTrack'] = outputs['CalculateTrackLength']['OUTPUT']

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Calculate segment
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'segment',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'regexp_substr("other_tags", \'"ref"=>"([^"]+)"\')',
            'INPUT': outputs['ClipSegments']['OUTPUT'],
            'OUTPUT': parameters['NetworkLines']
        }
        outputs['CalculateSegment'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['NetworkLines'] = outputs['CalculateSegment']['OUTPUT']

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Buffer track
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 20,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': outputs['CalculateTrackLength']['OUTPUT'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': parameters['TrackBuffer20M']
        }
        outputs['BufferTrack'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['TrackBuffer20M'] = outputs['BufferTrack']['OUTPUT']

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Reproject nodes
        alg_params = {
            'CONVERT_CURVED_GEOMETRIES': False,
            'INPUT': outputs['CalculateNode']['OUTPUT'],
            'OPERATION': None,
            'TARGET_CRS': 'ProjectCrs',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectNodes'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Reproject segments
        alg_params = {
            'CONVERT_CURVED_GEOMETRIES': False,
            'INPUT': outputs['CalculateSegment']['OUTPUT'],
            'OPERATION': None,
            'TARGET_CRS': 'ProjectCrs',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ReprojectSegments'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Calculate segment length
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'segment_length',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimal (double)
            'FORMULA': '$length',
            'INPUT': outputs['ReprojectSegments']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculateSegmentLength'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Calculate intersections
        alg_params = {
            'GRID_SIZE': None,
            'INPUT': outputs['CalculateSegmentLength']['OUTPUT'],
            'INPUT_FIELDS': ['osm_id','segment_length'],
            'OVERLAY': outputs['BufferTrack']['OUTPUT'],
            'OVERLAY_FIELDS': ['name'],
            'OVERLAY_FIELDS_PREFIX': None,
            'OUTPUT': parameters['Intersections']
        }
        outputs['CalculateIntersections'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Intersections'] = outputs['CalculateIntersections']['OUTPUT']

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Calculate intersection length
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'intersection_length',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimal (double)
            'FORMULA': '$length',
            'INPUT': outputs['CalculateIntersections']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculateIntersectionLength'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Calculate intersection %
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'intersection_percentage',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0,  # Decimal (double)
            'FORMULA': '100 * "intersection_length" / "segment_length"',
            'INPUT': outputs['CalculateIntersectionLength']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculateIntersection'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Calculate match flag
        alg_params = {
            'FIELD_LENGTH': 0,
            'FIELD_NAME': 'flag_match',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Integer (32 bit)
            'FORMULA': 'intersection_percentage >= 75',
            'INPUT': outputs['CalculateIntersection']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculateMatchFlag'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Join segments and intersections
        alg_params = {
            'DISCARD_NONMATCHING': True,
            'FIELD': 'osm_id',
            'FIELDS_TO_COPY': ['intersection_length','intersection_percentage','flag_match'],
            'FIELD_2': 'osm_id',
            'INPUT': outputs['CalculateSegmentLength']['OUTPUT'],
            'INPUT_2': outputs['CalculateMatchFlag']['OUTPUT'],
            'METHOD': 1,  # Take attributes of the first matching feature only (one-to-one)
            'PREFIX': None,
            'OUTPUT': parameters['SegmentMatching']
        }
        outputs['JoinSegmentsAndIntersections'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['SegmentMatching'] = outputs['JoinSegmentsAndIntersections']['OUTPUT']

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Filter matched segments
        alg_params = {
            'FIELD': 'flag_match',
            'INPUT': outputs['JoinSegmentsAndIntersections']['OUTPUT'],
            'OPERATOR': 0,  # =
            'VALUE': '1',
            'OUTPUT': parameters['MatchedSegments']
        }
        outputs['FilterMatchedSegments'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['MatchedSegments'] = outputs['FilterMatchedSegments']['OUTPUT']

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Basic statistics for fields
        alg_params = {
            'FIELD_NAME': 'segment_length',
            'INPUT_LAYER': outputs['FilterMatchedSegments']['OUTPUT'],
            'OUTPUT': parameters['MatchedSegmentsStats']
        }
        outputs['BasicStatisticsForFields'] = processing.run('native:basicstatisticsforfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['MatchedSegmentsStats'] = outputs['BasicStatisticsForFields']['OUTPUT']

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Buffer matched segments
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 20,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': outputs['FilterMatchedSegments']['OUTPUT'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['BufferMatchedSegments'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # Intersect matched segments and nodes
        alg_params = {
            'GRID_SIZE': None,
            'INPUT': outputs['ReprojectNodes']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'OVERLAY': outputs['BufferMatchedSegments']['OUTPUT'],
            'OVERLAY_FIELDS': ['osm_id'],
            'OVERLAY_FIELDS_PREFIX': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['IntersectMatchedSegmentsAndNodes'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # Rename segment osm_id
        alg_params = {
            'FIELD': 'osm_id_2',
            'INPUT': outputs['IntersectMatchedSegmentsAndNodes']['OUTPUT'],
            'NEW_NAME': 'osm_id_segment',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RenameSegmentOsm_id'] = processing.run('native:renametablefield', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # Delete duplicate nodes I
        alg_params = {
            'FIELDS': ['osm_id'],
            'INPUT': outputs['RenameSegmentOsm_id']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DeleteDuplicateNodesI'] = processing.run('native:removeduplicatesbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # Delete duplicate nodes II
        alg_params = {
            'FIELDS': ['node','osm_id_segment'],
            'INPUT': outputs['DeleteDuplicateNodesI']['OUTPUT'],
            'OUTPUT': parameters['MatchedNodes']
        }
        outputs['DeleteDuplicateNodesIi'] = processing.run('native:removeduplicatesbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['MatchedNodes'] = outputs['DeleteDuplicateNodesIi']['OUTPUT']

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # Basic statistics for fields
        alg_params = {
            'FIELD_NAME': 'osm_id',
            'INPUT_LAYER': outputs['DeleteDuplicateNodesIi']['OUTPUT'],
            'OUTPUT': parameters['MatchedNodesStats']
        }
        outputs['BasicStatisticsForFields_2'] = processing.run('native:basicstatisticsforfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['MatchedNodesStats'] = outputs['BasicStatisticsForFields_2']['OUTPUT']
        return results

    def name(self):
        return 'GPX Matching'

    def displayName(self):
        return 'GPX Matching'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return GpxMatching()
