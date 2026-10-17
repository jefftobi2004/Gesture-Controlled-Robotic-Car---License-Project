import socket

class ESPCommunicator:

    def __init__(self, esp_ip: str = "192.168.4.1", esp_port: int = 4210, confidence_threshold: float = 0.60):
        self.esp_ip               = esp_ip
        self.esp_port             = esp_port
        self.confidence_threshold = confidence_threshold
        self.last_sent            = ""
        self.trimitere_activa     = "True"

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.settimeout(0)

        print(f"[ESP] Communicator initializat → {self.esp_ip}:{self.esp_port}")

    def trimite_semn(self, gesture_name: str, confidence: float):
        if not self.trimitere_activa:
            return
        if confidence < self.confidence_threshold:
            return
        try:
            self._sock.sendto(gesture_name.encode("utf-8"), (self.esp_ip, self.esp_port))
            print(f"[ESP] Trimis: {gesture_name} ({confidence*100:.1f}%)")
            self.last_sent = gesture_name
        except Exception as e:
            print(f"[ESP] Eroare trimitere: {e}")

    def trimite_semn_direct(self, semn: str):
        try:
            self._sock.sendto(semn.encode("utf-8"), (self.esp_ip, self.esp_port))
            print(f"[ESP] Trimitere oprire: {semn}")
        except Exception as e:
            print(f"[ESP] Eroare: {e}")

    def trimite_viteza(self, viteza: int):
        mesaj = f"SPEED:{viteza}"
        try:
            self._sock.sendto(mesaj.encode("utf-8"), (self.esp_ip, self.esp_port))
            print(f"[ESP] Viteza setata: {viteza}")
        except Exception as e:
            print(f"[ESP] Eroare viteza: {e}")

    def close(self):
        try:
            self._sock.sendto("EXIT".encode("utf-8"), (self.esp_ip, self.esp_port))
            print("[ESP] Semnal EXIT trimis.")
        except:
            pass
        self._sock.close()
        print("[ESP] Socket inchis.")