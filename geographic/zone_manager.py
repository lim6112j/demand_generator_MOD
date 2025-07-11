import random
from dataclasses import dataclass


@dataclass
class GeographicZone:
    """Represents a geographic zone with boundaries and properties"""

    id: str
    name: str
    center_lat: float
    center_lon: float
    radius_km: float
    demand_weight: float = 1.0

    def is_point_in_zone(self, lat: float, lon: float) -> bool:
        """Check if a point is within this zone (simplified circular boundary)"""
        # Simple distance calculation (not precise for large distances)
        lat_diff = lat - self.center_lat
        lon_diff = lon - self.center_lon
        distance_km = ((lat_diff**2 + lon_diff**2) ** 0.5) * 111  # Rough km conversion
        return distance_km <= self.radius_km


@dataclass
class Stop:
    """Represents a transit stop"""

    id: str
    name: str
    lat: float
    lon: float
    zone_id: str
    stop_type: str = "bus"  # bus, train, metro, etc.


class StopRegistry:
    """Manages all transit stops in the system"""

    def __init__(self):
        self.stops: list[Stop] = []
        self.zones: list[GeographicZone] = []
        self._initialize_default_data()

    def _initialize_default_data(self):
        """Initialize with some default zones and stops for testing"""
        # Default zones (example city layout)
        self.zones = [
            GeographicZone("downtown", "Downtown", 40.7589, -73.9851, 2.0, 3.0),
            GeographicZone("midtown", "Midtown", 40.7505, -73.9934, 1.5, 2.5),
            GeographicZone("uptown", "Uptown", 40.7831, -73.9712, 2.5, 1.5),
            GeographicZone("suburbs", "Suburbs", 40.7282, -73.7949, 5.0, 1.0),
        ]

        # Default stops
        self.stops = [
            Stop("stop_001", "Main St & 1st Ave", 40.7589, -73.9851, "downtown"),
            Stop("stop_002", "Central Station", 40.7505, -73.9934, "midtown"),
            Stop("stop_003", "Park Plaza", 40.7831, -73.9712, "uptown"),
            Stop("stop_004", "Mall Transit Center", 40.7282, -73.7949, "suburbs"),
            Stop("stop_005", "University Campus", 40.7614, -73.9776, "downtown"),
            Stop("stop_006", "Hospital District", 40.7505, -73.9834, "midtown"),
        ]

    def get_random_stop(self) -> Stop:
        """Get a random stop weighted by zone demand"""
        zone_weights = {zone.id: zone.demand_weight for zone in self.zones}
        weighted_stops = []

        for stop in self.stops:
            weight = zone_weights.get(stop.zone_id, 1.0)
            weighted_stops.extend([stop] * int(weight * 10))  # Scale weights

        return random.choice(weighted_stops)

    def get_stops_in_zone(self, zone_id: str) -> list[Stop]:
        """Get all stops in a specific zone"""
        return [stop for stop in self.stops if stop.zone_id == zone_id]

    def add_stop(self, stop: Stop):
        """Add a new stop to the registry"""
        self.stops.append(stop)

    def add_zone(self, zone: GeographicZone):
        """Add a new zone to the registry"""
        self.zones.append(zone)
