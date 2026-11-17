import os
import sys
import json
import time
import shutil
import threading
import webbrowser
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, BackgroundTasks, HTTPException, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv, set_key

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_SHORTS_DIR = BASE_DIR / "output" / "shorts"
OUTPUT_DUBBED_DIR = BASE_DIR / "output" / "dubbed"
DOWNLOADS_DIR = BASE_DIR / "downloads"
WEB_DIR = BASE_DIR / "web"
CONFIG_PATH = BASE_DIR / "config" / "settings.json"
ENV_PATH = BASE_DIR / ".env"

for d in [OUTPUT_SHORTS_DIR, OUTPUT_DUBBED_DIR, DOWNLOADS_DIR, WEB_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Estado global do processamento
job_state = {
    "status": "idle",       # "idle", "running", "completed", "error"
    "stage": "",            # "download", "transcribe", "detect", "dub", "render"
    "progress": 0,          # 0 a 100
    "message": "Sistema pronto.",
    "logs": [],
    "current_clips": []
}

app = FastAPI(title="Cortes AI Studio")

# Habilitar CORS irrestrito para desenvolvimento local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir os arquivos de vídeo para o player HTML5 poder tocar diretamente
app.mount("/videos", StaticFiles(directory=str(OUTPUT_SHORTS_DIR)), name="videos")
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

class ProcessRequest(BaseModel):
    source: str
    enable_dubbing: bool = False
    translate_subtitles: bool = True
    voice: str = "pt-BR-AntonioNeural"
    max_clips: int = 3
    subtitle_style: str = "tiktok_yellow"
    auto_youtube: bool = False
    auto_instagram: bool = False

class UploadRequest(BaseModel):
    video_filename: str
    platform: str  # "youtube" ou "instagram"
    title: Optional[str] = None
    caption: Optional[str] = None

class ApiKeysRequest(BaseModel):
    gemini_key: Optional[str] = None
    instagram_user: Optional[str] = None
    instagram_pass: Optional[str] = None

class InstagramLoginRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    sessionid: Optional[str] = None

def add_log(msg: str):
    timestamp = time.strftime("%H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    job_state["logs"].append(entry)
    job_state["message"] = msg
    print(entry)

def run_pipeline_worker(req: ProcessRequest):
    global job_state
    try:
        job_state["status"] = "running"
        job_state["progress"] = 5
        job_state["logs"] = []
        job_state["current_clips"] = []
        
        from src.downloader import download_video
        from src.transcriber import transcribe_video
        from src.highlight_detector import detect_highlights
        from src.dubber import dub_clip, translate_text, translate_segments_to_pt
        from src.video_editor import render_vertical_short

        # 1. Download
        job_state["stage"] = "download"
        job_state["progress"] = 15
        add_log(f"Passo 1/5: Baixando vídeo: {req.source}")
        video_info = download_video(req.source, output_dir=str(DOWNLOADS_DIR))
        video_path = video_info["filepath"]
        add_log(f"[OK] Download concluído: {Path(video_path).name}")

        # 2. Transcrição
        job_state["stage"] = "transcribe"
        job_state["progress"] = 35
        add_log("Passo 2/5: Transcrevendo áudio com Faster-Whisper (palavra por palavra)...")
        transcript = transcribe_video(video_path, model_size="base")
        all_words = []
        for seg in transcript.get("segments", []):
            all_words.extend(seg.get("words", []))
        detected_lang = transcript.get("language", "pt")
        add_log(f"[OK] Transcrição concluída ({len(all_words)} palavras, idioma detectado: {detected_lang}).")

        # 3. Detecção de Ganchos Virais
        job_state["stage"] = "detect"
        job_state["progress"] = 55
        add_log("Passo 3/5: Analisando momentos virais com Inteligência Artificial...")
        clips = detect_highlights(transcript, max_clips=req.max_clips)
        add_log(f"[OK] {len(clips)} momentos virais identificados pela IA!")

        # 4. Processamento, Dublagem e Renderização 9:16
        job_state["stage"] = "render"
        step_progress = 35 / max(len(clips), 1)
        should_translate = req.translate_subtitles or req.enable_dubbing or (detected_lang != "pt")
        
        for idx, clip in enumerate(clips, 1):
            clean_title = "".join(c for c in clip.get("title", f"corte_{idx}") if c.isalnum() or c in (' ', '_', '-')).strip()
            out_filename = f"{int(time.time())}_{idx:02d}_{clean_title[:25]}.mp4"
            out_path = str(OUTPUT_SHORTS_DIR / out_filename)
            
            # Preparar legendas (traduzir para português se necessário)
            if should_translate and detected_lang != "pt":
                add_log(f"Traduzindo legendas do corte #{idx} para Português...")
                clip_words = translate_segments_to_pt(transcript.get("segments", []), clip["start"], clip["end"])
            else:
                clip_words = [w for w in all_words if clip["start"] <= w["start"] <= clip["end"]]

            dubbed_audio_path = None
            if req.enable_dubbing:
                job_state["stage"] = "dub"
                add_log(f"Passo 4/5: Dublando corte #{idx} para Português...")
                clip_text = " ".join([w["word"] for w in clip_words])
                if clip_text:
                    dubbed_audio_path = str(OUTPUT_DUBBED_DIR / f"dub_{idx}.mp3")
                    temp_orig_audio = str(OUTPUT_DUBBED_DIR / f"orig_{idx}.mp3")
                    os.system(f"ffmpeg -y -ss {clip['start']} -t {clip['end']-clip['start']} -i \"{video_path}\" -vn -ar 44100 -ac 2 \"{temp_orig_audio}\" >nul 2>&1")
                    dub_clip(temp_orig_audio, clip_text, dubbed_audio_path, voice=req.voice)
                    if os.path.exists(temp_orig_audio):
                        os.remove(temp_orig_audio)
            
            job_state["stage"] = "render"
            add_log(f"Passo 5/5: Renderizando corte #{idx} em 9:16 vertical com legendas animadas em Português...")
            render_vertical_short(
                source_video_path=video_path,
                start_sec=clip["start"],
                end_sec=clip["end"],
                output_path=out_path,
                subtitles_words=clip_words,
                dubbed_audio_path=dubbed_audio_path
            )
            
            # Salvar metadados com títulos virais sugeridos e legenda específica
            from src.highlight_detector import generate_specific_caption
            clip_text = " ".join([w["word"] for w in clip_words]) if clip_words else clip.get("title", "")
            
            suggested = clip.get("suggested_titles") or [
                clip.get("title", "ESSE DETALHE NO GTA 6 NINGUÉM VIU! 😱"),
                "A FÍSICA DO GTA 6 VAI SER INSANA! 🔥",
                "O SEGREDO DA ROCKSTAR NO GTA VI! 🎮"
            ]
            caption_ig = generate_specific_caption(clip_text, clip.get("title", suggested[0]), platform="instagram")
            caption_yt = generate_specific_caption(clip_text, clip.get("title", suggested[0]), platform="youtube")
            
            meta_path = Path(out_path).with_name(out_filename + ".json")
            try:
                with open(meta_path, "w", encoding="utf-8") as mf:
                    json.dump({
                        "title": clip.get("title", suggested[0]),
                        "suggested_titles": suggested,
                        "hook": clip.get("hook", ""),
                        "clip_text": clip_text,
                        "caption": caption_ig,
                        "caption_instagram": caption_ig,
                        "caption_youtube": caption_yt
                    }, mf, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[!] Erro ao salvar metadados: {e}")

            clip_info = {
                "filename": out_filename,
                "title": clip.get("title", suggested[0]),
                "suggested_titles": suggested,
                "caption": caption_ig,
                "caption_instagram": caption_ig,
                "caption_youtube": caption_yt,
                "hook": clip.get("hook", ""),
                "duration": round(clip["end"] - clip["start"], 1),
                "url": f"/videos/{out_filename}"
            }
            job_state["current_clips"].append(clip_info)
            job_state["progress"] = min(90, int(55 + (idx * step_progress)))

        # 5. Uploads automáticos opcionais
        if req.auto_youtube:
            job_state["stage"] = "upload_yt"
            add_log("Enviando clipes automaticamente para o YouTube Shorts...")
            from src.uploader_youtube import upload_short_to_youtube
            for c in job_state["current_clips"]:
                try:
                    upload_short_to_youtube(str(OUTPUT_SHORTS_DIR / c["filename"]), title=c["title"], description=c["hook"])
                    add_log(f"[YouTube] Publicado: {c['title']}")
                except Exception as e:
                    add_log(f"[YouTube Erro] {e}")

        if req.auto_instagram:
            job_state["stage"] = "upload_ig"
            add_log("Enviando clipes automaticamente para o Instagram Reels...")
            from src.uploader_instagram import upload_reel_to_instagram
            for c in job_state["current_clips"]:
                try:
                    upload_reel_to_instagram(str(OUTPUT_SHORTS_DIR / c["filename"]), caption=f"{c['title']}\n{c['hook']}")
                    add_log(f"[Instagram] Publicado: {c['title']}")
                except Exception as e:
                    add_log(f"[Instagram Erro] {e}")

        job_state["status"] = "completed"
        job_state["progress"] = 100
        add_log(f"✨ Concluído com sucesso! {len(job_state['current_clips'])} cortes gerados e prontos na Galeria.")

    except Exception as e:
        job_state["status"] = "error"
        add_log(f"ERRO durante o processamento: {str(e)}")
        print(f"Exception: {e}")

@app.get("/")
def get_index():
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Interface web em carregamento. Crie web/index.html"}

@app.get("/favicon.ico")
def get_favicon():
    return Response(content=b"", media_type="image/x-icon")

@app.get("/api/health")
def api_health():
    load_dotenv(override=True)
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    gemini_key = bool(os.getenv("GEMINI_API_KEY"))
    yt_secrets = (BASE_DIR / "client_secrets.json").exists()
    yt_token = (BASE_DIR / "token.pickle").exists()
    
    session_file = BASE_DIR / "instagram_session.json"
    ig_connected = session_file.exists()
    ig_user = os.getenv("INSTAGRAM_USERNAME", "")
    
    return {
        "ffmpeg": ffmpeg_ok,
        "python": sys.version.split()[0],
        "gemini_api": gemini_key,
        "youtube_configured": yt_secrets,
        "youtube_authenticated": yt_token,
        "instagram_configured": ig_connected or bool(ig_user),
        "instagram_session": ig_connected,
        "instagram_username": ig_user
    }

@app.post("/api/youtube/upload-secrets")
async def upload_youtube_secrets(file: UploadFile = File(...)):
    """Recebe o arquivo client_secrets.json e salva na raiz do projeto."""
    try:
        content = await file.read()
        parsed = json.loads(content.decode("utf-8"))
        if "installed" not in parsed and "web" not in parsed:
            raise ValueError("O arquivo enviado não contém o formato OAuth Client ID do Google Cloud.")
            
        secrets_file = BASE_DIR / "client_secrets.json"
        with open(secrets_file, "wb") as f:
            f.write(content)
            
        return {"status": "success", "message": "Arquivo client_secrets.json salvo com sucesso na raiz do projeto!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao salvar arquivo: {str(e)}")

@app.post("/api/youtube/auth")
def youtube_auth():
    """Inicia a autenticação OAuth oficial do Google para autorizar o YouTube."""
    try:
        from src.uploader_youtube import get_authenticated_service
        service = get_authenticated_service()
        channel_name = "Canal do YouTube"
        try:
            response = service.channels().list(part="snippet", mine=True).execute()
            items = response.get("items", [])
            if items:
                channel_name = items[0]["snippet"]["title"]
        except Exception:
            pass
        return {
            "status": "success",
            "channel": channel_name,
            "message": "Conectado com sucesso ao YouTube Shorts! Canal liberado e pronto para envio."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na autenticação do YouTube: {str(e)}")

@app.post("/api/instagram/login")
def instagram_login(req: InstagramLoginRequest):
    """Realiza o login direto no Instagram ou via sessionid e persiste o arquivo de sessao."""
    from instagrapi import Client
    cl = Client()
    try:
        session_file = BASE_DIR / "instagram_session.json"
        
        if req.sessionid and req.sessionid.strip():
            print("[*] Tentando login via SessionID do Instagram...")
            cl.login_by_sessionid(req.sessionid.strip())
        elif req.username and req.password:
            print(f"[*] Tentando login com credenciais do Instagram: {req.username}...")
            cl.login(req.username.strip(), req.password.strip())
            # Salvar no .env tambem
            set_key(str(ENV_PATH), "INSTAGRAM_USERNAME", req.username.strip())
            set_key(str(ENV_PATH), "INSTAGRAM_PASSWORD", req.password.strip())
        else:
            raise HTTPException(status_code=400, detail="Forneça Usuário e Senha ou o SessionID.")

        cl.dump_settings(str(session_file))
        info = cl.account_info()
        print(f"[OK] Instagram autenticado com sucesso: @{info.username}")
        
        return {
            "status": "success",
            "username": info.username,
            "full_name": info.full_name,
            "message": f"Conectado com sucesso como @{info.username}!"
        }
    except Exception as e:
        print(f"[!] Erro ao autenticar no Instagram: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/save-keys")
def save_keys(req: ApiKeysRequest):
    """Permite salvar usuário do Instagram e Chave Gemini direto pelo Painel."""
    if not ENV_PATH.exists():
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write("# Configuracoes salvas pelo Painel Web\n")
            
    if req.gemini_key is not None:
        set_key(str(ENV_PATH), "GEMINI_API_KEY", req.gemini_key.strip())
        os.environ["GEMINI_API_KEY"] = req.gemini_key.strip()

    if req.instagram_user is not None:
        set_key(str(ENV_PATH), "INSTAGRAM_USERNAME", req.instagram_user.strip())
        os.environ["INSTAGRAM_USERNAME"] = req.instagram_user.strip()

    if req.instagram_pass is not None:
        set_key(str(ENV_PATH), "INSTAGRAM_PASSWORD", req.instagram_pass.strip())
        os.environ["INSTAGRAM_PASSWORD"] = req.instagram_pass.strip()

    return {"status": "success", "message": "Credenciais salvas com sucesso no arquivo .env!"}

@app.get("/api/job")
def get_job_status():
    return job_state

@app.post("/api/process")
def start_processing(req: ProcessRequest, background_tasks: BackgroundTasks):
    global job_state
    if job_state["status"] == "running":
        raise HTTPException(status_code=400, detail="Já existe um processamento em andamento.")
    
    background_tasks.add_task(run_pipeline_worker, req)
    return {"status": "started", "message": "Processamento iniciado em segundo plano."}

@app.get("/api/clips")
def list_clips():
    """Lista todos os arquivos de vídeo gerados na pasta output/shorts com metadados e títulos virais."""
    clips = []
    if OUTPUT_SHORTS_DIR.exists():
        files = sorted(OUTPUT_SHORTS_DIR.glob("*.mp4"), key=os.path.getmtime, reverse=True)
        for f in files:
            stat = f.stat()
            size_mb = round(stat.st_size / (1024 * 1024), 2)
            
            meta_path = f.with_name(f.name + ".json")
            title = ""
            suggested_titles = []
            caption = ""
            
            from src.highlight_detector import generate_specific_caption
            mdata = {}
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as mf:
                        mdata = json.load(mf)
                        title = mdata.get("title", "")
                        suggested_titles = mdata.get("suggested_titles", [])
                        caption = mdata.get("caption", "")
                except:
                    pass
                    
            if not title:
                # Título contextual padrão baseado em GTA 6
                title = "ESSE DETALHE NO GTA 6 NINGUÉM VIU! 😱"
                suggested_titles = [
                    "ESSE DETALHE NO GTA 6 NINGUÉM VIU! 😱",
                    "A FÍSICA DO GTA 6 VAI SER INSANA! 🔥",
                    "O SEGREDO DA ROCKSTAR NO GTA VI! 🎮"
                ]

            clean_base = title.replace("#shorts", "").strip()
            clip_text = mdata.get("clip_text", clean_base)
            
            caption_ig = mdata.get("caption_instagram")
            caption_yt = mdata.get("caption_youtube")
            
            if not caption_ig or len(caption_ig) < 70 or "Neste" not in caption_ig:
                caption_ig = generate_specific_caption(clip_text, title, platform="instagram")
            if not caption_yt or len(caption_yt) < 70 or "Neste" not in caption_yt:
                caption_yt = generate_specific_caption(clip_text, title, platform="youtube")

            suggested_youtube = [
                f"{clean_base} #shorts",
                "A FÍSICA DO GTA 6 VAI REVOLUCIONAR! 🔥 #shorts",
                "O SEGREDO QUE A ROCKSTAR ESCONDEU NO GTA VI! 🎮 #shorts",
                "VOCÊ SABIA DESSE DETALHE NO GTA 6?! 🤯 #shorts",
                "OS NOVOS DETALHES DO GTA 6 IMPRESSIONAM! ✨ #shorts"
            ]

            clips.append({
                "filename": f.name,
                "title": title,
                "suggested_titles": suggested_titles,
                "suggested_titles_youtube": suggested_youtube,
                "caption": caption_ig,
                "caption_instagram": caption_ig,
                "caption_youtube": caption_yt,
                "size_mb": size_mb,
                "created_at": time.strftime("%d/%m/%Y %H:%M", time.localtime(stat.st_mtime)),
                "url": f"/videos/{f.name}"
            })
    return {"clips": clips}

@app.delete("/api/clips/{filename}")
def delete_clip(filename: str):
    """Remove um clipe gerado e seus arquivos associados (.json, .jpg)."""
    video_path = OUTPUT_SHORTS_DIR / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo de vídeo não encontrado.")
    
    try:
        video_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir o vídeo: {str(e)}")

    # Exclui metadados .json
    meta_path = video_path.with_name(filename + ".json")
    if meta_path.exists():
        try:
            meta_path.unlink()
        except Exception:
            pass

    # Exclui thumbnail .jpg se existir
    thumb_path = video_path.with_name(filename + ".jpg")
    if thumb_path.exists():
        try:
            thumb_path.unlink()
        except Exception:
            pass

    return {"status": "success", "message": f"Corte '{filename}' removido com sucesso!"}

@app.post("/api/upload")
def upload_clip(req: UploadRequest):
    try:
        video_path = OUTPUT_SHORTS_DIR / req.video_filename
        if not video_path.exists():
            raise HTTPException(status_code=404, detail=f"Vídeo '{req.video_filename}' não encontrado.")
            
        if req.platform == "youtube":
            from src.uploader_youtube import upload_short_to_youtube
            title = req.title or req.video_filename
            url = upload_short_to_youtube(str(video_path), title=title, description=req.caption or "")
            return {"status": "success", "platform": "youtube", "url": url, "message": "Publicado no YouTube Shorts com sucesso!"}
            
        elif req.platform == "instagram":
            from src.uploader_instagram import upload_reel_to_instagram
            res = upload_reel_to_instagram(str(video_path), caption=req.caption or "")
            reel_url = res.get("url") or f"https://www.instagram.com/reel/{res.get('code', '')}/"
            return {
                "status": "success",
                "platform": "instagram",
                "url": reel_url,
                "result": res,
                "message": "Publicado no Instagram Reels com sucesso!"
            }
            
        else:
            raise HTTPException(status_code=400, detail="Plataforma inválida. Use 'youtube' ou 'instagram'.")
    except HTTPException:
        raise
    except Exception as e:
        print(f"[!] Erro no endpoint /api/upload: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao publicar: {str(e)}")

def start_server(port: int = 5000, open_browser: bool = True):
    if open_browser and not os.getenv("NO_BROWSER"):
        threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    start_server(port=port)
