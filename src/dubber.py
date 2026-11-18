import os
import asyncio
import edge_tts
from pydub import AudioSegment

async def _synthesize_edge_tts(text: str, voice: str, output_path: str):
    """Gera áudio usando Microsoft Edge TTS (100% gratuito e realista em pt-BR)."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def generate_tts_audio(text: str, output_path: str, voice: str = "pt-BR-AntonioNeural") -> str:
    """Invoca o sintetizador de voz Edge-TTS assincronamente."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    asyncio.run(_synthesize_edge_tts(text, voice, output_path))
    return output_path

def translate_text(text: str, target_lang: str = "pt") -> str:
    """Traduz o texto para português brasileiro natural usando Gemini ou fallback de alta velocidade."""
    if not text or not text.strip():
        return ""

    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            prompt = f"Traduza o seguinte texto para português brasileiro natural, fluido e chamativo para shorts de GTA 6:\n\n{text}"
            for m in ["gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash-lite"]:
                try:
                    res = client.models.generate_content(model=m, contents=prompt)
                    if res.text and res.text.strip():
                        return res.text.strip()
                except Exception:
                    continue
        except Exception as e:
            print(f"[!] Erro ao traduzir com Gemini: {e}")

    # Fallback automático e gratuito via Google Translate
    try:
        import requests
        import urllib.parse
        url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=pt&dt=t&q=' + urllib.parse.quote(text)
        res = requests.get(url, timeout=6).json()
        translated = "".join([item[0] for item in res[0] if item and item[0]])
        if translated:
            return translated
    except Exception as e:
        print(f"[!] Erro no fallback de tradução: {e}")

    return text

def translate_segments_to_pt(segments: list, start_sec: float, end_sec: float) -> list:
    """
    Pega os segmentos de fala do trecho selecionado, traduz o texto para português
    e calcula os timestamps sincronizados por palavra para queimar na legenda.
    """
    translated_words = []
    
    # Filtrar segmentos que pertencem ao corte
    clip_segs = [s for s in segments if s["end"] >= start_sec and s["start"] <= end_sec]
    
    for seg in clip_segs:
        text = seg.get("text", "").strip()
        if not text:
            continue
            
        pt_text = translate_text(text)
        words = pt_text.split()
        if not words:
            continue
            
        seg_start = max(start_sec, seg["start"])
        seg_end = min(end_sec, seg["end"])
        duration = max(0.2, seg_end - seg_start)
        
        for i, w in enumerate(words):
            w_start = seg_start + (i / len(words)) * duration
            w_end = seg_start + ((i + 1) / len(words)) * duration
            translated_words.append({
                "word": w,
                "start": round(w_start, 2),
                "end": round(w_end, 2)
            })
            
    return translated_words

def dub_clip(original_audio_path: str, translated_text: str, output_dubbed_audio_path: str, voice: str = "pt-BR-AntonioNeural") -> str:
    """
    Cria a dublagem: sintetiza a nova voz em português e mistura com o áudio de fundo
    original (com ducking/atenuação de volume da faixa original).
    """
    temp_tts = output_dubbed_audio_path + ".temp_tts.mp3"
    print(f"[*] Gerando voz dublada ({voice})...")
    generate_tts_audio(translated_text, temp_tts, voice=voice)
    
    # Carregar nova voz e áudio original
    tts_audio = AudioSegment.from_file(temp_tts)
    orig_audio = AudioSegment.from_file(original_audio_path)
    
    # Baixar volume do áudio original (ducking para manter efeitos/música)
    ducked_orig = orig_audio - 14  # Reduz 14 dB
    
    # Combinar mantendo o comprimento do áudio
    mixed = ducked_orig.overlay(tts_audio)
    mixed.export(output_dubbed_audio_path, format="mp3")
    
    if os.path.exists(temp_tts):
        os.remove(temp_tts)
        
    print(f"[OK] Dublagem finalizada e mixada: {output_dubbed_audio_path}")
    return output_dubbed_audio_path
