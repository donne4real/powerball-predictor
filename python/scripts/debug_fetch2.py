"""See how numbers are structured in the HTML."""
with open(r'C:\Users\Public\powerball-predictor\debug.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find a draw row section
idx = html.find('June 3, 2026')
# Print a big chunk around the draw
section = html[idx:idx+800]
print(section)
