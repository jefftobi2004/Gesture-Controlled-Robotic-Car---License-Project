# Gesture-Controlled AI Robot & FPV Telemetry Center

An end-to-end computer vision and robotics project combining **MediaPipe hand landmarks recognition**, **Custom-trained MLP (Multi-layered Perceptron)
for gesture recognition**, **YOLOv8 real-time object detection**, custom **OpenCV HUD telemetry**, and an **ESP32-driven 4WD differential chassis** over low-latency UDP.

Designed with accessibility and assistive technology in mind, this project enables intuitive, hands-free, FPV (First Person View) vehicle navigation without requiring direct physical controllers or line-of-sight observation.

---

## Key Features

- **Custom-Trained Gesture Recognition Pipeline**: Uses MediaPipe purely for 21-keypoint hand landmark detection. Coordinates are preprocessed through a custom normalization pipeline (relative to the wrist origin for scale and position invariance) and fed into a **custom-trained TensorFlow Lite neural network** (`keypoint_classifier_final.tflite`).
- **Built-in Dataset Collection Tool**: Integrated data collection mode (`K` key) allowing real-time recording and labeling of normalized landmark feature vectors directly to CSV for custom model training.
- **Real-Time FPV Stream & Object Detection**: Integrates an onboard camera stream (IP Webcam via multithreaded capture) running YOLOv8 Nano for real-time environmental scanning.
- **Smart Session Persistence**: Non-redundant object capture logic records unique detected objects per session, saving cropped snapshots (`crop`) to disk for post-mission analysis.
- **Custom Vector Telemetry HUD**: Pure OpenCV HUD overlay displaying dynamic direction vectors, real-time PWM speed gauges, crosshairs, system logs, and communication status without GUI framework overhead.
- **Asynchronous UDP Communication**: Low-latency datagram socket interface (`ESPCommunicator`) between the Python control center and the ESP32 micro-controller.
- **Safety & Failsafe Mechanisms**: Spacebar toggle instantly suspends UDP transmission (software brake), with automatic motor cut-off on signal timeout.
- **GUI Launch Pad & Discovery Gallery**: Integrated Tkinter launcher (`ConfigMenu`) for IP/Camera index configuration and a session gallery (`SessionWindow`) to review discovered targets.

---

## System Architecture

<p align="center">
  <img src="./Assets/System%20Architecture%20for%20License%20Project.png" alt="System Architecture" width="600">
</p>

<p><a href="https://canva.link/5dnbi1l5qx22tfw">You can also find the design on Canva in a Romanian version by using this link</a></p
