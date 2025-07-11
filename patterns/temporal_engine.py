from datetime import datetime


class TimePattern:
    """Base class for time-based demand patterns"""

    def get_demand_multiplier(self, timestamp: datetime) -> float:
        """Return demand multiplier for given timestamp"""
        raise NotImplementedError


class HourlyPattern(TimePattern):
    """Demand pattern based on hour of day"""

    def __init__(self, hourly_multipliers: dict[int, float]):
        self.hourly_multipliers = hourly_multipliers

    def get_demand_multiplier(self, timestamp: datetime) -> float:
        return self.hourly_multipliers.get(timestamp.hour, 1.0)


class WeekdayPattern(TimePattern):
    """Demand pattern based on day of week"""

    def __init__(self, weekday_multipliers: dict[int, float]):
        # 0=Monday, 1=Tuesday, ..., 6=Sunday
        self.weekday_multipliers = weekday_multipliers

    def get_demand_multiplier(self, timestamp: datetime) -> float:
        return self.weekday_multipliers.get(timestamp.weekday(), 1.0)


class RushHourPattern(TimePattern):
    """Special pattern for rush hour peaks"""

    def __init__(
        self,
        morning_peak: tuple[int, int] = (7, 9),
        evening_peak: tuple[int, int] = (17, 19),
        peak_multiplier: float = 2.0,
    ):
        self.morning_start, self.morning_end = morning_peak
        self.evening_start, self.evening_end = evening_peak
        self.peak_multiplier = peak_multiplier

    def get_demand_multiplier(self, timestamp: datetime) -> float:
        hour = timestamp.hour

        # Morning rush hour
        if self.morning_start <= hour < self.morning_end:
            return self.peak_multiplier

        # Evening rush hour
        if self.evening_start <= hour < self.evening_end:
            return self.peak_multiplier

        return 1.0


class TemporalPatternEngine:
    """Manages multiple temporal patterns and calculates combined demand"""

    def __init__(self, config: dict[str, any]):
        self.patterns: list[TimePattern] = []
        self.base_rate = config.get("base_rate", 10.0)  # requests per minute
        self._initialize_patterns(config)

    def _initialize_patterns(self, config: dict[str, any]) -> None:
        """Initialize patterns from configuration"""

        # Hourly pattern
        if "hourly_pattern" in config:
            hourly_config = config["hourly_pattern"]
            self.patterns.append(HourlyPattern(hourly_config))
        else:
            # Default hourly pattern
            default_hourly = {
                6: 0.5,
                7: 1.5,
                8: 2.0,
                9: 1.8,
                10: 1.2,
                11: 1.3,
                12: 1.5,
                13: 1.4,
                14: 1.2,
                15: 1.3,
                16: 1.6,
                17: 2.2,
                18: 2.5,
                19: 2.0,
                20: 1.5,
                21: 1.0,
                22: 0.8,
                23: 0.5,
                0: 0.3,
                1: 0.2,
                2: 0.1,
                3: 0.1,
                4: 0.2,
                5: 0.3,
            }
            self.patterns.append(HourlyPattern(default_hourly))

        # Weekday pattern
        if "weekday_pattern" in config:
            weekday_config = config["weekday_pattern"]
            self.patterns.append(WeekdayPattern(weekday_config))
        else:
            # Default weekday pattern (Monday=0, Sunday=6)
            default_weekday = {0: 1.2, 1: 1.3, 2: 1.3, 3: 1.3, 4: 1.4, 5: 0.8, 6: 0.6}
            self.patterns.append(WeekdayPattern(default_weekday))

        # Rush hour pattern
        if "rush_hour_pattern" in config:
            rush_config = config["rush_hour_pattern"]
            morning_peak = (
                rush_config.get("morning_start", 7),
                rush_config.get("morning_end", 9),
            )
            evening_peak = (
                rush_config.get("evening_start", 17),
                rush_config.get("evening_end", 19),
            )
            peak_multiplier = rush_config.get("peak_multiplier", 2.0)
            self.patterns.append(RushHourPattern(morning_peak, evening_peak, peak_multiplier))
        else:
            # Default rush hour pattern
            self.patterns.append(RushHourPattern())

    def calculate_demand_rate(self, timestamp: datetime) -> float:
        """Calculate current demand rate based on all patterns"""
        total_multiplier = 1.0

        for pattern in self.patterns:
            total_multiplier *= pattern.get_demand_multiplier(timestamp)

        return self.base_rate * total_multiplier

    def add_pattern(self, pattern: TimePattern) -> None:
        """Add a custom pattern to the engine"""
        self.patterns.append(pattern)
