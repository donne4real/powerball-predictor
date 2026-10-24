"""Fetch live Powerball data from the web and update local history."""

import re
import urllib.request
from datetime import datetime
from typing import List, Optional, Tuple

from .data_loader import load_draws, add_draw


def fetch_year(year: int) -> List[Tuple]:
    """Fetch Powerball draws for a given year from lottery.net."""
    url = f"https://www.lottery.net/powerball/numbers/{year}"
    print(f"  Fetching {year} data from lottery.net...")

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [!] Failed to fetch {year}: {e}")
        return []

    draws = []
    # Find dates: "<br>Month Day, Year"
    for dm in re.finditer(r"<br>\s*(\w+)\s+(\d+),\s+(\d+)", html):
        month_name = dm.group(1)
        day = int(dm.group(2))
        year_num = int(dm.group(3))

        try:
            dt = datetime.strptime(f"{month_name} {day}, {year_num}", "%B %d, %Y")
            date_str = dt.strftime("%Y-%m-%d")
        except ValueError:
            try:
                dt = datetime.strptime(f"{month_name} {day}, {year_num}", "%b %d, %Y")
                date_str = dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Find numbers after this date
        us = html.find('<ul class="multi results powerball">', dm.end())
        if us == -1:
            continue
        ue = html.find('</ul>', us)
        if ue == -1:
            continue
        ul = html[us:ue]

        balls = re.findall(r'<li class="ball">\s*(\d+)', ul)
        pb_m = re.search(r'<li class="powerball">\s*(\d+)', ul)
        pp_m = re.search(r'<li class="power-play">\s*(\d+)', ul)

        if len(balls) >= 5 and pb_m:
            n1, n2, n3, n4, n5 = [int(b) for b in balls[:5]]
            pb = int(pb_m.group(1))
            mult = int(pp_m.group(1)) if pp_m else 1
            draws.append((date_str, n1, n2, n3, n4, n5, pb, mult))

    draws.sort(key=lambda d: d[0])
    print(f"  Found {len(draws)} draws for {year}")
    return draws


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
    pat = r"(\w+,\s+\w+\s+\d+,\s+\d+)[^0-9]*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)"
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
    print("\n  Powerball Data Fetcher")
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
    print(f"\n  [OK] Added {total_new} new draws!")
    print(f"  Total now: {len(load_draws())} draws\n")
    return total_new
