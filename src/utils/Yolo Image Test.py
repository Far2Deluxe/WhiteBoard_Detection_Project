from ultralytics import YOLO

model = YOLO("./runs/detect/train19/weights/best.pt")

results = model('./test3/whiteboards/Image (10).jpg')

results[0].show()