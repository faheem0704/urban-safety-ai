import cv2
import numpy as np


# Color palette for different class IDs (BGR)
COLORS = [
    (0, 255, 0),    # green
    (255, 0, 0),    # blue
    (0, 0, 255),    # red
    (255, 165, 0),  # orange
    (128, 0, 128),  # purple
    (0, 255, 255),  # yellow
    (255, 0, 255),  # magenta
    (0, 128, 255),  # light blue
]


def get_color(class_id: int) -> tuple:
    """Return a consistent BGR color for a given class ID."""
    return COLORS[class_id % len(COLORS)]


def draw_detections(frame: np.ndarray, detections: list) -> np.ndarray:
    """
    Draw YOLO bounding boxes and labels onto a frame.

    Args:
        frame: BGR image array from OpenCV.
        detections: List of detection dicts from extract_detections().

    Returns:
        Annotated frame with boxes and labels drawn.
    """
    annotated = frame.copy()

    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        class_id = det["class_id"]
        label = f"{det['class_name']} {det['confidence']:.2f}"
        color = get_color(class_id)

        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

        # Label background
        (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        label_y = max(y1, text_h + 4)
        cv2.rectangle(annotated, (x1, label_y - text_h - 4), (x1 + text_w, label_y + baseline), color, -1)
        cv2.putText(annotated, label, (x1, label_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

    return annotated


def extract_detections(result, class_names: list) -> list:
    """
    Extract structured detection data from a single YOLO result object.

    Args:
        result: A single ultralytics Results object (from model(frame)[0]).
        class_names: List of class name strings (model.names).

    Returns:
        List of dicts, each with keys:
            class_id (int), class_name (str), confidence (float),
            bbox (list[int]): [x1, y1, x2, y2] in pixel coords.
    """
    detections = []

    if result.boxes is None:
        return detections

    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        detections.append({
            "class_id": class_id,
            "class_name": class_names[class_id] if class_id < len(class_names) else str(class_id),
            "confidence": round(confidence, 4),
            "bbox": [int(x1), int(y1), int(x2), int(y2)],
        })

    return detections
