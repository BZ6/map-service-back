import unittest
from unittest.mock import patch, Mock
from shapely.geometry import Polygon, Point


from app import (
    add_ids_to_polygons,
    convert_to_shapely_polygons,
    build_spatial_index,
    find_intersections_with_index,
    find_multi_intersections,
    filter_points_by_intersections,
    sort_and_limit_points,
    haversine_distance,
    cluster_points,
    find_buffer_intersection_centers
)


class AppTest(unittest.TestCase):
    def test_add_ids_to_polygons(self):
        polygons = [
            [(0, 0), (1, 0), (1, 1)],
            [(2, 2), (3, 2), (3, 3), (2, 3)],
            [(4, 4), (5, 4), (5, 5), (4, 5), (4.5, 4.5)]
        ]

        result = add_ids_to_polygons(polygons)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['id'], 1)
        self.assertEqual(result[0]['polygon'], [(0, 0), (1, 0), (1, 1)])
        self.assertEqual(result[0]['points_count'], 3)
        self.assertEqual(result[1]['id'], 2)
        self.assertEqual(result[1]['polygon'], [(2, 2), (3, 2), (3, 3), (2, 3)])
        self.assertEqual(result[1]['points_count'], 4)
        self.assertEqual(result[2]['id'], 3)
        self.assertEqual(result[2]['polygon'], [(4, 4), (5, 4), (5, 5), (4, 5), (4.5, 4.5)])
        self.assertEqual(result[2]['points_count'], 5)

        ids = [item['id'] for item in result]
        self.assertEqual(ids, [1, 2, 3])

        for i, item in enumerate(result):
            self.assertEqual(item['points_count'], len(polygons[i]))
            self.assertEqual(item['polygon'][0], polygons[i][0])
            self.assertEqual(item['polygon'][-1], polygons[i][-1])
            self.assertEqual(len(item['polygon']), len(polygons[i]))

    def test_convert_to_shapely_polygons(self):
        polygons_with_ids = [
            {
                'id': 1,
                'polygon': [(0, 0), (1, 0), (1, 1), (0, 0)],
                'points_count': 4
            },
            {
                'id': 2,
                'polygon': [(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)],
                'points_count': 5
            }
        ]

        result = convert_to_shapely_polygons(polygons_with_ids)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 1)
        self.assertEqual(result[1]['id'], 2)
        self.assertIsInstance(result[0]['polygon'], Polygon)
        self.assertIsInstance(result[1]['polygon'], Polygon)
        self.assertEqual(result[0]['bounds'], (0, 0, 1, 1))
        self.assertEqual(result[1]['bounds'], (2, 2, 3, 3))
        self.assertGreater(result[0]['area'], 0)
        self.assertGreater(result[1]['area'], 0)

    def test_build_spatial_index(self):
        shapely_polygons = [
            {
                'id': 1,
                'polygon': Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
                'bounds': (0, 0, 1, 1)
            },
            {
                'id': 2,
                'polygon': Polygon([(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)]),
                'bounds': (2, 2, 3, 3)
            }
        ]

        idx, bboxes = build_spatial_index(shapely_polygons)
        self.assertIsNotNone(idx)
        self.assertEqual(len(bboxes), 2)
        self.assertEqual(bboxes[0], (0, 0, 1, 1))
        self.assertEqual(bboxes[1], (2, 2, 3, 3))

    def test_find_multi_intersections(self):
        intersection1 = Mock()
        intersection1.centroid = Mock()
        intersection1.centroid.x = 1.5
        intersection1.centroid.y = 1.5

        intersection2 = Mock()
        intersection2.centroid = Mock()
        intersection2.centroid.x = 2.0
        intersection2.centroid.y = 2.0

        intersections_dict = {
            (1, 2): intersection1,
            (1, 3): intersection1,
            (2, 3): intersection2
        }

        result = find_multi_intersections(intersections_dict)

        self.assertEqual(len(result), 2)
        self.assertIn((1.5, 1.5), result)
        self.assertEqual(result[(1.5, 1.5)], {1, 2, 3})
        self.assertIn((2.0, 2.0), result)
        self.assertEqual(result[(2.0, 2.0)], {2, 3})

    def test_filter_points_by_intersections(self):
        point_groups = {
            (0.5, 0.5): {1, 2},
            (1.5, 1.5): {1, 2, 3},
            (2.5, 2.5): {1, 2, 3, 4},
            (3.5, 3.5): {1},
        }

        filtered = filter_points_by_intersections(point_groups, min_intersections=2)
        self.assertEqual(len(filtered), 3)

        filtered = filter_points_by_intersections(point_groups, min_intersections=3)
        self.assertEqual(len(filtered), 2)

        for point in filtered:
            self.assertIn('coordinates', point)
            self.assertIn('weight', point)
            self.assertIn('buffer_ids', point)
            self.assertEqual(point['weight'], len(point['buffer_ids']))

    def test_sort_and_limit_points(self):
        points = [
            {'coordinates': [1, 1], 'weight': 2, 'buffer_ids': [1, 2]},
            {'coordinates': [2, 2], 'weight': 4, 'buffer_ids': [1, 2, 3, 4]},
            {'coordinates': [3, 3], 'weight': 3, 'buffer_ids': [1, 2, 3]},
            {'coordinates': [4, 4], 'weight': 1, 'buffer_ids': [1]}
        ]

        sorted_points = sort_and_limit_points(points, max_points=10)
        self.assertEqual(sorted_points[0]['weight'], 4)
        self.assertEqual(sorted_points[-1]['weight'], 1)

        limited = sort_and_limit_points(points, max_points=2)
        self.assertEqual(len(limited), 2)
        self.assertEqual(limited[0]['weight'], 4)
        self.assertEqual(limited[1]['weight'], 3)

    def test_haversine_distance(self):
        dist = haversine_distance(37.6176, 55.7558, 37.6176, 55.7558)
        self.assertAlmostEqual(dist, 0.0, places=2)

        dist = haversine_distance(37.6176, 55.7558, 37.6176, 55.7648)
        self.assertGreater(dist, 0.9)
        self.assertLess(dist, 1.1)

        dist1 = haversine_distance(0, 0, 1, 1)
        dist2 = haversine_distance(1, 1, 0, 0)
        self.assertAlmostEqual(dist1, dist2)

    def test_cluster_points_max_limit(self):
        points = [
            {'coordinates': [0, 0], 'weight': 1, 'buffer_ids': [1], 'buffer_count': 1},
            {'coordinates': [10, 10], 'weight': 2, 'buffer_ids': [2], 'buffer_count': 2},
            {'coordinates': [20, 20], 'weight': 3, 'buffer_ids': [3], 'buffer_count': 3},
            {'coordinates': [30, 30], 'weight': 4, 'buffer_ids': [4], 'buffer_count': 4},
            {'coordinates': [40, 40], 'weight': 5, 'buffer_ids': [5], 'buffer_count': 5}
        ]

        clustered = cluster_points(points, max_points=3, cluster_distance_km=0.1)
        self.assertEqual(len(clustered), 3)

    def test_find_buffer_intersection_centers_basic(self):
        polygons = [
            [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)],
            [(1, 1), (3, 1), (3, 3), (1, 3), (1, 1)],
            [(4, 4), (6, 4), (6, 6), (4, 6), (4, 4)]
        ]

        centers = find_buffer_intersection_centers(
            polygons,
            min_intersections=2,
            max_points=10
        )
        self.assertGreater(len(centers), 0)

        for center in centers:
            self.assertIn('coordinates', center)
            self.assertIn('weight', center)
            self.assertGreaterEqual(center['weight'], 2)
            self.assertIn('buffer_ids', center)

    def test_find_buffer_intersection_centers_no_intersections(self):
        polygons = [
            [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)],
            [(10, 10), (11, 10), (11, 11), (10, 11), (10, 10)]
        ]

        centers = find_buffer_intersection_centers(
            polygons,
            min_intersections=2,
            max_points=10
        )

        self.assertEqual(centers, [])

    def test_find_buffer_intersection_centers_max_points(self):
        polygons = []
        for i in range(10):
            polygons.append([
                (i, i), (i + 1, i), (i + 1, i + 1), (i, i + 1), (i, i)
            ])

        centers = find_buffer_intersection_centers(
            polygons,
            min_intersections=2,
            max_points=5
        )

        self.assertLessEqual(len(centers), 5)


