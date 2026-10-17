import cv2
import numpy as np
import time

GREEN   = (160, 229, 0)    
WHITE   = (255, 255, 255)
DIM     = (153, 136, 136)  
BLACK_T = (0, 0, 0)

FONT      = cv2.FONT_HERSHEY_SIMPLEX
FONT_MONO = cv2.FONT_HERSHEY_PLAIN

class HUD:

    def __init__(self):
        self.viteza         = 180
        self.directie       = "STOP"
        self.status         = True   
        self.gest_detectat  = "None"
        self.confidence     = 0.0

    def set_viteza(self, v: int):
        self.viteza = v

    def set_directie(self, d: str):
        self.directie = d

    def set_status(self, activ: bool):
        self.status = activ

    def set_gest(self, gest: str, confidence: float):
        self.gest_detectat = gest
        self.confidence    = confidence

    def render(self, frame: np.ndarray) -> np.ndarray:
        out = frame.copy()
        h, w = out.shape[:2]

        self._draw_colturi(out, w, h)
        self._draw_timestamp_rec(out)
        self._draw_gest_detectat(out, w)
        self._draw_viteza(out, h)
        self._draw_directie(out, w, h)
        self._draw_status(out, w, h)
        self._draw_crosshair(out, w, h)
        self._draw_linie_orizont(out, w, h)

        return out

    def _overlay_rect(self, frame, x, y, w, h, alpha=0.45):
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    def _draw_colturi(self, frame, w, h):
        margin = 20
        size   = 30
        t      = 2

        # stanga sus
        cv2.line(frame, (margin, margin), (margin, margin + size), GREEN, t)
        cv2.line(frame, (margin, margin), (margin + size, margin), GREEN, t)
        # dreapta sus
        cv2.line(frame, (w - margin, margin), (w - margin, margin + size), GREEN, t)
        cv2.line(frame, (w - margin, margin), (w - margin - size, margin), GREEN, t)
        # stanga jos
        cv2.line(frame, (margin, h - margin), (margin, h - margin - size), GREEN, t)
        cv2.line(frame, (margin, h - margin), (margin + size, h - margin), GREEN, t)
        # dreapta jos
        cv2.line(frame, (w - margin, h - margin), (w - margin, h - margin - size), GREEN, t)
        cv2.line(frame, (w - margin, h - margin), (w - margin - size, h - margin), GREEN, t)

    def _draw_timestamp_rec(self, frame):
        self._overlay_rect(frame, 20, 18, 160, 44)
        ts = time.strftime("%H:%M:%S")
        cv2.putText(frame, ts,
                    (30, 36), FONT, 0.38, DIM, 1, cv2.LINE_AA)
        cv2.circle(frame, (36, 52), 4, GREEN, -1)
        cv2.putText(frame, "REC",
                    (46, 56), FONT, 0.38, GREEN, 1, cv2.LINE_AA)

    def _draw_gest_detectat(self, frame, w):
        self._overlay_rect(frame, w - 200, 18, 180, 44)
        cv2.putText(frame, "GEST DETECTAT",
                    (w - 190, 33), FONT, 0.35, DIM, 1, cv2.LINE_AA)
        cv2.putText(frame, self.gest_detectat,
                    (w - 190, 52), FONT, 0.50, WHITE, 1, cv2.LINE_AA)
        conf_text = f"{self.confidence * 100:.1f}%"
        cv2.putText(frame, conf_text,
                    (w - 190 + 70, 52), FONT, 0.50, GREEN, 1, cv2.LINE_AA)

    def _draw_viteza(self, frame, h):
        self._overlay_rect(frame, 20, h - 90, 120, 72)
        cv2.putText(frame, "VITEZA",
                    (30, h - 68), FONT, 0.35, GREEN, 1, cv2.LINE_AA)
        cv2.putText(frame, str(self.viteza),
                    (30, h - 32), FONT, 0.90, WHITE, 2, cv2.LINE_AA)
        cv2.putText(frame, "PWM",
                    (95, h - 32), FONT, 0.35, DIM, 1, cv2.LINE_AA)

    def _draw_directie(self, frame, w, h):
        cx = w // 2
        cy = h - 55
        self._overlay_rect(frame, cx - 80, h - 90, 160, 72)

        directie_map = {
            "INAINTE": "INAINTE",
            "Open":    "INAINTE",
            "STOP":    "STOP",
            "Closed":  "STOP",
            "Left":    "STANGA",
            "Right":   "DREAPTA",
        }
        label = directie_map.get(self.directie, self.directie)

        # Sageata
        if label == "INAINTE":
            pts = np.array([[cx, cy - 18], [cx + 10, cy], [cx + 4, cy], [cx + 4, cy + 14], [cx - 4, cy + 14], [cx - 4, cy], [cx - 10, cy]], np.int32)
            cv2.fillPoly(frame, [pts], GREEN)
        elif label == "STOP":
            cv2.rectangle(frame, (cx - 10, cy - 10), (cx + 10, cy + 10), (80, 80, 220), -1)
        elif label == "STANGA":
            pts = np.array([[cx - 18, cy], [cx, cy - 10], [cx, cy - 4], [cx + 14, cy - 4], [cx + 14, cy + 4], [cx, cy + 4], [cx, cy + 10]], np.int32)
            cv2.fillPoly(frame, [pts], GREEN)
        elif label == "DREAPTA":
            pts = np.array([[cx + 18, cy], [cx, cy - 10], [cx, cy - 4], [cx - 14, cy - 4], [cx - 14, cy + 4], [cx, cy + 4], [cx, cy + 10]], np.int32)
            cv2.fillPoly(frame, [pts], GREEN)

        cv2.putText(frame, label,
                    (cx - 30, h - 26), FONT, 0.42, WHITE, 1, cv2.LINE_AA)

    def _draw_status(self, frame, w, h):
        self._overlay_rect(frame, w - 140, h - 90, 120, 72)
        cv2.putText(frame, "STATUS",
                    (w - 130, h - 68), FONT, 0.35, GREEN, 1, cv2.LINE_AA)

        if self.status:
            dot_color  = GREEN
            status_txt = "ACTIV"
        else:
            dot_color  = (80, 80, 220)
            status_txt = "PAUZA"

        cv2.circle(frame, (w - 130 + 6, h - 50), 5, dot_color, -1)
        cv2.putText(frame, status_txt,
                    (w - 130 + 16, h - 46), FONT, 0.45, WHITE, 1, cv2.LINE_AA)

        cv2.putText(frame, "SEMN TRIMIS",
                    (w - 130, h - 34), FONT, 0.32, DIM, 1, cv2.LINE_AA)
        cv2.putText(frame, self.gest_detectat[:10],
                    (w - 130, h - 22), FONT, 0.42, WHITE, 1, cv2.LINE_AA)

    def _draw_crosshair(self, frame, w, h):
        cx, cy = w // 2, h // 2
        size   = 12
        cv2.line(frame, (cx - size - 4, cy), (cx - 4, cy), GREEN, 1, cv2.LINE_AA)
        cv2.line(frame, (cx + 4, cy), (cx + size + 4, cy), GREEN, 1, cv2.LINE_AA)
        cv2.line(frame, (cx, cy - size - 4), (cx, cy - 4), GREEN, 1, cv2.LINE_AA)
        cv2.line(frame, (cx, cy + 4), (cx, cy + size + 4), GREEN, 1, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), 8, GREEN, 1, cv2.LINE_AA)

    def _draw_linie_orizont(self, frame, w, h):
        cy = h // 2
        cv2.line(frame, (80, cy), (w - 80, cy),
                 GREEN, 1, cv2.LINE_AA)