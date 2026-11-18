import os
import subprocess
import json
from pathlib import Path

def create_ass_subtitles(
    words: list,
    output_ass_path: str,
    video_width: int = 1080,
    video_height: int = 1920,
    hook_title: str = None,
    brand_tag: str = "@castro93c",
    duration_sec: float = 60.0
):
    """
    Gera um arquivo de legendas estilizado (.ass) no mais alto padrão de retenção:
    1. Marca d'água oficial no topo (@castro93c).
    2. Banner de Gancho Viral no topo (Box escuro com texto chamativo).
    3. Legendas estilo Karaokê no rodapé (destaca palavra por palavra em amarelo neon).
    """
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ViralShorts,Arial,66,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,5,2,2,40,40,400,1
Style: TopHook,Arial,52,&H00FFFFFF,&H000000FF,&H00000000,&HB0000000,-1,0,0,0,100,100,1,0,3,10,0,8,60,60,220,1
Style: BrandWatermark,Arial,38,&H00DFFF00,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,3,2,8,40,40,140,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    final_time = _format_ass_time(duration_sec + 2.0)

    # 1. Marca d'Água Oficial no Topo
    if brand_tag:
        clean_tag = brand_tag.strip()
        if not clean_tag.startswith("@"):
            clean_tag = f"@{clean_tag}"
        events.append(f"Dialogue: 0,0:00:00.00,{final_time},BrandWatermark,,0,0,0,,{{\\c&H00FFFF&}}⚡ {{\\c&HFFFFFF&}}{clean_tag}")

    # 2. Banner de Gancho no Topo
    if hook_title:
        clean_hook = hook_title.replace("#shorts", "").replace("#viral", "").strip().upper()
        # Se for muito longo, quebra em 2 linhas para perfeita harmonia visual
        if len(clean_hook) > 32:
            words_h = clean_hook.split()
            mid = len(words_h) // 2
            clean_hook = " ".join(words_h[:mid]) + "\\N" + " ".join(words_h[mid:])
        events.append(f"Dialogue: 0,0:00:00.00,{final_time},TopHook,,0,0,0,,{clean_hook}")

    # 3. Legendas Karaokê Dinâmicas no Rodapé
    if words:
        chunk_size = 4
        for i in range(0, len(words), chunk_size):
            chunk = words[i:i + chunk_size]
            if not chunk:
                continue
            
            # Se tivermos timestamps individuais por palavra, aplica efeito Karaokê
            has_word_timing = any(w.get("end", 0) > w.get("start", 0) for w in chunk)
            if has_word_timing:
                for active_idx, target_word in enumerate(chunk):
                    w_start = _format_ass_time(target_word["start"])
                    w_end = _format_ass_time(target_word["end"])
                    
                    styled_chunk = []
                    for j, w in enumerate(chunk):
                        w_text = w["word"].upper().strip()
                        if j == active_idx:
                            styled_chunk.append(f"{{\\c&H0000FFFF&}}{w_text}") # Destaque amarelo neon
                        else:
                            styled_chunk.append(f"{{\\c&H00FFFFFF&}}{w_text}") # Branco padrão
                    
                    line_text = " ".join(styled_chunk)
                    events.append(f"Dialogue: 1,{w_start},{w_end},ViralShorts,,0,0,0,,{line_text}")
            else:
                start_time = _format_ass_time(chunk[0]["start"])
                end_time = _format_ass_time(chunk[-1]["end"])
                text = " ".join([w["word"] for w in chunk]).upper()
                events.append(f"Dialogue: 1,{start_time},{end_time},ViralShorts,,0,0,0,,{{\\c&H0000FFFF&}}{text}")

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
    dubbed_audio_path: str = None,
    hook_title: str = None,
    brand_tag: str = "@castro93c"
) -> str:
    """
    Recorta o trecho selecionado, converte para 9:16 vertical (1080x1920) com fundo desfocado dinâmico,
    insere áudio dublado (se houver), banner de gancho no topo, marca d'água @castro93c e legendas karaokê via FFmpeg.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    duration = end_sec - start_sec
    
    # 1. Preparar legendas se fornecidas
    ass_path = None
    if subtitles_words or hook_title or brand_tag:
        relative_words = []
        if subtitles_words:
            for w in subtitles_words:
                if w["start"] >= start_sec and w["end"] <= end_sec:
                    relative_words.append({
                        "word": w["word"],
                        "start": max(0.0, w["start"] - start_sec),
                        "end": max(0.0, w["end"] - start_sec)
                    })
        ass_path = output_path + ".temp.ass"
        create_ass_subtitles(
            words=relative_words,
            output_ass_path=ass_path,
            hook_title=hook_title,
            brand_tag=brand_tag,
            duration_sec=duration
        )

    # 2. Montar filtro FFmpeg para transformar 16:9 em 9:16 vertical (1080x1920) com Blur no fundo
    filter_complex = (
        "[0:v]split=2[bg_in][fg_in];"
        "[bg_in]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
        "[fg_in]scale=1080:-1[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[v_merged]"
    )
    
    if ass_path and os.path.exists(ass_path):
        clean_ass = ass_path.replace("\\", "/").replace(":", "\\:")
        filter_complex += f";[v_merged]ass='{clean_ass}'[v_final]"
        final_video_map = "[v_final]"
    else:
        final_video_map = "[v_merged]"

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-t", str(duration),
        "-i", str(source_video_path)
    ]
    
    if dubbed_audio_path and os.path.exists(dubbed_audio_path):
        cmd.extend([
            "-i", str(dubbed_audio_path),
            "-filter_complex", filter_complex,
            "-map", final_video_map,
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_path)
        ])
    else:
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", final_video_map,
            "-map", "0:a?",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path)
        ])

    print(f"[*] Executando renderização FFmpeg 9:16 vertical...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"[!] Erro no FFmpeg: {res.stderr}")
        raise RuntimeError(f"FFmpeg falhou ao renderizar vídeo: {res.stderr[:200]}")
        
    # Limpeza do arquivo de legenda temporário
    if ass_path and os.path.exists(ass_path):
        try:
            os.remove(ass_path)
        except Exception:
            pass
            
    print(f"[OK] Corte renderizado com sucesso: {output_path}")
    return output_path
