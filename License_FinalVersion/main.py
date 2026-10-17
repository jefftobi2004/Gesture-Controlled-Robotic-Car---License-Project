import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import socket
import time
import threading

from utils.hud import HUD
from yolo_detector import YOLODetector
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from config_menu import ConfigMenu
import utils.landmarks_preprocessing as lprep
from utils.esp_communicator import ESPCommunicator
import utils.file_helper as fh

# --- Global Values ---
SELECTED_CAMERA = 0      # Laptop Camera
PHONE_IP = "192.168.4.3" # Phone IP Stream
RESOLUTION_HEIGHT = 450
RESOLUTION_WIDTH = 800

mesaje_log = [
        "[SYSTEM] Sistem initializat cu succes.",
        "[ESP32] Asteptare conexiune...",
        "[YOLO] Model incarcat complet in mod offline."
    ]

# MediaPipe Configs
mp_hands = mp.tasks.vision.HandLandmarksConnections
mp_drawing = mp.tasks.vision.drawing_utils
mp_drawing_styles = mp.tasks.vision.drawing_styles

class IPStreamThread:
    def __init__(self, url):
        self.stream = cv2.VideoCapture(url)
        self.ret = False
        self.frame = None
        self.stopped = False
        self.lock = threading.Lock()
        
    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self
        
    def update(self):
        while not self.stopped:
            try:
                ret, frame = self.stream.read()
                if not ret:
                    continue
                self.ret = ret
                self.frame = frame
            except:
                break
        
        if self.stream.isOpened():
            self.stream.release()
                
    def read(self):
        with self.lock:
            return self.ret, self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.stopped = True


