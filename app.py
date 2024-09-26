from flask import Flask, request, jsonify
import os
import uuid
import whisper
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

# Configuration
# UPLOAD_FOLDER = ''
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Azure Blob Storage Configuration
AZURE_CONNECTION_STRING = ''
CONTAINER_NAME = 'whisperaudio'

blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

def download_from_blob(blob_name, local_path):
    # Get the blob client
    blob_client = container_client.get_blob_client(blob=blob_name)
    
    # Download the blob to a local file
    download_file_path = os.path.join(local_path, blob_name)
    with open(download_file_path, "wb") as download_file:
        download_file.write(blob_client.download_blob().readall())
    
    return os.path.abspath(download_file_path)  # Full path of the downloaded file

# Define the path where files will be saved locally
local_upload_folder = "downloads"
os.makedirs(local_upload_folder, exist_ok=True)  # Create the folder if it doesn't exist

# Example usage in Flask API
@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio_file part in the request'}), 400

    file = request.files['audio_file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    unique_filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]

    try:
        print("req rec")
        # Upload the file to Azure Blob Storage
        blob_client = container_client.get_blob_client(unique_filename)
        blob_client.upload_blob(file)

        # Download the file back from Azure Blob Storage
        downloaded_file_path = download_from_blob(unique_filename, local_upload_folder)
        print(downloaded_file_path)

        # Use Whisper to transcribe the downloaded audio file
        model = whisper.load_model("tiny")
        print("loaded")
        result = model.transcribe(r"C:\Users\Harsh Dhariwal\Desktop\drug-discovery\downloads\fa8b5dfc-5959-42e1-8479-a521a391cd67.wav")
        print("transcribed")
        transcription = result['text']

        return jsonify({'transcription': transcription}), 200

    except Exception as e:
        return jsonify({'error': 'Transcription failed', 'details': str(e)}), 500

    