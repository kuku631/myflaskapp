import cv2
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import shutil

app = Flask(__name__)

# ----------------------------
# Folders
# ----------------------------
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "sr_frames"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ----------------------------
# Progress tracking dictionary
# ----------------------------
progress_dict = {}  # filename_no_ext -> progress %

# ----------------------------
# Routes
# ----------------------------
@app.route('/')
def home():
    return render_template('index.html')

# Serve SR frames including nested folders
@app.route('/sr_frames/<path:filename>')
def sr_frame(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

# Upload route
@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files[]')
    if not files:
        return jsonify({"status": "error", "message": "No files selected"})

    sr_urls = []

    for file in files:
        upload_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(upload_path)

        filename_no_ext, ext = os.path.splitext(file.filename)
        sr_folder = os.path.join(OUTPUT_FOLDER, filename_no_ext)
        os.makedirs(sr_folder, exist_ok=True)

        progress_dict[filename_no_ext] = 0  # initialize progress

        # If image
        if ext.lower() in ['.png', '.jpg', '.jpeg']:
            sr_path = os.path.join(sr_folder, file.filename)
            shutil.copy(upload_path, sr_path)
            sr_urls.append(f"/sr_frames/{filename_no_ext}/{file.filename}")
            progress_dict[filename_no_ext] = 100

        # If video
        else:
            cap = cv2.VideoCapture(upload_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

            for i in range(total_frames):
                ret, frame = cap.read()
                if not ret:
                    break

                sr_frame_name = f"frame_{i:04d}.png"
                sr_path = os.path.join(sr_folder, sr_frame_name)
                cv2.imwrite(sr_path, frame)

                # Update progress
                progress_percent = int(((i + 1) / total_frames) * 100)
                progress_dict[filename_no_ext] = progress_percent

                # Only save frame path for thumbnail preview
                if i == 0:
                    sr_urls.append(f"/sr_frames/{filename_no_ext}/{sr_frame_name}")

            cap.release()
            progress_dict[filename_no_ext] = 100  # complete

    return jsonify({"status": "success", "sr_urls": sr_urls})

# Progress route
@app.route('/progress/<filename>')
def progress(filename):
    percent = progress_dict.get(filename, 0)
    return jsonify({"progress": percent})

# ----------------------------
# Run Flask
# ----------------------------
if __name__ == "__main__":
    # host 0.0.0.0 = public access (for Render or Docker)
    # PORT env var = Render auto port, fallback 5000 for local run
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
