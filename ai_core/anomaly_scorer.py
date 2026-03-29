import math
from collections import deque


class AnomalyScorer:
    """
    Layer 1: Rule-based frame-level anomaly scorer.

    Changes from v1:
    - Resolution-aware movement threshold (4% of frame diagonal)
    - Crowding threshold raised to 15 persons (was 8)
    - Temporal smoothing: classification based on 10-frame rolling average
    - Tuned weights: spike 0.25, crowd 0.2, abandoned 0.30, movement 0.15
    """

    SMOOTHING_WINDOW = 10

    def __init__(self, rolling_window: int = 30):
        self.rolling_window = rolling_window
        self._person_history: deque = deque(maxlen=rolling_window)
        self._score_history: deque  = deque(maxlen=self.SMOOTHING_WINDOW)
        # Running frame-size estimate derived from observed bbox coordinates
        self._est_width:  float = 1920.0
        self._est_height: float = 1080.0

    def reset(self):
        """Clear all rolling state between videos."""
        self._person_history.clear()
        self._score_history.clear()
        self._est_width  = 1920.0
        self._est_height = 1080.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_frame(
        self,
        frame_idx: int,
        detections: list,
        prev_detections: list = None,
    ) -> dict:
        """
        Score a single frame with temporal smoothing applied to classification.

        Returns:
            {
                "score":             float  smoothed score (0.0–1.0),
                "raw_score":         float  per-frame score before smoothing,
                "classification":    str    based on smoothed score,
                "triggered_signals": list[str],
            }
        """
        self._update_resolution(detections)
        move_thresh = self._movement_threshold()

        raw  = 0.0
        triggered = []

        persons      = [d for d in detections if d["class_name"] == "person"]
        person_count = len(persons)

        # ── Signal 1: Person-count spike  (+0.25) ───────────────────────
        if self._person_history:
            rolling_avg = sum(self._person_history) / len(self._person_history)
            if rolling_avg > 0 and person_count > 1.5 * rolling_avg:
                raw += 0.25
                triggered.append("person_count_spike")

        self._person_history.append(person_count)  # update AFTER spike check

        # ── Signal 2: Crowding  (+0.2, threshold 15) ────────────────────
        if person_count > 15:
            raw += 0.2
            triggered.append("crowding")

        # ── Signal 3: Abandoned object  (+0.30) ─────────────────────────
        bags = [d for d in detections if d["class_name"] in ("handbag", "backpack")]
        for bag in bags:
            bx, by = _center(bag["bbox"])
            # Use resolution-aware proximity (same scale as movement threshold)
            has_nearby = any(
                _dist(bx, by, *_center(p["bbox"])) <= move_thresh
                for p in persons
            )
            if not has_nearby:
                raw += 0.30
                triggered.append("abandoned_object")
                break  # count once per frame

        # ── Signal 4: Rapid movement  (+0.15) ───────────────────────────
        if prev_detections is not None:
            for cls_name in {d["class_name"] for d in detections}:
                curr = [d for d in detections      if d["class_name"] == cls_name]
                prev = [d for d in prev_detections if d["class_name"] == cls_name]
                if curr and prev:
                    shift = _dist(*_avg_center(curr), *_avg_center(prev))
                    if shift > move_thresh:
                        raw += 0.15
                        triggered.append(f"rapid_movement_{cls_name}")
                        break  # add once per frame

        raw_score = round(min(1.0, max(0.0, raw)), 4)

        # ── Temporal smoothing ───────────────────────────────────────────
        self._score_history.append(raw_score)
        smoothed = round(sum(self._score_history) / len(self._score_history), 4)
        classification = _classify(smoothed)

        return {
            "score":             smoothed,
            "raw_score":         raw_score,
            "classification":    classification,
            "triggered_signals": triggered,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_resolution(self, detections: list) -> None:
        """Extend running frame-size estimate from observed bbox coordinates."""
        for d in detections:
            x2, y2 = d["bbox"][2], d["bbox"][3]
            if x2 > self._est_width:
                self._est_width  = float(x2)
            if y2 > self._est_height:
                self._est_height = float(y2)

    def _movement_threshold(self) -> float:
        """4% of the estimated frame diagonal in pixels."""
        return math.hypot(self._est_width, self._est_height) * 0.04


# ── Module-level helpers ───────────────────────────────────────────────────

def _center(bbox: list) -> tuple:
    return ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)


def _avg_center(detections: list) -> tuple:
    xs = [_center(d["bbox"])[0] for d in detections]
    ys = [_center(d["bbox"])[1] for d in detections]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _dist(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def _classify(score: float) -> str:
    if score >= 0.6:
        return "ANOMALY"
    if score >= 0.3:
        return "SUSPICIOUS"
    return "NORMAL"
