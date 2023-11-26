from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    redirect,
    session,
    url_for,
    flash,
    jsonify,
)
import os
from google.cloud import storage, firestore
from pyparsing import wraps
import pyrebase

# Firebase configuration
config = {
    "apiKey": "AIzaSyAE-naRVVTgwIMWsLgyPCWPhvMvsPuOfHU",
    "authDomain": "neat-planet-171823.firebaseapp.com",
    "projectId": "neat-planet-171823",
    "storageBucket": "neat-planet-171823.appspot.com",
    "messagingSenderId": "478630268567",
    "appId": "1:478630268567:web:af341152852119878623d2",
    "measurementId": "G-VWJ8XRNWNN",
    "databaseURL": "https://databaseName.firebaseio.com",
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()

app = Flask(__name__)
app.secret_key = "supersecretkey"

def user_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)

    return wrap


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = auth.sign_in_with_email_and_password(email, password)
        session["user"] = user
        return redirect(request.args.get("next") or "/")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        auth.create_user_with_email_and_password(email, password)
        return redirect("/login")
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

storage_client = storage.Client()
bucket_name = "group-13-project-2"
bucket = storage_client.bucket(bucket_name)

db = firestore.Client()
files_metadata_collection = db.collection("files_metadata")


@app.route("/")
@user_required
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
@user_required
def upload_file():
    if "file" not in request.files:
        return jsonify(error="No file part"), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify(error="No selected file"), 400

    # Save file to Google Cloud Storage
    blob = bucket.blob(file.filename)
    blob.content_disposition = "attachment; filename={}".format(file.filename)
    blob.upload_from_string(file.read(), content_type=file.content_type)
    blob.make_public()

    # Store metadata in Firestore
    metadata = {
        "filename": file.filename,
        "location": blob.public_url,
        "size": blob.size,
    }
    files_metadata_collection.add(metadata)

    return jsonify(success="File uploaded successfully")


@app.route("/view")
@user_required
def view_files():
    # Fetch metadata from Firestore
    files_metadata = files_metadata_collection.stream()
    files = [
        (doc.to_dict()["filename"], doc.to_dict()["location"]) for doc in files_metadata
    ]
    return render_template("view.html", files=files)


@app.route("/view/<filename>")
@user_required
def view_file(filename):
    metadata = next(
        files_metadata_collection.where("filename", "==", filename).stream()
    ).to_dict()
    return render_template("view-image.html", metadata=metadata)


@app.route("/download/<filename>")
@user_required
def download_file(filename):
    # We will redirect to the direct GCS URL for the file
    blob = bucket.blob(filename)
    return redirect(blob.public_url)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
