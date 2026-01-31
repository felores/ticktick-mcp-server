#!/usr/bin/env python3
"""
Command-line interface for TickTick MCP server.
"""

import sys
import argparse
import logging

from .src.server import main as server_main
from .src.auth import run_auth_flow
from .src.credentials import get_access_token


def check_auth_setup() -> bool:
    """Check if authentication is set up (tokens exist in persistent storage)."""
    return get_access_token() is not None


def main():
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(description="TickTick MCP Server")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # 'run' command for running the server
    run_parser = subparsers.add_parser("run", help="Run the TickTick MCP server")
    run_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    # 'auth' command for authentication
    subparsers.add_parser("auth", help="Authenticate with TickTick")

    args = parser.parse_args()

    # If no command specified, default to 'run'
    if not args.command:
        args.command = "run"

    # Run the appropriate command
    if args.command == "auth":
        sys.exit(run_auth_flow())

    elif args.command == "run":
        # Configure logging
        log_level = logging.DEBUG if args.debug else logging.WARNING
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Start the server
        try:
            server_main()
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
