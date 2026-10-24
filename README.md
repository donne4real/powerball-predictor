# ⚡ Powerball Predictor

Data-driven Powerball analysis: hot/cold number frequency, due-number tracking, and
weighted prediction strategies over **296 historical draws**.

**Live demo:** https://powerball-predictor.netlify.app

> Lottery draws are random by design. No strategy here can predict a winning combination.
> This is an entertainment and data-analysis tool.

---

## Two implementations, one engine

This repo holds the same analysis engine in two forms:

| | `python/` | `web/` |
|---|---|---|
| What | Flask REST API + CLI | Static single-page app |
| Runtime | Python 3.8+ | Browser only — no backend |
| Run it | `python run.py web` | Open `web/index.html` |
| Deploy | any Python host | Netlify / GitHub Pages / Cloudflare Pages |
| Port | 5000 | static files |

The `web/` version is a **faithful port** of the Python engine to JavaScript, not a
reimplementation. It was verified by running both engines against the same 296-draw
dataset and diffing every output — frequency maps, hot/cold rankings, due-number
ordering, pair counts, averages and the date span all match exactly.

---

## The engine

`powerball/engine.py` (Python) and `web/assets/js/engine.js` (JavaScript) implement the
same logic:

- **Frequency analysis** — occurrence counts for white balls (1–69) and powerballs (1–26)
- **Hot numbers** — most frequently drawn
- **Cold numbers** — least frequently drawn
- **Due numbers** — gone the longest without appearing
- **Top pairs** — most frequently co-occurring white-ball combinations
- **Weighted prediction** — each number weighted by `(count + 0.1) ** exponent`, then
  sampled

### Prediction strategies

| Strategy | Exponent | Behaviour |
|---|---|---|
| `balanced` | 1.2 | weighted random — favours hot slightly, keeps variety |
| `hot` | 2.5 | strongly favours the most-frequent numbers |
| `cold` | −1.5 | favours the least-frequent / due numbers |
| `random` | — | pure random, no historical bias |

The 5 white balls are sampled **without replacement** (Efraimidis–Spirakis keys — the same
distribution as `numpy.random.choice(..., replace=False, p=...)`); the powerball is sampled
with replacement from its weighted distribution.

---

## Python usage

```bash
cd python
pip install -r requirements.txt

python run.py predict              # 5 balanced predictions
python run.py predict -s hot -n 10 # 10 hot-strategy predictions
python run.py analyze              # frequency analysis
python run.py stats                # summary statistics
python run.py history -n 10        # recent draws
python run.py add 2025-06-04 5 12 28 44 69 10 -m 2
python run.py web                  # dashboard on http://127.0.0.1:5000
```

### REST API (Flask)

| Endpoint | Method | Returns |
|---|---|---|
| `/api/analysis` | GET | full analysis report |
| `/api/predict` | GET | predictions (`strategy`, `num`) |
| `/api/history` | GET | `{ "draws": [...] }` |
| `/api/add` | POST | add a draw result |

---

## Web usage

```bash
cd web
npx serve .
# or just open index.html - it is plain static files
```

The web build fetches `data/powerball_history.csv` and does every computation in the
browser. No API calls, no server, no tracking.

### Updating the data

Replace `web/data/powerball_history.csv` with an updated file in the same format and
redeploy. The web build reads it on load.

```csv
date,number1,number2,number3,number4,number5,powerball,multiplier
2026-06-03,3,17,30,44,49,12,3
```

Dates must be `YYYY-MM-DD`. White balls 1–69, powerball 1–26.

---

## Layout

```
python/
  powerball/
    engine.py        analysis + prediction engine
    data_loader.py   CSV loading, adding draws, starter data
    cli.py           command-line interface
    web.py           Flask REST API
    fetcher.py       live draw fetching
  templates/index.html
  data/powerball_history.csv
  scripts/           one-off maintenance and debug scripts
  run.py             entry point
  GEMINI.md          architecture notes
  test_core.py
web/
  index.html
  assets/js/engine.js   JS port of engine.py
  assets/js/app.js      UI
  assets/css/style.css
  data/powerball_history.csv
```

---

## Notes

- `web/` uses Chart.js from a CDN for the frequency histogram.
- The web build is a static site — it can go on Netlify, GitHub Pages or Cloudflare Pages
  with no build step.
- `python/scripts/` holds the one-off fetch and CLI repair scripts kept from development.

---

*Part of the [Leye Ajibola AI Engineer portfolio](https://leye-ajibola.netlify.app).*
