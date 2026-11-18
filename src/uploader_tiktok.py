import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

ENV_PATH = BASE_DIR / ".env"
TIKTOK_SESSION_FILE = CONFIG_DIR / "tiktok_session.json"

def get_tiktok_session_id() -> str:
    """Retorna o sessionid do TikTok configurado no .env ou no arquivo JSON."""
    load_dotenv(str(ENV_PATH), override=True)
    session_id = os.getenv("TIKTOK_SESSION_ID", "").strip()
    if session_id:
        return session_id
        
    if TIKTOK_SESSION_FILE.exists():
        try:
            with open(TIKTOK_SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("sessionid", "").strip()
        except Exception:
            pass
    return ""

def save_tiktok_session(session_id: str) -> bool:
    """Salva o sessionid do TikTok para reuso automático."""
    clean_id = session_id.strip()
    if not clean_id:
        return False
        
    # Salvar no .env
    if not ENV_PATH.exists():
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write("# Cortes AI Studio Env\n")
            
    set_key(str(ENV_PATH), "TIKTOK_SESSION_ID", clean_id)
    os.environ["TIKTOK_SESSION_ID"] = clean_id
    
    # Salvar em config/tiktok_session.json
    with open(TIKTOK_SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump({"sessionid": clean_id}, f, indent=2)
        
    return True

def is_tiktok_connected() -> bool:
    """Verifica se há um sessionid configurado."""
    return bool(get_tiktok_session_id())

def upload_to_tiktok(
    video_path: str,
    description: str,
    tags: list = None,
    session_id: str = None,
    headless: bool = False
) -> dict:
    """
    Publica um corte de vídeo vertical no TikTok utilizando o sessionid da conta.
    """
    sid = session_id or get_tiktok_session_id()
    if not sid:
        raise ValueError(
            "TikTok não configurado! Insira o cookie 'sessionid' da sua conta do TikTok no Painel Web (aba APIs & Configuração)."
        )

    p = Path(video_path)
    if not p.exists():
        raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {video_path}")

    # Monta a legenda completa com hashtags
    if tags is None:
        tags = ["#shorts", "#cortes", "#viral", "#foryou", "#fyp"]

    full_description = description
    for tag in tags:
        if tag.lower() not in full_description.lower():
            full_description += f" {tag}"

    full_description = full_description.strip()[:2200]

    print(f"[*] Iniciando upload para o TikTok: {p.name}...")
    print(f"[*] Legenda: {full_description[:80]}...")

    try:
        from tiktok_uploader.upload import upload_video
        
        # Monta os cookies compatíveis com Playwright com domínio e path corretos
        cookies_list = [
            {
                "name": "sessionid",
                "value": sid,
                "domain": ".tiktok.com",
                "path": "/"
            },
            {
                "name": "sessionid_ss",
                "value": sid,
                "domain": ".tiktok.com",
                "path": "/"
            }
        ]

        # Chama a biblioteca oficial tiktok-uploader com os cookies válidos
        failed_videos = upload_video(
            filename=str(p.resolve()),
            description=full_description,
            cookies_list=cookies_list,
            browser="chromium",
            visibility="everyone",
            headless=headless
        )

        if not failed_videos:
            print(f"[OK] Vídeo postado com sucesso no TikTok!")
            return {
                "status": "success",
                "platform": "tiktok",
                "message": "Vídeo publicado com sucesso no TikTok!",
                "video": p.name
            }
        else:
            raise Exception("O processo do TikTok não confirmou a publicação do vídeo. Verifique se o sessionid ainda é válido no seu navegador.")

    except Exception as e:
        err_msg = str(e)
        print(f"[!] Erro ao publicar no TikTok: {err_msg}")
        raise Exception(f"Erro ao publicar no TikTok: {err_msg}")

if __name__ == "__main__":
    sid = get_tiktok_session_id()
    print("Status TikTok:", "Conectado" if sid else "Não conectado")
