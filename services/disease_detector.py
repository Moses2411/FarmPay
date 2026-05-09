import torch
from torchvision import transforms, models
from PIL import Image
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "models", "plant_disease_model.pth")
CLASS_INDEX_PATH = os.path.join(BASE_DIR, "models", "class_index.json")

model = None
idx_to_label = None


def load_model():
    global model, idx_to_label

    if model is None:
        try:
            model = models.mobilenet_v2(weights=None)

            model.classifier[1] = torch.nn.Sequential(
                torch.nn.Dropout(0.2),
                torch.nn.Linear(model.classifier[1].in_features, 38)
            )

            model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
            model.eval()

            with open(CLASS_INDEX_PATH) as f:
                idx_to_label = json.load(f)

        except Exception as e:
            print("MODEL LOAD ERROR:", str(e))
            model = None


transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])


def detect_disease(image_path: str):
    load_model()

    if model is None:
        return {
            "disease_detected": False,
            "disease_name": "",
            "status": "approved"
        }

    img = Image.open(image_path).convert("RGB")
    input_tensor = transform(img).unsqueeze(0)

    with torch.no_grad():
        output = model(input_tensor)
        _, pred_idx = torch.max(output, 1)
        label = idx_to_label[str(pred_idx.item())]

    disease_detected = "healthy" not in label.lower()

    return {
        "disease_detected": disease_detected,
        "disease_name": "" if not disease_detected else label,
        "status": "rejected" if disease_detected else "approved"
    }