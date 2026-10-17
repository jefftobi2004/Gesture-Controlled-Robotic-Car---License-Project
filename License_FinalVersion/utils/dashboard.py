import cv2
import numpy as np
from datetime import datetime
from collections import deque

BG_DARK       = (18, 20, 24)       
BG_PANEL      = (24, 28, 34)       
BG_PANEL_ALT  = (28, 32, 40)       
TEAL          = (160, 210, 80)     
TEAL_DIM      = (100, 150, 55)     
WHITE         = (220, 225, 230)    
GRAY          = (100, 108, 120)    
GRAY_DIM      = (55, 60, 70)       
YELLOW        = (40, 200, 220)     
RED_DIM       = (60, 70, 180)      

FONT       = cv2.FONT_HERSHEY_SIMPLEX
FONT_MONO  = cv2.FONT_HERSHEY_PLAIN

class Dashboard:
    def __init__(self, cam_width=1280, cam_height=720):
        self.CAM_W   = cam_width
        self.H       = cam_height
        self.PANEL_W = 340
        self.W       = self.CAM_W + self.PANEL_W

        self.activ        = True
        self.viteza       = 180
        self.last_sign    = "—"
        self.esp_conectat = False

        self.log_tastatura_items = deque(maxlen=12)
        self.log_semne_items     = deque(maxlen=10)

        self.canvas = np.zeros((self.H, self.W, 3), dtype=np.uint8)

    def set_activ(self, activ: bool):
        self.activ = activ

    def set_speed(self, viteza: int):
        self.viteza = viteza

    def set_last_sign(self, semn: str):
        self.last_sign = semn

    def set_esp_conectat(self, conectat: bool):
        self.esp_conectat = conectat

    def log_keyboard(self, mesaj: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_tastatura_items.append((ts, mesaj))

    def log_signal(self, mesaj: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_semne_items.append((ts, mesaj))

    def render(self, camera_frame_rgb):
        self.canvas[:] = BG_DARK
        self._draw_camera(camera_frame_rgb)
        self._draw_panel()
        return self.canvas

    def _draw_camera(self, frame_rgb):
        if frame_rgb is None:
            return

        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        h, w = frame_bgr.shape[:2]

        if w != self.CAM_W or h != self.H:
            frame_bgr = cv2.resize(frame_bgr, (self.CAM_W, self.H))

        self.canvas[0:self.H, 0:self.CAM_W] = frame_bgr

        self._draw_dashed_rect(
            4, 4,
            self.CAM_W - 4, self.H - 4,
            TEAL_DIM, dash=12, gap=6, thickness=1
        )

        cv2.putText(self.canvas,
                    f"CAMERA {self.CAM_W}x{self.H}",
                    (16, self.H - 14),
                    FONT_MONO, 1.0, GRAY, 1, cv2.LINE_AA)

    def _draw_dashed_rect(self, x1, y1, x2, y2, color, dash=10, gap=5, thickness=1):
        pts = []

        for x in range(x1, x2, dash + gap):
            pts.append(((x, y1), (min(x + dash, x2), y1)))

        for x in range(x1, x2, dash + gap):
            pts.append(((x, y2), (min(x + dash, x2), y2)))

        for y in range(y1, y2, dash + gap):
            pts.append(((x1, y), (x1, min(y + dash, y2))))

        for y in range(y1, y2, dash + gap):
            pts.append(((x2, y), (x2, min(y + dash, y2))))

        for p1, p2 in pts:
            cv2.line(self.canvas, p1, p2, color, thickness, cv2.LINE_AA)

    def _draw_panel(self):
        px = self.CAM_W  
        pw = self.PANEL_W

        cv2.rectangle(self.canvas,
                      (px, 0), (self.W, self.H),
                      BG_PANEL, -1)

        cv2.line(self.canvas, (px, 0), (px, self.H), GRAY_DIM, 1)

        y = 0

        y = self._draw_status(px, pw, y)

        y = self._draw_separator(px, pw, y)

        y = self._draw_log_section(px, pw, y, "TASTATURA",
                                   self.log_tastatura_items)

        y = self._draw_separator(px, pw, y)

        y = self._draw_log_section(px, pw, y, "SEMNE TRIMISE",
                                   self.log_semne_items)

    def _draw_status(self, px, pw, y):
        pad = 18
        y += 28

        dot_color = TEAL if self.activ else RED_DIM
        dot_x = px + pad + 6
        cv2.circle(self.canvas, (dot_x, y), 6, dot_color, -1, cv2.LINE_AA)

        status_text = "ACTIV" if self.activ else "INACTIV"
        cv2.putText(self.canvas, status_text,
                    (dot_x + 14, y + 5),
                    FONT_MONO, 1.3, dot_color, 1, cv2.LINE_AA)

        esp_text = "ESP ●" if self.esp_conectat else "ESP ○"
        esp_color = TEAL if self.esp_conectat else GRAY
        cv2.putText(self.canvas, esp_text,
                    (px + pw - 72, y + 5),
                    FONT_MONO, 1.0, esp_color, 1, cv2.LINE_AA)

        y += 32

        cv2.putText(self.canvas, "SPD",
                    (px + pad, y + 5),
                    FONT_MONO, 1.1, GRAY, 1, cv2.LINE_AA)
        cv2.putText(self.canvas, str(self.viteza),
                    (px + pad + 52, y + 5),
                    FONT_MONO, 1.3, YELLOW, 1, cv2.LINE_AA)

        y += 28

        cv2.putText(self.canvas, "SEMN",
                    (px + pad, y + 5),
                    FONT_MONO, 1.1, GRAY, 1, cv2.LINE_AA)
        cv2.putText(self.canvas, self.last_sign,
                    (px + pad + 52, y + 5),
                    FONT_MONO, 1.3, WHITE, 1, cv2.LINE_AA)

        y += 32
        return y

    def _draw_separator(self, px, pw, y):
        y += 8
        cv2.line(self.canvas,
                 (px + 14, y), (px + pw - 14, y),
                 GRAY_DIM, 1)
        y += 8
        return y

    def _draw_log_section(self, px, pw, y, titlu, items):
        pad = 18
        y += 16

        cv2.putText(self.canvas, titlu,
                    (px + pad, y + 5),
                    FONT_MONO, 1.1, TEAL, 1, cv2.LINE_AA)
        y += 22

        cv2.line(self.canvas,
                 (px + pad, y), (px + pw - pad, y),
                 GRAY_DIM, 1)
        y += 10

        for ts, mesaj in list(items):
            cv2.rectangle(self.canvas,
                          (px + 8, y - 2),
                          (px + pw - 8, y + 16),
                          BG_PANEL_ALT, -1)

            cv2.putText(self.canvas, ts,
                        (px + pad, y + 12),
                        FONT_MONO, 0.95, GRAY, 1, cv2.LINE_AA)

            max_chars = 22
            text = mesaj if len(mesaj) <= max_chars else mesaj[:max_chars-1] + "…"
            cv2.putText(self.canvas, text,
                        (px + pad + 68, y + 12),
                        FONT_MONO, 0.95, WHITE, 1, cv2.LINE_AA)

            y += 20

        return y