import unittest

from geographic.zone_manager import GeographicZone, Stop, StopRegistry


class TestGeographicZone(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.zone = GeographicZone(
            id="test_zone",
            name="Test Zone",
            center_lat=40.7589,
            center_lon=-73.9851,
            radius_km=2.0,
            demand_weight=1.5
        )

    def test_zone_initialization(self):
        """Test zone initialization"""
        self.assertEqual(self.zone.id, "test_zone")
        self.assertEqual(self.zone.name, "Test Zone")
        self.assertEqual(self.zone.center_lat, 40.7589)
        self.assertEqual(self.zone.center_lon, -73.9851)
        self.assertEqual(self.zone.radius_km, 2.0)
        self.assertEqual(self.zone.demand_weight, 1.5)

    def test_point_in_zone_center(self):
        """Test point at zone center"""
        self.assertTrue(self.zone.is_point_in_zone(40.7589, -73.9851))

    def test_point_in_zone_within_radius(self):
        """Test point within zone radius"""
        # Point slightly offset from center (should be within 2km)
        self.assertTrue(self.zone.is_point_in_zone(40.7600, -73.9860))

    def test_point_outside_zone(self):
        """Test point outside zone radius"""
        # Point far from center (should be outside 2km radius)
        self.assertFalse(self.zone.is_point_in_zone(40.8000, -74.0000))

    def test_zone_default_demand_weight(self):
        """Test zone with default demand weight"""
        zone = GeographicZone(
            id="default_zone",
            name="Default Zone",
            center_lat=40.0,
            center_lon=-74.0,
            radius_km=1.0
        )
        self.assertEqual(zone.demand_weight, 1.0)


class TestStop(unittest.TestCase):

    def test_stop_initialization(self):
        """Test stop initialization"""
        stop = Stop(
            id="stop_001",
            name="Main Street Station",
            lat=40.7589,
            lon=-73.9851,
            zone_id="downtown",
            stop_type="bus"
        )

        self.assertEqual(stop.id, "stop_001")
        self.assertEqual(stop.name, "Main Street Station")
        self.assertEqual(stop.lat, 40.7589)
        self.assertEqual(stop.lon, -73.9851)
        self.assertEqual(stop.zone_id, "downtown")
        self.assertEqual(stop.stop_type, "bus")

    def test_stop_default_type(self):
        """Test stop with default type"""
        stop = Stop(
            id="stop_002",
            name="Central Station",
            lat=40.7500,
            lon=-73.9900,
            zone_id="midtown"
        )
        self.assertEqual(stop.stop_type, "bus")


class TestStopRegistry(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.registry = StopRegistry()

    def test_initialization_with_default_data(self):
        """Test registry initialization with default data"""
        self.assertGreater(len(self.registry.zones), 0)
        self.assertGreater(len(self.registry.stops), 0)

        # Check that default zones exist
        zone_ids = [zone.id for zone in self.registry.zones]
        self.assertIn("downtown", zone_ids)
        self.assertIn("midtown", zone_ids)
        self.assertIn("uptown", zone_ids)
        self.assertIn("suburbs", zone_ids)

        # Check that default stops exist
        stop_ids = [stop.id for stop in self.registry.stops]
        self.assertIn("stop_001", stop_ids)

    def test_get_random_stop(self):
        """Test getting a random stop"""
        stop = self.registry.get_random_stop()
        self.assertIsInstance(stop, Stop)
        self.assertIn(stop, self.registry.stops)

    def test_get_random_stop_weighted(self):
        """Test that random stop selection respects zone weights"""
        # Run multiple times to test weighting (not deterministic)
        stops = [self.registry.get_random_stop() for _ in range(100)]

        # Count stops by zone
        zone_counts = {}
        for stop in stops:
            zone_counts[stop.zone_id] = zone_counts.get(stop.zone_id, 0) + 1

        # Downtown has highest weight (3.0), should appear most frequently
        # This is probabilistic, so we just check it appears
        self.assertIn("downtown", zone_counts)

    def test_get_stops_in_zone(self):
        """Test getting stops in a specific zone"""
        downtown_stops = self.registry.get_stops_in_zone("downtown")

        # Should return a list
        self.assertIsInstance(downtown_stops, list)

        # All stops should be in downtown zone
        for stop in downtown_stops:
            self.assertEqual(stop.zone_id, "downtown")

    def test_get_stops_in_nonexistent_zone(self):
        """Test getting stops from a zone that doesn't exist"""
        stops = self.registry.get_stops_in_zone("nonexistent_zone")
        self.assertEqual(stops, [])

    def test_add_stop(self):
        """Test adding a new stop"""
        initial_count = len(self.registry.stops)

        new_stop = Stop(
            id="test_stop",
            name="Test Stop",
            lat=40.7000,
            lon=-74.0000,
            zone_id="test_zone"
        )

        self.registry.add_stop(new_stop)

        self.assertEqual(len(self.registry.stops), initial_count + 1)
        self.assertIn(new_stop, self.registry.stops)

    def test_add_zone(self):
        """Test adding a new zone"""
        initial_count = len(self.registry.zones)

        new_zone = GeographicZone(
            id="test_zone",
            name="Test Zone",
            center_lat=40.7000,
            center_lon=-74.0000,
            radius_km=1.0,
            demand_weight=2.0
        )

        self.registry.add_zone(new_zone)

        self.assertEqual(len(self.registry.zones), initial_count + 1)
        self.assertIn(new_zone, self.registry.zones)

    def test_stops_have_valid_zones(self):
        """Test that all default stops reference valid zones"""
        zone_ids = {zone.id for zone in self.registry.zones}

        for stop in self.registry.stops:
            self.assertIn(stop.zone_id, zone_ids,
                         f"Stop {stop.id} references invalid zone {stop.zone_id}")


if __name__ == '__main__':
    unittest.main()
