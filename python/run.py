#!/usr/bin/env python3
"""Powerball Predictor - Entry Point.

Usage:
    python run.py <command> [options]

Commands:
    predict     Generate predictions
    analyze     Show frequency analysis
    stats       Show summary statistics
    history     List recent draws
    add         Add a new draw result
    web         Launch the web dashboard

Examples:
    python run.py predict
    python run.py predict -s hot -n 10
    python run.py analyze
    python run.py history -n 5
    python run.py add 2025-06-04 3 17 28 44 69 10 -m 2
    python run.py web
"""

import sys


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == "web":
        from powerball.web import run_server
        port = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 5000
        run_server(port=port, debug=False)
    else:
        from powerball.cli import main as cli_main
        # Pass remaining args through (skip the script name)
        cli_main(sys.argv[1:])


if __name__ == "__main__":
    main()
