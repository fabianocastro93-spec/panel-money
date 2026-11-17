import os
import sys
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def check_health():
    """Verifica todos os requisitos do sistema e arquivos necessários."""
    print("\n🔍 DIAGNÓSTICO DO SISTEMA - CORTES AI")
    print("-" * 50)
    
    # 1. FFmpeg
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    print(f"[{'✔' if ffmpeg_ok else '✘'}] FFmpeg instalado: {'Detectado' if ffmpeg_ok else 'Não encontrado no PATH'}")
    
    # 2. Python
    print(f"[✔] Python versão: {sys.version.split()[0]}")
    
    # 3. Chave Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print(f"[✔] Gemini API Key: Configurada ({gemini_key[:4]}...{gemini_key[-4:]})")
    else:
        print("[!] Gemini API Key: Não configurada no .env (usará modo heurístico gratuito)")
        
    # 4. YouTube OAuth
    yt_secrets = os.path.exists("client_secrets.json")
    print(f"[{'✔' if yt_secrets else '!'}] Credenciais do YouTube (client_secrets.json): {'Presente' if yt_secrets else 'Pendente (necessário apenas para upload automático)'}")
    
    # 5. Instagram
    ig_user = os.getenv("INSTAGRAM_USERNAME")
    print(f"[{'✔' if ig_user else '!'}] Instagram: {'Configurado (' + ig_user + ')' if ig_user else 'Pendente no .env'}")
    
    print("-" * 50 + "\n")

def process_batch_file(filepath: str, dub: bool = False):
    """Processa uma lista de URLs de vídeos linha por linha."""
    if not os.path.exists(filepath):
        print(f"[!] Arquivo de links não encontrado: {filepath}")
        return
        
    with open(filepath, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
    print(f"[*] Processando lote com {len(urls)} vídeos...")
    from main import run_pipeline
    for idx, url in enumerate(urls, 1):
        print(f"\n🎥 [Vídeo {idx}/{len(urls)}] Ingestão: {url}")
        try:
            run_pipeline(url, enable_dubbing=dub)
        except Exception as e:
            print(f"[!] Erro ao processar {url}: {e}")

if __name__ == "__main__":
    if "--check" in sys.argv:
        check_health()
    elif "--batch" in sys.argv:
        batch_file = sys.argv[sys.argv.index("--batch") + 1] if len(sys.argv) > sys.argv.index("--batch") + 1 else "links.txt"
        dub = "--dub" in sys.argv
        process_batch_file(batch_file, dub=dub)
    else:
        check_health()
        print("💡 Dica de uso do Agente:")
        print("  python agent_helper.py --check             # Diagnostica o ambiente")
        print("  python agent_helper.py --batch links.txt   # Processa lista de vídeos em lote")
        print("  python main.py                             # Abre o menu interativo")
