from math import degrees
import torch
from torch.optim import AdamW
import ultralytics
from ultralytics import YOLO
from pathlib import Path


current_dir = Path(__file__).parent
project_dir = current_dir.parent.parent
yolo_models_dir = project_dir / "src" / "data"


def main():

    ## Checks Version of Yolo and the availablity of CUDA for training Via GPU
    print("Ultralytics version:", ultralytics.__version__)
    print("CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU Name:", torch.cuda.get_device_name(0))

    # Load YOLO model
    model = YOLO(project_dir / "src" / "data" / "yolov8s.pt")

    # Train on GPU (device=0). Reduce workers to avoid multiprocessing issues.
    model.train(
        data="conf.yaml",
        epochs=70,
        device=0,
        workers=0,
        lr0=0.001,           # Initial learning rate
        lrf=0.01,            # Final learning rate
        degrees=3,          # Image rotation degrees
        optimizer="AdamW",   # Optimizer as string
        patience=15,         # Early stopping patience
        imgsz=640,           # Image size
        batch=16,            # Batch size
        project = project_dir / "src" / "models" ,
        name = "Whiteboard Model",            
        save=True,           # Save checkpoints
        plots=True           # Generate training plots
    )


if __name__ == "__main__":
    main()