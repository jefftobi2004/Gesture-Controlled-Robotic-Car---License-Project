import cv2
from utils.hud import HUD

PHONE_URL = "http://192.168.4.2:8080/video"

def main():
    cap = cv2.VideoCapture(PHONE_URL)
    hud = HUD()

    hud.set_viteza(180)
    hud.set_directie("INAINTE")
    hud.set_status(True)
    hud.set_gest("Open", 0.942)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Nu pot citi feedul!")
            break

        frame = cv2.resize(frame, (1280, 720))
        frame = hud.render(frame)

        cv2.imshow("Camera masina", frame)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()