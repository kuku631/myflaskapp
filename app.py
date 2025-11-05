import os
import cv2
import shutil
import subprocess
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)

# ----------------------------
# Folder Configuration
# ----------------------------
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "sr_frames"
WINDOWS_OUTPUT_PATH = r"C:\INDOWINGS_OUTPUT"  # ✅ Visible to user

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(WINDOWS_OUTPUT_PATH, exist_ok=True)

# ----------------------------
# Progress Tracker
# ----------------------------
progress_dict = {}  # filename_no_ext -> progress %

# ----------------------------
# Routes
# ----------------------------
@app.route('/')
def home():
    """Render the frontend UI"""
    return render_template('index.html')

@app.route('/sr_frames/<path:filename>')
def sr_frame(filename):
    """Serve processed output frames"""
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/upload', methods=['POST'])
def upload():
    """Handle file uploads and start processing"""
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

        progress_dict[filename_no_ext] = 0  # Initialize progress

        # ----------------------------
        # IMAGE PROCESSING
        # ----------------------------
        if ext.lower() in ['.png', '.jpg', '.jpeg']:
            sr_path = os.path.join(sr_folder, file.filename)
            shutil.copy(upload_path, sr_path)

            # Copy to Windows visible folder
            shutil.copy(upload_path, os.path.join(WINDOWS_OUTPUT_PATH, file.filename))

            sr_urls.append(f"/sr_frames/{filename_no_ext}/{file.filename}")
            progress_dict[filename_no_ext] = 100

        # ----------------------------
        # VIDEO PROCESSING
        # ----------------------------
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

                # Update progress percentage
                progress_percent = int(((i + 1) / total_frames) * 100)
                progress_dict[filename_no_ext] = progress_percent

                # Save first frame for preview in frontend
                if i == 0:
                    sr_urls.append(f"/sr_frames/{filename_no_ext}/{sr_frame_name}")

            cap.release()
            progress_dict[filename_no_ext] = 100

            # Copy output folder to Windows directory
            dest_folder = os.path.join(WINDOWS_OUTPUT_PATH, filename_no_ext)
            if os.path.exists(dest_folder):
                shutil.rmtree(dest_folder)
            shutil.copytree(sr_folder, dest_folder)

    return jsonify({
        "status": "success",
        "sr_urls": sr_urls,
        "output_path": WINDOWS_OUTPUT_PATH
    })

@app.route('/progress/<filename>')
def progress(filename):
    """Return current processing progress"""
    percent = progress_dict.get(filename, 0)
    return jsonify({"progress": percent})

@app.route('/open-output-folder', methods=['GET'])
def open_output_folder():
    """Open output folder on Windows Explorer"""
    if os.name == 'nt':  # Works only on Windows
        subprocess.Popen(f'explorer "{WINDOWS_OUTPUT_PATH}"')
    return jsonify({"status": "opened", "path": WINDOWS_OUTPUT_PATH})

# ----------------------------
# Run the Flask App
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
