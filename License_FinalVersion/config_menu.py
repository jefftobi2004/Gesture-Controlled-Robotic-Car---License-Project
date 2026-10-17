import tkinter as tk
from PIL import Image, ImageTk
from session_window import SessionWindow

class ConfigMenu:
    def __init__(self, default_camera=0, default_ip="192.168.4.3"):
        self.root = tk.Tk()
        self.root.title("AI Vision Control Center - Launcher")
        
        self.root.geometry("1050x600")
        self.root.configure(bg="#0F172A")
        self.root.resizable(False, False)
        
        self.root.eval('tk::PlaceWindow . center')
        self.camera_index = default_camera
        self.phone_url = ""
        self.is_cancelled = True
        self.exit_app = False

        self.setup_ui(default_camera, default_ip)

    def setup_ui(self, default_camera, default_ip):
        left_panel = tk.Frame(self.root, bg="#1E293B", width=420, height=600)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        left_panel.pack_propagate(False)

        tk.Label(left_panel, text="CONTROL PANEL", font=("Segoe UI", 18, "bold"), 
                 bg="#1E293B", fg="#38BDF8").pack(pady=(50, 40))

        tk.Label(left_panel, text="CAMERA INDEX (LAPTOP)", font=("Segoe UI", 9, "bold"), 
                 bg="#1E293B", fg="#94A3B8").pack(anchor="w", padx=45, pady=(0, 5))
        
        self.camera_entry = tk.Entry(left_panel, font=("Segoe UI", 12), justify="center",
                                     bg="#334155", fg="#F8FAFC", bd=0, insertbackground="white")
        self.camera_entry.insert(0, str(default_camera))
        self.camera_entry.pack(fill="x", padx=45, ipady=10, pady=(0, 25))

        tk.Label(left_panel, text="ESP32 / PHONE IP ADDRESS", font=("Segoe UI", 9, "bold"), 
                 bg="#1E293B", fg="#94A3B8").pack(anchor="w", padx=45, pady=(0, 5))
        
        self.ip_entry = tk.Entry(left_panel, font=("Segoe UI", 12), justify="center",
                                 bg="#334155", fg="#F8FAFC", bd=0, insertbackground="white")
        self.ip_entry.insert(0, default_ip)
        self.ip_entry.pack(fill="x", padx=45, ipady=10, pady=(0, 45))

        self.btn_start = tk.Button(left_panel, text="LAUNCH SYSTEM", font=("Segoe UI", 11, "bold"), 
                                   bg="#0EA5E9", fg="#FFFFFF", bd=0, cursor="hand2",
                                   activebackground="#38BDF8", activeforeground="white", command=self.launch)
        self.btn_start.pack(fill="x", padx=45, ipady=12, pady=8)

        self.btn_session = tk.Button(left_panel, text="SESSION ITEMS DISCOVERED", font=("Segoe UI", 10, "bold"), 
                                     bg="#334155", fg="#F8FAFC", bd=0, cursor="hand2",
                                     activebackground="#475569", activeforeground="white", 
                                     command=self.open_gallery)
        self.btn_session.pack(fill="x", padx=45, ipady=12, pady=8)

        self.btn_exit = tk.Button(left_panel, text="EXIT APPLICATION", font=("Segoe UI", 10, "bold"), 
                                  bg="#EF4444", fg="#FFFFFF", bd=0, cursor="hand2",
                                  activebackground="#F87171", activeforeground="white", command=self.terminate)
        self.btn_exit.pack(fill="x", padx=45, ipady=12, pady=(35, 0))

        right_panel = tk.Frame(self.root, bg="#0F172A", width=630, height=600)
        right_panel.pack(side=tk.RIGHT, fill="both", expand=True)

        try:
            img_originala = Image.open("assets/line_art.png")
            img_redimensionata = img_originala.resize((500, 380), Image.Resampling.LANCZOS)
            self.car_img = ImageTk.PhotoImage(img_redimensionata)
            
            lbl_img = tk.Label(right_panel, image=self.car_img, bg="#0F172A")
            lbl_img.place(relx=0.5, rely=0.5, anchor="center") 
        except Exception as e:
            tk.Label(right_panel, text="PLACEHOLDER", 
                     font=("Segoe UI", 11), bg="#0F172A", fg="#334155").place(relx=0.5, rely=0.5, anchor="center")

    def launch(self):
        try:
            self.camera_index = int(self.camera_entry.get())
        except ValueError:
            self.camera_index = 0
            
        raw_ip = self.ip_entry.get().strip()
        self.phone_url = f"http://{raw_ip}:8080/video"
        
        self.is_cancelled = False
        self.root.quit()

    def open_gallery(self):
        SessionWindow(self.root)

    def terminate(self):
        self.exit_app = True
        self.root.quit()

    def show(self):
        self.root.mainloop()
        if self.root.winfo_exists():
            self.root.destroy()
        return self.is_cancelled, self.camera_index, self.phone_url, self.exit_app