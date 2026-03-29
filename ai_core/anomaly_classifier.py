import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split


# Feature vector layout (index → name):
#   0  avg_persons     – mean person count per frame in window
#   1  max_persons     – peak person count in window
#   2  std_persons     – std-dev of person count (temporal variation)
#   3  avg_confidence  – mean detection confidence across all objects
#   4  person_density  – avg_persons / 20 (normalised 0–1)
#   5  motion_score    – normalised average centre-shift of persons (0–1)
FEATURE_NAMES = [
    "avg_persons", "max_persons", "std_persons",
    "avg_confidence", "person_density", "motion_score",
]


class AnomalyClassifier:
    """
    Layer 2: Trained Random Forest anomaly classifier.

    Trained on synthetic feature vectors that represent NORMAL
    (low crowd, low motion) vs ANOMALY (high crowd, high motion) clips.
    Applied per-frame using a rolling window of recent detections.
    """

    DEFAULT_MODEL_PATH = "models/anomaly_classifier.pkl"

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        self.model_path = model_path
        self.model: RandomForestClassifier | None = None

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train_with_synthetic_data(self, n_per_class: int = 300, random_state: int = 42) -> None:
        """
        Generate synthetic feature vectors and train a Random Forest.
        Prints classification report on the held-out test split.
        Saves the model to self.model_path.
        """
        X, y = self._generate_synthetic_data(n_per_class, random_state)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=random_state, stratify=y
        )

        clf = RandomForestClassifier(n_estimators=100, random_state=random_state)
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        print("\n[ML Classifier] Classification Report:")
        print(classification_report(y_test, y_pred))

        os.makedirs(os.path.dirname(self.model_path) or ".", exist_ok=True)
        joblib.dump(clf, self.model_path)
        self.model = clf
        print(f"[ML Classifier] Model saved to: {self.model_path}")

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load model from disk. Trains with synthetic data if not found."""
        if Path(self.model_path).exists():
            self.model = joblib.load(self.model_path)
        else:
            print("[ML Classifier] No saved model found — training with synthetic data...")
            self.train_with_synthetic_data()

    def extract_features(self, frame_window: list) -> list:
        """
        Compute the 6-element feature vector from a window of frame dicts.

        Args:
            frame_window: List of frame dicts, each with a "detections" key
                          (same format as detections.json "frames" entries).

        Returns:
            [avg_persons, max_persons, std_persons, avg_confidence,
             person_density, motion_score]
        """
        if not frame_window:
            return [0.0] * 6

        person_counts = []
        confidences = []
        motion_scores = []
        prev_centers = None

        for frame_data in frame_window:
            dets = frame_data.get("detections", [])
            persons = [d for d in dets if d["class_name"] == "person"]
            person_counts.append(len(persons))

            for d in dets:
                confidences.append(d["confidence"])

            curr_centers = [
                ((d["bbox"][0] + d["bbox"][2]) / 2.0,
                 (d["bbox"][1] + d["bbox"][3]) / 2.0)
                for d in persons
            ]
            if prev_centers and curr_centers:
                avg_curr = np.mean(curr_centers, axis=0)
                avg_prev = np.mean(prev_centers, axis=0)
                shift = float(np.linalg.norm(avg_curr - avg_prev))
                # Normalise: 500 px shift → score 1.0 (suitable for 4K)
                motion_scores.append(min(shift / 500.0, 1.0))
            prev_centers = curr_centers

        avg_persons   = float(np.mean(person_counts))
        max_persons   = float(max(person_counts))
        std_persons   = float(np.std(person_counts)) if len(person_counts) > 1 else 0.0
        avg_conf      = float(np.mean(confidences)) if confidences else 0.0
        person_density = avg_persons / 20.0          # normalised to 0-1 (max ~20 persons)
        motion_score   = float(np.mean(motion_scores)) if motion_scores else 0.0

        return [avg_persons, max_persons, std_persons, avg_conf, person_density, motion_score]

    def predict(self, frame_window: list) -> dict:
        """
        Predict NORMAL, SUSPICIOUS, or ANOMALY from a rolling window of frames.

        Returns:
            {"label": "NORMAL" | "SUSPICIOUS" | "ANOMALY", "probability": float}
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        features = self.extract_features(frame_window)
        X = np.array(features, dtype=float).reshape(1, -1)
        label = str(self.model.predict(X)[0])
        proba = self.model.predict_proba(X)[0]
        class_idx = list(self.model.classes_).index(label)

        return {
            "label": label,
            "probability": round(float(proba[class_idx]), 4),
        }

    # ------------------------------------------------------------------
    # Synthetic data generation
    # ------------------------------------------------------------------

    def _generate_synthetic_data(self, n: int, seed: int):
        rng = np.random.RandomState(seed)

        def _make(avg_lo, avg_hi, mot_lo, mot_hi, dens_lo, dens_hi):
            avg  = rng.uniform(avg_lo, avg_hi, n)
            mx   = np.clip(avg * rng.uniform(1.0, 1.5, n) + rng.normal(0, 0.4, n), avg, None)
            std  = rng.uniform(0.1, max(0.2, (avg_hi - avg_lo) * 0.2), n)
            conf = rng.uniform(0.5, 0.9, n)
            dens = np.clip(rng.uniform(dens_lo, dens_hi, n) + rng.normal(0, 0.02, n), 0, 1)
            mot  = rng.uniform(mot_lo, mot_hi, n)
            return np.column_stack([avg, mx, std, conf, dens, mot])

        # NORMAL:     1–8 persons,  movement 0–0.3,  density 0–0.4
        X_normal     = _make(1,  8,  0.0, 0.3, 0.0, 0.4)
        # SUSPICIOUS: 5–12 persons, movement 0.2–0.5, density 0.3–0.6
        X_suspicious = _make(5, 12,  0.2, 0.5, 0.3, 0.6)
        # ANOMALY:    8–20 persons, movement 0.4–1.0, density 0.5–1.0
        X_anomaly    = _make(8, 20,  0.4, 1.0, 0.5, 1.0)

        X = np.vstack([X_normal, X_suspicious, X_anomaly])
        y = np.array(["NORMAL"] * n + ["SUSPICIOUS"] * n + ["ANOMALY"] * n)
        return X, y
