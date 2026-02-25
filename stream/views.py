from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import cv2
import json
import time
import threading

# ================= GLOBAL CAMERA =================

camera = cv2.VideoCapture(0)

lock = threading.Lock()
      
# ================= SETTINGS PER CAMERA =================

settings = {
    1: {"threshold": 128, "sepi": 100000, "sedang": 50000, "padat": 0},
    2: {"threshold": 128, "sepi": 100000, "sedang": 50000, "padat": 0},
    3: {"threshold": 128, "sepi": 100000, "sedang": 50000, "padat": 0},
    4: {"threshold": 128, "sepi": 100000, "sedang": 50000, "padat": 0},
}

camera_data = [
    {"status": "Sepi", "area": 0},
    {"status": "Sepi", "area": 0},
    {"status": "Sepi", "area": 0},
    {"status": "Sepi", "area": 0},
]

FPS = 15
FRAME_DELAY = 1 / FPS


# ================= PROCESS =================

def process_frame(frame, cam_id):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    th = settings[cam_id]["threshold"]

    _, thresh = cv2.threshold(gray, th, 255, cv2.THRESH_BINARY)

    area = cv2.countNonZero(thresh)

    sepi = settings[cam_id]["sepi"]
    sedang = settings[cam_id]["sedang"]

    if area > sepi:
        status = "Sepi"
    elif area > sedang:
        status = "Sedang"
    else:
        status = "Padat"

    camera_data[cam_id - 1] = {
        "status": status,
        "area": int(area)
    }

    return thresh


# ================= STREAM GENERATOR =================

def gen_frames(cam_id):

    while True:

        start_time = time.time()

        with lock:
            success, frame = camera.read()

        if not success:
            continue

        frame = process_frame(frame, cam_id)

        _, buffer = cv2.imencode('.jpg', frame)

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            buffer.tobytes() +
            b'\r\n'
        )

        elapsed = time.time() - start_time
        sleep_time = FRAME_DELAY - elapsed

        if sleep_time > 0:
            time.sleep(sleep_time)


# ================= VIDEO API =================

def video_feed(request, cam_id):

    return StreamingHttpResponse(
        gen_frames(cam_id),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


# ================= DATA API =================

def get_data(request):

    return JsonResponse({
        "cameras": camera_data
    })


# ================= UPDATE THRESHOLD =================

@csrf_exempt
def set_threshold(request):

    body = json.loads(request.body)

    cam = body["camera"]
    value = body["threshold"]

    settings[cam]["threshold"] = value

    return JsonResponse({"ok": True})


# ================= UPDATE CLASSIFICATION =================

@csrf_exempt
def set_classification(request):

    body = json.loads(request.body)

    cam = body["camera"]

    settings[cam]["sepi"] = body["sepi"]
    settings[cam]["sedang"] = body["sedang"]
    settings[cam]["padat"] = body["padat"]

    return JsonResponse({"ok": True})