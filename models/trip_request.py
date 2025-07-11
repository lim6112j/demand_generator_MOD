import json
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TripRequest:
    id: str
    origin_stop_id: str
    destination_stop_id: str
    timestamp: datetime
    passenger_count: int
    trip_purpose: str
    priority: int = 1

    def to_json(self) -> str:
        """Convert to JSON format for streaming"""
        data = {
            'id': self.id,
            'origin_stop_id': self.origin_stop_id,
            'destination_stop_id': self.destination_stop_id,
            'timestamp': self.timestamp.isoformat(),
            'passenger_count': self.passenger_count,
            'trip_purpose': self.trip_purpose,
            'priority': self.priority
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> 'TripRequest':
        """Create TripRequest from JSON string"""
        data = json.loads(json_str)
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
