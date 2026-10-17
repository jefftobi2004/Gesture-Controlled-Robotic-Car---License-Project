import os
import platform
import subprocess
import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class SessionWindow:
    def __init__(self, parent_root, base_dir="saved_sessions"):
        self.window = tk.Toplevel(parent_root)
        self.window.title("Session Items Discovered")
        self.window.geometry("850x650")
        self.window.configure(bg="#0F172A")
        
        self.base_dir = base_dir
        self.image_references = []
        
        self.setup_ui()

    def open_saved_sessions_directory(self):
        absolute_path = os.path.abspath(self.base_dir)
        if not os.path.exists(absolute_path):
            os.makedirs(absolute_path)
            
        current_os = platform.system()
        if current_os == "Windows":
            os.startfile(absolute_path)
        elif current_os == "Darwin":
            subprocess.run(["open", absolute_path])
        else:
            subprocess.run(["xdg-open", absolute_path])

    def setup_ui(self):
        top_bar = tk.Frame(self.window, bg="#0F172A")
        top_bar.pack(fill="x", padx=30, pady=(20, 10))

        tk.Label(top_bar, text="DISCOVERED OBJECTS GALLERY", font=("Segoe UI", 14, "bold"), 
                 bg="#0F172A", fg="#38BDF8").pack(side=tk.LEFT)
        
        btn_open_folder = tk.Button(top_bar, text="📁 OPEN DIRECTORY", font=("Segoe UI", 9, "bold"),
                                    bg="#10B981", fg="#FFFFFF", bd=0, cursor="hand2",
                                    activebackground="#34D399", activeforeground="white",
                                    command=self.open_saved_sessions_directory)
        btn_open_folder.pack(side=tk.RIGHT, ipady=6, padx=5)

        if not os.path.exists(self.base_dir) or not os.listdir(self.base_dir):
            tk.Label(self.window, text="No saved session history found on disk.", 
                     font=("Segoe UI", 11), bg="#0F172A", fg="#475569").pack(pady=150)
            return

        container = tk.Frame(self.window, bg="#0F172A")
        container.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        canvas = tk.Canvas(container, bg="#0F172A", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#0F172A")

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Sorting folders chronologically
        session_folders = sorted(
            [d for d in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, d))],
            key=lambda x: int(x.split('_')[1]) if '_' in x and x.split('_')[1].isdigit() else 0
        )

        MAX_COLUMNS = 4

        for folder in session_folders:
            folder_path = os.path.join(self.base_dir, folder)
            images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            if not images:
                continue 

            session_header = tk.Frame(scroll_frame, bg="#334155", padx=10, pady=5)
            session_header.pack(fill="x", pady=(20, 10))
            
            display_name = folder.replace("_", " ").upper()
            tk.Label(session_header, text=display_name, font=("Segoe UI", 10, "bold"), 
                     bg="#334155", fg="#38BDF8").pack(side=tk.LEFT)

            grid_frame = tk.Frame(scroll_frame, bg="#0F172A")
            grid_frame.pack(fill="x", pady=5)

            col_idx = 0
            row_idx = 0

            for img_name in images:
                img_path = os.path.join(folder_path, img_name)
                object_label = os.path.splitext(img_name)[0].upper()

                card = tk.Frame(grid_frame, bg="#1E293B", bd=0, padx=8, pady=8)
                card.grid(row=row_idx, column=col_idx, padx=10, pady=10, sticky="nsew")

                frame_cv = cv2.imread(img_path)
                if frame_cv is not None:
                    rgb_frame = cv2.cvtColor(frame_cv, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb_frame).resize((150, 120), Image.Resampling.LANCZOS)
                    tk_img = ImageTk.PhotoImage(pil_img)
                    self.image_references.append(tk_img) 
                    
                    lbl_thumb = tk.Label(card, image=tk_img, bg="#1E293B")
                    lbl_thumb.pack(side=tk.TOP, pady=(0, 6))

                lbl_text = tk.Label(card, text=object_label, font=("Segoe UI", 9, "bold"), 
                                    bg="#1E293B", fg="#F8FAFC", wraplength=140)
                lbl_text.pack(side=tk.TOP)

                col_idx += 1
                if col_idx >= MAX_COLUMNS:
                    col_idx = 0
                    row_idx += 1

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")