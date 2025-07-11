import json
import os
import tempfile
import time
import unittest
from datetime import datetime
from unittest.mock import patch

from demand_generator import DemandGenerator
from models.trip_request import TripRequest


class TestDemandGenerator(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test fixtures"""
        # Create a temporary config file for testing
        self.config_data = {
            "streaming": {
                "rate_per_second": 0.1,
                "output_format": "json",
                "burst_enabled": True,
            },
            "temporal_patterns": {
                "base_rate": 5.0,
                "hourly_pattern": {8: 2.0, 17: 2.5},
                "weekday_pattern": {0: 1.2, 6: 0.6},
                "rush_hour_pattern": {
                    "morning_start": 7,
                    "morning_end": 9,
                    "evening_start": 17,
                    "evening_end": 19,
                    "peak_multiplier": 2.0,
                },
            },
            "geographic": {
                "default_zones": [
                    {
                        "id": "test_zone_1",
                        "name": "Test Zone 1",
                        "center_lat": 40.7589,
                        "center_lon": -73.9851,
                        "radius_km": 2.0,
                        "demand_weight": 2.0,
                    },
                    {
                        "id": "test_zone_2",
                        "name": "Test Zone 2",
                        "center_lat": 40.7505,
                        "center_lon": -73.9934,
                        "radius_km": 1.5,
                        "demand_weight": 1.5,
                    },
                ]
            },
        }

        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        import yaml

        yaml.dump(self.config_data, self.temp_config)
        self.temp_config.close()

        self.demand_generator = DemandGenerator(self.temp_config.name)

    def tearDown(self) -> None:
        """Clean up test fixtures"""
        # Stop any running streaming
        if self.demand_generator.running:
            self.demand_generator.stop_streaming()

        # Remove temporary config file
        os.unlink(self.temp_config.name)

    def test_initialization(self) -> None:
        """Test that DemandGenerator initializes correctly"""
        self.assertIsNotNone(self.demand_generator.config)
        self.assertIsNotNone(self.demand_generator.stop_registry)
        self.assertIsNotNone(self.demand_generator.temporal_engine)
        self.assertEqual(self.demand_generator.base_rate, 0.1)
        self.assertEqual(self.demand_generator.output_format, "json")
        self.assertTrue(self.demand_generator.burst_enabled)
        self.assertFalse(self.demand_generator.running)

    def test_calculate_requests_count(self):
        """Test request count calculation"""
        # Test with exact integer rate
        count = self.demand_generator._calculate_requests_count(2.0)
        self.assertGreaterEqual(count, 2)

        # Test with fractional rate
        count = self.demand_generator._calculate_requests_count(1.5)
        self.assertIn(count, [1, 2])  # Should be 1 or 2 due to randomness

        # Test with zero rate
        count = self.demand_generator._calculate_requests_count(0.0)
        self.assertEqual(count, 0)

    @patch("demand_generator.datetime")
    def test_generate_trip_request(self, mock_datetime):
        """Test trip request generation"""
        # Mock current time
        test_time = datetime(2023, 6, 15, 8, 30, 0)
        mock_datetime.now.return_value = test_time

        trip_request = self.demand_generator._generate_trip_request(test_time)

        self.assertIsInstance(trip_request, TripRequest)
        self.assertTrue(trip_request.id.startswith("trip_"))
        self.assertIsNotNone(trip_request.origin_stop_id)
        self.assertIsNotNone(trip_request.destination_stop_id)
        self.assertEqual(trip_request.timestamp, test_time)
        self.assertIn(trip_request.passenger_count, range(1, 5))
        self.assertIn(
            trip_request.trip_purpose,
            ["work", "shopping", "leisure", "medical", "education"],
        )
        self.assertIn(trip_request.priority, range(1, 4))

    @patch("builtins.print")
    def test_send_to_output_stream_json(self, mock_print: any) -> None:
        """Test JSON output stream"""
        test_time = datetime(2023, 6, 15, 8, 30, 0)
        trip_request = self.demand_generator._generate_trip_request(test_time)

        self.demand_generator._send_to_output_stream(trip_request)

        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]

        # Verify it's valid JSON
        parsed = json.loads(output)
        self.assertEqual(parsed["id"], trip_request.id)

    @patch("builtins.print")
    def test_send_to_output_stream_text(self, mock_print: any) -> None:
        """Test text output stream"""
        self.demand_generator.output_format = "text"
        test_time = datetime(2023, 6, 15, 8, 30, 0)
        trip_request = self.demand_generator._generate_trip_request(test_time)

        self.demand_generator._send_to_output_stream(trip_request)

        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]
        self.assertIn("Generated trip:", output)
        self.assertIn(trip_request.id, output)

    @patch("time.sleep")
    @patch("demand_generator.datetime")
    def test_streaming_loop_single_iteration(self, mock_datetime: any, mock_sleep: any) -> None:
        """Test a single iteration of the streaming loop"""
        # Mock current time
        test_time = datetime(2023, 6, 15, 8, 30, 0)  # Thursday morning rush hour
        mock_datetime.now.return_value = test_time

        # Start streaming in a separate thread
        self.demand_generator.start_streaming()

        # Let it run for a short time
        time.sleep(0.1)

        # Stop streaming
        self.demand_generator.stop_streaming()

        # Verify sleep was called (indicating loop ran)
        mock_sleep.assert_called()

    def test_start_stop_streaming(self) -> None:
        """Test starting and stopping the streaming process"""
        # Initially not running
        self.assertFalse(self.demand_generator.running)
        self.assertIsNone(self.demand_generator.thread)

        # Start streaming
        self.demand_generator.start_streaming()
        self.assertTrue(self.demand_generator.running)
        self.assertIsNotNone(self.demand_generator.thread)

        # Stop streaming
        self.demand_generator.stop_streaming()
        self.assertFalse(self.demand_generator.running)

        # Thread should be joined and finished
        if self.demand_generator.thread:
            self.assertFalse(self.demand_generator.thread.is_alive())

    def test_start_streaming_when_already_running(self) -> None:
        """Test that starting streaming when already running has no effect"""
        self.demand_generator.start_streaming()
        first_thread = self.demand_generator.thread

        # Try to start again
        self.demand_generator.start_streaming()

        # Should be the same thread
        self.assertEqual(first_thread, self.demand_generator.thread)

        self.demand_generator.stop_streaming()


if __name__ == "__main__":
    unittest.main()
