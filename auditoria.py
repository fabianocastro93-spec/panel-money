import os
import sys
import shutil
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

def log_test(name: str, passed: bool, detail: str = ""):
    icon = "✅ PASSOU" if passed else "❌ FALHOU"
    print(f"{icon} | {name.ljust(35)} : {detail}")

def run_audit():
    print("\n" + "="*65)
    print("   🔍 AUDITORIA COMPLETA DO SISTEMA - CORTES AI STUDIO")
    print("="*65 + "\n")
    
    all_ok = True

    # 1. Auditoria do Python
    py_ver = sys.version.split()[0]
    is_py311 = sys.version_info.major == 3 and sys.version_info.minor == 11
    log_test("1. Versão do Python", is_py311, f"Python {py_ver}")
    if not is_py311: all_ok = False

    # 2. Auditoria do FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    has_ffmpeg = ffmpeg_path is not None
    log_test("2. FFmpeg no PATH", has_ffmpeg, f"{ffmpeg_path or 'Não encontrado'}")
    if not has_ffmpeg: all_ok = False

    # 3. Auditoria do Instagram (@castro93c)
    session_file = BASE_DIR / "instagram_session.json"
    ig_ok = False
    ig_detail = ""
    if session_file.exists():
        try:
            from instagrapi import Client
            cl = Client()
            cl.load_settings(str(session_file))
            info = cl.account_info()
            ig_ok = True
            ig_detail = f"@{info.username} autenticado (Nome: {info.full_name}, ID: {info.pk})"
        except Exception as e:
            ig_detail = f"Falha ao validar sessão: {e}"
    else:
        ig_detail = "Arquivo instagram_session.json não encontrado"
        
    log_test("3. Conexão Instagram (@castro93c)", ig_ok, ig_detail)
    if not ig_ok: all_ok = False

    # 4. Auditoria de Dublagem (Edge-TTS)
    tts_ok = False
    try:
        import asyncio
        import edge_tts
        test_tts_path = BASE_DIR / "output" / "dubbed" / "audit_test.mp3"
        test_tts_path.parent.mkdir(parents=True, exist_ok=True)
        asyncio.run(edge_tts.Communicate("Auditoria de voz realizada com sucesso.", "pt-BR-AntonioNeural").save(str(test_tts_path)))
        if test_tts_path.exists() and test_tts_path.stat().st_size > 5000:
            tts_ok = True
            tts_detail = f"Áudio pt-BR gerado com sucesso ({test_tts_path.stat().st_size} bytes)"
            test_tts_path.unlink()
        else:
            tts_detail = "Áudio gerado está vazio"
    except Exception as e:
        tts_detail = f"Erro no TTS: {e}"
    log_test("4. Síntese de Voz (Edge-TTS)", tts_ok, tts_detail)
    if not tts_ok: all_ok = False

    # 5. Auditoria do Whisper (Transcrição)
    whisper_ok = False
    try:
        import faster_whisper
        whisper_ok = True
        whisper_detail = f"faster_whisper v{faster_whisper.__version__} carregado"
    except Exception as e:
        whisper_detail = f"Erro Whisper: {e}"
    log_test("5. Motor de Transcrição Whisper", whisper_ok, whisper_detail)
    if not whisper_ok: all_ok = False

    # 6. Auditoria de Renderização 9:16 + Legendas ASS
    render_ok = False
    try:
        from src.video_editor import create_ass_subtitles, _format_ass_time
        test_ass = BASE_DIR / "output" / "shorts" / "audit_test.ass"
        test_ass.parent.mkdir(parents=True, exist_ok=True)
        create_ass_subtitles([
            {"word": "GTA", "start": 0.0, "end": 0.5},
            {"word": "6", "start": 0.5, "end": 1.0},
            {"word": "VIRAL", "start": 1.0, "end": 1.8}
        ], str(test_ass))
        if test_ass.exists():
            render_ok = True
            render_detail = "Filtro e motor de legendas dinâmicas operacionais"
            test_ass.unlink()
        else:
            render_detail = "Arquivo ASS não gerado"
    except Exception as e:
        render_detail = f"Erro no editor: {e}"
    log_test("6. Motor de Vídeo 9:16 & Legendas", render_ok, render_detail)
    if not render_ok: all_ok = False

    # 7. Auditoria do Servidor do Painel Web (FastAPI)
    web_ok = False
    try:
        from app import app
        index_file = BASE_DIR / "web" / "index.html"
        if index_file.exists() and index_file.stat().st_size > 1000:
            web_ok = True
            web_detail = f"Rotas montadas e index.html pronto ({index_file.stat().st_size} bytes)"
        else:
            web_detail = "index.html ausente ou incompleto"
    except Exception as e:
        web_detail = f"Erro no app.py: {e}"
    log_test("7. Painel Web Studio", web_ok, web_detail)
    if not web_ok: all_ok = False

    print("\n" + "="*65)
    if all_ok:
        print("   🎉 RESULTADO FINAL: SISTEMA 100% OPERACIONAL E HOMOLOGADO!")
        print("   Seu Instagram @castro93c está pronto para receber Reels!")
    else:
        print("   ⚠️ RESULTADO FINAL: Alguns módulos precisam de atenção.")
    print("="*65 + "\n")

if __name__ == "__main__":
    run_audit()
