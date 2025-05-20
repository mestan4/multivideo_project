import torch
import numpy as np
import cv2

class YOLODetector:
    def __init__(self, model_name='yolov5s', device=None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = torch.hub.load('ultralytics/yolov5', model_name, pretrained=True).to(self.device)
        self.model.eval()

    def detect(self, frame):
        """
        Frame girişi alır, YOLO ile analiz eder ve:
        - anotlanmış kare
        - tespit edilen kişi sayısı (class 0) döner
        """
        results = self.model(frame)
        annotated = results.render()[0]  # BGR annotated image
        people = sum(1 for c in results.pred[0][:, -1] if int(c) == 0)
        return annotated, people
2