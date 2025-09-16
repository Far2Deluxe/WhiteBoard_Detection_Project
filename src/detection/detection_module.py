import os
import cv2
import numpy as np
import shutil
from ultralytics import YOLO

def detect_whiteboards(folder_path, model_path="./runs/detect/train19/weights/best.pt", conf_threshold=0.5):
    """
    Detect whiteboards in images from a folder.

    Args:
        folder_path (str): Path to folder containing images
        model_path (str): Path to YOLO trained model weights
        conf_threshold (float): Confidence threshold for detection

    Returns:
        dict: {
            "detected_images": list of image paths with detections,
            "undetected_images": list of image filenames without detections,
            "stats": dictionary of summary statistics
        }
    """
    model = YOLO(model_path)

    detected_images = []
    undetected_images = []
    confidence_scores = []
    image_confidences = {}
    total_images = 0
    detected_count = 0
    total_detections = 0

    for filename in os.listdir(folder_path):
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            total_images += 1
            image_path = os.path.join(folder_path, filename)

            # Run YOLO detection
            results = model.predict(image_path, conf=conf_threshold, verbose=False)

            # Load image for dimension reference
            img = cv2.imread(image_path)
            if img is not None:
                img_height, img_width = img.shape[:2]
            else:
                img_width, img_height = 640, 640

            detections = len(results[0].boxes)
            if detections > 0:
                detected_count += 1
                total_detections += detections
                detected_images.append(image_path)
                max_conf = 0.0
                for box in results[0].boxes:
                    conf = float(box.conf[0])
                    confidence_scores.append(conf)
                    if conf > max_conf:
                        max_conf = conf
                image_confidences[image_path] = max_conf
            else:
                undetected_images.append(filename)

    # Summary stats
    detection_rate = (detected_count / total_images * 100) if total_images > 0 else 0
    avg_detections = total_detections / detected_count if detected_count > 0 else 0
    avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
    min_confidence = np.min(confidence_scores) if confidence_scores else 0
    max_confidence = np.max(confidence_scores) if confidence_scores else 0

    stats = {
        "total_images": total_images,
        "detected_count": detected_count,
        "undetected_count": len(undetected_images),
        "detection_rate": detection_rate,
        "total_detections": total_detections,
        "avg_detections": avg_detections,
        "avg_confidence": avg_confidence,
        "confidence_range": (min_confidence, max_confidence)
    }

    return {
        "detected_images": detected_images,
        "undetected_images": undetected_images,
        "stats": stats,
        "image_confidences": image_confidences,
    }


def move_detected_images(detected_image_paths, source_folder):
    """
    Move detected whiteboard images into a 'Whiteboards' folder.

    Args:
        detected_image_paths (list): List of detected image paths
        source_folder (str): Original source folder

    Returns:
        int: Number of successfully moved files
    """
    whiteboards_folder = os.path.join(source_folder, "Whiteboards")
    os.makedirs(whiteboards_folder, exist_ok=True)

    moved_count = 0
    for image_path in detected_image_paths:
        try:
            filename = os.path.basename(image_path)
            destination_path = os.path.join(whiteboards_folder, filename)
            shutil.move(image_path, destination_path)
            moved_count += 1
        except Exception as e:
            print(f"❌ Failed to move {os.path.basename(image_path)}: {e}")

    return moved_count
