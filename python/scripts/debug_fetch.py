"""Debug the fetch HTML parsing."""
with open(r'C:\Users\Public\powerball-predictor\debug.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Search for draw data
targets = ['June 3', 'Wednesday', 'Monday', '2026', '14 16 38']
for t in targets:
    idx = html.find(t)
    if idx >= 0:
        print(f'Found "{t}" at pos {idx}')
        print(repr(html[max(0,idx-20):idx+100]))
        print()
    else:
        print(f'Not found: "{t}"')
