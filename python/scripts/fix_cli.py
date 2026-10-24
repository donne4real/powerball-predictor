"""Update CLI with fetch and export features."""
import sys

path = r'C:\Users\Public\powerball-predictor\powerball\cli.py'
with open(path, 'r') as f:
    c = f.read()

# 1. Update imports
c = c.replace(
    'from .data_loader import load_draws, add_draw, get_data_path\nfrom .engine import generate_prediction, analyze_draws',
    'import json\nimport csv\nimport os\nfrom pathlib import Path\nfrom datetime import datetime\nfrom .data_loader import load_draws, add_draw, get_data_path\nfrom .engine import generate_prediction, analyze_draws, frequency_analysis'
)

# 2. Add --export to predict subparser
c = c.replace(
    "p.add_argument('-s', '--strategy', choices=['balanced', 'hot', 'cold', 'random'],\n                   default='balanced', help='Prediction strategy (default: balanced)')",
    "p.add_argument('-s', '--strategy', choices=['balanced', 'hot', 'cold', 'random'],\n                   default='balanced', help='Prediction strategy (default: balanced)')\n    p.add_argument('-o', '--export', metavar='FILE', type=str, default=None,\n                   help='Export predictions to JSON file')"
)

# 3. Add fetch command before add command
c = c.replace(
    "    a = sub.add_parser('add', help='Add a new draw result')",
    "    sub.add_parser('fetch', help='Fetch latest historical data from the web')\n\n    a = sub.add_parser('add', help='Add a new draw result')"
)

# 4. Update cmd_predict to handle --export
old_predict = """def cmd_predict(args, draws):
    predictions = generate_prediction(draws, strategy=args.strategy, num_predictions=args.num)
    strategy_name = args.strategy.upper()
    print(f\"\\n{'='*55}\")
    print(f\"  POWERBALL PREDICTIONS  [{strategy_name} strategy]\")
    print(f\"{'='*55}\")
    for i, pred in enumerate(predictions, 1):
        ws = \"  \".join(f\"{n:>2}\" for n in pred[\"white\"])
        print(f\"\\n  #{i}:  White: {ws}  |  PB: {pred['powerball']:>2}\")
    print(f\"\\n  Based on history from {get_data_path()}\")
    print(f\"{'='*55}\")
    print(\"  NOTE: For entertainment purposes only. Play responsibly!\\n\")"""

new_predict = """def cmd_predict(args, draws):
    predictions = generate_prediction(draws, strategy=args.strategy, num_predictions=args.num)
    strategy_name = args.strategy.upper()
    print(f\"\\n{'='*55}\")
    print(f\"  POWERBALL PREDICTIONS  [{strategy_name} strategy]\")
    print(f\"{'='*55}\")
    for i, pred in enumerate(predictions, 1):
        ws = \"  \".join(f\"{n:>2}\" for n in pred[\"white\"])
        print(f\"\\n  #{i}:  White: {ws}  |  PB: {pred['powerball']:>2}\")
    print(f\"\\n  Based on history from {get_data_path()}\")
    print(f\"{'='*55}\")
    print(\"  NOTE: For entertainment purposes only. Play responsibly!\\n\")

    # Export to file if requested
    if args.export:
        export_data = {
            \"exported_at\": datetime.now().isoformat(),
            \"strategy\": args.strategy,
            \"total_draws_analyzed\": len(draws),
            \"predictions\": predictions,
        }
        filepath = args.export
        if not filepath.endswith('.json'):
            filepath += '.json'
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        print(f\"  [Exported to {filepath}]\\n\")"""

c = c.replace(old_predict, new_predict)

# 5. Add cmd_fetch function
c = c.replace(
    "def cmd_add(args, draws=None):\n    add_draw(args.date, args.n1, args.n2, args.n3, args.n4, args.n5, args.pb, args.multiplier)",
    "def cmd_fetch(args, draws=None):\n    \"\"\"Fetch latest data from the web.\"\"\"\n    from .fetcher import fetch_and_update\n    fetch_and_update()\n\n\ndef cmd_add(args, draws=None):\n    add_draw(args.date, args.n1, args.n2, args.n3, args.n4, args.n5, args.pb, args.multiplier)"
)

# 6. Update main() to handle fetch
c = c.replace(
    '    if args.command in ("predict", "analyze", "stats", "history"):',
    '    if args.command == "fetch":\n        cmd_fetch(args)\n    elif args.command in ("predict", "analyze", "stats", "history"):'
)

with open(path, 'w') as f:
    f.write(c)
print('CLI updated successfully')
