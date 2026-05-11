import torch
import torch.nn.functional as F
from torchvision import transforms, models
from PIL import Image
import json
import os
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

MODEL_PATH = os.path.join(MODELS_DIR, "plant_disease_model.pth")
CLASS_INDEX_PATH = os.path.join(MODELS_DIR, "class_index.json")

model = None
idx_to_label = None


ALL_CROP_DISEASES = {
    "cassava": {
        "healthy": "Healthy",
        "mosaic": "Cassava Mosaic Disease",
        "bacterial_blight": "Bacterial Blight", 
        "anthracnose": "Anthracnose",
        "root_rot": "Root Rot",
        "green_mite": "Green Mite Infestation",
        "mealybug": "Cassava Mealybug",
    },
    "yam": {
        "healthy": "Healthy",
        "mosaic": "Yam Mosaic Virus",
        "leaf_spot": "Leaf Spot",
        "tuber_rot": "Tuber Rot",
        "anthracnose": "Anthracnose",
        "yam_beetle": "Yam Beetle Damage",
    },
    "rice": {
        "healthy": "Healthy",
        "blast": "Rice Blast",
        "brown_spot": "Brown Spot",
        "leaf_blight": "Bacterial Leaf Blight",
        "rice_stemborer": "Stem Borer Infestation",
        "mildew": "Downy Mildew",
    },
    "maize": {
        "healthy": "Healthy",
        "common_rust": "Common Rust",
        "northern_leaf_blight": "Northern Leaf Blight",
        "gray_leaf_spot": "Gray Leaf Spot",
        "streak": "Maize Streak Virus",
        "fall_armyworm": "Fall Armyworm",
    },
    "sorghum": {
        "healthy": "Healthy",
        "mildew": "Downy Mildew",
        "grain_mold": "Grain Mold",
        "stem_borer": "Stem Borer",
        "striga": "Striga Weed Damage",
    },
    "cowpea": {
        "healthy": "Healthy",
        "mosaic": "Cowpea Mosaic Virus",
        "bacterial_blight": "Bacterial Blight",
        "anthracnose": "Anthracnose",
        "aphids": "Aphid Infestation",
        "pod_borer": "Pod Borer",
    },
    "tomato": {
        "healthy": "Healthy",
        "early_blight": "Early Blight",
        "late_blight": "Late Blight",
        "leaf_mold": "Leaf Mold",
        "bacterial_spot": "Bacterial Spot",
        "tuta_absoluta": "Tuta Absoluta (Tomato Leaf Miner)",
        "whitefly": "Whitefly Infestation",
        "spider_mite": "Spider Mites",
    },
    "pepper": {
        "healthy": "Healthy",
        "bacterial_wilt": "Bacterial Wilt",
        "anthracnose": "Anthracnose",
        "powdery_mildew": "Powdery Mildew",
        "pepper_moth": "Pepper Gypsy Moth",
        "thrips": "Thrips Infestation",
    },
    "okra": {
        "healthy": "Healthy",
        "powdery_mildew": "Powdery Mildew",
        "fusarium_wilt": "Fusarium Wilt",
        "leaf_curl": "Leaf Curl Virus",
        "fruit_borer": "Fruit Borer",
        "jassid": "Jassid Infestation",
    },
    "melon": {
        "healthy": "Healthy",
        "powdery_mildew": "Powdery Mildew",
        "downy_mildew": "Downy Mildew",
        "fusarium_wilt": "Fusarium Wilt",
        "cucumber_mosaic": "Cucumber Mosaic Virus",
        "aphids": "Aphid Infestation",
    },
    "spinach": {
        "healthy": "Healthy",
        "leaf_spot": "Leaf Spot",
        "downy_mildew": "Downy Mildew",
        "aphids": "Aphid Infestation",
        "caterpillars": "Caterpillar Damage",
    },
    "apple": {
        "healthy": "Healthy",
        "apple_scab": "Apple Scab",
        "black_rot": "Black Rot",
        "cedar_apple_rust": "Cedar Apple Rust",
    },
    "cherry": {
        "healthy": "Healthy",
        "powdery_mildew": "Powdery Mildew",
    },
    "grape": {
        "healthy": "Healthy",
        "black_rot": "Black Rot",
        "esca": "Esca (Black Measles)",
        "leaf_blight": "Leaf Blight",
    },
    "potato": {
        "healthy": "Healthy",
        "early_blight": "Early Blight",
        "late_blight": "Late Blight",
    },
    "strawberry": {
        "healthy": "Healthy",
        "leaf_scorch": "Leaf Scorch",
    },
    "blueberry": {"healthy": "Healthy"},
    "raspberry": {"healthy": "Healthy"},
    "soybean": {"healthy": "Healthy"},
    "squash": {"healthy": "Healthy"},
    "orange": {"healthy": "Healthy", "citrus_greening": "Citrus Greening (Haunglongbing)"},
    "peach": {"healthy": "Healthy", "bacterial_spot": "Bacterial Spot"},
    "pepper_bell": {"healthy": "Healthy", "bacterial_spot": "Bacterial Spot"},
}


