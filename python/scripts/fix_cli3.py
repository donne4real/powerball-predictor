"""Fix CLI: add --export arg to predict subparser."""
path = r'C:\Users\Public\powerball-predictor\powerball\cli.py'
with open(path, 'r') as f:
    c = f.read()

old = '                   default="balanced", help="Prediction strategy (default: balanced)")\n\n    sub.add_parser("analyze"'
new = '                   default="balanced", help="Prediction strategy (default: balanced)")\n    p.add_argument("-o", "--export", metavar="FILE", type=str, default=None,\n                   help="Export predictions to JSON file")\n\n    sub.add_parser("analyze"'

c = c.replace(old, new)
with open(path, 'w') as f:
    f.write(c)
print('Done')
