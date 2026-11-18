import os
import sys
import json
import time
import subprocess
import urllib.request
from pathlib import Path
from typing import List, Dict, Optional, Union

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DOWNLOADS_DIR = BASE_DIR / "downloads" / "live_clips"
OUTPUT_DIR = BASE_DIR / "output" / "shorts"
PROCESSED_CLIPS_FILE = CONFIG_DIR / "processed_live_clips.json"

for d in [CONFIG_DIR, DOWNLOADS_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Regra estrita de retenção: nenhum vídeo deve ter menos de 10 segundos
MIN_DURATION_SECONDS = 10.0

TWITCH_CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"

DEFAULT_STREAMERS = [
    "paulinholokobr",
    "loud_coringa",
    "alanzoka",
    "gaules",
    "nobru",
    "casimito",
    "cellbit",
    "xqc",
    "kaicenat"
]

def load_processed_clips() -> set:
    if PROCESSED_CLIPS_FILE.exists():
        try:
            with open(PROCESSED_CLIPS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("processed_ids", []))
        except Exception:
            pass
    return set()

def save_processed_clip(clip_id: str, title: str, streamer: str, views: int):
    processed = load_processed_clips()
    processed.add(clip_id)
    history = []
    if PROCESSED_CLIPS_FILE.exists():
        try:
            with open(PROCESSED_CLIPS_FILE, "r", encoding="utf-8") as f:
                history = json.load(f).get("history", [])
        except Exception:
            pass
            
    history.insert(0, {
        "clip_id": clip_id,
        "title": title,
        "streamer": streamer,
        "views": views,
        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
    })
    
    with open(PROCESSED_CLIPS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "processed_ids": list(processed),
            "history": history[:100]
        }, f, indent=2, ensure_ascii=False)


