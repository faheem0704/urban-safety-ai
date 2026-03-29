import json
import os
import sys
from pathlib import Path

from ai_core.detector import VideoDetector

VIDEO_PATH = "test_videos/sample.mp4"
OUTPUT_VIDEO = "outputs/annotated.mp4"
OUTPUT_JSON = "outputs/detections.json"


def main():
    if not Path(VIDEO_PATH).exists():
        print(f"[ERROR] Video not found: {VIDEO_PATH}")
        print("Place a video file at test_videos/sample.mp4 and re-run.")
        sys.exit(1)

    print(f"[INFO] Loading YOLOv8n detector...")
    detector = VideoDetector(model_name="yolov8n.pt", confidence=0.4)

    print(f"[INFO] Processing video: {VIDEO_PATH}")
    results = detector.process(VIDEO_PATH, output_path=OUTPUT_VIDEO)

    summary = detector.summarize(results)

    print("\n--- Detection Summary ---")
    print(f"  Total frames processed : {summary['total_frames']}")
    print(f"  Frames with detections : {summary['frames_with_detections']}")
    print(f"  Total detections       : {summary['total_detections']}")
    if summary["class_counts"]:
        print("  Objects detected:")
        for cls, count in sorted(summary["class_counts"].items(), key=lambda x: -x[1]):
            print(f"    {cls:<20} {count}")
    print(f"\n[INFO] Annotated video saved to: {OUTPUT_VIDEO}")

    os.makedirs("outputs", exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[INFO] Detection data saved to:  {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
