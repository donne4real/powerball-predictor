import unittest
from powerball.engine import generate_prediction, frequency_analysis, analyze_draws
from powerball.data_loader import create_starter_data, load_draws
import os
from pathlib import Path

class TestEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_csv = Path("test_history.csv")
        create_starter_data(cls.test_csv)
        cls.draws = load_draws(cls.test_csv)

    @classmethod
    def tearDownClass(cls):
        if cls.test_csv.exists():
            cls.test_csv.unlink()

    def test_frequency_analysis(self):
        white_freq, pb_freq = frequency_analysis(self.draws)
        self.assertEqual(len(white_freq), 69)
        self.assertEqual(len(pb_freq), 26)
        self.assertTrue(all(isinstance(v, int) for v in white_freq.values()))

    def test_generate_prediction(self):
        for strategy in ["balanced", "hot", "cold", "random"]:
            preds = generate_prediction(self.draws, strategy=strategy, num_predictions=3)
            self.assertEqual(len(preds), 3)
            for p in preds:
                self.assertEqual(len(p["white"]), 5)
                self.assertTrue(1 <= p["powerball"] <= 26)
                for n in p["white"]:
                    self.assertTrue(1 <= n <= 69)

    def test_analyze_draws(self):
        analysis = analyze_draws(self.draws)
        self.assertIn("total_draws", analysis)
        self.assertIn("white_freq", analysis)
        self.assertIn("pb_freq", analysis)
        self.assertIn("hot_white", analysis)
        self.assertIn("cold_white", analysis)

if __name__ == "__main__":
    unittest.main()
