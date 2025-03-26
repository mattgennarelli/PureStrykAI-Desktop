import cv2
import easyocr
import numpy as np
from PIL import Image
import os
import re
from database import insert_swing_data

reader = easyocr.Reader(['en'], gpu=True)

CROP_BOTTOM_PERCENTAGE = 0.25
SCALE_FACTOR = 2.5

def preprocess_image(image_path):
    image = cv2.imread(image_path)
    height = image.shape[0]
    cropped = image[int(height * (1 - CROP_BOTTOM_PERCENTAGE)):, :]
    cropped = cv2.resize(cropped, (0, 0), fx=SCALE_FACTOR, fy=SCALE_FACTOR, interpolation=cv2.INTER_CUBIC)

    lab = cv2.cvtColor(cropped, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(enhanced, -1, sharpen_kernel)

    return sharpened

def extract_ocr_blocks(image):
    result = reader.readtext(image)
    blocks = []
    for item in result:
        text, conf, bbox = item[1], item[2], item[0]
        if isinstance(text, list):
            text = " ".join(map(str, text))
        blocks.append({'text': text, 'conf': conf, 'bbox': bbox})
    return blocks

def get_center(bbox):
    xs = [pt[0] for pt in bbox]
    ys = [pt[1] for pt in bbox]
    return np.mean(xs), np.mean(ys)

def match_metrics(blocks):
    metric_labels = [
        'TOTAL', 'CARRY', 'CURVE', 'CLUB SPEED', 'BALL SPEED',
        'SMASH FAC', 'SPIN RATE', 'ATTACK ANG', 'CLUB PATH',
        'FACE ANG', 'HEIGHT'
    ]

    label_map = {}
    value_map = []

    for block in blocks:
        raw_text = block['text']
        if not isinstance(raw_text, str):
            continue
        clean = raw_text.strip().upper().replace("FAC.", "FAC").replace("ANG.", "ANG").replace("_", "").replace("°", "").strip()
        center = get_center(block['bbox'])
        if clean in metric_labels:
            label_map[clean] = {'pos': center}
        elif any(char.isdigit() for char in clean):
            value_map.append({'text': clean, 'pos': center})

    structured = {}

    for label, meta in label_map.items():
        label_x, label_y = meta['pos']
        candidates = []
        for val in value_map:
            val_x, val_y = val['pos']
            dx = abs(val_x - label_x)
            dy = abs(val_y - label_y)
            if 15 < dy < 150:
                dist = np.hypot(dx, dy)
                candidates.append((dist, val['text']))
        if candidates:
            best = sorted(candidates, key=lambda x: x[0])[0][1]
            structured[label] = best

    return structured, blocks

def extract_club_name(blocks):
    club_pattern = re.compile(r'\b(\d{1,2}\s*IRON|PW|GW|SW|LW|DRIVER|HYBRID|WOOD|WEDGE)\b', re.IGNORECASE)
    for block in blocks:
        text = block['text']
        if not isinstance(text, str):
            continue
        match = club_pattern.search(text.upper())
        if match:
            return match.group(1).upper().replace("  ", " ").replace(" ", " ").title()
    return None

if __name__ == "__main__":
    image_path = "screenshots/sample3.png"
    processed = preprocess_image(image_path)
    ocr_blocks = extract_ocr_blocks(processed)
    structured_metrics, all_blocks = match_metrics(ocr_blocks)

    print("\n===== STRUCTURED METRICS =====\n")
    for key in structured_metrics:
        print(f"{key:>12}: {structured_metrics[key]}")

    print("\n===== CLUB INFO =====\n")
    club_name = extract_club_name(all_blocks)
    print(f"Clean Club Name: {club_name}")

    # Save to database
    try:
        insert_swing_data(
            club_type=club_name,
            club_speed=float(structured_metrics.get("CLUB SPEED", 0)),
            ball_speed=float(structured_metrics.get("BALL SPEED", 0)),
            spin_rate=float(structured_metrics.get("SPIN RATE", 0)),
            club_path=float(structured_metrics.get("CLUB PATH", 0)),
            face_angle=float(structured_metrics.get("FACE ANG", 0)),
            attack_angle=float(structured_metrics.get("ATTACK ANG", 0)),
            carry_distance=float(structured_metrics.get("CARRY", 0)),
            curve=structured_metrics.get("CURVE", ""),
            smash_factor=float(structured_metrics.get("SMASH FAC", 0)),
            apex=float(structured_metrics.get("HEIGHT", 0))
        )

        print("\n✅ Swing data successfully inserted into the database.")
    except Exception as e:
        print("\n❌ Failed to insert swing data:", e)