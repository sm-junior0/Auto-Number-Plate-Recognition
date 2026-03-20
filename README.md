# 🚗 ANPR — Automatic Number Plate Recognition

A real-time **Automatic Number Plate Recognition** system built from scratch using **OpenCV** and **Tesseract OCR**. The project processes a live webcam feed to detect, align, read, and validate vehicle license plates, logging confirmed results to a CSV file with timestamps.

![Temporal Validation Demo](screenshots/Screenshot%20From%202026-03-20%2021-31-52.png)

---

## ✨ Features

- **Real-time detection** — Identifies license plate candidates from a live camera feed using edge detection and contour analysis.
- **Perspective correction** — Warps detected plate regions into a clean, axis-aligned rectangle for reliable OCR.
- **OCR with Tesseract** — Extracts alphanumeric characters from pre-processed plate images.
- **Regex validation** — Matches OCR output against the `AAA000A` plate format (e.g. `RAA782E`).
- **Temporal majority voting** — Buffers multiple reads over consecutive frames and uses a majority-vote strategy to confirm the final plate string, reducing false positives.
- **Cooldown-based CSV logging** — Saves confirmed plates with timestamps to `data/logs/plates_log.csv`, with a configurable cooldown to prevent duplicate entries.
- **Static image mode** — `validate.py` supports `--image` and `--roi` flags for single-image analysis and region-of-interest selection.
- **Dummy plate generator** — `create_dummy_plate.py` creates a synthetic test image for pipeline validation without a physical plate.

---

## 📂 Project Structure

```
anpr-main/
├── data/
│   └── logs/
│       └── plates_log.csv        # Auto-generated CSV log of confirmed plates
├── screenshots/                  # Demo screenshots
├── src/
│   ├── camera.py                 # Step 1 — Webcam feed test
│   ├── detect.py                 # Step 2 — Contour-based plate detection
│   ├── align.py                  # Step 3 — Perspective warp / alignment
│   ├── ocr.py                    # Step 4 — Tesseract OCR extraction
│   ├── validate.py               # Step 5 — Regex validation + ROI support
│   ├── temporal.py               # Step 6 — Full pipeline with temporal voting & CSV logging
│   ├── test_pipeline.py          # Static image test harness
│   └── create_dummy_plate.py     # Synthetic plate image generator
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🛠️ Prerequisites

| Dependency | Purpose |
|---|---|
| **Python 3.10+** | Runtime |
| **Tesseract OCR** | External OCR engine (must be installed separately) |
| **Webcam** | Required for real-time modules (`camera.py`, `detect.py`, etc.) |

### Installing Tesseract OCR

<details>
<summary><strong>Windows</strong></summary>

1. Download the installer from the [UB-Mannheim Tesseract builds](https://github.com/UB-Mannheim/tesseract/wiki).
2. Run the installer (default path: `C:\Program Files\Tesseract-OCR`).
3. Add the install directory to your **system PATH**:
   - *Settings → System → About → Advanced system settings → Environment Variables*
   - Edit the `Path` variable and add `C:\Program Files\Tesseract-OCR`
4. Restart your terminal and verify:
   ```bash
   tesseract --version
   ```

</details>

<details>
<summary><strong>Ubuntu / Debian</strong></summary>

```bash
sudo apt update
sudo apt install tesseract-ocr -y
```

</details>

<details>
<summary><strong>macOS</strong></summary>

```bash
brew install tesseract
```

</details>

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/anpr.git
cd anpr
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

| OS | Command |
|---|---|
| **Windows (PowerShell)** | `.\venv\Scripts\Activate.ps1` |
| **Windows (CMD)** | `.\venv\Scripts\activate.bat` |
| **Linux / macOS** | `source venv/bin/activate` |

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Tesseract

```bash
tesseract --version
```

If this prints a version number, you're ready to go.

---

## 📖 Usage Guide

The modules are designed to be run **sequentially**, each one building on the concepts of the previous. This makes it easy to understand and debug each stage of the pipeline independently.

### Step 1 — Test Camera

Opens a live webcam feed to confirm your camera is working.

```bash
python src/camera.py
```

### Step 2 — Detect Plates

Runs edge detection + contour filtering to identify rectangular plate-like regions and draws green bounding boxes around candidates.

```bash
python src/detect.py
```

### Step 3 — Align Plates

Adds perspective warping so detected plates are transformed into a flat, axis-aligned rectangle for cleaner OCR.

```bash
python src/align.py
```

### Step 4 — Extract Text (OCR)

Applies Otsu thresholding and runs Tesseract OCR on the aligned plate image. The raw extracted text is overlaid on the video feed.

```bash
python src/ocr.py
```

### Step 5 — Validate OCR Output

Validates the OCR output against the `AAA000A` regex pattern. Supports optional flags:

```bash
# Live webcam mode
python src/validate.py

# Single image mode
python src/validate.py --image path/to/image.jpg

# With region-of-interest selection
python src/validate.py --image path/to/image.jpg --roi
```

### Step 6 — Full Pipeline (Temporal Voting + Logging)

The complete system: detects → aligns → reads → validates → confirms via majority vote → logs to CSV.

```bash
python src/temporal.py
```

Confirmed plates are saved to `data/logs/plates_log.csv` in the format:

| Plate Number | Timestamp |
|---|---|
| RAA782E | 2026-03-20 21:31:52 |

> **Press `q`** to exit any graphical window.

---

## 🧪 Testing

### Static Image Test

Use `test_pipeline.py` to run the full detection → alignment → OCR → validation pipeline on a single image:

```bash
cd src
python test_pipeline.py path/to/car_image.jpg
```

### Generate a Dummy Plate

Create a synthetic test image with the text `ABC 123 D` embedded on a grey background:

```bash
python src/create_dummy_plate.py
```

The generated image is saved to `data/plates/dummy_plate.jpg`.

---

## ⚙️ Configuration

Key constants can be adjusted at the top of each source file:

| Constant | Default | Description |
|---|---|---|
| `MIN_AREA` | `600` | Minimum contour area to qualify as a plate candidate |
| `AR_MIN` / `AR_MAX` | `2.0` / `8.0` | Aspect ratio range for plate-shaped rectangles |
| `W_OUT` / `H_OUT` | `450` / `140` | Output dimensions for the warped plate image |
| `BUFFER_SIZE` | `5` | Number of frames used for temporal majority voting |
| `COOLDOWN` | `10` | Seconds before the same plate can be logged again |
| `PLATE_RE` | `[A-Z]{3}[0-9]{3}[A-Z]` | Regex pattern for valid plate format |

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| `TesseractNotFoundError` | Install Tesseract OCR and add it to your system PATH (see [Prerequisites](#-prerequisites)) |
| `Camera not opened` | Ensure a webcam is connected and not in use by another application |
| No plates detected | Adjust `MIN_AREA`, lighting conditions, or try `--roi` to narrow the search area |
| OCR returns garbage | Ensure the plate is well-lit and within ~1 metre of the camera |

---

## 📄 License

This project is available for educational and personal use.

---

## 🙏 Acknowledgements

- [OpenCV](https://opencv.org/) — Computer vision library
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) — Open-source OCR engine
- [pytesseract](https://pypi.org/project/pytesseract/) — Python wrapper for Tesseract
