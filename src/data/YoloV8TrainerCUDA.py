import torch
import ultralytics
from ultralytics import YOLO
from pathlib import Path
import os

current_dir = Path(__file__).parent
project_dir = current_dir.parent.parent
yolo_models_dir = project_dir / "src" / "data"


def main():
    print("Ultralytics version:", ultralytics.__version__)
    print("CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU Name:", torch.cuda.get_device_name(0))

    # Load YOLO model
    model = YOLO(project_dir / "src" / "data" / "yolov8s.pt")

    # Train on GPU (device=0). Reduce workers to avoid multiprocessing issues.
    model.train(
        data= project_dir / "conf.yaml",
        epochs=200,
        device=0,
        workers=0,   # <--- IMPORTANT for Windows
        project = project_dir / "src" / "models" ,
        name = "Whiteboard Model"
    
    )


if __name__ == "__main__":
    main()