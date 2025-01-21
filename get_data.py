import os
import json
import io
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv
import streamlit as st

load_dotenv()
st.secrets(f"CLIENT_ID: {os.getenv('CLIENT_ID')}")
st.secrets(f"PROJECT_ID: {os.getenv('PROJECT_ID')}")
st.secrets(f"SCOPES: {os.getenv('SCOPES')}")

SCOPES = [os.getenv('SCOPES')]

def authenticate():
    """Authentifie l'utilisateur et retourne le service Google Drive."""
    creds = None
    try:
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
    except Exception as e:
        print(f"Erreur d'authentification : {e}")
        return None


def download_file_and_load_json(service, file_name):
    """Télécharge un fichier depuis Google Drive et charge son contenu JSON."""
    try:
        query = f"name='{file_name}'"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        if not files:
            raise FileNotFoundError(f"Aucun fichier trouvé avec le nom : {file_name}")
        
        file_id = files[0]['id']
        request = service.files().get_media(fileId=file_id)
        
        file_data = io.BytesIO()
        downloader = MediaIoBaseDownload(file_data, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Téléchargement {int(status.progress() * 100)}%.")
        
        file_data.seek(0)
        data = json.load(file_data)
        return data

    except FileNotFoundError as e:
        print(f"Erreur : {e}")
        return None
    except Exception as e:
        print(f"Erreur lors du téléchargement ou du chargement du fichier : {e}")
        return None


def get_data_file():
    """Obtient le fichier de données à partir de Google Drive."""
    service = authenticate()
    if service is None:
        return {"error": "Échec de l'authentification"}
    
    json_data = download_file_and_load_json(service, "splits.json")
    if json_data is None:
        return {"error": "Échec du téléchargement ou du chargement du fichier JSON"}
    
    return json_data
