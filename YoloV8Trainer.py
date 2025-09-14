import ultralytics
from ultralytics import YOLO

print(ultralytics.__version__)

model = YOLO("yolov8n.yaml") 
model.train(data="conf.yaml", epochs=100)

