"""CLI interface for the Powerball Predictor."""

import argparse
import json
import csv
import os
from pathlib import Path
from datetime import datetime
from .data_loader import load_draws, add_draw, get_data_path
from .engine import generate_prediction, analyze_draws, frequency_analysis


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="powerball",
        description=" Powerball Predictor  Analyze history & predict Powerball numbers.",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    p = sub.add_parser("predict", help="Generate Powerball predictions")
    p.add_argument("-n", "--num", type=int, default=5, help="Number of predictions (default: 5)")
    p.add_argument("-s", "--strategy", choices=["balanced", "hot", "cold", "random"],
                   default="balanced", help="Prediction strategy (default: balanced)")
    p.add_argument("-o", "--export", metavar="FILE", type=str, default=None,
                   help="Export predictions to JSON file")

    sub.add_parser("analyze", help="Show frequency analysis of historical draws")
    sub.add_parser("stats", help="Show summary statistics")

    h = sub.add_parser("history", help="List recent draws")
    h.add_argument("-n", "--num", type=int, default=10, help="Number of recent draws (default: 10)")

    sub.add_parser("fetch", help="Fetch latest historical data from the web")

    a = sub.add_parser("add", help="Add a new draw result")
    a.add_argument("date", help="Date (YYYY-MM-DD)")
    a.add_argument("n1", type=int, help="White ball 1")
    a.add_argument("n2", type=int, help="White ball 2")
    a.add_argument("n3", type=int, help="White ball 3")
    a.add_argument("n4", type=int, help="White ball 4")
    a.add_argument("n5", type=int, help="White ball 5")
    a.add_argument("pb", type=int, help="Powerball number")
    a.add_argument("-m", "--multiplier", type=int, default=1, help="Multiplier")

    return parser
def cmd_predict(args, draws):
    predictions = generate_prediction(draws, strategy=args.strategy, num_predictions=args.num)
    strategy_name = args.strategy.upper()
    print(f"\n{'='*55}")
    print(f"  POWERBALL PREDICTIONS  [{strategy_name} strategy]")
    print(f"{'='*55}")
    for i, pred in enumerate(predictions, 1):
        ws = "  ".join(f"{n:>2}" for n in pred["white"])
        print(f"\n  #{i}:  White: {ws}  |  PB: {pred['powerball']:>2}")
    print(f"\n  Based on history from {get_data_path()}")
    print(f"{'='*55}")
    print("  NOTE: For entertainment purposes only. Play responsibly!\n")

    # Export to file if requested
    if args.export:
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "strategy": args.strategy,
            "total_draws_analyzed": len(draws),
            "predictions": predictions,
        }
        filepath = args.export
        if not filepath.endswith('.json'):
            filepath += '.json'
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        print(f"  [Exported to {filepath}]\n")



def cmd_analyze(args, draws):
    analysis = analyze_draws(draws)
    print(f"\n{'='*55}")
    print(f"   POWERBALL ANALYSIS")
    print(f"{'='*55}")
    print(f"\n  Total draws: {analysis['total_draws']}")
    print(f"  Date range:  {analysis['date_range'][0]} to {analysis['date_range'][1]}")
    print(f"\n   HOTTEST WHITE BALLS (top 15):")
    for num, count in analysis["hot_white"]:
        pct = count / analysis["total_draws"] * 100
        bar = "#" * max(1, int(pct / 2))
        print(f"    {num:>2}: {count:>3}x ({pct:.1f}%)  {bar}")
    print(f"\n  COLDEST WHITE BALLS (bottom 15):")
    for num, count in analysis["cold_white"]:
        print(f"    {num:>2}: {count:>3}x")
    print(f"\n   HOTTEST POWERBALLS:")
    for num, count in analysis["hot_pb"]:
        pct = count / analysis["total_draws"] * 100
        print(f"    {num:>2}: {count:>3}x ({pct:.1f}%)")
    print(f"\n   MOST DUE WHITE BALLS:")
    for i, num in enumerate(analysis["due_white"][:15], 1):
        print(f"    {i:>2}. {num:>2}")
    print(f"\n   TOP NUMBER PAIRS:")
    for (a, b), count in analysis["top_pairs"][:10]:
        print(f"    ({a:>2}, {b:>2}): {count}x")
    print()


def cmd_stats(args, draws):
    analysis = analyze_draws(draws)
    wf, pf = analysis["white_freq"], analysis["pb_freq"]
    print(f"\n{'='*55}")
    print(f"   POWERBALL STATISTICS")
    print(f"{'='*55}")
    print(f"\n   Total draws:      {analysis['total_draws']}")
    print(f"   Date range:       {analysis['date_range'][0]} to {analysis['date_range'][1]}")
    print(f"   Data file:        {get_data_path()}")
    print(f"\n   White balls (1-69):")
    print(f"    Most frequent:  {analysis['hot_white'][0][0]} ({analysis['hot_white'][0][1]}x)")
    print(f"    Least frequent: {analysis['cold_white'][0][0]} ({analysis['cold_white'][0][1]}x)")
    print(f"    Frequency range: {min(wf.values())}-{max(wf.values())}")
    print(f"\n   Powerballs (1-26):")
    print(f"    Most frequent:  {analysis['hot_pb'][0][0]} ({analysis['hot_pb'][0][1]}x)")
    print(f"    Least frequent: {analysis['cold_pb'][0][0]} ({analysis['cold_pb'][0][1]}x)")
    print(f"    Frequency range: {min(pf.values())}-{max(pf.values())}\n")


def cmd_history(args, draws):
    n = min(args.num, len(draws))
    print(f"\n{'='*55}")
    print(f"   RECENT DRAWS (last {n})")
    print(f"{'='*55}")
    for d in draws[-n:]:
        ws = f"{d['number1']:>2}  {d['number2']:>2}  {d['number3']:>2}  {d['number4']:>2}  {d['number5']:>2}"
        print(f"  {d['date']}  |  {ws}  |  PB: {d['powerball']:>2}  |  x{d.get('multiplier', 1)}")
    print()


def cmd_fetch(args, draws=None):
    """Fetch latest data from the web."""
    from .fetcher import fetch_and_update
    fetch_and_update()


def cmd_add(args, draws=None):
    add_draw(args.date, args.n1, args.n2, args.n3, args.n4, args.n5, args.pb, args.multiplier)


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return

    if args.command == "fetch":
        cmd_fetch(args)
    elif args.command in ("predict", "analyze", "stats", "history"):
        draws = load_draws()
        if not draws:
            print("[ERROR] No draw data available. Run 'powerball add' to add draws first.")
            return
        {"predict": cmd_predict, "analyze": cmd_analyze,
         "stats": cmd_stats, "history": cmd_history}[args.command](args, draws)
    elif args.command == "add":
        cmd_add(args)


if __name__ == "__main__":
    main()

