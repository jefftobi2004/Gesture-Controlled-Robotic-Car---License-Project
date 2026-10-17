import cv2
from ultralytics import YOLO

class YOLODetector:
    def __init__(self, model_name="yolov8n.pt", confidence_threshold=0.50):
        print(f"[INFO] Loading YOLO model ({model_name})...")
        self.model = YOLO(model_name)
        self.confidence_threshold = confidence_threshold

    def process_frame(self, frame):
        if frame is None:
            return None

        annotated_frame = frame.copy()
        results = self.model(frame, verbose=False)[0]

        self.detected_crops = {}
        
        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = self.model.names[class_id]
            
            if confidence > self.confidence_threshold:
                crop = frame[y1:y2, x1:x2]
                if crop.size > 0:
                    self.detected_crops[class_name] = crop
                
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                
                label = f"{class_name} {confidence*100:.0f}%"
                cv2.putText(annotated_frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                            
        return annotated_frame