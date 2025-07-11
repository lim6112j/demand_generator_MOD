
# Transit Demand Generator

A configurable real-time transit demand generator that simulates realistic passenger trip requests based on temporal patterns, geographic zones, and configurable parameters.

## Features

- **Real-time Streaming**: Generates trip requests in real-time with configurable rates
- **Temporal Patterns**: Supports hourly, weekday, and rush hour demand patterns
- **Geographic Zones**: Weighted zone-based origin/destination selection
- **Configurable Output**: JSON or text output formats
- **Burst Patterns**: Realistic arrival patterns with Poisson-like distribution
- **Comprehensive Testing**: Full unit test coverage for all components

## Project Structure

```
demand_generator/
├── config/
│   └── demand_config.yaml          # Main configuration file
├── geographic/
│   ├── __init__.py
│   └── zone_manager.py             # Geographic zones and stops management
├── models/
│   └── trip_request.py             # Trip request data model
├── patterns/
│   ├── __init__.py
│   └── temporal_engine.py          # Temporal demand patterns
├── demand_generator.py             # Main demand generator class
├── main.py                         # CLI entry point
├── test_demand_generator.py        # Tests for main generator
├── test_temporal_engine.py         # Tests for temporal patterns
├── test_zone_manager.py            # Tests for geographic components
└── README.md
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd demand_generator
```

2. Install dependencies using uv:
```bash
uv sync
```

## Usage

### Basic Usage

Run the demand generator with default configuration:

```bash
uv run python main.py
```

### Configuration Options

Specify a custom configuration file:

```bash
uv run python main.py --config path/to/your/config.yaml
```

Run for a specific duration (in seconds):

```bash
uv run python main.py --duration 60
```

### Example Output

The generator outputs trip requests in JSON format:

```json
{
  "id": "trip_20231215_083045_1234",
  "origin_stop_id": "stop_001",
  "destination_stop_id": "stop_003",
  "timestamp": "2023-12-15T08:30:45",
  "passenger_count": 2,
  "trip_purpose": "work",
  "priority": 1
}
```

## Configuration

The system is configured via YAML files. See `config/demand_config.yaml` for a complete example.

### Key Configuration Sections

#### Streaming Configuration
```yaml
streaming:
  rate_per_second: 0.167      # Base rate (10 requests/minute)
  output_format: "json"       # "json" or "text"
  burst_enabled: true         # Enable realistic burst patterns
```

#### Temporal Patterns
```yaml
temporal_patterns:
  base_rate: 10.0             # Base requests per minute
  
  # Hour-specific multipliers (0-23)
  hourly_pattern:
    8: 2.0                    # 2x demand at 8 AM
    17: 2.5                   # 2.5x demand at 5 PM
  
  # Weekday multipliers (0=Monday, 6=Sunday)
  weekday_pattern:
    0: 1.2                    # 20% higher on Monday
    6: 0.6                    # 40% lower on Sunday
  
  # Rush hour configuration
  rush_hour_pattern:
    morning_start: 7
    morning_end: 9
    evening_start: 17
    evening_end: 19
    peak_multiplier: 1.5      # Additional 50% during rush hours
```

#### Geographic Zones
```yaml
geographic:
  default_zones:
    - id: "downtown"
      name: "Downtown"
      center_lat: 40.7589
      center_lon: -73.9851
      radius_km: 2.0
      demand_weight: 3.0      # Higher weight = more trips
```

## Architecture

### Core Components

1. **DemandGenerator**: Main orchestrator that coordinates all components
2. **TemporalPatternEngine**: Calculates demand rates based on time patterns
3. **StopRegistry**: Manages geographic zones and transit stops
4. **TripRequest**: Data model for generated trip requests

### Temporal Patterns

The system supports multiple overlapping temporal patterns:

- **Hourly Pattern**: Different demand levels throughout the day
- **Weekday Pattern**: Variations between weekdays and weekends
- **Rush Hour Pattern**: Additional peaks during commute times

All patterns are multiplicative, so a Monday morning rush hour combines all three multipliers.

### Geographic Distribution

Trip origins and destinations are selected from predefined zones with configurable weights. Higher weight zones generate more trips, simulating areas with higher transit demand.

## Testing

Run all tests:

```bash
uv run pytest test_*.py -v
```

Run specific test files:

```bash
uv run pytest test_demand_generator.py -v
uv run pytest test_temporal_engine.py -v
uv run pytest test_zone_manager.py -v
```

### Test Coverage

- **DemandGenerator**: Initialization, streaming control, trip generation
- **TemporalPatternEngine**: Pattern calculations, multiplier combinations
- **Geographic Components**: Zone management, stop selection, weighting

## Development

### Adding New Temporal Patterns

1. Create a new class inheriting from `TimePattern` in `patterns/temporal_engine.py`
2. Implement the `get_demand_multiplier(timestamp)` method
3. Add the pattern to `TemporalPatternEngine._initialize_patterns()`

### Adding New Geographic Features

1. Extend the `GeographicZone` or `Stop` classes in `geographic/zone_manager.py`
2. Update the `StopRegistry` to handle new features
3. Modify the configuration schema as needed

### Configuration Schema

The system uses YAML configuration with the following top-level sections:

- `streaming`: Output and rate control
- `temporal_patterns`: Time-based demand patterns
- `geographic`: Zones and stops configuration
- `trip_request`: Request generation parameters
- `output`: Logging and output formatting

## Examples

### High-Frequency Testing

Generate 1 request per second for 30 seconds:

```bash
uv run python main.py --duration 30
```

With custom config:
```yaml
streaming:
  rate_per_second: 1.0
  output_format: "json"
```

### Rush Hour Simulation

Configure peak multipliers for realistic rush hour patterns:

```yaml
temporal_patterns:
  rush_hour_pattern:
    morning_start: 7
    morning_end: 9
    evening_start: 17
    evening_end: 19
    peak_multiplier: 3.0      # 3x normal demand
```

### Weekend vs Weekday

Different patterns for weekends:

```yaml
temporal_patterns:
  weekday_pattern:
    0: 1.0    # Monday - normal
    1: 1.0    # Tuesday - normal
    2: 1.0    # Wednesday - normal
    3: 1.0    # Thursday - normal
    4: 1.1    # Friday - slightly higher
    5: 0.7    # Saturday - 30% lower
    6: 0.5    # Sunday - 50% lower
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Add your license information here]