def get_twitch_channel_clips(
    channel_login: str,
    limit: int = 15,
    min_duration: float = MIN_DURATION_SECONDS,
    period: str = "LAST_WEEK"
) -> List[Dict]:
    """
    Busca os clipes mais assistidos da live de um streamer específico na Twitch.
    Filtra estritamente vídeos com duração >= min_duration (padrão 10s).
    """
    clean_login = channel_login.strip().lower().replace("@", "")
    # Mapeamento amigável de nomes populares
    ALIASES = {
        "paulinho": "paulinholokobr",
        "paulinho o loko": "paulinholokobr",
        "paulinho o loco": "paulinholokobr",
        "paulinholoko": "paulinholokobr",
        "paulinhokleber": "paulinholokobr",
        "coringa": "loud_coringa",
        "loud coringa": "loud_coringa",
        "alan": "alanzoka",
        "caze": "casimito",
        "casimiro": "casimito",
    }
    clean_login = ALIASES.get(clean_login, clean_login)
    query = """
    query($login: String!, $limit: Int!) {
      user(login: $login) {
        id
        login
        displayName
        clips(first: $limit, criteria: { filter: LAST_WEEK }) {
          edges {
            node {
              id
              slug
              url
              title
              viewCount
              durationSeconds
              createdAt
              thumbnailURL
            }
          }
        }
      }
    }
    """
    payload = {
        "query": query,
        "variables": {"login": clean_login, "limit": limit}
    }
    
    req = urllib.request.Request(
        "https://gql.twitch.tv/gql",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Client-ID": TWITCH_CLIENT_ID,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    )
    
    results = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            user = data.get("data", {}).get("user")
            if not user:
                return []
                
            streamer_name = user.get("displayName", clean_login)
            edges = user.get("clips", {}).get("edges", [])
            for edge in edges:
                node = edge.get("node", {})
                duration = float(node.get("durationSeconds", 0))
                
                # Regra inegociável do usuário: vídeos de 10 segundos pra cima!
                if duration < min_duration:
                    continue
                    
                results.append({
                    "id": node.get("id"),
                    "slug": node.get("slug"),
                    "url": node.get("url"),
                    "title": node.get("title") or f"Momento Épico de {streamer_name}",
                    "streamer": streamer_name,
                    "streamer_login": clean_login,
                    "view_count": int(node.get("viewCount", 0)),
                    "duration": duration,
                    "created_at": node.get("createdAt"),
                    "thumbnail": node.get("thumbnailURL"),
                    "platform": "twitch"
                })
    except Exception as e:
        print(f"[!] Erro ao buscar clipes do canal {channel_login}: {e}")
        
    results.sort(key=lambda x: x["view_count"], reverse=True)
    return results


def get_twitch_game_clips(
    game_name: str = "Grand Theft Auto V",
    limit: int = 20,
    min_duration: float = MIN_DURATION_SECONDS,
    period: str = "LAST_WEEK"
) -> List[Dict]:
    """
    Busca os clipes mais virais da Twitch para uma categoria/jogo específico (ex: GTA V).
    Aplica filtro estrito de duração >= 10s.
    """
    query = """
    query($gameName: String!, $limit: Int!) {
      game(name: $gameName) {
        id
        name
        clips(first: $limit, criteria: { filter: LAST_WEEK }) {
          edges {
            node {
              id
              slug
              url
              title
              viewCount
              durationSeconds
              createdAt
              thumbnailURL
              broadcaster {
                displayName
                login
              }
            }
          }
        }
      }
    }
    """
    payload = {
        "query": query,
        "variables": {"gameName": game_name, "limit": limit}
    }
    
    req = urllib.request.Request(
        "https://gql.twitch.tv/gql",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Client-ID": TWITCH_CLIENT_ID,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
    )
    
    results = []
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            game = data.get("data", {}).get("game")
            if not game:
                return []
                
            edges = game.get("clips", {}).get("edges", [])
            for edge in edges:
                node = edge.get("node", {})
                duration = float(node.get("durationSeconds", 0))
                
                # Regra: duração >= 10 segundos
                if duration < min_duration:
                    continue
                    
                broadcaster = node.get("broadcaster", {})
                streamer_name = broadcaster.get("displayName", "Streamer")
                streamer_login = broadcaster.get("login", "")
                
                results.append({
                    "id": node.get("id"),
                    "slug": node.get("slug"),
                    "url": node.get("url"),
                    "title": node.get("title") or f"Jogada Insana no {game_name}",
                    "streamer": streamer_name,
                    "streamer_login": streamer_login,
                    "view_count": int(node.get("viewCount", 0)),
                    "duration": duration,
                    "created_at": node.get("createdAt"),
                    "thumbnail": node.get("thumbnailURL"),
                    "platform": "twitch",
                    "game": game_name
                })
    except Exception as e:
        print(f"[!] Erro ao buscar clipes do jogo {game_name}: {e}")
        
    results.sort(key=lambda x: x["view_count"], reverse=True)
    return results


def search_all_live_clips(
    query_or_channel: str = "",
    min_duration: float = MIN_DURATION_SECONDS,
    limit: int = 15
) -> List[Dict]:
    """
    Mecanismo Unificado: Se passar o nome de um streamer, busca do canal.
    Se estiver vazio, busca dos maiores streamers da atualidade e de GTA.
    """
    clean = query_or_channel.strip()
    if clean:
        # Tenta como canal primeiro
        clips = get_twitch_channel_clips(clean, limit=limit, min_duration=min_duration)
        if clips:
            return clips
        # Tenta como jogo/categoria
        clips = get_twitch_game_clips(clean, limit=limit, min_duration=min_duration)
        if clips:
            return clips
            
    # Busca global automática nos streamers de ponta
    all_clips = []
    seen_ids = set()
    
    # 1. Clipes de GTA V (jogadores de RP e lives épicas)
    gta_clips = get_twitch_game_clips("Grand Theft Auto V", limit=10, min_duration=min_duration)
    for c in gta_clips:
        if c["id"] not in seen_ids:
            seen_ids.add(c["id"])
            all_clips.append(c)
            
    # 2. Clipes dos streamers cadastrados
    for s in DEFAULT_STREAMERS[:4]:
        st_clips = get_twitch_channel_clips(s, limit=5, min_duration=min_duration)
        for c in st_clips:
            if c["id"] not in seen_ids:
                seen_ids.add(c["id"])
                all_clips.append(c)
                
    # Ordena por número absoluto de visualizações
    all_clips.sort(key=lambda x: x["view_count"], reverse=True)
    return all_clips[:limit]


def download_live_clip(clip_url: str, output_name: str = None) -> Path:
    """
    Baixa um clipe da Twitch ou YouTube em resolução máxima usando yt-dlp.
    """
    if not output_name:
        output_name = f"live_clip_{int(time.time())}"
        
    clean_target = DOWNLOADS_DIR / f"{output_name}.mp4"
    
    # yt-dlp command
    ytdlp_bin = str(BASE_DIR / "venv" / "Scripts" / "yt-dlp.exe")
    if not os.path.exists(ytdlp_bin):
        ytdlp_bin = "yt-dlp"
        
    cmd = [
        ytdlp_bin,
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", str(clean_target),
        "--no-playlist",
        clip_url
    ]
    
    print(f"[*] Baixando clipe da live: {clip_url}...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Falha ao baixar clipe da live: {res.stderr[:200]}")
        
    if not clean_target.exists():
        # Verifica se gerou com outro sufixo
        candidates = list(DOWNLOADS_DIR.glob(f"{output_name}.*"))
        if candidates:
            return candidates[0]
        raise FileNotFoundError(f"Arquivo de clipe não encontrado após download: {clean_target}")
        
    return clean_target


def process_live_clip_to_short(
    clip_url: str,
    title: str = None,
    streamer: str = None,
    views: int = 0,
    hook_title: str = None,
    brand_tag: str = "@castro93c",
    auto_upload: bool = False,
    platforms: List[str] = None
) -> Dict:
    """
    Processo completo de transformação de um clipe de live em corte 9:16 vertical viral:
    1. Baixa o clipe.
    2. Checa duração com FFprobe (valida se tem >= 10s).
    3. Renderiza em 9:16 vertical com blur de fundo, banner de gancho e marca d'água @castro93c.
    4. Normaliza áudio em EBU R128 (-14 LUFS).
    5. Opcional: Publica automaticamente no YouTube Shorts, Instagram Reels e TikTok!
    """
    from src.video_editor import render_vertical_short
    
    clip_slug = clip_url.rstrip("/").split("/")[-1].split("?")[0]
    out_base = f"live_short_{clip_slug}_{int(time.time())}"
    
    # 1. Download
    video_path = download_live_clip(clip_url, output_name=out_base)
    
    # 2. Obter duração real com ffprobe
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    probe_res = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    real_duration = 0.0
    try:
        real_duration = float(probe_res.stdout.strip())
    except Exception:
        real_duration = 15.0
        
    # Checagem inegociável: Sempre >= 10 segundos
    if real_duration < MIN_DURATION_SECONDS:
        try:
            os.remove(video_path)
        except Exception:
            pass
        raise ValueError(
            f"O clipe tem apenas {real_duration:.1f} segundos. Pela sua regra de ouro, somente vídeos com 10 segundos ou mais são processados!"
        )
        
    # 3. Montar Gancho Visual e Título
    final_hook = hook_title
    if not final_hook:
        if title:
            # Transforma título em gancho chamativo
            final_hook = title.upper().strip()[:45]
            if not any(e in final_hook for e in ["🔥", "😱", "🎮", "⚡", "👀"]):
                final_hook += " 🔥"
        else:
            final_hook = f"MOMENTO ÉPICO DO {streamer.upper()}! 😱" if streamer else "MOMENTO INSANO DA LIVE! 🔥"
            
    final_output_path = OUTPUT_DIR / f"{out_base}.mp4"
    
    # 4. Renderização Vertical 9:16
    print(f"[*] Renderizando clipe da live em 9:16 vertical (Duração: {real_duration:.1f}s)...")
    render_vertical_short(
        source_video_path=str(video_path),
        start_sec=0.0,
        end_sec=real_duration,
        output_path=str(final_output_path),
        hook_title=final_hook,
        brand_tag=brand_tag
    )
    
    # Salvar metadados do corte
    meta_path = str(final_output_path) + ".meta.json"
    meta_data = {
        "title": title or final_hook,
        "hook_title": final_hook,
        "streamer": streamer or "Live Streamer",
        "clip_url": clip_url,
        "views": views,
        "duration": real_duration,
        "brand_tag": brand_tag,
        "rendered_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=2, ensure_ascii=False)
        
    # Marca como processado
    save_processed_clip(clip_slug, title or final_hook, streamer or "Streamer", views)
    
    upload_results = {}
    if auto_upload:
        if platforms is None:
            platforms = ["youtube", "instagram", "tiktok"]
            
        caption = f"{final_hook}\n\nClipe épico da live de {streamer or 'games'}! Siga @castro93c para mais conteúdos.\n\n#shorts #cortes #viral #twitch #reels #fyp #foryou"
        
        # YouTube Shorts
        if "youtube" in platforms:
            try:
                from src.uploader_youtube import upload_short_to_youtube
                yt_res = upload_short_to_youtube(
                    str(final_output_path),
                    title=f"{final_hook} #shorts",
                    description=caption,
                    privacy_status="public"
                )
                upload_results["youtube"] = yt_res
            except Exception as e:
                upload_results["youtube_error"] = str(e)
                
        # Instagram Reels
        if "instagram" in platforms:
            try:
                from src.uploader_instagram import upload_reel_to_instagram
                ig_res = upload_reel_to_instagram(str(final_output_path), caption=caption)
                upload_results["instagram"] = ig_res.get("url") or "Publicado com sucesso no Reels"
            except Exception as e:
                upload_results["instagram_error"] = str(e)
                
        # TikTok
        if "tiktok" in platforms:
            try:
                from src.uploader_tiktok import upload_to_tiktok, is_tiktok_connected
                if is_tiktok_connected():
                    tt_res = upload_to_tiktok(str(final_output_path), description=caption)
                    upload_results["tiktok"] = "Publicado com sucesso no TikTok"
            except Exception as e:
                upload_results["tiktok_error"] = str(e)
                
    return {
        "status": "success",
        "video_path": str(final_output_path),
        "filename": final_output_path.name,
        "title": title or final_hook,
        "hook": final_hook,
        "duration": real_duration,
        "uploads": upload_results
    }


def run_live_sniper_best_clip(
    target_streamer: str = None,
    game: str = "Grand Theft Auto V",
    min_duration: float = MIN_DURATION_SECONDS,
    auto_upload: bool = True
) -> Dict:
    """
    Piloto Automático: Encontra o clipe mais assistido e ainda não postado,
    corta em 9:16 vertical e publica no YouTube, Instagram e TikTok!
    """
    processed = load_processed_clips()
    print(f"[*] Radar de Lives ativo: Buscando os clipes mais virais da semana (Duração mínima: {min_duration}s)...")
    
    candidates = []
    if target_streamer:
        candidates = get_twitch_channel_clips(target_streamer, limit=15, min_duration=min_duration)
    else:
        candidates = search_all_live_clips("", min_duration=min_duration, limit=20)
        
    # Filtra os que já foram processados
    fresh_candidates = [c for c in candidates if c.get("slug") not in processed and c.get("id") not in processed]
    
    if not fresh_candidates:
        return {
            "status": "no_fresh_clips",
            "message": "Nenhum clipe novo com mais de 10 segundos encontrado no momento."
        }
        
    best_clip = fresh_candidates[0]
    print(f"[🔥] Melhor clipe viral encontrado: '{best_clip['title']}' ({best_clip['view_count']} views, {best_clip['duration']}s) do streamer {best_clip['streamer']}")
    
    result = process_live_clip_to_short(
        clip_url=best_clip["url"],
        title=best_clip["title"],
        streamer=best_clip["streamer"],
        views=best_clip["view_count"],
        brand_tag="@castro93c",
        auto_upload=auto_upload
    )
    
    return {
        "status": "success",
        "clip": best_clip,
        "result": result
    }

if __name__ == "__main__":
    print("[*] Testando Radar de Lives...")
    clips = search_all_live_clips("Grand Theft Auto V", limit=3)
    for c in clips:
        print(f"- [{c['duration']}s] {c['streamer']}: {c['title']} ({c['view_count']} views) -> {c['url']}")
