from .anomaly_classifier import AnomalyClassifier
from .anomaly_scorer import AnomalyScorer
from .detector import VideoDetector


class SafetyMonitor:
    """
    Combined two-layer safety pipeline.

    Layer 1 (rule-based):  AnomalyScorer  → score + triggered signals
    Layer 2 (ML):          AnomalyClassifier → label + probability

    Final decision rule:
        ANOMALY    if either layer returns ANOMALY
        SUSPICIOUS if Layer 1 returns SUSPICIOUS (and ML says NORMAL)
        NORMAL     otherwise
    """

    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        confidence: float = 0.4,
        window_size: int = 30,
    ):
        self.detector   = VideoDetector(model_name, confidence)
        self.scorer     = AnomalyScorer(rolling_window=window_size)
        self.classifier = AnomalyClassifier()
        self.classifier.load()
        self.window_size = window_size

    # ------------------------------------------------------------------
    # Primary entry points
    # ------------------------------------------------------------------

    def process_video(self, video_path: str, output_path: str = None) -> dict:
        """Run YOLO on a video file, then apply both anomaly layers."""
        detection_results = self.detector.process(video_path, output_path)
        return self.process_detections(detection_results)

    def process_detections(self, detection_results: dict) -> dict:
        """
        Apply both anomaly layers to pre-computed YOLO detections.

        Args:
            detection_results: Dict in the format produced by VideoDetector.process()
                               (keys: video, fps, total_frames, resolution, frames).

        Returns:
            Dict with per-frame results:
            {
                "video":        str,
                "fps":          float,
                "total_frames": int,
                "frames": [
                    {
                        "frame":               int,
                        "rule_based":          {score, classification, triggered_signals},
                        "ml_classifier":       {label, probability},
                        "final_classification": "NORMAL" | "SUSPICIOUS" | "ANOMALY",
                    },
                    ...
                ]
            }
        """
        self.scorer.reset()
        frames = detection_results["frames"]
        frame_window: list = []
        frame_results = []

        for i, frame_data in enumerate(frames):
            dets      = frame_data["detections"]
            prev_dets = frames[i - 1]["detections"] if i > 0 else None

            # Layer 1 ── rule-based
            rule_result = self.scorer.score_frame(i, dets, prev_dets)

            # Maintain sliding window for Layer 2
            frame_window.append(frame_data)
            if len(frame_window) > self.window_size:
                frame_window.pop(0)

            # Layer 2 ── ML classifier
            ml_result = self.classifier.predict(frame_window)

            # Final decision
            final = _combine(rule_result["classification"], ml_result["label"])

            frame_results.append({
                "frame":                frame_data["frame"],
                "rule_based":          rule_result,
                "ml_classifier":       ml_result,
                "final_classification": final,
            })

        return {
            "video":        detection_results.get("video", ""),
            "fps":          detection_results.get("fps", 30.0),
            "total_frames": len(frame_results),
            "frames":       frame_results,
        }


# ── Helper ─────────────────────────────────────────────────────────────────

def _combine(rule_cls: str, ml_label: str) -> str:
    if rule_cls == "ANOMALY" or ml_label == "ANOMALY":
        return "ANOMALY"
    if rule_cls == "SUSPICIOUS":
        return "SUSPICIOUS"
    return "NORMAL"
