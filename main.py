import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

from src.downloader import download_video
from src.transcriber import transcribe_video
from src.highlight_detector import detect_highlights
from src.dubber import dub_clip, translate_text, translate_segments_to_pt
from src.video_editor import render_vertical_short

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "settings.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def run_pipeline(
    input_source: str,
    enable_dubbing: bool = False,
    auto_upload_yt: bool = False,
    auto_upload_ig: bool = False
):
    config = load_config()
    print("\n" + "="*60)
    print("   🚀 INICIANDO PIPELINE DE CORTES VIRAIS (SHORTS & REELS)")
    print("="*60 + "\n")
    
    # Passo 1: Download ou verificação de arquivo local
    video_info = download_video(input_source, output_dir=config.get("general", {}).get("downloads_dir", "downloads"))
    video_path = video_info["filepath"]
    video_title = video_info["title"]
    
    # Passo 2: Transcrição com Whisper
    trans_config = config.get("transcription", {})
    transcript = transcribe_video(
        video_path,
        model_size=trans_config.get("model_size", "base"),
        device=trans_config.get("device", "auto")
    )
    
    # Coletar todas as palavras com timestamps
    all_words = []
    for seg in transcript.get("segments", []):
        all_words.extend(seg.get("words", []))
        
    # Passo 3: Detecção de Momentos Virais
    max_clips = config.get("highlight_detection", {}).get("max_clips_per_video", 3)
    clips = detect_highlights(transcript, max_clips=max_clips)
    
    print(f"\n🎬 {len(clips)} cortes selecionados para produção:")
    for idx, c in enumerate(clips, 1):
        print(f"  [{idx}] {c.get('title', 'Corte')} ({c['start']}s -> {c['end']}s)")
        print(f"      Gancho: \"{c.get('hook', '')}\"")
        
    output_base_dir = config.get("general", {}).get("output_dir", "output/shorts")
    os.makedirs(output_base_dir, exist_ok=True)
    
    generated_videos = []
    
    detected_lang = transcript.get("language", "pt")
    should_translate = enable_dubbing or (detected_lang != "pt")

    # Passo 4: Processamento e Edição de cada corte
    for idx, clip in enumerate(clips, 1):
        clean_title = "".join(c for c in clip.get("title", f"corte_{idx}") if c.isalnum() or c in (' ', '_', '-')).strip()
        out_filename = f"{idx:02d}_{clean_title[:30]}.mp4"
        out_path = os.path.join(output_base_dir, out_filename)
        
        print(f"\n[{idx}/{len(clips)}] Processando: {clean_title}...")
        
        # Preparar legendas em português se necessário
        if should_translate and detected_lang != "pt":
            print(f"[*] Traduzindo legendas para Português...")
            clip_words = translate_segments_to_pt(transcript.get("segments", []), clip["start"], clip["end"])
        else:
            clip_words = [w for w in all_words if clip["start"] <= w["start"] <= clip["end"]]

        dubbed_audio_path = None
        # Dublagem (se solicitado)
        if enable_dubbing:
            clip_text = " ".join([w["word"] for w in clip_words])
            if clip_text:
                print(f"[*] Gerando voz dublada para o corte {idx}...")
                dubbed_audio_path = os.path.join("output", "dubbed", f"dub_{idx}.mp3")
                temp_orig_audio = os.path.join("output", "dubbed", f"orig_{idx}.mp3")
                os.makedirs(os.path.dirname(temp_orig_audio), exist_ok=True)
                os.system(f"ffmpeg -y -ss {clip['start']} -t {clip['end']-clip['start']} -i \"{video_path}\" -vn -ar 44100 -ac 2 \"{temp_orig_audio}\" >nul 2>&1")
                dub_clip(temp_orig_audio, clip_text, dubbed_audio_path)
                if os.path.exists(temp_orig_audio):
                    os.remove(temp_orig_audio)
        
        # Renderização do vídeo 9:16 vertical com legendas animadas em Português
        render_vertical_short(
            source_video_path=video_path,
            start_sec=clip["start"],
            end_sec=clip["end"],
            output_path=out_path,
            subtitles_words=clip_words,
            dubbed_audio_path=dubbed_audio_path
        )
        
        generated_videos.append({
            "path": out_path,
            "title": clip.get("title", f"Corte Viral {idx}"),
            "description": f"{clip.get('hook', '')}\n\n#shorts #viral #cortes"
        })

    print("\n" + "="*60)
    print(f"✨ CONCLUÍDO! {len(generated_videos)} vídeos gerados na pasta: {output_base_dir}")
    print("="*60)
    
    # Passo 5: Uploads (se ativados)
    if auto_upload_yt:
        from src.uploader_youtube import upload_short_to_youtube
        for v in generated_videos:
            try:
                upload_short_to_youtube(v["path"], title=v["title"], description=v["description"])
            except Exception as e:
                print(f"[!] Erro ao subir no YouTube: {e}")
                
    if auto_upload_ig:
        from src.uploader_instagram import upload_reel_to_instagram
        for v in generated_videos:
            try:
                upload_reel_to_instagram(v["path"], caption=f"{v['title']}\n{v['description']}")
            except Exception as e:
                print(f"[!] Erro ao subir no Instagram: {e}")

def interactive_menu():
    print("""
===========================================================
  ✂️  CORTES AI - GERADOR AUTOMÁTICO DE SHORTS E REELS  ✂️
===========================================================
1. Processar vídeo (YouTube, TikTok ou arquivo local)
2. Processar com Dublagem em Português (Edge-TTS)
3. Fazer Upload de vídeo para YouTube Shorts
4. Fazer Upload de vídeo para Instagram Reels
5. Sair
    """)
    choice = input("Escolha uma opção (1-5): ").strip()
    
    if choice == "1":
        src = input("Cole a URL do vídeo ou o caminho do arquivo MP4: ").strip()
        if src:
            run_pipeline(src, enable_dubbing=False)
    elif choice == "2":
        src = input("Cole a URL do vídeo ou o caminho do arquivo MP4: ").strip()
        if src:
            run_pipeline(src, enable_dubbing=True)
    elif choice == "3":
        video = input("Caminho do vídeo (.mp4): ").strip()
        title = input("Título do Short: ").strip()
        from src.uploader_youtube import upload_short_to_youtube
        upload_short_to_youtube(video, title)
    elif choice == "4":
        video = input("Caminho do vídeo (.mp4): ").strip()
        caption = input("Legenda do Reels: ").strip()
        from src.uploader_instagram import upload_reel_to_instagram
        upload_reel_to_instagram(video, caption)
    else:
        print("Saindo...")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        source = sys.argv[1]
        dub = "--dub" in sys.argv
        yt = "--youtube" in sys.argv
        ig = "--instagram" in sys.argv
        run_pipeline(source, enable_dubbing=dub, auto_upload_yt=yt, auto_upload_ig=ig)
    else:
        interactive_menu()
