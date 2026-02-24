from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import cv2
import numpy as np
import threading
import time
import json

# ================= CAMERA =================

class Camera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.frame = None
        self.running = True

        threading.Thread(target=self.update, daemon=True).start()

    def update(self):
        while self.running:

            if not self.cap.isOpened():
                print("❌ Kamera gagal")
                time.sleep(1)
                self.cap = cv2.VideoCapture(0)
                continue

            success, frame = self.cap.read()

            if success:
                self.frame = frame

            time.sleep(0.05)

    def get_frame(self):
        return self.frame


camera = Camera()

# ================= SETTINGS 4 CAMERA =================

cam_settings = [
    {"threshold": 120, "sepi": 100000, "sedang": 50000, "padat": 0},
    {"threshold": 130, "sepi": 100000, "sedang": 50000, "padat": 0},
    {"threshold": 140, "sepi": 100000, "sedang": 50000, "padat": 0},
    {"threshold": 150, "sepi": 100000, "sedang": 50000, "padat": 0},
]

# ================= PROCESS =================

def process_frame(frame, setting):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    _, binary = cv2.threshold(
        gray,
        setting["threshold"],
        255,
        cv2.THRESH_BINARY
    )

    area = int(cv2.countNonZero(binary))

    if area > setting["sepi"]:
        status = "Padat"
    elif area > setting["sedang"]:
        status = "Sedang"
    else:
        status = "Sepi"

    binary = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    return binary, area, status


# ================= VIDEO STREAM =================

def gen_frames():

    while True:

        frame = camera.get_frame()

        if frame is None:
            continue

        frame = cv2.resize(frame, (320, 240))

        cams = []

        for i in range(4):

            img, area, status = process_frame(frame, cam_settings[i])

            cv2.putText(
                img,
                f"CAM {i+1} | {status} | {area}",
                (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1
            )

            cams.append(img)

        top = np.hstack((cams[0], cams[1]))
        bottom = np.hstack((cams[2], cams[3]))
        combined = np.vstack((top, bottom))

        ret, buffer = cv2.imencode('.jpg', combined)

        if not ret:
            continue

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            buffer.tobytes() +
            b'\r\n'
        )


def video_feed(request):
    return StreamingHttpResponse(
        gen_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


# ================= DATA FEED =================

def data_feed(request):

    frame = camera.get_frame()

    if frame is None:
        return JsonResponse({"error": "no frame"})

    results = []

    for i in range(4):

        _, area, status = process_frame(frame, cam_settings[i])

        results.append({
            "cam": i + 1,
            "status": status,
            "area": area,
            "threshold": cam_settings[i]["threshold"],
        })

    return JsonResponse({"cameras": results})


# ================= UPDATE THRESHOLD =================

@csrf_exempt
def set_threshold(request):

    if request.method == "POST":

        data = json.loads(request.body.decode("utf-8"))

        cam = int(data.get("cam", 1)) - 1
        threshold = int(data.get("threshold", 120))

        cam_settings[cam]["threshold"] = threshold

        return JsonResponse({"message": "ok"})

    return JsonResponse({"error": "invalid"}, status=405)


# ================= UPDATE CLASS =================

@csrf_exempt
def set_classification(request):

    if request.method == "POST":

        data = json.loads(request.body.decode("utf-8"))

        cam = int(data.get("cam", 1)) - 1

        cam_settings[cam]["sepi"] = int(data.get("sepi"))
        cam_settings[cam]["sedang"] = int(data.get("sedang"))
        cam_settings[cam]["padat"] = int(data.get("padat"))

        return JsonResponse({"message": "ok"})

    return JsonResponse({"error": "invalid"}, status=405)