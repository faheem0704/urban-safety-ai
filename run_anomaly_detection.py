import json
import os
import sys
from pathlib import Path

VIDEO_PATH       = "test_videos/sample.mp4"
DETECTIONS_JSON  = "outputs/detections.json"
OUTPUT_JSON      = "outputs/anomaly_results.json"
OUTPUT_TXT       = "outputs/anomaly_summary.txt"


def main():
    # ── Step 1: Ensure ML model is trained ────────────────────────────
    from ai_core.anomaly_classifier import AnomalyClassifier
    clf = AnomalyClassifier()
    if not Path(clf.model_path).exists():
        print("[INFO] No saved classifier found — training with synthetic data...")
        clf.train_with_synthetic_data()
    else:
        print(f"[INFO] Found trained classifier at: {clf.model_path}")

    # ── Step 2: Load or run YOLO detections ───────────────────────────
    if Path(DETECTIONS_JSON).exists():
        print(f"[INFO] Loading cached detections from: {DETECTIONS_JSON}")
        with open(DETECTIONS_JSON) as f:
            detection_results = json.load(f)
    else:
        if not Path(VIDEO_PATH).exists():
            print(f"[ERROR] Video not found: {VIDEO_PATH}")
            sys.exit(1)
        print(f"[INFO] Running YOLO detection on: {VIDEO_PATH}")
        from ai_core.detector import VideoDetector
        detector = VideoDetector()
        detection_results = detector.process(VIDEO_PATH)
        os.makedirs("outputs", exist_ok=True)
        with open(DETECTIONS_JSON, "w") as f:
            json.dump(detection_results, f, indent=2)
        print(f"[INFO] Detections cached to: {DETECTIONS_JSON}")

    # ── Step 3: Run combined anomaly pipeline ─────────────────────────
    print("[INFO] Running two-layer anomaly detection pipeline...")
    from ai_core.combined_detector import SafetyMonitor
    monitor = SafetyMonitor()
    results = monitor.process_detections(detection_results)

    # ── Step 4: Summarise ─────────────────────────────────────────────
    fps    = results["fps"]
    counts = {"NORMAL": 0, "SUSPICIOUS": 0, "ANOMALY": 0}
    anomaly_ts: list[float] = []

    for fd in results["frames"]:
        cls = fd["final_classification"]
        counts[cls] = counts.get(cls, 0) + 1
        if cls == "ANOMALY":
            anomaly_ts.append(round(fd["frame"] / fps, 2))

    anomaly_groups = _group_timestamps(anomaly_ts, gap=1.0)

    print("\n" + "=" * 48)
    print("  Urban Safety AI — Anomaly Detection Summary")
    print("=" * 48)
    print(f"  Video          : {results['video']}")
    print(f"  Total frames   : {results['total_frames']}")
    print(f"  FPS            : {fps}")
    print(f"  Duration       : {results['total_frames'] / fps:.1f}s")
    print(f"\n  NORMAL         : {counts['NORMAL']:>5}")
    print(f"  SUSPICIOUS     : {counts['SUSPICIOUS']:>5}")
    print(f"  ANOMALY        : {counts['ANOMALY']:>5}")

    if anomaly_groups:
        print(f"\n  Anomaly time ranges ({len(anomaly_groups)} event(s)):")
        for s, e in anomaly_groups[:20]:
            print(f"    {s:>6.1f}s  –  {e:.1f}s")
        if len(anomaly_groups) > 20:
            print(f"    ... and {len(anomaly_groups) - 20} more")
    else:
        print("\n  No anomaly events detected.")
    print("=" * 48)

    # ── Step 5: Save outputs ──────────────────────────────────────────
    os.makedirs("outputs", exist_ok=True)

    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[INFO] Full results saved to  : {OUTPUT_JSON}")

    summary_lines = [
        "Urban Safety AI — Anomaly Detection Summary",
        "=" * 48,
        f"Video         : {results['video']}",
        f"Total frames  : {results['total_frames']}",
        f"FPS           : {fps}",
        f"Duration      : {results['total_frames'] / fps:.1f}s",
        "",
        f"NORMAL        : {counts['NORMAL']}",
        f"SUSPICIOUS    : {counts['SUSPICIOUS']}",
        f"ANOMALY       : {counts['ANOMALY']}",
        "",
    ]
    if anomaly_groups:
        summary_lines.append(f"Anomaly time ranges ({len(anomaly_groups)} event(s)):")
        for s, e in anomaly_groups:
            summary_lines.append(f"  {s:.1f}s – {e:.1f}s")
    else:
        summary_lines.append("No anomaly events detected.")

    with open(OUTPUT_TXT, "w") as f:
        f.write("\n".join(summary_lines) + "\n")
    print(f"[INFO] Summary saved to       : {OUTPUT_TXT}")


def _group_timestamps(timestamps: list, gap: float = 1.0) -> list:
    """Merge consecutive timestamps within `gap` seconds into (start, end) tuples."""
    if not timestamps:
        return []
    groups = []
    start = prev = timestamps[0]
    for ts in timestamps[1:]:
        if ts - prev > gap:
            groups.append((start, prev))
            start = ts
        prev = ts
    groups.append((start, prev))
    return groups


if __name__ == "__main__":
    main()
