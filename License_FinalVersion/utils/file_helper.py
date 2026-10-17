def load_labels(path = "model/data/labels.txt"):
    with open(path, "r") as f:
        labels = [line.strip() for line in f.readlines()]
    return labels

import csv

def append_to_csv(data, label, filename="model/data/keypoint_final.csv"):
    row = [label] + data

    with open(filename, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

import os
import cv2

def get_next_session_dir(base_dir="saved_sessions"):
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    existing = [d for d in os.listdir(base_dir) if d.startswith("Session_")]
    numbers = [int(d.split("_")[1]) for d in existing if d.split("_")[1].isdigit()]
    next_num = max(numbers) + 1 if numbers else 1
    
    new_dir = os.path.join(base_dir, f"Session_{next_num}")
    os.makedirs(new_dir)
    return new_dir

def save_session_frame(session_dir, label, frame):
    img_filename = f"{label}.jpg".replace("/", "_")
    img_path = os.path.join(session_dir, img_filename)
    cv2.imwrite(img_path, frame)
    print(f"[DISK] Snapshot persisted: {img_path}")