import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import random
import yaml
from models.trip_request import TripRequest
from geographic.zone_manager import StopRegistry
from patterns.temporal_engine import TemporalPatternEngine

class DemandGenerator:
    def __init__(self, config_path: str):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.stop_registry = StopRegistry()
        self.temporal_engine = TemporalPatternEngine(self.config['temporal_patterns'])
        
        # Set up streaming parameters
        self.base_rate = self.config['streaming']['rate_per_second']
        self.output_format = self.config['streaming']['output_format']
        self.burst_enabled = self.config['streaming']['burst_enabled']
        
        # Threading control
        self.running = False
        self.thread = None
        
    def start_streaming(self):
        """Start the demand generation streaming process"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._streaming_loop)
        self.thread.start()
        
    def stop_streaming(self):
        """Clean shutdown of streaming process"""
        self.running = False
        if self.thread:
            self.thread.join()
            
    def _streaming_loop(self):
        """Main streaming loop - generates trip requests based on temporal patterns"""
        while self.running:
            current_time = datetime.now()
            
            # Get current demand rate multiplier
            demand_multiplier = self.temporal_engine.get_demand_rate(current_time)
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
        zones = list(self.config['geographic']['zones'])
        origin_zone = random.choice(zones)['id']
        destination_zone = random.choice(zones)['id']
        
        # Get random stops from selected zones
        origin_stop = self.stop_registry.get_random_stop_in_zone(origin_zone)
        destination_stop = self.stop_registry.get_random_stop_in_zone(destination_zone)
        
        # Generate trip request
        trip_request = TripRequest(
            id=f"trip_{timestamp.strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
            origin_stop_id=origin_stop,
            destination_stop_id=destination_stop,
            timestamp=timestamp,
            passenger_count=random.randint(1, 4),
            trip_purpose=random.choice(['work', 'shopping', 'leisure', 'medical', 'education']),
            priority=random.randint(1, 3)
        )
        
        return trip_request
        
    def _send_to_output_stream(self, trip_request: TripRequest):
        """Send trip request to output stream"""
        if self.output_format == 'json':
            output = trip_request.to_json()
            print(output)  # For now, print to console
        else:
            print(f"Generated trip: {trip_request.id}")
