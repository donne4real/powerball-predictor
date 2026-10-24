"""Fix #2: add fetch parser to CLI."""
path = r'C:\Users\Public\powerball-predictor\powerball\cli.py'
with open(path, 'r') as f:
    c = f.read()

# Add fetch subparser before add
c = c.replace(
    '    a = sub.add_parser("add",',
    '    sub.add_parser("fetch", help="Fetch latest historical data from the web")\n\n    a = sub.add_parser("add",'
)

with open(path, 'w') as f:
    f.write(c)
print('Fixed')
