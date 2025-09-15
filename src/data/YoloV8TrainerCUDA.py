import torch
import ultralytics
from ultralytics import YOLO


def main():
    print("Ultralytics version:", ultralytics.__version__)
    print("CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU Name:", torch.cuda.get_device_name(0))

    # Load YOLO model
    model = YOLO("yolov8s.pt")

    # Train on GPU (device=0). Reduce workers to avoid multiprocessing issues.
    model.train(
        data="conf.yaml",
        epochs=200,
        device=0,
        workers=0   # <--- IMPORTANT for Windows
    )


if __name__ == "__main__":
    main()