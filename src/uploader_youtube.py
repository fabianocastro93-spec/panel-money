import os
import pickle
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CLIENT_SECRETS = BASE_DIR / "client_secrets.json"
DEFAULT_TOKEN_FILE = BASE_DIR / "token.pickle"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def get_authenticated_service(client_secrets_file: str = None):
    """Autentica na API do YouTube usando OAuth 2.0 e salva o token para reuso."""
    creds = None
    token_path = DEFAULT_TOKEN_FILE
    secrets_path = Path(client_secrets_file) if client_secrets_file else DEFAULT_CLIENT_SECRETS
    
    if token_path.exists():
        try:
            with open(token_path, "rb") as token:
                creds = pickle.load(token)
        except Exception:
            creds = None
            
    # Verifica se as credenciais possuem todos os escopos necessários
    existing_scopes = set(getattr(creds, "scopes", []) or [])
    required_scopes = set(SCOPES)
    scopes_match = required_scopes.issubset(existing_scopes)

    if not creds or not creds.valid or not scopes_match:
        if creds and creds.expired and creds.refresh_token and scopes_match:
            creds.refresh(Request())
        else:
            if not secrets_path.exists():
                raise FileNotFoundError(
                    f"Arquivo '{secrets_path.name}' não encontrado na pasta do projeto! "
                    "Baixe o arquivo de credenciais OAuth 2.0 no Google Cloud Console e coloque em cortes/client_secrets.json."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)
            
    return build("youtube", "v3", credentials=creds)

def upload_short_to_youtube(
    video_path: str,
    title: str,
    description: str = "",
    tags: list = None,
    privacy_status: str = "public",
    client_secrets_file: str = None
):
    """
    Faz o upload automático de um vídeo para o YouTube Shorts.
    """
    if tags is None:
        tags = ["shorts", "cortes", "viral", "reels", "gta6", "gtavi"]
        
    # Adicionar tag #shorts ao título se não existir para o YouTube reconhecer como Short
    if "#shorts" not in title.lower():
        title = f"{title} #shorts"

    youtube = get_authenticated_service(client_secrets_file)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description or f"{title}\n\nInscreva-se para mais novidades do GTA 6!",
            "tags": tags,
            "categoryId": "20" # 20 = Gaming (Jogos)
        },
        "status": {
            "privacyStatus": privacy_status, # "public", "unlisted" ou "private"
            "selfDeclaredMadeForKids": False
        }
    }

    print(f"[*] Fazendo upload para YouTube Shorts: {title}...")
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    try:
        response = request.execute()
        video_id = response.get("id")
        video_url = f"https://youtube.com/shorts/{video_id}"
        print(f"[OK] Upload concluído no YouTube Shorts! Link: {video_url}")
        return video_url
    except Exception as e:
        err_msg = str(e)
        if "youtubeSignupRequired" in err_msg:
            raise Exception("Seu canal no YouTube ainda não foi criado nessa conta Google. Acesse https://www.youtube.com/create_channel no navegador para ativar seu canal e tente novamente!")
        raise
