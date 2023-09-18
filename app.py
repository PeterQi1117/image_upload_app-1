from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash, jsonify
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = os.path.abspath('uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify(error="No file part"), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify(error="No selected file"), 400
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    return jsonify(success="File uploaded successfully")

@app.route('/view')
def view_files():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('view.html', files=files)

@app.route('/download/<filename>')
def download_file(filename):
    full_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
