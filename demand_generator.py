import random
import threading
import time
from datetime import datetime
from typing import Optional

import yaml

from geographic.zone_manager import StopRegistry
from models.trip_request import TripRequest
from patterns.temporal_engine import TemporalPatternEngine


class DemandGenerator:
    def __init__(self, config_path: str):
        # Load configuration
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        # Initialize components
        self.stop_registry = StopRegistry()
        self.temporal_engine = TemporalPatternEngine(self.config["temporal_patterns"])
        # Set up streaming parameters
        self.base_rate = self.config["streaming"].get(
            "rate_per_second", 0.167
        )  # Default to 10 requests per minute
        self.output_format = self.config["streaming"]["output_format"]
        self.burst_enabled = self.config["streaming"].get("burst_enabled", True)
        # Threading control
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start_streaming(self) -> None:
        """Start the demand generation streaming process"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._streaming_loop)
        self.thread.start()

    def stop_streaming(self) -> None:
        """Clean shutdown of streaming process"""
        self.running = False
        if self.thread:
            self.thread.join()

    def _streaming_loop(self) -> None:
        """Main streaming loop - generates trip requests based on temporal patterns"""
        while self.running:
            current_time = datetime.now()
            # Get current demand rate multiplier
            demand_multiplier = self.temporal_engine.calculate_demand_rate(current_time)
            current_rate = self.base_rate * demand_multiplier
            # Generate trip requests for this time period
            num_requests = self._calculate_requests_count(current_rate)
            for _ in range(num_requests):
                trip_request = self._generate_trip_request(current_time)
                self._send_to_output_stream(trip_request)
            # Sleep until next generation cycle
            time.sleep(1.0)  # Generate every second

    def _calculate_requests_count(self, rate: float) -> int:
        """Calculate number of requests to generate based on current rate"""
        base_count = int(rate)
        # Add randomness for burst patterns if enabled
        if self.burst_enabled:
            # Use Poisson-like distribution for realistic arrival patterns
            remainder = rate - base_count
            if random.random() < remainder:
                base_count += 1
        return base_count

    def _generate_trip_request(self, timestamp: datetime) -> TripRequest:
        """Generate a single trip request"""
        # Select random origin and destination zones
        zones = self.config["geographic"]["default_zones"]
        origin_zone = random.choice(zones)["id"]
        destination_zone = random.choice(zones)["id"]
        # Get random stops from selected zones
        origin_stops = self.stop_registry.get_stops_in_zone(origin_zone)
        destination_stops = self.stop_registry.get_stops_in_zone(destination_zone)
        # Fallback to any random stop if zone has no stops
        origin_stop = (
            random.choice(origin_stops).id
            if origin_stops
            else self.stop_registry.get_random_stop().id
        )
        destination_stop = (
            random.choice(destination_stops).id
            if destination_stops
            else self.stop_registry.get_random_stop().id
        )
        # Generate trip request
        trip_request = TripRequest(
            id=f"trip_{timestamp.strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
            origin_stop_id=origin_stop,
            destination_stop_id=destination_stop,
            timestamp=timestamp,
            passenger_count=random.randint(1, 4),
            trip_purpose=random.choice(["work", "shopping", "leisure", "medical", "education"]),
            priority=random.randint(1, 3),
        )
        return trip_request

    def _send_to_output_stream(self, trip_request: TripRequest) -> None:
        """Send trip request to output stream"""
        if self.output_format == "json":
            output = trip_request.to_json()
            print(output)  # For now, print to console
        else:
            print(f"Generated trip: {trip_request.id}")
