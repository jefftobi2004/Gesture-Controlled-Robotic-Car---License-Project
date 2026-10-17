import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf

import socket
import time

from utils.dashboard import Dashboard

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import utils.landmarks_preprocessing as lprep
from utils.esp_communicator import ESPCommunicator
import utils.file_helper as fh

# Default values

SELECTED_CAMERA = 0
RESOLUTION_HEIGHT = 720
RESOLUTION_WIDTH = 1280

mp_hands = mp.tasks.vision.HandLandmarksConnections
mp_drawing = mp.tasks.vision.drawing_utils
mp_drawing_styles = mp.tasks.vision.drawing_styles

def main():
    # Creating an HandLandmarker object.
    base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1
    )
    detector = vision.HandLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(SELECTED_CAMERA)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION_HEIGHT)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION_WIDTH)

    esp = ESPCommunicator()
    
    """
    dashboard = Dashboard(cam_width=RESOLUTION_WIDTH, cam_height=RESOLUTION_HEIGHT)
    viteza = 180
    trimitere_activa = True

    dashboard.log_keyboard("Program started")
    dashboard.log_keyboard("SPACE = Pause/Resume Signals")
    dashboard.log_keyboard("+ / -  = Adjust Speed")
    dashboard.log_keyboard("K - Data Collection Mode")
    dashboard.log_keyboard("Esc - Exit Program !!!")
    """
    
    interpreter = tf.lite.Interpreter(model_path="model/training/keypoint_classifier_final.tflite")
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    labels = fh.load_labels()
    collecting_mode = False
    send_data = False

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Camera could not be accessed !")
            break
        
        frame = cv2.flip(frame, 1)

        # Conversion to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Conversion to MediaPipe Image format
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Run detection
        detection_result = detector.detect(mp_image)

        # Draw landmarks
        annotated_image = draw_landmarks_on_image(rgb_frame, detection_result, interpreter, 
                                                  input_details, output_details, labels, 
                                                  esp, send_data)
        cv2.imshow("Hand Sign Detection", cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))

        #final_frame = dashboard.render(annotated_image)
        #cv2.imshow("Hand Sign Detection", cv2.cvtColor(final_frame, cv2.COLOR_RGB2BGR))

        key = cv2.waitKey(1)

        if key == 27:
            break

        """

        if key == ord(' '):
            trimitere_activa = not trimitere_activa
            esp.trimitere_activa = trimitere_activa
            dashboard.set_trimitere(trimitere_activa)
            if trimitere_activa:
                dashboard.log_keyboard("Signals RESUMED")
            else:
                esp.trimite_semn_direct("Closed")
                dashboard.log_keyboard("Signals Paused")

        if key == ord('+'):
            viteza = min(viteza + 20, 255)
            esp.trimite_viteza(viteza)
            dashboard.set_speed(viteza)
            dashboard.log_keyboard(f"Viteza → {viteza}")

        if key == ord('-'):
            viteza = max(viteza - 20, 0)
            esp.trimite_viteza(viteza)
            dashboard.set_speed(viteza)
            dashboard.log_keyboard(f"Viteza → {viteza}")

        """
        
        if key == ord('k') or key == ord('K'):
            collecting_mode = not collecting_mode
            print(f"Data Collection Mode: {'ON' if collecting_mode else 'OFF'}")
            #dashboard.log_keyboard(f"Collect {'ON' if collecting_mode else 'OFF'}")

        if key == ord(' '):
            send_data = not send_data

        if collecting_mode:
            collect_data(key, detection_result, labels)


    cap.release()
    cv2.destroyAllWindows()
    esp.close()

###########################################################################

def draw_landmarks_on_image(rgb_image, detection_result, interpreter, input_details, output_details, labels, esp, send_data):

    hand_landmarks_list = detection_result.hand_landmarks # (x, y, z) coordinates of the hand landmarks
    handedness_list = detection_result.handedness # Left or right hand
    annotated_image = np.copy(rgb_image)

    if hand_landmarks_list:
        for idx in range(len(hand_landmarks_list)):
            hand_landmarks = hand_landmarks_list[idx]
            handedness = handedness_list[idx]

            # Inversing the handedness since we're flipping the image horizontally
            hand_label = handedness[0].category_name
            if hand_label == "Left":
                hand_label = "Right"
            else:
                hand_label = "Left"

            # Preprocessing
            processed = lprep.preprocess_landmarks(hand_landmarks)
            input_data = np.array([processed], dtype=np.float32)

            # Interpreter for the model saved with .tflite 
            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()

            # Predicted result and its confidence in it
            prediction = interpreter.get_tensor(output_details[0]['index'])
            gesture_index = np.argmax(prediction)
            gesture_name = labels[gesture_index]
            confidence = prediction[0][gesture_index]

            # Sending predicted gesture to the microcontroller
            if send_data:
                esp.trimite_semn(gesture_name, confidence)
            #dashboard.set_last_sign(gesture_name)
            #dashboard.log_signal(f"{gesture_name} {confidence*100:.0f}%")

            # Bounding Box
            height, width, _ = annotated_image.shape
            x_coords = [lm.x for lm in hand_landmarks]
            y_coords = [lm.y for lm in hand_landmarks]

            x_min = int(min(x_coords) * width)
            y_min = int(min(y_coords) * height)
            x_max = int(max(x_coords) * width)
            y_max = int(max(y_coords) * height)

            cv2.rectangle(annotated_image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

            
            # Draw label
            text = f"{hand_label}: {gesture_name} ({confidence*100:.1f}%)"

            cv2.putText(
                annotated_image,
                text,
                (x_min, y_min - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA
            )

            # Draw landmarks
            mp_drawing.draw_landmarks(
                annotated_image,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

    return annotated_image

###########################################################################

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

###########################################################################

if __name__ == "__main__":
    main()

