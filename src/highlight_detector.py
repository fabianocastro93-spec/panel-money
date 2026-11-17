import os
import json
import re
from src.dubber import translate_text

def generate_viral_titles(clip_text: str, niche: str = "gta6") -> list:
    """
    Gera 3 opções de títulos chamativos com alta taxa de cliques (CTR)
    e emojis, de acordo com o que foi falado no vídeo.
    """
    if not clip_text or not clip_text.strip():
        return [
            "DETALHE INSANO NO GTA 6! 😱",
            "A ROCKSTAR ESCONDEU ISSO NO GTA VI! 🔥",
            "VOCÊ PERCEBEU ESSE SEGREDO NO GTA 6?! 🎮"
        ]

    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            prompt = f"""
Você é um especialista em títulos virais para YouTube Shorts e Instagram Reels sobre o universo de games e GTA 6.
Analise a fala desse clipe:
"{clip_text[:300]}"

Crie exatamente 3 títulos ultra-chamativos, curtos (máximo 50 caracteres), em MAIÚSCULAS e com emojis atraentes que façam a pessoa querer assistir até o fim.
Retorne apenas um JSON puro com uma lista de strings:
["TÍTULO 1 🔥", "TÍTULO 2 😱", "TÍTULO 3 🎮"]
"""
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            titles = json.loads(res.text.strip())
            if isinstance(titles, list) and len(titles) >= 3:
                return titles[:3]
        except Exception as e:
            print(f"[!] Erro ao gerar títulos com Gemini: {e}")

    # Fallback inteligente baseado no texto traduzido
    pt_text = translate_text(clip_text[:120])
    # Limpar pontuações finais
    clean_text = re.sub(r'[\.\,\!\?]', '', pt_text).strip()
    words = clean_text.split()
    
    short_hook = " ".join(words[:5]).upper() if len(words) >= 3 else "NOVIDADE CHOCANTE"
    
    # Identificar temas comuns de GTA 6
    lower_text = pt_text.lower()
    if any(k in lower_text for k in ["gráfico", "visual", "lindo", "textura"]):
        tema = "OS GRÁFICOS DO GTA 6"
    elif any(k in lower_text for k in ["física", "água", "cabelo", "vento"]):
        tema = "A NOVA FÍSICA DO GTA 6"
    elif any(k in lower_text for k in ["polícia", "carro", "viatura", "perseguição"]):
        tema = "A NOVA POLÍCIA DO GTA 6"
    elif any(k in lower_text for k in ["mapa", "vice city", "cidade", "tamanho"]):
        tema = "O TAMANHO DO MAPA DO GTA 6"
    elif any(k in lower_text for k in ["dinheiro", "bilhões", "custo", "orçamento"]):
        tema = "O ORÇAMENTO ABSURDO DO GTA 6"
    elif any(k in lower_text for k in ["lúcia", "lucia", "jason", "personagem", "casal"]):
        tema = "OS PROTAGONISTAS DO GTA 6"
    else:
        tema = "ESSE SEGREDO DO GTA 6"

    return [
        f"{tema} VAI SER INSANO! 🔥",
        f"VOCÊ PERCEBEU ISSO NO GTA VI?! 😱",
        f"{short_hook} NO GTA 6! 🎮"
    ]

def detect_highlights(transcription_data: dict, max_clips: int = 3, min_sec: int = 25, max_sec: int = 60) -> list:
    """
    Analisa a transcrição com IA para identificar os trechos mais virais
    e já sugere títulos inteligentes de acordo com cada trecho.
    """
    segments = transcription_data.get("segments", [])
    if not segments:
        print("[!] Nenhum segmento para analisar.")
        return []

    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if gemini_key:
        try:
            return _detect_with_gemini(transcription_data, max_clips, min_sec, max_sec, gemini_key)
        except Exception as e:
            print(f"[!] Erro ao usar Gemini API ({e}). Usando analisador inteligente interno...")
            
    return _detect_heuristic(segments, max_clips, min_sec, max_sec)

def _detect_with_gemini(transcription_data: dict, max_clips: int, min_sec: int, max_sec: int, api_key: str) -> list:
    print("[*] Analisando momentos virais com Gemini IA...")
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=api_key)
    
    segments_summary = []
    for s in transcription_data.get("segments", []):
        segments_summary.append(f"[{s['start']}s -> {s['end']}s]: {s['text']}")
        
    transcript_text = "\n".join(segments_summary)
    if len(transcript_text) > 40000:
        transcript_text = transcript_text[:40000] + "\n...[truncado]..."
        
    prompt = f"""
Você é um editor sênior especializado em cortes virais de GTA 6 para YouTube Shorts e Reels.
Analise a transcrição abaixo e selecione os {max_clips} MELHORES trechos virais ({min_sec}s a {max_sec}s).

Para cada trecho:
- Crie um "title" chamativo e curto em português com emojis (Ex: "A FÍSICA DA ÁGUA NO GTA 6! 🔥").
- Crie 3 "suggested_titles" alternativos para o criador poder escolher.
- Crie um "hook" forte que resume o clímax.

Transcrição:
{transcript_text}

Responda ESTRITAMENTE em formato JSON:
[
  {{
    "start": 12.5,
    "end": 55.0,
    "title": "A FÍSICA DO GTA 6 VAI REVOLUCIONAR! 🔥",
    "suggested_titles": [
      "A FÍSICA DO GTA 6 VAI REVOLUCIONAR! 🔥",
      "VOCÊ VIU ESSE DETALHE NO GTA VI?! 😱",
      "O SEGREDO DA ROCKSTAR NO GTA 6! 🎮"
    ],
    "hook": "Olha o nível de detalhe que a Rockstar colocou nesse jogo!",
    "virality_reason": "Curiosidade técnica surpreendente"
  }}
]
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    content = response.text.strip()
    clips = json.loads(content)
    print(f"[OK] {len(clips)} momentos virais identificados com títulos pela IA!")
    return clips

def _detect_heuristic(segments: list, max_clips: int, min_sec: int, max_sec: int) -> list:
    """Fallback inteligente: localiza trechos com alta densidade e cria títulos temáticos baseados no texto."""
    print("[*] Identificando cortes e gerando títulos contextuais...")
    clips = []
    
    total_duration = segments[-1]["end"] if segments else 0
    step = total_duration / (max_clips + 1) if total_duration > 0 else 60
    
    for i in range(max_clips):
        target_start = (i + 1) * step
        matched_seg = min(segments, key=lambda s: abs(s["start"] - target_start))
        start_time = matched_seg["start"]
        end_time = min(start_time + 45.0, total_duration)
        
        # Coletar texto falado desse trecho
        clip_texts = [s["text"] for s in segments if start_time <= s["start"] <= end_time]
        full_clip_text = " ".join(clip_texts)
        
        # Gerar 3 opções de títulos de acordo com o que foi falado no vídeo
        suggested = generate_viral_titles(full_clip_text, niche="gta6")
        main_title = suggested[0]
        
        translated_hook = translate_text(matched_seg["text"][:75])
        
        clips.append({
            "start": round(start_time, 2),
            "end": round(end_time, 2),
            "title": main_title,
            "suggested_titles": suggested,
            "hook": translated_hook + "...",
            "virality_reason": "Trecho de alta curiosidade temática"
        })
        
    return clips