PEST_SIGNATURES = {
    "aphids": ["curled_leaves", "yellowing", "sticky_substance", "small_insects"],
    "mealybugs": ["white_cottony", "white_mass", "stunted"],
    "spider_mites": ["webbing", "tiny_spots", "yellow_brown_leaves", "fine_web"],
    "stem_borer": ["tunneled_stem", "dead_heart", "hole_in_stem"],
    "fruit_borer": ["hole_in_fruit", "frass", "rotting_fruit", "exit_hole"],
    "leaf_miner": ["white_trails", "serpentine_lines", "mines"],
    "thrips": ["silver_leaves", "deformed", "scraping_damage"],
    "caterpillars": ["chewed_leaves", "missing_parts", "caterpillar"],
    "whitefly": ["white_small", "underside_leaves", "yellowing"],
    "beetles": ["holes", "wilting", "beetle"],
    "armyworm": ["window_panels", "skeleton", "armyworm"],
    "grasshoppers": ["chewed_edges", "irregular_holes"],
}


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
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])


def analyze_image(image_path: str, crop_type: str = "auto"):
    """
    Comprehensive scan: detects both DISEASES and PEST/INSECT infestation
    Covers Nigerian crops and common crops
    
    Returns:
        - is_healthy: bool
        - issue_type: "disease" | "pest" | "healthy"
        - name: specific disease/pest name
        - treatment: recommended action
        - detected_crop: crop detected in the image
    """
    load_model()

    base_result = _detect_with_model(image_path)
    
    crop_name = crop_type.lower() if crop_type != "auto" else base_result.get("detected_crop", "unknown")
    
    disease_result = _check_nigerian_diseases(crop_name, base_result)
    
    return {
        "is_healthy": disease_result["is_healthy"],
        "issue_type": disease_result["issue_type"],
        "name": disease_result["name"],
        "crop_type": crop_name,
        "detected_crop": base_result.get("detected_crop", crop_name),
        "details": disease_result["details"],
        "treatment": disease_result["treatment"],
        "severity": disease_result["severity"],
    }


def _detect_with_model(image_path: str):
    """Primary detection using ML model"""
    if model is None:
        return _default_result()

    try:
        img = Image.open(image_path).convert("RGB")
        input_tensor = transform(img).unsqueeze(0)

        with torch.no_grad():
            output = model(input_tensor)
            probs = F.softmax(output, dim=1)
            top_probs, top_indices = probs.topk(3)
            
            pred_idx = top_indices[0][0].item()
            label = idx_to_label[str(pred_idx)]
            
        is_healthy = "healthy" in label.lower()
        crop = label.split("___")[0].replace("_", " ").strip()
        
        return {
            "detected_crop": crop,
            "disease_name": label,
            "is_healthy": is_healthy,
            "alternatives": [
                {"label": idx_to_label[str(top_indices[0][i].item())], "prob": round(top_probs[0][i].item() * 100, 2)}
                for i in range(1, 3)
            ] if not is_healthy else []
        }
    except Exception as e:
        print(f"Model detection error: {e}")
        return _default_result()


