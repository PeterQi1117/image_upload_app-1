from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash, jsonify
import os
from google.cloud import storage, firestore

app = Flask(__name__)
app.secret_key = "supersecretkey"

storage_client = storage.Client()
bucket_name = 'group-13-project-2'
bucket = storage_client.bucket(bucket_name)

db = firestore.Client()
files_metadata_collection = db.collection('files_metadata')

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
    
    # Save file to Google Cloud Storage
    blob = bucket.blob(file.filename)
    blob.content_disposition = "attachment; filename={}".format(file.filename)
    blob.upload_from_string(file.read(), content_type=file.content_type)
    blob.make_public()
    
    # Store metadata in Firestore
    metadata = {
        'filename': file.filename,
        'location': blob.public_url,
        'size': blob.size
    }
    files_metadata_collection.add(metadata)
    
    return jsonify(success="File uploaded successfully")

@app.route('/view')
def view_files():
    # Fetch metadata from Firestore
    files_metadata = files_metadata_collection.stream()
    files = [(doc.to_dict()['filename'], doc.to_dict()['location']) for doc in files_metadata]
    return render_template('view.html', files=files)

@app.route('/view/<filename>')
def view_file(filename):
    metadata = next(files_metadata_collection.where('filename', '==', filename).stream()).to_dict()
    return render_template('view-image.html', metadata=metadata)

@app.route('/download/<filename>')
def download_file(filename):
    # We will redirect to the direct GCS URL for the file
    blob = bucket.blob(filename)
    return redirect(blob.public_url)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
