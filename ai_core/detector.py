import cv2
import json
import os
from pathlib import Path

from ultralytics import YOLO

from .utils import draw_detections, extract_detections


class VideoDetector:
    """
    Runs YOLOv8 object detection on a video file frame by frame.

    Usage:
        detector = VideoDetector()
        results = detector.process("test_videos/sample.mp4", "outputs/annotated.mp4")
    """

    def __init__(self, model_name: str = "yolov8n.pt", confidence: float = 0.4):
        """
        Args:
            model_name: YOLOv8 model weights file. Downloads automatically on first run.
            confidence: Minimum confidence threshold for detections (0–1).
        """
        self.model = YOLO(model_name)
        self.confidence = confidence
        self.class_names = self.model.names  # dict {id: name}

    def process(self, video_path: str, output_path: str = None) -> dict:
        """
        Process a video file, annotate detections, and return structured results.

        Args:
            video_path: Path to the input video file.
            output_path: Path for the annotated output video. If None, no video is saved.

        Returns:
            Dict with keys:
                "video": input path,
                "total_frames": int,
                "fps": float,
                "frames": list of per-frame detection data.

        Raises:
            FileNotFoundError: If the input video cannot be opened.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        writer = None
        if output_path:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_results = []
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            yolo_results = self.model(frame, conf=self.confidence, verbose=False)
            detections = extract_detections(yolo_results[0], self.class_names)

            if writer:
                annotated = draw_detections(frame, detections)
                writer.write(annotated)

            frame_results.append({
                "frame": frame_idx,
                "detections": detections,
            })
            frame_idx += 1

        cap.release()
        if writer:
            writer.release()

        return {
            "video": str(video_path),
            "total_frames": frame_idx,
            "fps": fps,
            "resolution": [width, height],
            "frames": frame_results,
        }

    def summarize(self, results: dict) -> dict:
        """
        Produce a high-level summary from process() output.

        Returns:
            Dict with total detections, per-class counts, and frames with detections.
        """
        class_counts: dict[str, int] = {}
        frames_with_detections = 0

        for frame_data in results["frames"]:
            if frame_data["detections"]:
                frames_with_detections += 1
            for det in frame_data["detections"]:
                name = det["class_name"]
                class_counts[name] = class_counts.get(name, 0) + 1

        total = sum(class_counts.values())

        return {
            "total_detections": total,
            "frames_with_detections": frames_with_detections,
            "total_frames": results["total_frames"],
            "class_counts": class_counts,
        }
