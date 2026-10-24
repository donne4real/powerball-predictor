"""Flask web interface for the Powerball Predictor."""

from flask import Flask, jsonify, render_template, request

from .data_loader import load_draws, add_draw, get_data_path
from .engine import generate_prediction, analyze_draws

# Point Flask to the correct templates folder (project root, not package root)
import os
_templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
app = Flask(__name__, template_folder=_templates_dir)


@app.route("/")
def index():
    """Render the main dashboard page."""
    draws = load_draws()
    analysis = analyze_draws(draws) if draws else None
    return render_template("index.html", analysis=analysis)


@app.route("/api/analysis")
def api_analysis():
    """Return analysis data as JSON."""
    draws = load_draws()
    if not draws:
        return jsonify({"error": "No data available"}), 404
    return jsonify(analyze_draws(draws))


@app.route("/api/predict", methods=["GET", "POST"])
def api_predict():
    """Return predictions as JSON.

    Query params (GET) or JSON body (POST):
        strategy (str): balanced, hot, cold, or random (default: balanced)
        num/count (int): Number of predictions (default: 5)
    """
    draws = load_draws()
    if not draws:
        return jsonify({"error": "No data available"}), 404

    if request.method == "POST":
        data = request.get_json() or {}
        strategy = data.get("strategy", "balanced")
        num = int(data.get("count", data.get("num", 5)))
    else:
        strategy = request.args.get("strategy", "balanced")
        num = int(request.args.get("num", 5))

    num = min(num, 20)
    
    # Map frontend strategy names to backend
    strategy_map = {
        "frequency": "hot",
        "due": "cold"
    }
    backend_strategy = strategy_map.get(strategy, strategy)
    
    predictions = generate_prediction(draws, strategy=backend_strategy, num_predictions=num)
    
    # Format for frontend
    formatted_preds = []
    for p in predictions:
        formatted_preds.append({
            "white_balls": p["white"],
            "powerball": p["powerball"],
            "strategy": p["strategy"]
        })

    return jsonify({
        "strategy": strategy,
        "predictions": formatted_preds,
        "total_draws_analyzed": len(draws),
    })


@app.route("/api/history")
def api_history():
    """Return recent draw history as JSON.

    Query params:
        num (int): Number of draws (default: 20)
    """
    draws = load_draws()
    if not draws:
        return jsonify({"error": "No data available"}), 404
    num = min(int(request.args.get("num", 20)), 100)
    recent = draws[-num:]
    
    # Format for frontend
    formatted_history = []
    for d in recent:
        formatted_history.append({
            "date": d["date"],
            "white_balls": [d["number1"], d["number2"], d["number3"], d["number4"], d["number5"]],
            "powerball": d["powerball"]
        })
        
    return jsonify({"draws": formatted_history})


@app.route("/api/add", methods=["POST"])
def api_add():
    """Add a new draw via POST JSON body.

    Body: {"date": "YYYY-MM-DD", "n1":1, "n2":2, "n3":3, "n4":4, "n5":5, "powerball":10, "multiplier":2}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    try:
        add_draw(
            data["date"], int(data["n1"]), int(data["n2"]), int(data["n3"]),
            int(data["n4"]), int(data["n5"]), int(data["powerball"]),
            int(data.get("multiplier", 1)),
        )
        return jsonify({"status": "ok", "message": f"Draw on {data['date']} added."})
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


def run_server(host="127.0.0.1", port=5000, debug=False):
    """Run the Flask web server."""
    print(f"\n  🎱 Powerball Predictor Web App")
    print(f"  {'='*40}")
    print(f"  Open: http://{host}:{port}")
    print(f"  Data: {get_data_path()}")
    print(f"  {'='*40}\n")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server(debug=True)
