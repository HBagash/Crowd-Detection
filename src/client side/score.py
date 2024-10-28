import torch
import json
from PIL import Image
from io import BytesIO
from ultralytics import YOLO

# Initialize the model once
def init():
    global model
    model = YOLO('yolov8-heads.pt')  # Load your model here
    model.eval()  # Set the model to evaluation mode

# Handle requests to the model
def run(raw_data):
    # Decode the input data
    image = Image.open(BytesIO(raw_data))
    results = model(image)

    # Prepare the output
    output = []
    for result in results:
        for box in result.boxes:
            output.append({
                "confidence": box.conf.item(),
                "bbox": box.xyxy[0].tolist()  # Convert tensor to list
            })

    return json.dumps(output)
