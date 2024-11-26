import speech_recognition as sr
import tkinter as tk
import customtkinter as ctk
from dotenv import load_dotenv
import os
import threading
import requests
import json
import webbrowser  # Para abrir os links no navegador

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# URL da API Llama3
url_llama = "http://localhost:11434/api/chat"
# Chave da API do YouTube
youtube_api_key = os.getenv("YOUTUBE_API_KEY")

# Inicializa o reconhecedor de fala
recognizer = sr.Recognizer()

# Definição de cores
COR_PRETA = "#000000"
COR_BRANCA = "#FFFFFF"
COR_LARANJA = "#D35400"
COR_AMARELO_CLARO = "#F39C12"
COR_AMARELO_VIBRANTE = "#F1C40F"

# Função para chamar a API do Llama3
def llama3(prompt):
    data = {
        "model": "llama3.2",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "format": "json",
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url_llama, headers=headers, json=data)
        return response.json()["message"]["content"]
    except Exception as e:
        return {"error": f"Erro ao conectar à API Llama3: {e}"}

# Função para buscar vídeos no YouTube
def buscar_videos_youtube(query):
    query = query.replace(" ", "+")
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&key={youtube_api_key}&maxResults=3&q={query}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            links = []
            for item in data['items']:
                links.append(f"https://www.youtube.com/watch?v={item['id']['videoId']}")
            return links
        else:
            return ["Erro ao acessar a API do YouTube."]
    except Exception as e:
        return [f"Erro: {e}"]

# Função para abrir o link no navegador
def abrir_link(url):
    webbrowser.open(url)

# Função para reconhecer e processar a fala
def reconhecer_fala():
    idioma = idioma_combobox.get()
    texto_label.configure(text="Diga algo...")
    root.update()

    def reconhecimento_em_thread():
        progress_bar.pack(pady=10)
        progress_bar.start()
        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source)
                texto = recognizer.recognize_google(audio, language=idioma)
                texto_label.configure(text=f"Você disse: {texto}")
                
                # Chama a API Llama3 para gerar a lista de exercícios
                prompt = f"Me indique 3 exercícios para {texto}, Responder usando JSON apenas lista com nome."
                resposta_llama = llama3(prompt)
                if "error" in resposta_llama:
                    resultado_label.configure(text=resposta_llama["error"])
                    return
                
                # Processa a resposta JSON
                try:
                    resposta_dict = json.loads(resposta_llama)
                    exercicios = resposta_dict.get("exercicios", [])
                    print(exercicios)
                    if not exercicios:
                        resultado_label.configure(text="Nenhum exercício encontrado na resposta.")
                        return
                except json.JSONDecodeError:
                    resultado_label.configure(text="Erro ao decodificar a resposta da API.")
                    return

                # Busca vídeos no YouTube para cada exercício
                links = []
                for exercicio in exercicios:
                    video_links = buscar_videos_youtube(exercicio)
                    if video_links:  # Garante que há vídeos disponíveis
                        links.append(video_links[0])  # Pega apenas o primeiro vídeo para cada exercício

                # Limpa a área dos botões antes de adicionar os novos
                for widget in botoes_frame.winfo_children():
                    widget.destroy()

                # Adiciona botões para os links dos vídeos
                if not links:
                    resultado_label.configure(text="Nenhum vídeo encontrado.")
                else:
                    resultado_label.configure(text="Vídeos encontrados:")
                    for i, (exercicio, link) in enumerate(zip(exercicios, links)):  # Combina exercícios e links
                        botao_video = ctk.CTkButton(
                            botoes_frame,
                            text=f"Vídeo {i + 1}: {exercicio}",
                            fg_color=COR_LARANJA,
                            hover_color=COR_AMARELO_CLARO,
                            text_color=COR_BRANCA,
                            command=lambda url=link: abrir_link(url)
                        )
                        botao_video.pack(pady=5)

            except sr.UnknownValueError:
                texto_label.configure(text="Não foi possível entender o que você disse.")
            except sr.RequestError:
                texto_label.configure(text="Erro ao acessar o serviço de reconhecimento de voz.")
            finally:
                progress_bar.stop()
                progress_bar.pack_forget()

    threading.Thread(target=reconhecimento_em_thread, daemon=True).start()

# Configuração da interface gráfica
root = ctk.CTk()
root.title("Esporte Vibes: Exercícios e Vídeos")
root.geometry("400x600")
root.configure(bg=COR_PRETA)

# Label para exibir o texto reconhecido
texto_label = ctk.CTkLabel(root, text="Reconhecimento de voz", font=("Arial", 16), wraplength=580, text_color=COR_LARANJA)
texto_label.pack(pady=20)

# Label para exibir os resultados
resultado_label = ctk.CTkLabel(root, text="", font=("Arial", 14), wraplength=580, fg_color=COR_BRANCA, text_color=COR_AMARELO_CLARO)
resultado_label.pack(pady=10)

# Frame para adicionar os botões dinamicamente
botoes_frame = ctk.CTkFrame(root)
botoes_frame.pack(pady=10)

# ComboBox para selecionar o idioma
idioma_label = ctk.CTkLabel(root, text="Escolha o idioma de reconhecimento:", font=("Arial", 12), text_color=COR_PRETA)
idioma_label.pack(pady=10)

idioma_combobox = ctk.CTkComboBox(root, values=["pt-BR", "en-US"], fg_color=COR_AMARELO_VIBRANTE, text_color=COR_PRETA)
idioma_combobox.set("pt-BR")
idioma_combobox.pack(pady=10)

# Barra de progresso
progress_bar = ctk.CTkProgressBar(root, width=300, fg_color=COR_AMARELO_CLARO, progress_color=COR_LARANJA)

# Botão para iniciar o reconhecimento de voz
botao = ctk.CTkButton(root, text="Iniciar Reconhecimento", fg_color=COR_LARANJA, hover_color=COR_AMARELO_CLARO, text_color=COR_BRANCA, command=reconhecer_fala)
botao.pack(pady=10)

# Botão para sair
exit = ctk.CTkButton(root, text="Sair", fg_color=COR_LARANJA, hover_color=COR_AMARELO_CLARO, text_color=COR_BRANCA, command=root.destroy)
exit.pack(pady=10)

# Executa o loop da interface gráfica
root.mainloop()
