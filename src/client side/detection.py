from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
import cv2
import torch
from ultralytics import YOLO
import numpy as np
import mss
import time
import requests
import os
import threading
import JsonResponse

class Detection(QThread):
    changePixmap = pyqtSignal(QImage)
    peopleCountChanged = pyqtSignal(int)

    def __init__(self, token, location, receiver):
        super(Detection, self).__init__()
        self.running = True
        self.token = token
        self.location = location
        self.receiver = receiver

        # Load the YOLOv8 Nano model
        self.model = YOLO('weights/yolov8-heads.pt')  # Nano model for better performance

        self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        self.model.to(self.device)

        self.threshold = 15  # Population threshold
        self.threshold_duration = 3  # Duration in seconds
        self.cooldown_duration = 10  # Cooldown period in seconds
        self.exceeded_threshold_time = None  # Start time when threshold is exceeded
        self.last_saved_time = time.time()  # Initialize the last saved time to current time

    def run(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Capturing the primary monitor for screen capture

            while self.running:
                frame = self.capture_screen(sct, monitor)
                person_count = self.perform_inference(frame)

                # Emit the people count signal immediately after inference
                self.peopleCountChanged.emit(person_count)
                
                # Debugging population count
                print(f"[DEBUG] Detected Person Count: {person_count}")

                self.check_and_save_frame(frame, person_count)

                # Convert to RGB for display in PyQt5
                rgbImage = self.convert_to_qimage(frame)
                self.changePixmap.emit(rgbImage)

    def capture_screen(self, sct, monitor):
        """Capture the screen and return the processed frame."""
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        img = cv2.resize(img, (854, 480))  # Reduce resolution for better performance
        frame = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # Convert to BGR (as mss captures in RGB)
        return frame

    def get_current_population(request):
        latest_alert = UploadAlert.objects.latest('date_created')
        return JsonResponse({
            'location': latest_alert.location,
            'population_count': latest_alert.population_count,
        })


    def perform_inference(self, frame):
        """Perform inference with the YOLOv8 model and return the person count."""
        results = self.model(frame, device=self.device, conf=0.25, iou=0.25)
        person_count = 0

        for result in results:
            for box in result.boxes:
                coords = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, coords)
                confidence = box.conf.item()

                if confidence > 0.4:
                    person_count += 1
                    self.draw_head_circle(frame, x1, y1, x2, y2, confidence)

        return person_count

    def draw_head_circle(self, frame, x1, y1, x2, y2, confidence):
        """Draw a circle around the detected head."""
        head_y1 = y1
        head_y2 = y1 + int((y2 - y1) / 3)  # Adjust for the top third of the bounding box
        center_x = (x1 + x2) // 2
        center_y = (head_y1 + head_y2) // 2
        radius = max(5, (head_y2 - head_y1) // 2)

        cv2.circle(frame, (center_x, center_y), radius, (0, 255, 0), 2)
        cv2.putText(frame, f'Head {confidence:.2f}', (center_x - radius, head_y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    def check_and_save_frame(self, frame, person_count):
        """Check conditions and save the frame if the population threshold is exceeded."""
        current_time = time.time()

        if person_count > self.threshold:
            if self.exceeded_threshold_time is None:
                self.exceeded_threshold_time = current_time
                print(f"[DEBUG] Population threshold exceeded at {self.exceeded_threshold_time}")
            elif current_time - self.exceeded_threshold_time >= self.threshold_duration:
                print(f"[DEBUG] Threshold duration exceeded by {current_time - self.exceeded_threshold_time} seconds")
                if current_time - self.last_saved_time >= self.cooldown_duration:
                    print(f"[DEBUG] Cooldown period exceeded. Saving frame.")
                    saved_image_path = self.save_frame(frame)
                    if saved_image_path:
                        print(f"[DEBUG] Frame saved at {saved_image_path}. Starting post_detection thread.")
                        threading.Thread(target=self.post_detection, args=(saved_image_path, person_count)).start()
                    self.last_saved_time = current_time  # Update the last saved time
                    self.exceeded_threshold_time = None  # Reset the timer after saving the frame
        else:
            if self.exceeded_threshold_time is not None:
                print("[DEBUG] Population dropped below threshold. Resetting threshold timer.")
            self.exceeded_threshold_time = None  # Reset timer if count drops below threshold

    def save_frame(self, frame):
        """Save the frame with a timestamp."""
        try:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            file_path = f"saved_frame/overcrowded_{timestamp}.jpg"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure directory exists
            cv2.imwrite(file_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            print(f"[DEBUG] Frame saved: {file_path}")
            return file_path
        except Exception as e:
            print(f"[ERROR] Error saving frame: {e}")
            return None

    def convert_to_qimage(self, frame):
        """Convert the frame to a QImage for display in PyQt5."""
        rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgbImage.shape
        bytesPerLine = channels * width
        return QImage(rgbImage.data, width, height, bytesPerLine, QImage.Format_RGB888)

    def stop(self):
        self.running = False
        self.wait()

    def post_detection(self, file_path, person_count):
        """Sends alert to the server asynchronously."""
        try:
            print(f"[DEBUG] Sending post request with population_count={person_count}")
            url = 'http://127.0.0.1:8000/api/images/'
            headers = {'Authorization': 'Token ' + self.token}
            with open(file_path, 'rb') as image_file:
                files = {'image': image_file}
                data = {
                    'user_ID': self.token,
                    'location': self.location,
                    'alert_receiver': self.receiver,
                    'population_count': person_count
                }
                response = requests.post(url, files=files, headers=headers, data=data)

            if response.ok:
                print('[DEBUG] Alert was sent to the server')
            else:
                print(f'[ERROR] Unable to send alert to the server: {response.status_code} {response.text}')
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request failed: {e}")
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred: {e}")


