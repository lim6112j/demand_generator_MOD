import unittest
from datetime import datetime
from typing import Any

from patterns.temporal_engine import (
    HourlyPattern,
    RushHourPattern,
    TemporalPatternEngine,
    WeekdayPattern,
)


class TestTimePatterns(unittest.TestCase):
    def test_hourly_pattern(self) -> None:
        """Test hourly demand pattern"""
        hourly_multipliers = {8: 2.0, 17: 2.5, 2: 0.1}
        pattern = HourlyPattern(hourly_multipliers)

        # Test defined hours
        morning_time = datetime(2023, 6, 15, 8, 30, 0)
        self.assertEqual(pattern.get_demand_multiplier(morning_time), 2.0)

        evening_time = datetime(2023, 6, 15, 17, 45, 0)
        self.assertEqual(pattern.get_demand_multiplier(evening_time), 2.5)

        night_time = datetime(2023, 6, 15, 2, 15, 0)
        self.assertEqual(pattern.get_demand_multiplier(night_time), 0.1)

        # Test undefined hour (should default to 1.0)
        undefined_time = datetime(2023, 6, 15, 12, 0, 0)
        self.assertEqual(pattern.get_demand_multiplier(undefined_time), 1.0)

    def test_weekday_pattern(self) -> None:
        """Test weekday demand pattern"""
        weekday_multipliers = {0: 1.2, 4: 1.4, 6: 0.6}  # Monday, Friday, Sunday
        pattern = WeekdayPattern(weekday_multipliers)

        # Test Monday (weekday 0)
        monday = datetime(2023, 6, 12, 10, 0, 0)  # June 12, 2023 is a Monday
        self.assertEqual(pattern.get_demand_multiplier(monday), 1.2)

        # Test Friday (weekday 4)
        friday = datetime(2023, 6, 16, 10, 0, 0)  # June 16, 2023 is a Friday
        self.assertEqual(pattern.get_demand_multiplier(friday), 1.4)

        # Test Sunday (weekday 6)
        sunday = datetime(2023, 6, 18, 10, 0, 0)  # June 18, 2023 is a Sunday
        self.assertEqual(pattern.get_demand_multiplier(sunday), 0.6)

        # Test undefined weekday (should default to 1.0)
        tuesday = datetime(2023, 6, 13, 10, 0, 0)  # June 13, 2023 is a Tuesday
        self.assertEqual(pattern.get_demand_multiplier(tuesday), 1.0)

    def test_rush_hour_pattern(self) -> None:
        """Test rush hour demand pattern"""
        pattern = RushHourPattern(morning_peak=(7, 9), evening_peak=(17, 19), peak_multiplier=2.5)

        # Test morning rush hour
        morning_rush = datetime(2023, 6, 15, 8, 0, 0)
        self.assertEqual(pattern.get_demand_multiplier(morning_rush), 2.5)

        # Test evening rush hour
        evening_rush = datetime(2023, 6, 15, 18, 0, 0)
        self.assertEqual(pattern.get_demand_multiplier(evening_rush), 2.5)

        # Test non-rush hour
        midday = datetime(2023, 6, 15, 12, 0, 0)
        self.assertEqual(pattern.get_demand_multiplier(midday), 1.0)

        # Test edge cases
        before_morning_rush = datetime(2023, 6, 15, 6, 59, 0)
        self.assertEqual(pattern.get_demand_multiplier(before_morning_rush), 1.0)

        after_morning_rush = datetime(2023, 6, 15, 9, 0, 0)
        self.assertEqual(pattern.get_demand_multiplier(after_morning_rush), 1.0)

    def test_rush_hour_pattern_default_values(self) -> None:
        """Test rush hour pattern with default values"""
        pattern = RushHourPattern()

        # Default morning rush (7-9)
        morning_rush = datetime(2023, 6, 15, 8, 0, 0)
        self.assertEqual(pattern.get_demand_multiplier(morning_rush), 2.0)

        # Default evening rush (17-19)
        evening_rush = datetime(2023, 6, 15, 18, 0, 0)
        self.assertEqual(pattern.get_demand_multiplier(evening_rush), 2.0)


