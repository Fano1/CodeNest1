from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for, session, Response
from werkzeug.utils import secure_filename
import sqlite3
import os
import cv2
from AIshit.genAi import ProtocolGenerateContent

app = Flask(__name__)
app.secret_key = 'something_secure'

# Folder setup
PERM_UPLOAD_FOLDER = 'uploads'
app.config['PERM_UPLOAD_FOLDER'] = PERM_UPLOAD_FOLDER
os.makedirs(PERM_UPLOAD_FOLDER, exist_ok=True)

TEMP_UPLOAD_FOLDER = 'temp_uploads'
app.config['TEMP_UPLOAD_FOLDER'] = TEMP_UPLOAD_FOLDER
os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)

camera = cv2.VideoCapture(0)

def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Get frame dimensions
            height, width, _ = frame.shape
            center_x, center_y = width // 2, height // 2

            # Draw a blue circle in the center
            cv2.circle(frame, (center_x, center_y), 40, (255, 0, 0), 4)  # BGR color

            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Yield frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Database init
def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS pins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL,
            lng REAL,
            review TEXT,
            rating REAL,
            image TEXT
        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pin_id INTEGER,
            username TEXT,
            message TEXT,
            FOREIGN KEY (pin_id) REFERENCES pins(id)
        )''')

#main Routes
@app.route('/')
def main():
    return render_template("main.html")

@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/maps')
def maps():
    return render_template("maps.html")

@app.route('/ai', methods=['GET', 'POST'])
def ai():
    output_text = None
    image_url = None

    if request.method == 'POST':
        user_text = request.form.get('user_text')
        image_file = request.files.get('image_file')

        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['TEMP_UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image_url = f"/temp_uploads/{filename}"

            content = (
                "Your name is Tanya. You are a female Foodie. You are quick, witty , loves to crack jokes and give advise."
                "Tell me the possible allergent in the following food and a general overview "
                "on what should I eat with it or after it to maintain a balanced diet. Also some good "
                "advice on what might pair best with the given food and other small tips. "
                "IMPORTANTLY: Make it short sweet and understandable in paragraph format and no **. "
                f"additional info {user_text}"
            )

            cam = ProtocolGenerateContent(cnt=content, path=image_path)
            res = cam.InputImage()
            # Save to session or temp var to flash it during GET
            session['output_text'] = res
            session['image_url'] = image_url

        return redirect(url_for('ai'))  # This triggers a fresh GET

    # Handle the redirected GET
    output_text = session.pop('output_text', None)
    image_url = session.pop('image_url', None)

    return render_template('ai.html', output_text=output_text, image_url=image_url)
    
@app.route('/video')
def video():
    return render_template('video.html')


#additional functions
@app.route('/maps/add_pin', methods=['POST'])
def add_pin():
    lat = float(request.form['lat'])
    lng = float(request.form['lng'])
    review = request.form['review']
    rating = request.form['rating']
    file = request.files.get('image')
    filename = ""

    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['PERM_UPLOAD_FOLDER'], filename))

    with sqlite3.connect("database.db") as conn:
        conn.execute("INSERT INTO pins (lat, lng, review, image, rating) VALUES (?, ?, ?, ?, ?)",
                     (lat, lng, review, filename, rating))

    return jsonify({"status": "success"})

# Get pins
@app.route('/maps/get_pins')
def get_pins():
    with sqlite3.connect("database.db") as conn:
        pins = conn.execute("SELECT lat, lng, review, rating, image FROM pins").fetchall()
    return jsonify(pins)

@app.route('/maps/add_reply', methods=['POST'])
def add_reply():
    pin_id = request.form['pin_id']
    username = request.form['username']
    message = request.form['message']

    with sqlite3.connect("database.db") as conn:
        conn.execute(
            "INSERT INTO replies (pin_id, username, message) VALUES (?, ?, ?)",
            (pin_id, username, message)
        )

    return jsonify({"status": "success"})

@app.route('/maps/get_replies/<int:pin_id>')
def get_replies(pin_id):
    with sqlite3.connect("database.db") as conn:
        replies = conn.execute(
            "SELECT username, message FROM replies WHERE pin_id = ?",
            (pin_id,)
        ).fetchall()

    return jsonify(replies)

# Serve uploaded images
@app.route('/temp_uploads/<filename>')
def temp_uploaded_file(filename):
    return send_from_directory(app.config['TEMP_UPLOAD_FOLDER'], filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['PERM_UPLOAD_FOLDER'], filename)


@app.route('/video/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
