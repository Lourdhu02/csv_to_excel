from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import pandas as pd
import os
import io
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')  # Replace this with env var in production
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create the upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if 'csv_file' not in request.files:
            flash("No file part in the request")
            return redirect(request.url)

        file = request.files['csv_file']
        if file.filename == "":
            flash("No file selected")
            return redirect(request.url)

        if file and file.filename.lower().endswith(".csv"):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            try:
                df = pd.read_csv(file_path)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Sheet1")
                output.seek(0)
                os.remove(file_path)

                return send_file(
                    output,
                    download_name="converted.xlsx",
                    as_attachment=True,
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                logger.error(f"Error during conversion: {e}")
                flash("There was an error processing your file.")
                return redirect(url_for("index"))
        else:
            flash("Invalid file type. Please upload a CSV file.")
            return redirect(request.url)

    return render_template("index.html")

# Only for local development; use waitress/gunicorn in production
if __name__ == "__main__":
    from waitress import serve
