import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import utils.landmarks_preprocessing as lprep
import utils.file_helper as fh

# Default values
MARGIN = 10
FONT_SIZE = 1
FONT_THICKNESS = 1
HANDEDNESS_TEXT_COLOR = (88, 205, 54)

mp_hands = mp.tasks.vision.HandLandmarksConnections
mp_drawing = mp.tasks.vision.drawing_utils
mp_drawing_styles = mp.tasks.vision.drawing_styles

def main():

    # Creating an HandLandmarker object.
    base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2
    )
    detector = vision.HandLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(0)

    model = tf.keras.models.load_model("model/training/keypoint_classifier.keras")
    labels = fh.load_labels()
    collecting_mode = False

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
        annotated_image = draw_landmarks_on_image(rgb_frame, detection_result, model, labels)
        cv2.imshow("Hand Landmark Detection", cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))

        key = cv2.waitKey(1)

        if key == 27:
            break
        
        if key == ord('k') or key == ord('K'):
            collecting_mode = not collecting_mode
            print(f"Data Collection Mode: {'ON' if collecting_mode else 'OFF'}")

        if collecting_mode:
            collect_data(key, detection_result, labels)


    cap.release()
    cv2.destroyAllWindows()

###########################################################################

def draw_landmarks_on_image(rgb_image, detection_result, model, labels):

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

            # Prepocessing and Prediction
            processed = lprep.preprocess_landmarks(hand_landmarks)
            input_data = np.array([processed], dtype = np.float32)

            prediction = model.predict(input_data, verbose = 0)
            gesture_index = np.argmax(prediction)
            gesture_name = labels[gesture_index]

            # Model confidence
            confidence = prediction[0][gesture_index]

            # Bounding Box
            height, width, _ = annotated_image.shape
            x_coords = [lm.x for lm in hand_landmarks]
            y_coords = [lm.y for lm in hand_landmarks]

            x_min = int(min(x_coords) * width)
            y_min = int(min(y_coords) * height)
            x_max = int(max(x_coords) * width)
            y_max = int(max(y_coords) * height)

            cv2.rectangle(annotated_image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

            # Drawing the label
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

            # Drawing landmarks
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
