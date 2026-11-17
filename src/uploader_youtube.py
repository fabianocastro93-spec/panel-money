import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service(client_secrets_file: str = "client_secrets.json"):
    """Autentica na API do YouTube usando OAuth 2.0 e salva o token para reuso."""
    creds = None
    token_file = "token.pickle"
    
    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secrets_file):
                raise FileNotFoundError(
                    f"Arquivo '{client_secrets_file}' não encontrado! "
                    "Baixe o arquivo de credenciais OAuth 2.0 no Google Cloud Console e coloque na raiz do projeto."
                )
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(token_file, "wb") as token:
            pickle.dump(creds, token)
            
    return build("youtube", "v3", credentials=creds)

def upload_short_to_youtube(
    video_path: str,
    title: str,
    description: str = "",
    tags: list = None,
    privacy_status: str = "private",
    client_secrets_file: str = "client_secrets.json"
):
    """
    Faz o upload automático de um vídeo para o YouTube Shorts.
    """
    if tags is None:
        tags = ["shorts", "cortes", "viral", "reels"]
        
    # Adicionar tag #shorts ao título se não existir para o YouTube reconhecer como Short
    if "#shorts" not in title.lower():
        title = f"{title} #shorts"

    youtube = get_authenticated_service(client_secrets_file)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description or f"{title}\n\nInscreva-se para mais cortes!",
            "tags": tags,
            "categoryId": "24" # Entretenimento
        },
        "status": {
            "privacyStatus": privacy_status, # "private", "unlisted" ou "public"
            "selfDeclaredMadeForKids": False
        }
    }

    print(f"[*] Fazendo upload para YouTube Shorts: {title}...")
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    response = request.execute()
    video_id = response.get("id")
    video_url = f"https://youtube.com/shorts/{video_id}"
    print(f"[OK] Upload concluído no YouTube Shorts! Link: {video_url}")
    return video_url
