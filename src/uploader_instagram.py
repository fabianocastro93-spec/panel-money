import os
from pathlib import Path
from instagrapi import Client

BASE_DIR = Path(__file__).resolve().parent.parent
SESSION_FILE = BASE_DIR / "instagram_session.json"

def get_instagram_client(username: str = None, password: str = None) -> Client:
    """Inicia cliente do Instagram com persistência de sessão para evitar bloqueios."""
    cl = Client()
    
    # Se já existir sessão salva, tenta carregar
    if SESSION_FILE.exists():
        try:
            cl.load_settings(str(SESSION_FILE))
            print("[*] Sessão do Instagram carregada com sucesso.")
            return cl
        except Exception as e:
            print(f"[!] Não foi possível carregar a sessão salva: {e}")
            
    # Caso contrário, faz login com credenciais
    user = username or os.getenv("INSTAGRAM_USERNAME")
    pwd = password or os.getenv("INSTAGRAM_PASSWORD")
    
    if not user or not pwd:
        raise ValueError("Credenciais do Instagram não configuradas (.env ou parâmetros).")
        
    print(f"[*] Fazendo login no Instagram como: {user}...")
    cl.login(user, pwd)
    cl.dump_settings(str(SESSION_FILE))
    print("[OK] Login efetuado e sessão persistida.")
    return cl

def upload_reel_to_instagram(video_path: str, caption: str = "", username: str = None, password: str = None):
    """
    Publica um vídeo curto como Reels no Instagram.
    Retorna um dicionário serializável em JSON com ID e URL do Reel.
    """
    vpath = Path(video_path)
    if not vpath.exists():
        raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {video_path}")

    cl = get_instagram_client(username, password)
    
    if not caption:
        caption = "🔥 Corte do dia! #cortes #viral #reels #shorts"
        
    print(f"[*] Fazendo upload do Reels no Instagram: {vpath.name}...")
    media = cl.clip_upload(
        path=vpath,
        caption=caption
    )
    
    pk = getattr(media, "pk", "")
    code = getattr(media, "code", "")
    reel_url = f"https://www.instagram.com/reel/{code}/" if code else ""
    print(f"[OK] Reels publicado com sucesso no Instagram! ID: {pk} | Link: {reel_url}")
    
    return {
        "status": "success",
        "id": str(pk),
        "code": str(code),
        "url": reel_url,
        "caption": caption
    }