def main():

    while True:
        # Starting Main Menu
        menu = ConfigMenu(SELECTED_CAMERA, PHONE_IP)
        is_cancelled, selected_camera, phone_url, exit_app = menu.show()
        
        if is_cancelled or exit_app:
            print("[INFO] Launcher closed by user. Exiting...")
            return
        
        current_session_dir = fh.get_next_session_dir()
        active_session_detections = set()

        # Creating a HandLandmarker object.
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
        detector = vision.HandLandmarker.create_from_options(options)

        interpreter = tf.lite.Interpreter(model_path="model/training/keypoint_classifier_final.tflite")
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        labels = fh.load_labels()

        # Hardware and HUD
        esp = ESPCommunicator()
        hud = HUD()
        
        # Default car settings
        viteza = 180
        directie = "INAINTE"
        collecting_mode = False
        send_data = False

        # HUD Initializer
        hud.set_viteza(viteza)
        hud.set_directie(directie)
        hud.set_status(send_data)
        hud.set_gest("None", 0.0)

        # Initializing laptop camera
        cap_semne = cv2.VideoCapture(selected_camera)
        cap_semne.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION_HEIGHT)
        cap_semne.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION_WIDTH)

        
        print("[INFO] Se conectează la camera mașinii (IP Webcam)...")
        phone_stream = IPStreamThread(phone_url).start()
        time.sleep(1.5) 

        print("[SUCCESS] Sistemul integrat a pornit. Apasă ESC pentru a închide.")

        yolo_detector = YOLODetector(confidence_threshold=0.50)

        while cap_semne.isOpened():
            
            ret_semne, frame_semne = cap_semne.read()
            ret_telefon, frame_telefon = phone_stream.read()

            if not ret_semne:
                print("[EROARE] Nu se poate accesa camera laptopului!")
                break

            frame_semne = cv2.flip(frame_semne, 1)
            rgb_frame = cv2.cvtColor(frame_semne, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            
            detection_result = detector.detect(mp_image)

            detected_gesture = "None"
            gesture_confidence = 0.0

            if detection_result.hand_landmarks:
                hand_landmarks = detection_result.hand_landmarks[0]
                processed = lprep.preprocess_landmarks(hand_landmarks)
                input_data = np.array([processed], dtype=np.float32)

                interpreter.set_tensor(input_details[0]['index'], input_data)
                interpreter.invoke()

                prediction = interpreter.get_tensor(output_details[0]['index'])
                gesture_index = np.argmax(prediction)
                detected_gesture = labels[gesture_index]
                gesture_confidence = float(prediction[0][gesture_index])

                if send_data:
                    esp.trimite_semn(detected_gesture, gesture_confidence)
            
            hud.set_gest(detected_gesture, gesture_confidence)
            hud.set_viteza(viteza)
            hud.set_directie(directie)
            hud.set_status(send_data)

            annotated_rgb = draw_landmarks_on_image(
                rgb_frame, detection_result, interpreter, input_details, 
                output_details, labels, esp, send_data
            )
            frame_semne_final = cv2.cvtColor(annotated_rgb, cv2.COLOR_RGB2BGR)

            if ret_telefon and frame_telefon is not None:
                frame_telefon_resized = cv2.resize(frame_telefon, (RESOLUTION_WIDTH, RESOLUTION_HEIGHT))
                frame_telefon_final = yolo_detector.process_frame(frame_telefon_resized)

                for label, crop in getattr(yolo_detector, 'detected_crops', {}).items():
                    if label not in active_session_detections:
                        active_session_detections.add(label)
                        
                        fh.save_session_frame(current_session_dir, label, crop)

                frame_telefon_final = hud.render(frame_telefon_final)
            else:
                frame_telefon_final = np.zeros((RESOLUTION_HEIGHT, RESOLUTION_WIDTH, 3), dtype=np.uint8)
                cv2.putText(frame_telefon_final, "CONECTARE IP WEBCAM...", (420, 360), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            frame_semne_final_resized = cv2.resize(frame_semne_final, (RESOLUTION_WIDTH, RESOLUTION_HEIGHT))
            frame_telefon_resized = cv2.resize(frame_telefon_final, (RESOLUTION_WIDTH, RESOLUTION_HEIGHT))

            interfata_sus = np.hstack((frame_semne_final_resized, frame_telefon_resized))

            panou_mesaje = np.zeros((120, RESOLUTION_WIDTH * 2, 3), dtype=np.uint8)
            cv2.line(panou_mesaje, (0, 0), (RESOLUTION_WIDTH * 2, 0), (40, 40, 40), 2)

            for idx, msg in enumerate(mesaje_log[-4:]):
                color = (0, 255, 0) if "[CONTROL]" in msg else (255, 180, 100) if "[STATUS]" in msg else (200, 200, 200)
                cv2.putText(panou_mesaje, msg, (20, 25 + idx * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

            interfata_finala = np.vstack((interfata_sus, panou_mesaje))
            
            cv2.imshow("Centru de Control Integrat (Laptop Sign AI | Car FPV HUD)", interfata_finala)

            key = cv2.waitKey(1)

            if key == 27: 
                break

            if key == ord(' '): 
                send_data = not send_data
                mesaje_log.append(f"[STATUS] Trimitere date ESP32: {"ACTIVATA" if send_data else "DEZACTIVATA"}")

            if key == ord('+'):
                viteza = min(viteza + 20, 255)
                esp.trimite_viteza(viteza)
                mesaje_log.append(f"[CONTROL] Viteza crescuta la: {viteza}")

            if key == ord('-'):
                viteza = max(viteza - 20, 0)
                esp.trimite_viteza(viteza)
                mesaje_log.append(f"[CONTROL] Viteza scazuta la: {viteza}")

            if key in [ord('k'), ord('K')]:
                collecting_mode = not collecting_mode
                mesaje_log.append(f"[DATA] Mod Colectare Date: {'ACTIVAT' if collecting_mode else 'DEZACTIVAT'}")

            if collecting_mode:
                collect_data(key, detection_result, labels)

        phone_stream.stop()
        cap_semne.release()
        cv2.destroyAllWindows()
        esp.close()


def draw_landmarks_on_image(rgb_image, detection_result, interpreter, input_details, output_details, labels, esp, send_data):
    hand_landmarks_list = detection_result.hand_landmarks
    handedness_list = detection_result.handedness
    annotated_image = np.copy(rgb_image)

    if hand_landmarks_list:
        for idx in range(len(hand_landmarks_list)):
            hand_landmarks = hand_landmarks_list[idx]
            handedness = handedness_list[idx]

            hand_label = handedness[0].category_name
            if hand_label == "Left":
                hand_label = "Right"
            else:
                hand_label = "Left"

            processed = lprep.preprocess_landmarks(hand_landmarks)
            input_data = np.array([processed], dtype=np.float32)

            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()

            prediction = interpreter.get_tensor(output_details[0]['index'])
            gesture_index = np.argmax(prediction)
            gesture_name = labels[gesture_index]
            confidence = prediction[0][gesture_index]

            if send_data:
                esp.trimite_semn(gesture_name, confidence)

            height, width, _ = annotated_image.shape
            x_coords = [lm.x for lm in hand_landmarks]
            y_coords = [lm.y for lm in hand_landmarks]

            x_min = int(min(x_coords) * width)
            y_min = int(min(y_coords) * height)
            x_max = int(max(x_coords) * width)
            y_max = int(max(y_coords) * height)

            cv2.rectangle(annotated_image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            text = f"{hand_label}: {gesture_name} ({confidence*100:.1f}%)"

            cv2.putText(
                annotated_image, text, (x_min, y_min - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA
            )

            mp_drawing.draw_landmarks(
                annotated_image, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

    return annotated_image


def collect_data(key, detection_result, labels):
    if ord('0') <= key <= ord('9'):
        label_index = key - ord('0')
        if label_index < len(labels):
            if detection_result.hand_landmarks:
                hand_landmarks = detection_result.hand_landmarks[0]
                processed = lprep.preprocess_landmarks(hand_landmarks)
                fh.append_to_csv(processed, label_index)
                print(f" [DATA SAVED] Sample for: {labels[label_index]}")
            else:
                print(" [WARNING] No hand detected!")


if __name__ == "__main__":
    main()