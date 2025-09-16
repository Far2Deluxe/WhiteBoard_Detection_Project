import os
from ultralytics import YOLO
from pathlib import Path

current_dir = Path(__file__).parent
project_dir = current_dir.parent.parent

# Path to your trained model
MODEL_PATH = project_dir / "src" / "models" / "Whiteboard Model4" / "weights" / "best.pt"   # replace with your path

# Path to the folder containing images to check
IMAGE_FOLDER = project_dir / "src" / "data" / "images to test"     # replace with your folder path

# Path to the folder containing the labels files and images
RESULTS_FOLDER = project_dir / "results" / "detected_images"   # replace with your folder path

# Confidence threshold for detection
CONF_THRESHOLD = 0.5 


# Load your custom trained model
model = YOLO(MODEL_PATH)

os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Run inference on all images in the source directory
results = model.predict(source=IMAGE_FOLDER, conf=CONF_THRESHOLD, save=False, stream=True)

# Get class names from the model
class_names = model.names
# Find the class ID for 'Whiteboard' (replace with your actual class name if different)
whiteboard_class_id = None
for idx, name in class_names.items():
    if name.lower() == 'whiteboard':
        whiteboard_class_id = idx
        break

if whiteboard_class_id is None:
    raise ValueError("Whiteboard class not found in model names.")

# Process results
for result in results:
    # Check if any detection is a whiteboard
    detections = result.boxes
    if detections is not None:
        class_ids = detections.cls.int().tolist()
        if whiteboard_class_id in class_ids:
            # Get the image path
            img_path = result.path
            # Generate output path
            output_path = os.path.join(RESULTS_FOLDER, os.path.basename(img_path))
            # Save the image (original or annotated)
            result.save(filename=output_path)  # Saves annotated image
            # Alternatively, to save the original image without annotations:
            # import shutil
            # shutil.copy(img_path, output_path)
            print(f"Saved image with whiteboard: {output_path}")