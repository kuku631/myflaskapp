INDOWINGS ESRGAN - EST frontend
-------------------------------

How to run (static):
1) Option A (open directly): double-click index.html (some browsers block fetch for local files)
2) Option B (recommended): serve with Python static server:
   - Linux/Mac: run run_server.sh (make executable) or: python3 -m http.server 8080
   - Windows: run run_server.bat or: python -m http.server 8080
   Then open http://127.0.0.1:8080/index.html

Backend requirements (Flask):
- POST /upload          => handles files[] (multipart/form-data). returns JSON {status, task_id?, result_zip?}
- POST /extract_frames  => handles video (multipart/form-data). returns {status, frames_extracted? or task_id?}
- GET  /progress/<id>  => optional; returns {status: "running"|"done"|"error", progress: 0-100, result_zip?: "/downloads/res.zip"}
- GET  /frames_list    => optional; return list of frame URLs e.g. ["/sr_frames/frame_0001.jpg", ...]

CORS:
- If frontend served from a different origin than backend, enable CORS in Flask:
    from flask_cors import CORS
    CORS(app)

Packaging:
- Zip the folder: `zip -r frontend_est.zip frontend_est/` and send to QA
