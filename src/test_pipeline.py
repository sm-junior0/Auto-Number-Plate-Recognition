import cv2
import sys
import numpy as np
import temporal

def test_static_image(image_path):
    print(f"Testing image: {image_path}")
    frame = cv2.imread(image_path)
    if frame is None:
        print("Error: Could not read image.")
        sys.exit(1)

    candidates = temporal.find_plate_candidates(frame)
    if not candidates:
        print("No plate candidates found.")
        sys.exit(1)

    print(f"Found {len(candidates)} candidates.")
    rect = max(candidates, key=lambda r: r[1][0] * r[1][1])
    plate_img = temporal.warp_plate(frame, rect)
    
    cv2.imwrite("data/plates/test_aligned.jpg", plate_img)
    print("Saved aligned plate to data/plates/test_aligned.jpg")

    raw_text = temporal.read_plate_text(plate_img)
    print(f"Raw OCR Text: {raw_text}")

    valid_plate = temporal.extract_valid_plate(raw_text)
    if valid_plate:
        print(f"Valid Plate Found: {valid_plate}")
    else:
        print("No valid plate format detected.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_static_image(sys.argv[1])
    else:
        print("Usage: python test_pipeline.py <image_path>")
