#!/usr/bin/env python3
"""
Main entry point for the demand generator.
"""

import argparse
import signal
import sys

from demand_generator import DemandGenerator


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\nShutting down demand generator...')
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description='Transit Demand Generator')
    parser.add_argument(
        '--config',
        default='config/demand_config.yaml',
        help='Path to configuration file (default: config/demand_config.yaml)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        help='Run for specified number of seconds (default: run indefinitely)'
    )

    args = parser.parse_args()

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Initialize demand generator
        print(f"Loading configuration from: {args.config}")
        generator = DemandGenerator(args.config)

        # Start streaming
        print("Starting demand generation...")
        print("Press Ctrl+C to stop")
        generator.start_streaming()

        if args.duration:
            print(f"Running for {args.duration} seconds...")
            import time
            time.sleep(args.duration)
            generator.stop_streaming()
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
                print("Demand generator stopped.")

    except FileNotFoundError:
        print(f"Error: Configuration file '{args.config}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
