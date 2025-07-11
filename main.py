#!/usr/bin/env python3
"""
Main entry point for the demand generator.
"""

import argparse
import signal
import sys
from typing import Any

from demand_generator import DemandGenerator


def signal_handler(sig: int, frame: Any) -> None:
    """Handle Ctrl+C gracefully"""
    # Don't print anything - let main() handle cleanup messages
    sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Transit Demand Generator")
    parser.add_argument(
        "--config",
        default="config/demand_config.yaml",
        help="Path to configuration file (default: config/demand_config.yaml)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        help="Run for specified number of seconds (default: run indefinitely)",
    )

    args = parser.parse_args()

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Initialize demand generator
        generator = DemandGenerator(args.config)

        # Only print status messages if not in JSON output mode
        if generator.output_format != "json":
            print(f"Loading configuration from: {args.config}")
            print("Starting demand generation...")
            print("Press Ctrl+C to stop")

        generator.start_streaming()

        if args.duration:
            if generator.output_format != "json":
                print(f"Running for {args.duration} seconds...")
            import time

            time.sleep(args.duration)
            generator.stop_streaming()
            if generator.output_format != "json":
                print("Finished generating demand.")
        else:
            # Run indefinitely until interrupted
            try:
                while generator.running:
                    import time

                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                generator.stop_streaming()
                if generator.output_format != "json":
                    print("Demand generator stopped.")

    except FileNotFoundError:
        print(f"Error: Configuration file '{args.config}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