class TestTemporalPatternEngine(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test fixtures"""
        self.config = {
            "base_rate": 10.0,
            "hourly_pattern": {8: 2.0, 17: 2.5},
            "weekday_pattern": {0: 1.2, 6: 0.6},
            "rush_hour_pattern": {
                "morning_start": 7,
                "morning_end": 9,
                "evening_start": 17,
                "evening_end": 19,
                "peak_multiplier": 1.5,
            },
        }
        self.engine = TemporalPatternEngine(self.config)

    def test_initialization_with_config(self) -> None:
        """Test engine initialization with provided config"""
        self.assertEqual(self.engine.base_rate, 10.0)
        self.assertEqual(len(self.engine.patterns), 3)  # hourly, weekday, rush hour

    def test_initialization_with_defaults(self) -> None:
        """Test engine initialization with default patterns"""
        minimal_config: dict[str, float] = {"base_rate": 5.0}
        engine = TemporalPatternEngine(minimal_config)

        self.assertEqual(engine.base_rate, 5.0)
        self.assertEqual(len(engine.patterns), 3)  # Should still have all 3 default patterns

    def test_calculate_demand_rate_combined_patterns(self) -> None:
        """Test demand rate calculation with multiple patterns"""
        # Monday morning rush hour: should combine all multipliers
        monday_morning_rush = datetime(2023, 6, 12, 8, 0, 0)  # Monday, 8 AM

        # Expected: base_rate * hourly_multiplier * weekday_multiplier * rush_hour_multiplier
        # 10.0 * 2.0 * 1.2 * 1.5 = 36.0
        rate = self.engine.calculate_demand_rate(monday_morning_rush)
        self.assertEqual(rate, 36.0)

    def test_calculate_demand_rate_partial_patterns(self) -> None:
        """Test demand rate with only some patterns active"""
        # Sunday afternoon (no rush hour, different weekday multiplier)
        sunday_afternoon = datetime(2023, 6, 18, 14, 0, 0)  # Sunday, 2 PM

        # Expected: base_rate * 1.0 (no hourly) * 0.6 (Sunday) * 1.0 (no rush hour)
        # 10.0 * 1.0 * 0.6 * 1.0 = 6.0
        rate = self.engine.calculate_demand_rate(sunday_afternoon)
        self.assertEqual(rate, 6.0)

    def test_calculate_demand_rate_no_multipliers(self) -> None:
        """Test demand rate when no patterns apply"""
        # Tuesday midday (no special patterns)
        tuesday_midday = datetime(2023, 6, 13, 12, 0, 0)  # Tuesday, 12 PM

        # Expected: base_rate * 1.0 * 1.0 * 1.0 = 10.0
        rate = self.engine.calculate_demand_rate(tuesday_midday)
        self.assertEqual(rate, 10.0)

    def test_add_custom_pattern(self) -> None:
        """Test adding a custom pattern to the engine"""
        initial_pattern_count = len(self.engine.patterns)

        # Add a custom hourly pattern
        custom_pattern = HourlyPattern({12: 3.0})
        self.engine.add_pattern(custom_pattern)

        self.assertEqual(len(self.engine.patterns), initial_pattern_count + 1)

        # Test that the new pattern affects calculations
        noon_time = datetime(2023, 6, 15, 12, 0, 0)
        rate = self.engine.calculate_demand_rate(noon_time)

        # Should include the custom pattern's multiplier
        self.assertGreater(rate, self.engine.base_rate)

    def test_engine_with_minimal_config(self) -> None:
        """Test engine behavior with minimal configuration"""
        minimal_config: dict[str, Any] = {}
        engine = TemporalPatternEngine(minimal_config)

        # Should use default base rate
        self.assertEqual(engine.base_rate, 10.0)

        # Should still calculate rates
        test_time = datetime(2023, 6, 15, 12, 0, 0)
        rate = engine.calculate_demand_rate(test_time)
        self.assertIsInstance(rate, float)
        self.assertGreater(rate, 0)


if __name__ == "__main__":
    unittest.main()
