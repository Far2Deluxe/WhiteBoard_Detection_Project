import os
import cv2
import numpy as np
import shutil
from ultralytics import YOLO
from pathlib import Path

current_dir = Path(__file__).parent
project_dir = current_dir.parent.parent

# Path to your trained model
MODEL_PATH = project_dir / "src" / "models" / "Whiteboard Model4" / "weights" / "best.pt"  # replace with your path

# Path to the folder containing photos to check
IMAGE_FOLDER = project_dir / "test"  # replace with your folder path

# Confidence threshold for detection
CONF_THRESHOLD = 0.5  # increase to reduce false positives if needed

# Load the trained model
model = YOLO(MODEL_PATH)

def move_detected_images_to_whiteboards_folder(detected_image_paths, source_folder):
    """
    Move all detected whiteboard images to a 'Whiteboards' folder within the source folder.
    
    Args:
        detected_image_paths (list): List of full paths to detected images
        source_folder (str): Path to the source folder containing the images
    """
    # Create Whiteboards folder path
    whiteboards_folder = os.path.join(source_folder, "Whiteboards")
    
    # Create the Whiteboards folder if it doesn't exist
    os.makedirs(whiteboards_folder, exist_ok=True)
    print(f"\n📁 Created/verified Whiteboards folder: {whiteboards_folder}")
    
    moved_count = 0
    for image_path in detected_image_paths:
        try:
            # Get just the filename from the full path
            filename = os.path.basename(image_path)
            destination_path = os.path.join(whiteboards_folder, filename)
            
            # Move the file
            shutil.move(image_path, destination_path)
            print(f"   ✅ Moved: {filename}")
            moved_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed to move {os.path.basename(image_path)}: {str(e)}")
    
    print(f"\n📊 Successfully moved {moved_count} out of {len(detected_image_paths)} detected images to Whiteboards folder")
    return moved_count

# Count of images with at least one detected whiteboard
detected_count = 0
total_images = 0
total_detections = 0
confidence_scores = []
undetected_images = []  # List to store images with no detections
detected_images = []  # List to store images with whiteboard detections

print("=" * 80)
print("WHITEBOARD DETECTION ACCURACY REPORT")
print("=" * 80)

# Iterate over all images in the folder
for filename in os.listdir(IMAGE_FOLDER):
    if filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
        total_images += 1
        image_path = os.path.join(IMAGE_FOLDER, filename)
        
        # Run prediction
        results = model.predict(image_path, conf=CONF_THRESHOLD, verbose=False)
        
        # Get image dimensions for relative coordinates
        img = cv2.imread(image_path)
        if img is not None:
            img_height, img_width = img.shape[:2]
        else:
            img_width, img_height = 640, 640  # fallback dimensions
        
        # Check if at least one whiteboard was detected
        detections = len(results[0].boxes)
        if detections > 0:
            detected_count += 1
            total_detections += detections
            detected_images.append(image_path)  # Add to detected images list
            
            print(f"\n📸 {filename}")
            print(f"   ✅ Detections: {detections}")
            
            # Display details for each detection
            for i, box in enumerate(results[0].boxes):
                conf = float(box.conf[0])
                confidence_scores.append(conf)
                
                # Get bounding box coordinates (xyxy format)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # Convert to relative coordinates
                rel_x1 = x1 / img_width
                rel_y1 = y1 / img_height
                rel_x2 = x2 / img_width
                rel_y2 = y2 / img_height
                
                # Calculate bounding box area
                bbox_area = (x2 - x1) * (y2 - y1)
                rel_area = bbox_area / (img_width * img_height)
                
                print(f"   🎯 Detection {i+1}:")
                print(f"      Confidence: {conf:.3f}")
                print(f"      Coordinates: ({x1:.0f}, {y1:.0f}, {x2:.0f}, {y2:.0f})")
                print(f"      Relative: ({rel_x1:.3f}, {rel_y1:.3f}, {rel_x2:.3f}, {rel_y2:.3f})")
                print(f"      Area: {bbox_area:.0f} pixels ({rel_area:.1%} of image)")
        else:
            undetected_images.append(filename)
            print(f"\n📸 {filename}")
            print(f"   ❌ No whiteboards detected")

# Move detected images to Whiteboards folder
if detected_images:
    print("\n" + "=" * 80)
    print("MOVING DETECTED IMAGES TO WHITEBOARDS FOLDER")
    print("=" * 80)
    moved_count = move_detected_images_to_whiteboards_folder(detected_images, IMAGE_FOLDER)
else:
    print("\n" + "=" * 80)
    print("MOVING DETECTED IMAGES TO WHITEBOARDS FOLDER")
    print("=" * 80)
    print("ℹ️  No whiteboard images detected to move.")

# Calculate and display summary statistics
detection_rate = (detected_count / total_images * 100) if total_images > 0 else 0
avg_detections = total_detections / detected_count if detected_count > 0 else 0
avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
min_confidence = np.min(confidence_scores) if confidence_scores else 0
max_confidence = np.max(confidence_scores) if confidence_scores else 0

print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)
print(f"Total images processed: {total_images}")
print(f"Images with whiteboards: {detected_count}")
print(f"Images without whiteboards: {len(undetected_images)}")
print(f"Detection rate: {detection_rate:.1f}%")
print(f"Total detections: {total_detections}")
print(f"Average detections per positive image: {avg_detections:.2f}")
print(f"Average confidence: {avg_confidence:.3f}")
print(f"Confidence range: {min_confidence:.3f} - {max_confidence:.3f}")

# Display list of undetected images
if undetected_images:
    print("\n" + "=" * 80)
    print("IMAGES WITH NO WHITEBOARD DETECTIONS")
    print("=" * 80)
    for i, filename in enumerate(undetected_images, 1):
        print(f"{i:3d}. {filename}")
    print(f"\nTotal undetected images: {len(undetected_images)}")
else:
    print("\n" + "=" * 80)
    print("IMAGES WITH NO WHITEBOARD DETECTIONS")
    print("=" * 80)
    print("🎉 All images had whiteboard detections!")

print("=" * 80)