# 🎬 Cortes AI - Pipeline de Vídeos Virais, Dublagem e Uploads

Este projeto foi criado em `C:\Users\fabia\OneDrive\Desktop\cortes` para automatizar completamente a criação de cortes verticais (Shorts para YouTube e Reels para Instagram) a partir de vídeos longos ou links da internet, com suporte a **recorte por legendas (Whisper)**, **detecção de momentos virais por IA**, **dublagem em Português** e **publicação automática**.

---

## 🌟 1. Melhores Repositórios do GitHub Pesquisados

Abaixo estão os projetos open-source mais relevantes encontrados no GitHub que você pode usar de forma complementar ou estudar o código:

| Repositório GitHub | Destaques | Link |
| :--- | :--- | :--- |
| **`jeturing/openshorts`** | **Alternativa aberta ao OpusClip**: Detecta momentos virais com IA, faz Face-Tracking vertical (9:16) com MediaPipe/YOLO, gera legendas automáticas com Whisper e possui módulo de **dublagem e clonagem de voz**. | [github.com/jeturing/openshorts](https://github.com/jeturing/openshorts) |
| **`shubhxtech/AutoShorts`** | Roda 100% local, extrai os melhores trechos, adiciona legendas estilo TikTok/MrBeast, efeitos de zoom e possui **módulo integrado de auto-post no YouTube e Instagram**. | [github.com/shubhxtech/AutoShorts](https://github.com/shubhxtech/AutoShorts) |
| **`jianchang512/pyvideotrans`** | **O padrão ouro em Dublagem de Vídeo**: Reconhece fala, traduz para qualquer idioma, clona vozes (F5-TTS, CosyVoice, ChatTTS, Edge-TTS) e sincroniza boca/áudio com o vídeo original. Possui GUI completa para Windows. | [github.com/jianchang512/pyvideotrans](https://github.com/jianchang512/pyvideotrans) |
| **`iiwhocaresii/reels-studio`** | Automatizador de agendamento e repost de vídeos para Instagram Reels e Shorts usando GitHub Actions ou local. | [github.com/iiwhocaresii/reels-studio](https://github.com/iiwhocaresii/reels-studio) |
| **`Anil-matcha/AI-Youtube-Shorts-Generator`** | Script Python direto para transformar vídeos do YouTube em shorts verticais com legendas embutidas. | [github.com/Anil-matcha/AI-Youtube-Shorts-Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) |

---

## 🚀 2. Estrutura do Seu Projeto Criado

```
C:\Users\fabia\OneDrive\Desktop\cortes\
├── web/
│   └── index.html               # Painel Web Moderno (Dark Mode, Player 9:16, Controles)
├── app.py                       # Servidor Web do Painel (FastAPI + Uvicorn)
├── iniciar_painel.bat           # Atalho de 1 clique para abrir o Painel Web no Navegador
├── iniciar_painel.ps1           # Atalho PowerShell
├── config/
│   ├── settings.json            # Configurações de resolução, estilos de legenda e modelos
│   └── templates_legendas.json
├── src/
│   ├── downloader.py             # Baixa vídeos do YouTube/TikTok ou valida arquivo local (.mp4)
│   ├── transcriber.py            # Transcrição local com Faster-Whisper (timings de palavras)
│   ├── highlight_detector.py     # IA (Gemini ou Heurística) encontra os momentos de maior retenção
│   ├── dubber.py                 # Dublagem em PT-BR (Edge-TTS) com ducking de volume
│   ├── video_editor.py           # Converte para 9:16 vertical (1080x1920) + Legendas dinâmicas
│   ├── uploader_youtube.py       # Upload autenticado para YouTube Shorts
│   └── uploader_instagram.py     # Upload autenticado para Instagram Reels
├── downloads/                    # Vídeos originais baixados
├── output/
│   ├── shorts/                   # Vídeos finais prontos para postar
│   └── dubbed/                   # Áudios e faixas mixadas de dublagem
├── setup_env.bat                 # Instalador automático para Windows (Prompt de Comando)
├── setup_env.ps1                 # Instalador automático para Windows (PowerShell)
├── agent_helper.py               # Agente CLI de diagnóstico e processamento em lote
├── links.txt.example             # Exemplo para lista de vídeos a processar
├── requirements.txt              # Bibliotecas necessárias
├── .env.example                  # Modelo de chaves e senhas
└── main.py                       # Orquestrador interativo via terminal
```

---

## 🛠️ 3. Como Instalar e Rodar Passo a Passo

### Passo 1: Executar o instalador automático
Abra a pasta do projeto e dê dois cliques no arquivo:
```cmd
setup_env.bat
```
*(Ou execute `.\setup_env.ps1` no PowerShell como Administrador)*.  
Ele irá:
1. Verificar e instalar o **Python 3.11** e **Git** via Winget (caso ainda não estejam instalados).
2. Criar o ambiente virtual isolado (`venv`).
3. Instalar automaticamente todas as bibliotecas necessárias do `requirements.txt`.

### Passo 2: Configurar chaves (Opcional, mas recomendado)
Renomeie o arquivo `.env.example` para `.env` e preencha suas chaves:
- **`GEMINI_API_KEY`**: Para que a IA analise o roteiro e encontre os momentos virais com máxima precisão.
- **Instagram**: Seu usuário e senha para upload de Reels.
- **YouTube**: Coloque seu `client_secrets.json` na raiz do projeto (gerado no Google Cloud Console para YouTube Data API v3).

### 🌐 Modo Recomendado: Painel Web no Navegador (1 Clique)
Basta dar dois cliques no arquivo:
👉 **[iniciar_painel.bat](file:///C:/Users/fabia/OneDrive/Desktop/cortes/iniciar_painel.bat)**

O painel será aberto automaticamente no seu navegador em **`http://localhost:5000`** com:
- Player de vídeo vertical estilo smartphone
- Acompanhamento em tempo real das etapas
- Botão de upload direto para YouTube e Instagram

---

### 💻 Modo Terminal (Alternativo)
Com o ambiente ativado, execute:
```powershell
.\venv\Scripts\python.exe main.py
```
O menu exibirá as opções:
```text
1. Processar vídeo (YouTube, TikTok ou arquivo local)
2. Processar com Dublagem em Português (Edge-TTS)
3. Fazer Upload de vídeo para YouTube Shorts
4. Fazer Upload de vídeo para Instagram Reels
5. Sair
```

### Passo 4: Executar via Linha de Comando (Modo Direto)
Você também pode rodar diretamente com flags:
```powershell
# Gerar cortes simples com legendas dinâmicas
.\venv\Scripts\python.exe main.py "https://www.youtube.com/watch?v=EXEMPLO"

# Gerar cortes COM DUBLAGEM para Português
.\venv\Scripts\python.exe main.py "https://www.youtube.com/watch?v=EXEMPLO" --dub

# Gerar cortes e enviar automaticamente para YouTube e Instagram
.\venv\Scripts\python.exe main.py "https://www.youtube.com/watch?v=EXEMPLO" --youtube --instagram
```

---

## 🎨 4. Como funciona o Recorte 9:16 e as Legendas

1. **Formato 9:16 (1080x1920)**:  
   O editor aplica automaticamente o efeito de **fundo dinâmico desfocado (Blur Background)** com o vídeo centralizado ou corte inteligente. Isso garante que nenhum elemento seja cortado e o vídeo fique profissional para celulares.
2. **Legendas Queimadas Estilo TikTok/MrBeast**:  
   O sistema utiliza o formato `.ass` com fonte grossa, contorno preto forte e cor chamativa (amarelo/branco) sincronizado com cada palavra gerada pelo Whisper.
3. **Dublagem com Ducking de Áudio**:  
   A nova voz gerada pelo Edge-TTS (100% gratuita) é sobreposta à faixa original atenuando o som de fundo em -14dB, mantendo a música e os efeitos do vídeo original.

---

## 🤖 5. Skill e Agente Integrados

Este projeto inclui:
1. **Skill `cortes-ai-workflow`**: Registrada em `.agents/skills/cortes-ai-workflow/SKILL.md` e globalmente em `~/.gemini/config/skills/`, permitindo que o Antigravity execute o workflow de forma autônoma sempre que solicitado.
2. **Subagente `viral-clips-agent`**: Agente especialista dedicado que pode ser chamado diretamente para baixar vídeos, fazer diagnósticos de ambiente, revisar legendas e realizar uploads.
3. **Agente CLI local (`agent_helper.py`)**:
   - `python agent_helper.py --check`: Valida se o FFmpeg, variáveis de ambiente e dependências estão 100% operacionais.
   - `python agent_helper.py --batch links.txt`: Processa dezenas de vídeos em fila sem intervenção manual.