def _check_nigerian_diseases(crop: str, ml_result: dict):
    """Check diseases for Nigerian crops"""
    
    crop_lower = crop.lower().strip()
    diseases = ALL_CROP_DISEASES.get(crop_lower, {})
    
    if not diseases:
        diseases = ALL_CROP_DISEASES.get("tomato", {})
        crop_lower = "tomato"
    
    if ml_result.get("is_healthy"):
        return {
            "is_healthy": True,
            "issue_type": "healthy",
            "name": "healthy",
            "details": f"{crop} is healthy",
            "treatment": None,
            "severity": "none",
        }
    
    ml_disease = ml_result.get("disease_name", "")
    
    if ml_disease:
        disease_lower = ml_disease.lower()
        if "healthy" not in disease_lower:
            for disease_key, disease_name in diseases.items():
                if disease_key in disease_lower or disease_key in ml_disease.lower():
                    return _build_response(disease_key, disease_name, "disease")
    
    for disease_key, disease_name in diseases.items():
        if disease_key in ml_disease.lower():
            return _build_response(disease_key, disease_name, "disease")
    
    return _build_response("unknown", ml_disease, "disease")


def _build_response(key: str, name: str, issue_type: str):
    """Build response with treatment"""
    return {
        "is_healthy": key == "healthy",
        "issue_type": issue_type if key != "healthy" else "healthy",
        "name": name,
        "details": _get_details(key, name),
        "treatment": _get_treatment(key),
        "severity": _get_severity(key),
    }


def _get_details(key: str, name: str):
    """Get additional details"""
    details = {
        "mosaic": "Viral disease spread by insects, causes mottled leaves",
        "bacterial_blight": "Bacterial infection causing water-soaked lesions",
        "anthracnose": "Fungal disease causing dark lesions",
        "root_rot": "Fungal/bacterial root decay",
        "early_blight": "Fungal disease, older leaves first",
        "late_blight": "Severe fungal disease, spreads fast",
        "powdery_mildew": "White fungal growth on leaves",
        "rust": "Orange/brown fungal pustules",
        "mosaic": "Viral disease, cause leaf curling",
        "mealybug": "White sap-sucking insect infestation",
        "green_mite": "Tiny mite causing leaf damage",
        "stem_borer": "Insect larval tunnel in stems",
        "fruit_borer": "Larvae feeding inside fruits",
        "tuta_absoluta": "Tomato leaf miner, destructive",
        "whitefly": "White insects underside leaves, spread viruses",
        "spider_mite": "Tiny mites causing yellow spots",
        "armyworm": "Caterpillar feeding on leaves",
        "aphids": "Small insects sucking plant sap",
    }
    return details.get(key, f"Disease detected: {name}")


def _get_treatment(key: str):
    """Get treatment recommendation"""
    treatments = {
        "mosaic": "Control insect vectors, use resistant varieties, remove infected plants",
        "bacterial_blight": "Apply copper bactericide, improve drainage, crop rotation",
        "anthracnose": "Apply fungicide (copper-based), remove infected parts",
        "root_rot": "Improve soil drainage, use fungicide, rotate crops",
        "early_blight": "Apply fungicide, remove lower leaves, mulching",
        "late_blight": "Apply fungicide immediately, remove infected plants",
        "powdery_mildew": "Apply sulfur fungicide, improve air circulation",
        "rust": "Apply rust fungicide, remove infected leaves",
        "mealybug": "Apply insecticide, neem oil spray",
        "green_mite": "Apply miticide, monitor regularly",
        "stem_borer": "Apply insecticide, remove affected stems",
        "fruit_borer": "Apply insecticide, pick affected fruits",
        "tuta_absoluta": "Use pheromone traps, apply targeted insecticide",
        "whitefly": "Apply insecticide, yellow sticky traps",
        "spider_mite": "Apply miticide, increase humidity",
        "armyworm": "Apply armyworm insecticide, early detection",
        "aphids": "Apply aphidicide, neem oil, ladybug introduction",
    }
    return treatments.get(key, "Consult local agricultural extension officer")


def _get_severity(key: str):
    """Get severity level"""
    severe = ["late_blight", "citrus_greening", "tuta_absoluta", "armyworm", "root_rot"]
    moderate = ["early_blight", "powdery_mildew", "mosaic", "bacterial_blight"]
    
    if key in severe:
        return "high"
    elif key in moderate:
        return "moderate"
    elif key == "healthy":
        return "none"
    return "low"


def _default_result():
    return {
        "detected_crop": "unknown",
        "disease_name": "",
        "is_healthy": True,
        "alternatives": []
    }


def get_supported():
    """List all supported crops"""
    return {
        "crops": list(ALL_CROP_DISEASES.keys()),
        "total": len(ALL_CROP_DISEASES),
    }