class TestIntegration(unittest.TestCase):
    def test_full_pipeline(self):
        polygons = [
            [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)],
            [(1, 1), (3, 1), (3, 3), (1, 3), (1, 1)],
            [(0.5, 0.5), (2.5, 0.5), (2.5, 2.5), (0.5, 2.5), (0.5, 0.5)]
        ]

        polygons_with_ids = add_ids_to_polygons(polygons)
        self.assertEqual(len(polygons_with_ids), 3)

        shapely_polygons = convert_to_shapely_polygons(polygons_with_ids)
        self.assertEqual(len(shapely_polygons), 3)

        spatial_idx, bboxes = build_spatial_index(shapely_polygons)
        self.assertIsNotNone(spatial_idx)
        self.assertEqual(len(bboxes), 3)

        intersections = find_intersections_with_index(shapely_polygons, spatial_idx, bboxes)
        self.assertGreater(len(intersections), 0)

        point_groups = find_multi_intersections(intersections)
        self.assertGreater(len(point_groups), 0)

        filtered_points = filter_points_by_intersections(point_groups, min_intersections=2)
        self.assertGreater(len(filtered_points), 0)

        clustered_points = cluster_points(filtered_points, max_points=10)
        self.assertGreater(len(clustered_points), 0)

        result_points = sort_and_limit_points(clustered_points, max_points=10)
        self.assertGreater(len(result_points), 0)

        for point in result_points:
            self.assertIn('coordinates', point)
            self.assertIn('weight', point)
            self.assertGreaterEqual(point['weight'], 2)

        centers = find_buffer_intersection_centers(polygons, min_intersections=2, max_points=10)
        self.assertGreater(len(centers), 0)


if __name__ == '__main__':
    unittest.main()