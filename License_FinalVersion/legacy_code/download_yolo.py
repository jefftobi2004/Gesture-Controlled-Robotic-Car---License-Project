from ultralytics import YOLO

print("[INFO] Starting download...")
model = YOLO("yolov8n.pt")
print("[SUCCESS] Model downloaded successfully!")