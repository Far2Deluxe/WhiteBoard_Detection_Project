import os
import shutil
from ultralytics import YOLO
from pathlib import Path

current_dir = Path(__file__).parent
project_dir = current_dir.parent.parent


def classify_and_move_whiteboards(folder_path, model_path="runs/classify/train/weights/best.pt", conf_threshold=0.5):
    """
    Classify images in a folder as 'whiteboard' or 'not_whiteboard' using a YOLO classification model.
    Moves detected whiteboard images into a 'Whiteboards' subfolder inside the given folder.

    Args:
        folder_path (str): Path to folder with images
        model_path (str): Path to YOLO classification model (best.pt)
        conf_threshold (float): Minimum confidence to accept classification as whiteboard

    Returns:
        dict: {
            "moved_count": int,
            "whiteboard_images": list of moved image paths,
            "not_whiteboard_images": list of skipped image paths
        }
    """
    # Load YOLO classification model
    model = YOLO(model_path)

    # Create Whiteboards folder
    whiteboards_folder = os.path.join(folder_path, "Whiteboards")
    os.makedirs(whiteboards_folder, exist_ok=True)

    moved_count = 0
    whiteboard_images = []
    not_whiteboard_images = []

    # Iterate over all images
    for filename in os.listdir(folder_path):
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            image_path = os.path.join(folder_path, filename)

            # Run classification
            results = model.predict(image_path, verbose=False)

            # results[0].probs gives probabilities per class
            probs = results[0].probs.data.cpu().numpy()
            class_names = results[0].names
            predicted_class = class_names[probs.argmax()]
            confidence = probs.max()

            if predicted_class == "whiteboard" and confidence >= conf_threshold:
                # Move to Whiteboards folder
                destination = os.path.join(whiteboards_folder, filename)
                shutil.move(image_path, destination)
                moved_count += 1
                whiteboard_images.append(destination)
                print(f"✅ {filename} → Whiteboard ({confidence:.2f})")
            else:
                not_whiteboard_images.append(image_path)
                print(f"❌ {filename} → Not Whiteboard ({confidence:.2f})")

    return {
        "moved_count": moved_count,
        "whiteboard_images": whiteboard_images,
        "not_whiteboard_images": not_whiteboard_images
    }


if __name__ == "__main__":
    folder = "./test"  # change to your folder path
    model = project_dir / "src" / "models" / "Whiteboard Model Classification5" / "weights" / "best.pt" # path to your trained classifier
    results = classify_and_move_whiteboards(folder, model, conf_threshold=0.5)

    print("\n📊 Summary:")
    print(f"Moved {results['moved_count']} images into Whiteboards/")
    print(f"Remaining (not whiteboard): {len(results['not_whiteboard_images'])}")
