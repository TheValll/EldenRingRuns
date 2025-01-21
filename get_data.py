import os
import json
import io
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv

load_dotenv()

SCOPES = [os.getenv('SCOPES')]

def authenticate():
    """Authentifie l'utilisateur et retourne le service Google Drive."""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": os.getenv('CLIENT_ID'),
                        "project_id": os.getenv('PROJECT_ID'),
                        "auth_uri": os.getenv('AUTH_URI'),
                        "token_uri": os.getenv('TOKEN_URI'),
                        "auth_provider_x509_cert_url": os.getenv('AUTH_PROVIDER_X509_CERT_URL'),
                        "client_secret": os.getenv('CLIENT_SECRET'),
                        "redirect_uris": [os.getenv('REDIRECT_URIS')]
                    }
                },
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

def download_file_and_load_json(service, file_name):
    query = f"name='{file_name}'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])

    if not files:
        print(f"Aucun fichier trouvé avec le nom : {file_name}")
        return None
    
    file_id = files[0]['id']
    request = service.files().get_media(fileId=file_id)
    
    file_data = io.BytesIO()
    downloader = MediaIoBaseDownload(file_data, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Téléchargement {int(status.progress() * 100)}%.")
    
    file_data.seek(0)
    data = json.load(file_data)
    return data


def get_data_file():
    service = authenticate()
    json_data = download_file_and_load_json(service, "splits.json")
    return json_data