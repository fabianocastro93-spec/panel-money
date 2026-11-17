---
name: cortes-ai-workflow
description: >-
  Automação para criação, recorte por legendas, dublagem em português e upload de cortes virais para YouTube Shorts e Instagram Reels no projeto Cortes AI.
---

# Cortes AI Workflow Skill

Esta skill instrui o agente sobre como executar e gerenciar o pipeline de cortes virais em `C:\Users\fabia\OneDrive\Desktop\cortes`.

## Objetivos da Skill
1. **Baixar ou Ingerir Vídeos:** Usar `src/downloader.py` para URLs do YouTube/TikTok ou arquivos MP4 locais.
2. **Transcrição e Timestamps:** Usar `src/transcriber.py` com Faster-Whisper para obter palavras e tempos precisos.
3. **Detecção de Ganchos Virais:** Usar `src/highlight_detector.py` com Gemini ou heurística para selecionar os 3 a 5 melhores trechos de 25s a 60s.
4. **Dublagem Opcional:** Usar `src/dubber.py` com Edge-TTS para tradução e voz em português com ducking do áudio de fundo original.
5. **Conversão 9:16 e Legendas:** Usar `src/video_editor.py` para gerar vídeos verticais (1080x1920) com fundo desfocado e legendas no estilo TikTok/MrBeast.
6. **Uploads:** Usar `src/uploader_youtube.py` e `src/uploader_instagram.py` para enviar os vídeos gerados.

## Comandos Rápidos de Execução

```powershell
# Ativar ambiente virtual
cd "C:\Users\fabia\OneDrive\Desktop\cortes"
.\venv\Scripts\activate.ps1

# Executar corte simples
python main.py "<URL_OU_ARQUIVO>"

# Executar com dublagem
python main.py "<URL_OU_ARQUIVO>" --dub

# Executar com upload automático
python main.py "<URL_OU_ARQUIVO>" --youtube --instagram
```
