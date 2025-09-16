from ultralytics import YOLO
from pathlib import Path

current_dir = Path(__file__).parent
project_dir = current_dir.parent.parent
yolo_models_dir = project_dir / "src" / "data"

# Create a classification model (ResNet18 backbone is default)
# Use the model name instead of .pt file - YOLO will download the pre-trained weights automatically


def main():
    model = YOLO("yolov8s-cls.pt")  # n = nano version, good for fast training

# Train
    model.train(
        data=project_dir /"data" / "images" ,     # path to dataset folder with train/val subfolders
        epochs=100,          # number of training epochs
        imgsz=324,          # image size for classification
        batch=32,
        patience=15,
        optimizer="AdamW",  # good for classification
        dropout=0.2,        # reduce overfitting
        lr0=0.001,
        lrf=0.01,
        save = True,
        verbose=True,
        project = project_dir / "src" / "models" ,
        name = "Whiteboard Model Classification"    ,
            # batch size
)

# Validate on val set
    metrics = model.val()
    print(metrics)

# Save final model
    model.export(format="torchscript")  # you can also export to onnx, tflite etc.

if __name__ == "__main__":
    main()