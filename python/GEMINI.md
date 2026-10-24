# Powerball Predictor

Data-driven analysis and prediction engine for Powerball numbers.

## Architecture

- **Engine (`powerball/engine.py`):** Core logic for frequency analysis and weighted predictions.
- **CLI (`powerball/cli.py`):** Command-line interface for analysis, statistics, and history.
- **Web (`powerball/web.py`):** Flask-based REST API and dashboard.
- **Data (`powerball/data_loader.py`):** CSV management and persistence.

## Prediction Engine

The predictor uses a weighted random selection based on historical frequencies.

### Strategies
- **Balanced (Default):** Uses an exponent of `1.2` to slightly favor hot numbers while maintaining variety.
- **Hot:** Uses an exponent of `2.5` to strongly favor the most frequent numbers.
- **Cold:** Uses an exponent of `-1.5` to favor numbers that haven't appeared frequently (due numbers).
- **Random:** Pure random selection.

### Implementation Detail
Weights are calculated as `(count + 0.1) ** exponent`. This ensures that even numbers with zero hits have a non-zero probability, especially when using negative exponents for the "Cold" strategy.

## Web API Conventions

The frontend and backend use a specific mapping for data consistency:

- **Predictions:** Backend returns `white`, frontend expects `white_balls`.
- **History:** `api/history` returns a JSON object with a `draws` key containing the list of recent draws.
- **Strategies:** UI labels "Frequency" and "Due" map to "hot" and "cold" respectively in the backend.

## Development & Testing

### Testing
Run core logic tests before committing changes:
```bash
python test_core.py
```

### Data Updates
Fetch latest historical data:
```bash
python run.py fetch
```

### Local Web Server
```bash
python run.py web
```

## Standards
- **Dependencies:** Keep `requirements.txt` lean. Avoid heavy plotting libraries in the core engine; use Chart.js for visualization in the web dashboard.
- **Data Integrity:** Always use `data_loader.py` for CSV access to ensure date sorting and consistent column mapping.
