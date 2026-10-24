/* ============================================================
   Powerball Predictor - analysis & prediction engine
   --------------------------------------------------------
   A faithful port of the Python engine (powerball/engine.py and
   powerball/data_loader.py) to JavaScript, so the whole tool runs
   in the browser with no backend.

   Ported behaviour preserved exactly:
     - frequency counting over white balls and powerballs
     - hot / cold ranking (stable sort, same tie order as Python)
     - "due" numbers = longest since last appearance
     - weighted random with weight = (count + 0.1) ** exponent
     - weighted sampling WITHOUT replacement for the 5 white balls
       (Efraimidis-Spirakis keys; same distribution as
        numpy.random.choice(..., replace=False, p=...))
     - weighted sampling WITH replacement for the single powerball
   ============================================================ */

(function (global) {
  "use strict";

  // Powerball ranges
  const WHITE_MIN = 1, WHITE_MAX = 69;
  const POWERBALL_MIN = 1, POWERBALL_MAX = 26;
  const NUM_WHITE = 5;

  const COL = {
    DATE: "date",
    N1: "number1", N2: "number2", N3: "number3", N4: "number4", N5: "number5",
    PB: "powerball", MP: "multiplier"
  };

  /* ---------- data loading ---------- */

  /** Parse CSV text into draw objects, sorted by date ascending. */
  function parseDraws(csvText) {
    const lines = csvText.split(/\r?\n/).filter((l) => l.trim().length > 0);
    if (lines.length < 2) return [];

    const header = lines[0].split(",").map((h) => h.trim());
    const idx = {};
    header.forEach((h, i) => { idx[h] = i; });

    const draws = [];
    for (let i = 1; i < lines.length; i++) {
      const row = lines[i].split(",");
      if (row.length < header.length) continue;
      try {
        draws.push({
          date: row[idx[COL.DATE]].trim(),
          number1: parseInt(row[idx[COL.N1]], 10),
          number2: parseInt(row[idx[COL.N2]], 10),
          number3: parseInt(row[idx[COL.N3]], 10),
          number4: parseInt(row[idx[COL.N4]], 10),
          number5: parseInt(row[idx[COL.N5]], 10),
          powerball: parseInt(row[idx[COL.PB]], 10),
          multiplier: parseInt(row[idx[COL.MP]] || "1", 10) || 1
        });
      } catch (e) {
        continue; // skip malformed rows, matching the Python loader
      }
    }
    draws.sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
    return draws;
  }

  /** Load draws from a URL (used for the bundled CSV). */
  async function loadDraws(url) {
    const res = await fetch(url, { cache: "no-cache" });
    if (!res.ok) throw new Error("Could not load draw history (" + res.status + ")");
    return parseDraws(await res.text());
  }

  /* ---------- analysis ---------- */

  function extractWhiteNumbers(draws) {
    const nums = [];
    for (const d of draws) nums.push(d[COL.N1], d[COL.N2], d[COL.N3], d[COL.N4], d[COL.N5]);
    return nums;
  }

  function extractPowerballs(draws) {
    return draws.map((d) => d[COL.PB]);
  }

  /**
   * Frequency of each white ball and each powerball.
   * Insertion order matters for tie-breaking, so this mirrors the
   * Python Counter + setdefault fill order exactly.
   */
  function frequencyAnalysis(draws) {
    const whiteFreq = new Map();
    const pbFreq = new Map();

    for (const n of extractWhiteNumbers(draws)) {
      whiteFreq.set(n, (whiteFreq.get(n) || 0) + 1);
    }
    for (const n of extractPowerballs(draws)) {
      pbFreq.set(n, (pbFreq.get(n) || 0) + 1);
    }
    for (let n = WHITE_MIN; n <= WHITE_MAX; n++) {
      if (!whiteFreq.has(n)) whiteFreq.set(n, 0);
    }
    for (let n = POWERBALL_MIN; n <= POWERBALL_MAX; n++) {
      if (!pbFreq.has(n)) pbFreq.set(n, 0);
    }
    return { whiteFreq: whiteFreq, pbFreq: pbFreq };
  }

  /** Most frequently drawn numbers. Stable sort, same tie order as Python. */
  function hotNumbers(freq, topN) {
    topN = topN || 15;
    return Array.from(freq.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, topN);
  }

  /** Least frequently drawn numbers. */
  function coldNumbers(freq, topN) {
    topN = topN || 15;
    return Array.from(freq.entries())
      .sort((a, b) => a[1] - b[1])
      .slice(0, topN);
  }

  /** Numbers that have gone the longest without appearing. */
  function dueNumbers(draws) {
    const whiteNums = extractWhiteNumbers(draws);
    const pbNums = extractPowerballs(draws);

    const whiteLast = new Map();
    for (let i = 0; i < whiteNums.length; i++) {
      const n = whiteNums[whiteNums.length - 1 - i]; // reversed iteration
      if (!whiteLast.has(n)) whiteLast.set(n, i);
    }
    const pbLast = new Map();
    for (let i = 0; i < pbNums.length; i++) {
      const n = pbNums[pbNums.length - 1 - i];
      if (!pbLast.has(n)) pbLast.set(n, i);
    }

    const range = (min, max, last) => {
      const out = [];
      for (let n = min; n <= max; n++) out.push(n);
      out.sort((a, b) => {
        const la = last.has(a) ? last.get(a) : -1;
        const lb = last.has(b) ? last.get(b) : -1;
        return lb - la; // reverse=True in Python
      });
      return out;
    };

    return {
      dueWhite: range(WHITE_MIN, WHITE_MAX, whiteLast),
      duePb: range(POWERBALL_MIN, POWERBALL_MAX, pbLast)
    };
  }

  /* ---------- prediction ---------- */

  /** Weighted pick of a single item (replacement allowed). */
  function weightedPick(weights) {
    let total = 0;
    for (const w of weights) total += w;
    let r = Math.random() * total;
    for (let i = 0; i < weights.length; i++) {
      r -= weights[i];
      if (r <= 0) return i;
    }
    return weights.length - 1;
  }

  /**
   * Weighted sample WITHOUT replacement.
   * Efraimidis-Spirakis: key = u^(1/w), take the k largest keys.
   * Produces the same distribution as numpy.random.choice(replace=False, p=...).
   */
  function weightedSampleWithoutReplacement(weights, k) {
    const keyed = weights.map((w, i) => ({ i: i, key: Math.pow(Math.random(), 1 / w) }));
    keyed.sort((a, b) => b.key - a.key);
    return keyed.slice(0, k).map((x) => x.i);
  }

  function randomPrediction() {
    const pool = [];
    for (let n = WHITE_MIN; n <= WHITE_MAX; n++) pool.push(n);
    // Fisher-Yates partial shuffle for 5 distinct whites
    for (let i = 0; i < NUM_WHITE; i++) {
      const j = i + Math.floor(Math.random() * (pool.length - i));
      const t = pool[i]; pool[i] = pool[j]; pool[j] = t;
    }
    const white = pool.slice(0, NUM_WHITE).sort((a, b) => a - b);
    const powerball = POWERBALL_MIN + Math.floor(Math.random() * (POWERBALL_MAX - POWERBALL_MIN + 1));
    return { white: white, powerball: powerball };
  }

  function weightedPrediction(whiteFreq, pbFreq, exponent) {
    const whiteNums = [], pbNums = [];
    for (let n = WHITE_MIN; n <= WHITE_MAX; n++) whiteNums.push(n);
    for (let n = POWERBALL_MIN; n <= POWERBALL_MAX; n++) pbNums.push(n);

    const weightsFor = (freq, nums, exp) => nums.map((n) => Math.pow((freq.get(n) || 0) + 0.1, exp));

    const whiteWeights = weightsFor(whiteFreq, whiteNums, exponent);
    const pbWeights = weightsFor(pbFreq, pbNums, exponent);

    const whiteIdx = weightedSampleWithoutReplacement(whiteWeights, NUM_WHITE);
    const white = whiteIdx.map((i) => whiteNums[i]).sort((a, b) => a - b);

    const pbIdx = weightedPick(pbWeights);
    return { white: white, powerball: pbNums[pbIdx] };
  }

  /**
   * Generate predictions.
   *   balanced (1.2) - slightly favours hot numbers
   *   hot      (2.5) - strongly favours most-frequent numbers
   *   cold    (-1.5) - favours least-frequent / due numbers
   *   random          - pure random, no historical bias
   */
  function generatePrediction(draws, strategy, numPredictions) {
    strategy = strategy || "balanced";
    numPredictions = numPredictions || 5;

    if (!draws || draws.length === 0) {
      const out = [];
      for (let i = 0; i < numPredictions; i++) {
        const p = randomPrediction();
        p.strategy = strategy;
        out.push(p);
      }
      return out;
    }

    const fa = frequencyAnalysis(draws);
    const out = [];
    for (let i = 0; i < numPredictions; i++) {
      let pred;
      if (strategy === "random") {
        pred = randomPrediction();
      } else if (strategy === "hot") {
        pred = weightedPrediction(fa.whiteFreq, fa.pbFreq, 2.5);
      } else if (strategy === "cold") {
        pred = weightedPrediction(fa.whiteFreq, fa.pbFreq, -1.5);
      } else {
        pred = weightedPrediction(fa.whiteFreq, fa.pbFreq, 1.2);
      }
      pred.strategy = strategy;
      out.push(pred);
    }
    return out;
  }

  /* ---------- full report ---------- */

  /** Python-style round: correct to `digits` decimals, half-to-even. */
  function pyRound(x, digits) {
    const d = Math.pow(10, digits);
    const scaled = Number((x * d).toPrecision(15));
    const floor = Math.floor(scaled);
    const diff = scaled - floor;
    let out;
    if (Math.abs(diff - 0.5) < 1e-9) {
      out = floor % 2 === 0 ? floor : floor + 1;
    } else {
      out = Math.round(scaled);
    }
    return out / d;
  }

  function analyzeDraws(draws) {
    const fa = frequencyAnalysis(draws);
    const due = dueNumbers(draws);

    const pairCount = new Map();
    for (const d of draws) {
      const whites = [d[COL.N1], d[COL.N2], d[COL.N3], d[COL.N4], d[COL.N5]].sort((a, b) => a - b);
      for (let i = 0; i < whites.length; i++) {
        for (let j = i + 1; j < whites.length; j++) {
          const key = whites[i] + "-" + whites[j];
          pairCount.set(key, (pairCount.get(key) || 0) + 1);
        }
      }
    }
    // Counter.most_common: sorted by count desc, stable on insertion order
    const topPairs = Array.from(pairCount.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20)
      .map((e) => [e[0], e[1]]);

    const dates = draws.map((d) => d[COL.DATE]);
    // Python min()/max() on ISO date strings is lexicographic
    const minDate = dates.length ? dates.reduce((a, b) => (a < b ? a : b)) : "";
    const maxDate = dates.length ? dates.reduce((a, b) => (a > b ? a : b)) : "";

    const allWhite = extractWhiteNumbers(draws);
    const allPb = extractPowerballs(draws);

    const hotW = hotNumbers(fa.whiteFreq, 15);
    const coldW = coldNumbers(fa.whiteFreq, 15);
    const hotP = hotNumbers(fa.pbFreq, 10);
    const coldP = coldNumbers(fa.pbFreq, 10);

    const whiteFreqList = [], pbFreqList = [];
    for (let n = WHITE_MIN; n <= WHITE_MAX; n++) whiteFreqList.push(fa.whiteFreq.get(n) || 0);
    for (let n = POWERBALL_MIN; n <= POWERBALL_MAX; n++) pbFreqList.push(fa.pbFreq.get(n) || 0);

    const avg = (arr) => (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0);

    return {
      total_draws: draws.length,
      date_range: [minDate, maxDate],
      span: dates.length ? minDate + " to " + maxDate : "",
      white_freq: fa.whiteFreq,
      pb_freq: fa.pbFreq,
      white_freq_list: whiteFreqList,
      pb_freq_list: pbFreqList,
      powerball_freq: pbFreqList,
      hot_white: hotW,
      cold_white: coldW,
      hot_pb: hotP,
      cold_pb: coldP,
      hot_powerball: hotP.slice(0, 10).map((p) => p[0]),
      cold_powerball: coldP.slice(0, 10).map((p) => p[0]),
      due_white: due.dueWhite.slice(0, 15),
      due_pb: due.duePb.slice(0, 10),
      top_pairs: topPairs,
      most_common_pb: hotP.length ? hotP[0][0] : null,
      avg_white: pyRound(avg(allWhite), 1),
      avg_powerball: pyRound(avg(allPb), 1)
    };
  }

  global.PowerballEngine = {
    WHITE_MIN: WHITE_MIN, WHITE_MAX: WHITE_MAX,
    POWERBALL_MIN: POWERBALL_MIN, POWERBALL_MAX: POWERBALL_MAX,
    parseDraws: parseDraws,
    loadDraws: loadDraws,
    frequencyAnalysis: frequencyAnalysis,
    hotNumbers: hotNumbers,
    coldNumbers: coldNumbers,
    dueNumbers: dueNumbers,
    generatePrediction: generatePrediction,
    analyzeDraws: analyzeDraws
  };
})(typeof window !== "undefined" ? window : this);
