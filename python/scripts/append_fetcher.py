"""Append remaining functions to fetcher.py"""
more_code = '''

def fetch_latest_from_powerball_com():
    """Fetch the most recent draw from powerball.com."""
    url = "https://www.powerball.com/"
    print("  Checking powerball.com for latest draw...")
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [!] Failed: {e}")
        return None
    pat = r"(\\w+,\\s+\\w+\\s+\\d+,\\s+\\d+)[^0-9]*(\\d+)\\s+(\\d+)\\s+(\\d+)\\s+(\\d+)\\s+(\\d+)\\s+(\\d+)"
    match = re.search(pat, html)
    if not match:
        print("  [!] Could not parse powerball.com data")
        return None
    n1, n2, n3, n4, n5 = int(match.group(2)), int(match.group(3)), int(match.group(4)), int(match.group(5)), int(match.group(6))
    pb = int(match.group(7))
    for fmt in ("%a, %b %d, %Y", "%A, %B %d, %Y"):
        try:
            dt = datetime.strptime(match.group(1), fmt)
            return (dt.strftime("%Y-%m-%d"), n1, n2, n3, n4, n5, pb, 1)
        except ValueError:
            pass
    print(f"  [!] Could not parse date: {match.group(1)}")
    return None


def merge_draws(existing, new_draws):
    """Merge new draws into existing CSV, avoiding duplicates."""
    existing_dates = {d["date"] for d in existing}
    count = 0
    for draw in new_draws:
        if draw[0] not in existing_dates:
            add_draw(*draw)
            existing_dates.add(draw[0])
            count += 1
    return count


def fetch_and_update():
    """Fetch latest data from the web and update the local CSV."""
    print("\\n  Powerball Data Fetcher")
    print("  ========================")
    existing = load_draws()
    print(f"  Current data: {len(existing)} draws")
    total_new = 0
    for year in (2025, 2026):
        draws = fetch_year(year)
        total_new += merge_draws(existing, draws)
        existing = load_draws()
    latest = fetch_latest_from_powerball_com()
    if latest:
        total_new += merge_draws(existing, [latest])
    print(f"\\n  [OK] Added {total_new} new draws!")
    print(f"  Total now: {len(load_draws())} draws\\n")
    return total_new
'''

with open(r'C:\Users\Public\powerball-predictor\powerball\fetcher.py', 'a') as f:
    f.write(more_code)
print('Appended successfully')
