import cv2
import numpy as np
import pytesseract
import re
import argparse
import time

MIN_AREA = 600
AR_MIN, AR_MAX = 2.0, 8.0
W_OUT, H_OUT = 450, 140

PLATE_RE = re.compile(r'[A-Z]{3}[0-9]{3}[A-Z]')
ALNUM_RE = re.compile(r'[A-Z0-9]')


def find_plate_candidates(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 100, 200)

    contours, _ = cv2.findContours(
        edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    candidates = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < MIN_AREA:
            continue

        rect = cv2.minAreaRect(cnt)
        (_, _), (w, h), _ = rect
        if w <= 0 or h <= 0:
            continue

        ar = max(w, h) / max(1.0, min(w, h))
        if AR_MIN <= ar <= AR_MAX:
            candidates.append(rect)

    return candidates


def order_points(pts):
    pts = np.array(pts, dtype=np.float32)

    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    top_left = pts[np.argmin(s)]
    bottom_right = pts[np.argmax(s)]
    top_right = pts[np.argmin(diff)]
    bottom_left = pts[np.argmax(diff)]

    return np.array(
        [top_left, top_right, bottom_right, bottom_left],
        dtype=np.float32
    )


def warp_plate(frame, rect):
    box = cv2.boxPoints(rect)
    src = order_points(box)

    dst = np.array([
        [0, 0],
        [W_OUT - 1, 0],
        [W_OUT - 1, H_OUT - 1],
        [0, H_OUT - 1]
    ], dtype=np.float32)

    M = cv2.getPerspectiveTransform(src, dst)

    warped = cv2.warpPerspective(frame, M, (W_OUT, H_OUT))

    return warped


def read_plate_text(plate_img):
    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    thresh = cv2.threshold(
        blur,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    text = pytesseract.image_to_string(
        thresh,
        config='--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    )

    return text.strip().replace(" ", ""), thresh


def extract_valid_plate(text):
    text = text.upper().replace(" ", "")

    m = PLATE_RE.search(text)

    if m:
        return m.group(0)

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--image",
        dest="image_path",
        help="Run validation on a single image path instead of the webcam"
    )
    parser.add_argument(
        "--roi",
        action="store_true",
        help="Drag to select a region of interest (ROI) to search for the plate"
    )
    args = parser.parse_args()

    cap = None
    single_frame = None
    if args.image_path:
        single_frame = cv2.imread(args.image_path)
        if single_frame is None:
            raise FileNotFoundError(f"Could not read image: {args.image_path}")
    else:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Camera not opened")

    roi_rect = None
    if args.roi and single_frame is not None:
        # Select ROI once for single-image mode.
        r = cv2.selectROI("Select ROI", single_frame, fromCenter=False, showCrosshair=True)
        cv2.destroyWindow("Select ROI")
        x, y, w, h = [int(v) for v in r]
        if w > 0 and h > 0:
            roi_rect = (x, y, w, h)

    while True:
        if single_frame is not None:
            frame = single_frame.copy()
            ok = True
        else:
            ok, frame = cap.read()

        if not ok:
            break

        if args.roi and roi_rect is None:
            # Select ROI once for webcam mode (first valid frame).
            r = cv2.selectROI("Select ROI", frame, fromCenter=False, showCrosshair=True)
            cv2.destroyWindow("Select ROI")
            x, y, w, h = [int(v) for v in r]
            if w > 0 and h > 0:
                roi_rect = (x, y, w, h)

        vis = frame.copy()

        offset_x, offset_y = 0, 0
        proc_frame = frame
        if roi_rect is not None:
            rx, ry, rw, rh = roi_rect
            offset_x, offset_y = rx, ry
            proc_frame = frame[ry : ry + rh, rx : rx + rw]
            cv2.rectangle(vis, (rx, ry), (rx + rw, ry + rh), (255, 0, 0), 2)

        candidates = find_plate_candidates(proc_frame)

        msg = "Searching for plate..."
        color = (0, 200, 255)

        plate_img = None
        thresh = None

        if not hasattr(main, "_last_ocr_time"):
            main._last_ocr_time = 0.0
            main._last_best = None

        now = time.time()
        run_ocr = (now - main._last_ocr_time) >= 0.35

        if candidates:
            best = None
            best_score = None

            if run_ocr:
                candidates_sorted = sorted(
                    candidates,
                    key=lambda r: r[1][0] * r[1][1],
                    reverse=True
                )[:6]

                for rect in candidates_sorted:
                    candidate_plate = warp_plate(proc_frame, rect)
                    candidate_text, candidate_thresh = read_plate_text(candidate_plate)
                    candidate_valid = extract_valid_plate(candidate_text)

                    cleaned = candidate_text.upper().replace(" ", "").replace("-", "")
                    alnum_count = len(ALNUM_RE.findall(cleaned))
                    score = (1 if candidate_valid else 0, alnum_count)

                    if best is None or score > best_score:
                        best = (rect, candidate_plate, candidate_text, candidate_thresh, candidate_valid)
                        best_score = score

                main._last_best = best
                main._last_ocr_time = now
            else:
                best = main._last_best

            if best is not None:
                rect, plate_img, raw_text, thresh, valid_plate = best
            else:
                rect = None

            if rect is not None:
                box = cv2.boxPoints(rect).astype(int)
                if roi_rect is not None:
                    box[:, 0] += offset_x
                    box[:, 1] += offset_y

                cv2.polylines(vis, [box], True, (0, 255, 0), 2)

                msg = "Validating OCR"
                color = (0, 255, 0)

                x = int(np.max(box[:, 0])) - 300
                y = int(np.max(box[:, 1])) + 25

                x = min(x, vis.shape[1] - 200)
                y = min(y, vis.shape[0] - 10)

                if valid_plate:
                    cv2.putText(
                        vis,
                        f"VALID: {valid_plate}",
                        (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2
                    )
                else:
                    if raw_text:
                        cv2.putText(
                            vis,
                            f"OCR: {raw_text}",
                            (x, y),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 165, 255),
                            2
                        )

        cv2.putText(
            vis,
            msg,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            color,
            2
        )

        cv2.putText(
            vis,
            "Press q to quit",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.imshow("Validation Stage", vis)

        if plate_img is not None:
            cv2.imshow("Aligned Plate", plate_img)

        if thresh is not None:
            cv2.imshow("Thresholded Plate", thresh)

        if single_frame is not None:
            cv2.waitKey(0)
            break

        if (cv2.waitKey(1) & 0xFF) == ord('q'):
            break

    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
