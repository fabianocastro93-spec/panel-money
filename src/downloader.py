import os
import sys
from pathlib import Path
import yt_dlp

def download_video(url_or_path: str, output_dir: str = "downloads") -> dict:
    """
    Verifica se a entrada é um arquivo local ou uma URL (YouTube, TikTok, etc.)
    e baixa o vídeo com a melhor qualidade disponível.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Se for um arquivo local que já existe
    if os.path.exists(url_or_path):
        abs_path = os.path.abspath(url_or_path)
        print(f"[OK] Usando arquivo local: {abs_path}")
        return {
            "title": Path(abs_path).stem,
            "filepath": abs_path,
            "is_local": True
        }
        
    print(f"[*] Iniciando download da URL: {url_or_path}")
    
    out_template = os.path.join(output_dir, "%(title)s [%(id)s].%(ext)s")
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': out_template,
        'noplaylist': True,
        'quiet': False,
        'no_warnings': True,
        'merge_output_format': 'mp4'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url_or_path, download=True)
        filename = ydl.prepare_filename(info)
        # Garantir extensão .mp4 caso tenha feito merge
        if not filename.endswith(".mp4"):
            filename = os.path.splitext(filename)[0] + ".mp4"
            
        print(f"[OK] Download concluído: {filename}")
        return {
            "title": info.get('title', 'video'),
            "duration": info.get('duration', 0),
            "filepath": os.path.abspath(filename),
            "is_local": False
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        download_video(sys.argv[1])
    else:
        print("Uso: python downloader.py <URL_OU_CAMINHO>")
