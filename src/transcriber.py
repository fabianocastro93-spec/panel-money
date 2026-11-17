import os
import json
from faster_whisper import WhisperModel

def transcribe_video(video_path: str, model_size: str = "base", device: str = "auto") -> dict:
    """
    Transcreve o áudio do vídeo usando faster-whisper com timestamps exatos no nível da palavra.
    Retorna uma lista de segmentos com textos e palavras cronometradas.
    """
    print(f"[*] Carregando modelo Whisper ({model_size})...")
    # 'int8' roda rapidamente em CPUs e GPUs comuns
    model = WhisperModel(model_size, device=device, compute_type="int8")
    
    print(f"[*] Transcrevendo áudio de: {video_path}")
    segments, info = model.transcribe(
        video_path,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    print(f"[OK] Idioma detectado: {info.language} (Probabilidade: {info.language_probability:.2f})")
    
    results = []
    full_text = []
    
    for segment in segments:
        words_data = []
        if segment.words:
            for word in segment.words:
                words_data.append({
                    "word": word.word.strip(),
                    "start": round(word.start, 2),
                    "end": round(word.end, 2),
                    "probability": round(word.probability, 2)
                })
                
        seg_item = {
            "id": segment.id,
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip(),
            "words": words_data
        }
        results.append(seg_item)
        full_text.append(segment.text.strip())
        
    output_data = {
        "language": info.language,
        "language_probability": round(info.language_probability, 2),
        "full_text": " ".join(full_text),
        "segments": results
    }
    
    # Salvar cache da transcrição em JSON
    cache_path = os.path.splitext(video_path)[0] + "_transcript.json"
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"[OK] Transcrição concluída! Salva em: {cache_path}")
    return output_data

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        transcribe_video(sys.argv[1])
    else:
        print("Uso: python transcriber.py <caminho_video>")
