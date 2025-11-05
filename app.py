import cv2
import os
import shutil
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)

UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/sr_frames"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

progress_dict = {}

def process_video(filename_no_ext, upload_path, sr_folder):
    """Runs in background thread to extract frames."""
    try:
        cap = cv2.VideoCapture(upload_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

        for i in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                break

            sr_frame_name = f"frame_{i:04d}.png"
            sr_path = os.path.join(sr_folder, sr_frame_name)
            cv2.imwrite(sr_path, frame)

            progress_dict[filename_no_ext] = int(((i + 1) / total_frames) * 100)

        cap.release()
        progress_dict[filename_no_ext] = 100
    except Exception as e:
        progress_dict[filename_no_ext] = -1
        print(f"❌ Error processing video {filename_no_ext}: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/sr_frames/<path:filename>')
def sr_frame(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/upload', methods=['POST'])
def upload():
    try:
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
            progress_dict[filename_no_ext] = 0

            # Image case
            if ext.lower() in ['.png', '.jpg', '.jpeg']:
                sr_path = os.path.join(sr_folder, file.filename)
                shutil.copy(upload_path, sr_path)
                sr_urls.append(f"/sr_frames/{filename_no_ext}/{file.filename}")
                progress_dict[filename_no_ext] = 100
            else:
                # Video case -> background thread
                thread = threading.Thread(target=process_video, args=(filename_no_ext, upload_path, sr_folder))
                thread.daemon = True
                thread.start()
                sr_urls.append(f"/sr_frames/{filename_no_ext}/frame_0000.png")

        return jsonify({
            "status": "success",
            "sr_urls": sr_urls
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/progress/<filename>')
def progress(filename):
    percent = progress_dict.get(filename, 0)
    return jsonify({"progress": percent})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
