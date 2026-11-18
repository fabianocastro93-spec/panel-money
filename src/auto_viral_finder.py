import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

DOWNLOADS_DIR = BASE_DIR / "downloads"
OUTPUT_SHORTS_DIR = BASE_DIR / "output" / "shorts"
CONFIG_DIR = BASE_DIR / "config"
PROCESSED_FILE = CONFIG_DIR / "processed_videos.json"
HISTORY_FILE = CONFIG_DIR / "viral_automation_log.json"

for d in [DOWNLOADS_DIR, OUTPUT_SHORTS_DIR, CONFIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def get_processed_ids() -> set:
    if PROCESSED_FILE.exists():
        try:
            with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()

def mark_video_processed(video_id: str, title: str = ""):
    processed = get_processed_ids()
    processed.add(video_id)
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(list(processed), f, ensure_ascii=False, indent=2)

def log_automation_entry(entry: dict):
    history = []
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    history.insert(0, entry)
    # Mantém os últimos 100 registros
    history = history[:100]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def search_viral_gta6_videos(max_results: int = 25) -> list:
    """
    Pesquisa no YouTube pelos vídeos de GTA 6 com MAIOR NÚMERO DE VISUALIZAÇÕES.
    Prioriza estritamente os maiores sucessos virais (centenas de milhares a milhões de views)
    para garantir que os cortes sejam feitos exclusivamente do conteúdo mais assistido do mundo.
    """
    queries = [
        "GTA 6 gameplay details secrets",
        "GTA 6 trailer reveals rockstar",
        "GTA 6 news updates facts",
        "GTA 6 graphics physics details",
        "GTA 6 easter eggs insane details",
        "GTA VI map leaks gameplay"
    ]
    
    processed = get_processed_ids()
    candidates = []
    
    yt_dlp_cmd = str(BASE_DIR / "venv" / "Scripts" / "yt-dlp.exe")
    if not os.path.exists(yt_dlp_cmd):
        yt_dlp_cmd = "yt-dlp"

    print(f"[*] Rastreando YouTube por vídeos de GTA 6 com o MÁXIMO de visualizações...")
    for query in queries:
        cmd = [
            yt_dlp_cmd,
            f"ytsearch{max_results}:{query}",
            "--dump-json",
            "--flat-playlist",
            "--no-warnings"
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=35)
            for line in res.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    vid_id = data.get("id")
                    duration = data.get("duration") or 0
                    views = data.get("view_count") or 0
                    
                    # Filtros: não processado antes, duração viável para cortes (entre 40s e 25 minutos)
                    if vid_id and vid_id not in processed and 40 <= duration <= 1500:
                        candidates.append({
                            "id": vid_id,
                            "url": f"https://www.youtube.com/watch?v={vid_id}",
                            "title": data.get("title", "GTA 6 Video"),
                            "views": int(views),
                            "duration": duration,
                            "channel": data.get("channel", "")
                        })
                except Exception:
                    continue
        except Exception as e:
            print(f"[!] Erro ao buscar com query '{query}': {e}")
            
    # Remover duplicatas mantendo o maior número de views
    seen = {}
    for c in candidates:
        if c["id"] not in seen or c["views"] > seen[c["id"]]["views"]:
            seen[c["id"]] = c
            
    unique_candidates = list(seen.values())

    # PRIORIZAÇÃO ABSOLUTA: Ordenar rigorosamente do MAIOR número de visualizações para o menor
    unique_candidates.sort(key=lambda x: x["views"], reverse=True)
    
    print(f"[*] Total de {len(unique_candidates)} vídeos únicos analisados. Top 3 mais assistidos:")
    for i, top in enumerate(unique_candidates[:3], 1):
        print(f"    #{i} - {top['title']} ({top['views']:,} visualizações)")
        
    return unique_candidates

def process_single_video(top_video: dict, auto_youtube: bool = True, auto_instagram: bool = True, auto_tiktok: bool = True) -> dict:
    """
    Baixa um vídeo específico, detecta corte viral, gera legendas em português
    e publica automaticamente nas redes sociais.
    """
    print("\n" + "=" * 60)
    print(f"[*] Processando Vídeo Viral: '{top_video['title']}'")
    print(f"[*] Views: {top_video['views']:,} | Duração: {top_video['duration']}s | Canal: {top_video['channel']}")
    print(f"[*] URL: {top_video['url']}")
    print("=" * 60)

    from src.downloader import download_video
    from src.transcriber import transcribe_video
    from src.highlight_detector import detect_highlights, generate_specific_caption
    from src.dubber import translate_segments_to_pt
    from src.video_editor import render_vertical_short

    # 1. Download
    print("\n[1/5] Baixando vídeo com yt-dlp...")
    vinfo = download_video(top_video["url"], output_dir=str(DOWNLOADS_DIR))
    video_path = vinfo["filepath"]

    # 2. Transcrição
    print("\n[2/5] Transcrevendo áudio com Faster-Whisper...")
    transcript = transcribe_video(video_path, model_size="base")
    detected_lang = transcript.get("language", "pt")

    # 3. Detectar o melhor corte viral (25 a 45 segundos)
    print("\n[3/5] Identificando momento viral e gancho sonoro...")
    clips = detect_highlights(transcript, max_clips=1, min_sec=25, max_sec=45)
    if not clips:
        clips = [{
            "start": 5.0,
            "end": 38.0,
            "title": "ESSE DETALHE NO GTA 6 VAI SER INSANO! 🔥",
            "suggested_titles": ["ESSE DETALHE NO GTA 6 VAI SER INSANO! 🔥"]
        }]
    clip = clips[0]

    # 4. Traduzir legendas para PT e Renderizar em 9:16
    print("\n[4/5] Traduzindo legendas para PT-BR e renderizando em 9:16 vertical...")
    clip_words = translate_segments_to_pt(transcript.get("segments", []), clip["start"], clip["end"])
    clip_text = " ".join([w["word"] for w in clip_words]) if clip_words else clip["title"]

    out_filename = f"{int(time.time())}_auto_{top_video['id']}.mp4"
    out_path = str(OUTPUT_SHORTS_DIR / out_filename)

    # Títulos e legendas específicas de acordo com o que foi falado
    title = clip.get("title", "ESSE DETALHE NO GTA 6 VAI SER INSANO! 🔥")
    
    render_vertical_short(
        source_video_path=video_path,
        start_sec=clip["start"],
        end_sec=clip["end"],
        output_path=out_path,
        subtitles_words=clip_words,
        hook_title=title,
        brand_tag="@castro93c"
    )
    caption_ig = generate_specific_caption(clip_text, title, platform="instagram")
    caption_yt = generate_specific_caption(clip_text, title, platform="youtube")

    meta_path = Path(out_path).with_name(out_filename + ".json")
    with open(meta_path, "w", encoding="utf-8") as mf:
        json.dump({
            "title": title,
            "suggested_titles": clip.get("suggested_titles", [title]),
            "suggested_titles_youtube": [f"{title.replace('#shorts','').strip()} #shorts"],
            "caption": caption_ig,
            "caption_instagram": caption_ig,
            "caption_youtube": caption_yt,
            "clip_text": clip_text,
            "source_url": top_video["url"]
        }, mf, ensure_ascii=False, indent=2)

    # 5. Postagem Automática
    print("\n[5/5] Realizando postagens automáticas...")
    results = {}

    if auto_youtube:
        try:
            from src.uploader_youtube import upload_short_to_youtube
            yt_url = upload_short_to_youtube(out_path, title=title, description=caption_yt, privacy_status="public")
            results["youtube"] = yt_url
            print(f"[OK] Postado com sucesso no YouTube Shorts: {yt_url}")
        except Exception as e:
            print(f"[!] Erro ao postar no YouTube: {e}")
            results["youtube_error"] = str(e)

    if auto_instagram:
        try:
            from src.uploader_instagram import upload_reel_to_instagram
            ig_res = upload_reel_to_instagram(out_path, caption=caption_ig)
            results["instagram"] = ig_res.get("url") or ig_res
            print(f"[OK] Postado com sucesso no Instagram Reels!")
        except Exception as e:
            print(f"[!] Erro ao postar no Instagram: {e}")
            results["instagram_error"] = str(e)

    if auto_tiktok:
        try:
            from src.uploader_tiktok import is_tiktok_connected, upload_to_tiktok
            if is_tiktok_connected():
                tt_res = upload_to_tiktok(out_path, description=f"{title}\n{caption_ig}")
                results["tiktok"] = "Publicado no TikTok com sucesso!"
                print(f"[OK] Postado com sucesso no TikTok!")
        except Exception as e:
            print(f"[!] Erro ao postar no TikTok: {e}")
            results["tiktok_error"] = str(e)

    # Marcar vídeo como processado
    mark_video_processed(top_video["id"], top_video["title"])

    # Salva no histórico de automação
    log_automation_entry({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "video_id": top_video["id"],
        "video_title": top_video["title"],
        "views": top_video["views"],
        "clip_file": out_filename,
        "clip_title": title,
        "results": results
    })

    return {
        "status": "success",
        "video_title": top_video["title"],
        "clip_file": out_filename,
        "clip_title": title,
        "results": results
    }

def process_and_post_auto(count: int = 1, auto_youtube: bool = True, auto_instagram: bool = True, auto_tiktok: bool = True) -> list:
    """
    Busca os vídeos virais mais quentes de GTA 6, processa os cortes virais com legendas em PT
    e publica automaticamente no YouTube Shorts, Instagram Reels e TikTok!
    """
    print("=" * 65)
    print(f"  INICIANDO BUSCA E POSTAGEM AUTOMÁTICA DE VÍDEOS VIRAIS GTA 6 (META: {count} VÍDEO(S))")
    print("=" * 65)

    candidates = search_viral_gta6_videos()
    if not candidates:
        print("[!] Nenhum vídeo novo de GTA 6 encontrado que atenda aos critérios.")
        return []

    processed_reports = []
    selected_videos = candidates[:count]
    print(f"[*] {len(selected_videos)} vídeo(s) viral(is) selecionado(s) para produção e postagem:")
    for idx, v in enumerate(selected_videos, 1):
        print(f"    {idx}. {v['title']} ({v['views']:,} visualizações)")

    for idx, vid in enumerate(selected_videos, 1):
        print(f"\n>>> INICIANDO PROCESSO DO VÍDEO {idx} DE {len(selected_videos)} <<<")
        try:
            report = process_single_video(vid, auto_youtube=auto_youtube, auto_instagram=auto_instagram, auto_tiktok=auto_tiktok)
            processed_reports.append(report)
        except Exception as e:
            print(f"[!] Falha no processamento do vídeo '{vid['title']}': {e}")
            processed_reports.append({
                "status": "error",
                "video_title": vid["title"],
                "error": str(e)
            })

    print("\n" + "=" * 65)
    print(f"  CICLO AUTOMÁTICO CONCLUÍDO! {len(processed_reports)} VÍDEO(S) PROCESSADO(S)")
    print("=" * 65)
    return processed_reports

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Piloto Automático de Vídeos Virais GTA 6")
    parser.add_argument("--count", type=int, default=1, help="Quantidade de vídeos virais para postar (padrão: 1)")
    parser.add_argument("--no-yt", action="store_true", help="Não postar no YouTube Shorts")
    parser.add_argument("--no-ig", action="store_true", help="Não postar no Instagram Reels")
    parser.add_argument("--no-tt", action="store_true", help="Não postar no TikTok")
    args = parser.parse_args()

    process_and_post_auto(
        count=args.count,
        auto_youtube=not args.no_yt,
        auto_instagram=not args.no_ig,
        auto_tiktok=not args.no_tt
    )
