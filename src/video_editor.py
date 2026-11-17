import os
import subprocess
import json
from pathlib import Path

def create_ass_subtitles(words: list, output_ass_path: str, video_width: int = 1080, video_height: int = 1920):
    """
    Gera um arquivo de legendas estilizado (.ass) no padrão viral do TikTok / YouTube Shorts:
    Fonte grossa, amarela/branca com contorno preto e posicionamento centralizado na parte inferior.
    """
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ViralShorts,Arial,65,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,4,2,2,40,40,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    
    # Agrupar palavras em blocos de 3 a 5 palavras para leitura rápida estilo shorts
    chunk_size = 4
    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        if not chunk:
            continue
        start_time = _format_ass_time(chunk[0]["start"])
        end_time = _format_ass_time(chunk[-1]["end"])
        text = " ".join([w["word"] for w in chunk]).upper()
        events.append(f"Dialogue: 0,{start_time},{end_time},ViralShorts,,0,0,0,,{text}")

    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))
        
    return output_ass_path

def _format_ass_time(seconds: float) -> str:
    """Converte segundos em formato ASS (H:MM:SS.cs)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    return f"{hrs:01d}:{mins:02d}:{secs:02d}.{centis:02d}"

def render_vertical_short(
    source_video_path: str,
    start_sec: float,
    end_sec: float,
    output_path: str,
    subtitles_words: list = None,
    dubbed_audio_path: str = None
) -> str:
    """
    Recorta o trecho selecionado, converte para 9:16 vertical (1080x1920) com fundo desfocado dinâmico,
    insere áudio dublado (se houver) e queima as legendas estilizadas via FFmpeg.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    duration = end_sec - start_sec
    
    # 1. Preparar legendas se fornecidas
    ass_path = None
    if subtitles_words:
        # Ajustar timestamps relativos ao corte
        relative_words = []
        for w in subtitles_words:
            if w["start"] >= start_sec and w["end"] <= end_sec:
                relative_words.append({
                    "word": w["word"],
                    "start": max(0.0, w["start"] - start_sec),
                    "end": max(0.0, w["end"] - start_sec)
                })
        if relative_words:
            ass_path = output_path + ".temp.ass"
            create_ass_subtitles(relative_words, ass_path)

    # 2. Montar filtro FFmpeg para transformar 16:9 em 9:16 vertical (1080x1920) com Blur no fundo
    # Fundo: escala para 1080x1920 esticada + blur forte
    # Frente: escala mantendo proporção (1080x608 aproximadamente) sobreposta no centro
    filter_complex = (
        "[0:v]split=2[bg_in][fg_in];"
        "[bg_in]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
        "[fg_in]scale=1080:-1[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[v_merged]"
    )
    
    if ass_path and os.path.exists(ass_path):
        # Escapar caminho para o filtro ass do FFmpeg no Windows
        clean_ass = ass_path.replace("\\", "/").replace(":", "\\:")
        filter_complex += f";[v_merged]ass='{clean_ass}'[v_final]"
        final_video_map = "[v_final]"
    else:
        final_video_map = "[v_merged]"

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-t", str(duration),
        "-i", source_video_path
    ]
    
    if dubbed_audio_path and os.path.exists(dubbed_audio_path):
        cmd += ["-i", dubbed_audio_path]
        audio_map = "1:a"
    else:
        audio_map = "0:a"
        
    cmd += [
        "-filter_complex", filter_complex,
        "-map", final_video_map,
        "-map", audio_map,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_path
    ]

    print(f"[*] Renderizando corte vertical 9:16 ({duration:.1f}s) em: {output_path}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        print(f"[ERRO FFmpeg]: {result.stderr[-400:]}")
        raise RuntimeError("Erro na renderização do vídeo com FFmpeg.")

    # Limpar arquivo temporário de legenda
    if ass_path and os.path.exists(ass_path):
        os.remove(ass_path)
        
    print(f"[OK] Vídeo vertical gerado com sucesso: {output_path}")
    return output_path
