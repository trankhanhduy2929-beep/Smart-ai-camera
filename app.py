import cv2
import json
import time
import threading
import os
import sqlite3
import datetime
import numpy as np
import paho.mqtt.client as mqtt
from flask import Flask, render_template, request, jsonify, send_from_directory

# --- CẤU HÌNH ---
DB_PATH = '/data/db/smartcam.db'
FACE_DIR = '/share/camera_faces' # Đổi sang /share để dễ lấy file nếu cần
CONFIG_PATH = '/data/options.json'

# Tạo thư mục nếu chưa có
if not os.path.exists(FACE_DIR):
    os.makedirs(FACE_DIR)
if not os.path.exists('/data/db'):
    os.makedirs('/data/db')

# --- FLASK APP ---
app = Flask(__name__, template_folder='/templates', static_folder='/static')

# --- MQTT SETUP ---
try:
    with open(CONFIG_PATH) as f:
        config = json.load(f)
except:
    config = {}

mqtt_client = mqtt.Client()
if config.get('mqtt_user'):
    mqtt_client.username_pw_set(config['mqtt_user'], config['mqtt_password'])

def connect_mqtt():
    try:
        mqtt_client.connect(config.get('mqtt_host', 'core-mosquitto'), config.get('mqtt_port', 1883), 60)
        mqtt_client.loop_start()
        print("MQTT Connected")
    except Exception as e:
        print(f"MQTT Error: {e}")

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cameras 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, rtsp_url TEXT, active INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS faces 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, cam_name TEXT, filename TEXT, timestamp DATETIME)''')
    conn.commit()
    conn.close()

# --- GLOBAL VARS ---
active_threads = {}
stop_events = {}
face_cascade = cv2.CascadeClassifier('/haarcascade_frontalface_default.xml')

# --- CAMERA LOGIC ---
def camera_worker(cam_id, cam_name, rtsp_url, stop_event):
    print(f"Starting worker for {cam_name}")
    sanitized_name = cam_name.lower().replace(" ", "_")
    topic_state = f"smartcam/{sanitized_name}/last_face"
    
    # Payload discovery cho HA
    discovery_payload = {
        "name": f"{cam_name} Last Face",
        "unique_id": f"smartcam_face_{cam_id}",
        "state_topic": topic_state,
        "json_attributes_topic": topic_state, 
        "icon": "mdi:face-recognition",
        "platform": "mqtt"
    }
    mqtt_client.publish(f"homeassistant/sensor/{sanitized_name}_face/config", json.dumps(discovery_payload), retain=True)

    cap = cv2.VideoCapture(rtsp_url)
    fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)
    
    last_motion = 0
    
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            time.sleep(5)
            # Reconnect logic
            cap.release()
            cap = cv2.VideoCapture(rtsp_url)
            continue
            
        small = cv2.resize(frame, (640, 360))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        fgmask = fgbg.apply(small)
        motion_level = np.count_nonzero(fgmask)
        
        # Ngưỡng motion
        if motion_level > 5000:
            current_time = time.time()
            if current_time - last_motion > 3.0: # Cooldown 3s
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                for (x, y, w, h) in faces:
                    # Crop & Save
                    face_img = small[y:y+h, x:x+w]
                    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{sanitized_name}_{timestamp_str}.jpg"
                    filepath = os.path.join(FACE_DIR, filename)
                    
                    cv2.imwrite(filepath, face_img)
                    
                    # DB Insert
                    try:
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute("INSERT INTO faces (cam_name, filename, timestamp) VALUES (?, ?, ?)", 
                                  (cam_name, filename, datetime.datetime.now()))
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        print(f"DB Error: {e}")
                        
                    # MQTT Publish
                    payload = {
                        "value": timestamp_str,
                        "filename": filename,
                        "cam_name": cam_name
                    }
                    mqtt_client.publish(topic_state, json.dumps(payload))
                    
                    last_motion = current_time
                    break 
                    
        time.sleep(0.05)
    
    cap.release()
    print(f"Stopped worker for {cam_name}")

def refresh_camera_threads():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, name, rtsp_url, active FROM cameras")
        rows = c.fetchall()
        conn.close()
        
        current_db_ids = [r[0] for r in rows]

        # Stop deleted cameras
        for t_id in list(active_threads.keys()):
            if t_id not in current_db_ids:
                stop_events[t_id].set()
                active_threads[t_id].join()
                del active_threads[t_id]
                del stop_events[t_id]
        
        # Start new cameras
        for row in rows:
            c_id, name, url, active = row
            if active and c_id not in active_threads:
                stop_event = threading.Event()
                t = threading.Thread(target=camera_worker, args=(c_id, name, url, stop_event))
                t.daemon = True
                t.start()
                active_threads[c_id] = t
                stop_events[c_id] = stop_event
    except Exception as e:
        print(f"Refresh Thread Error: {e}")

# --- FLASK ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cameras', methods=['GET', 'POST', 'DELETE'])
def handle_cameras():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    if request.method == 'GET':
        c.execute("SELECT * FROM cameras")
        rows = c.fetchall()
        conn.close()
        return jsonify(rows)
    
    elif request.method == 'POST':
        try:
            data = request.json
            if not data or 'name' not in data or 'url' not in data:
                return jsonify({"error": "Thieu du lieu"}), 400
                
            c.execute("INSERT INTO cameras (name, rtsp_url, active) VALUES (?, ?, 1)", (data['name'], data['url']))
            conn.commit()
            conn.close()
            
            # Refresh threads
            refresh_camera_threads()
            return jsonify({"status": "ok", "message": "Da them camera"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    elif request.method == 'DELETE':
        cam_id = request.args.get('id')
        c.execute("DELETE FROM cameras WHERE id=?", (cam_id,))
        conn.commit()
        conn.close()
        refresh_camera_threads()
        return jsonify({"status": "ok"})

@app.route('/api/faces')
def get_faces():
    date_filter = request.args.get('date')
    cam_filter = request.args.get('cam')
    
    query = "SELECT * FROM faces WHERE 1=1"
    params = []
    
    if date_filter:
        query += " AND date(timestamp) = ?"
        params.append(date_filter)
    if cam_filter:
        query += " AND cam_name = ?"
        params.append(cam_filter)
        
    query += " ORDER BY timestamp DESC LIMIT 50"
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

@app.route('/faces/<filename>')
def serve_face(filename):
    return send_from_directory(FACE_DIR, filename)

if __name__ == '__main__':
    init_db()
    connect_mqtt()
    refresh_camera_threads()
    app.run(host='0.0.0.0', port=2929)