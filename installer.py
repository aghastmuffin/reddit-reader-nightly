import tkinter as tk 
from tkinter import messagebox
import os, http.client
import urllib.request
root = tk.Tk()
root.withdraw()

if messagebox.askokcancel("RedditReader Basic Nightly Installer", "Welcome to the Nightly Installer for RedditReader, this is a BETA installer, and will be flushed out to make it more installer-like, visually, however it functions perfectly fine, press ok to confirm installation of RedditReader-Nightly-Newest and all of it's required dependances (NOTE: some assets may have to be downloaded by reddit reader on first startup)."):
    pass
else:
    exit(0)

def request(url:str, type="GET"):
    conn = http.client.HTTPSConnection(url)
    conn.request(type, "/")
    response = conn.getresponse()
    data = response.read()
    return data.decode("utf-8")
os.makedirs("redditreader", exist_ok=True)
with open("redditreader/requirements.txt", "w") as f:
    try:
        f.write(request("https://raw.githubusercontent.com/aghastmuffin/reddit-reader-nightly/refs/heads/main/requirements.txt"))
    except:
        f.write("""requests
pyttsx3
wave
yt_dlp
PyQt6
moviepy
vosk""")
os.system("pip install -r redditreader/requirements.txt")
os.system("winget install ffmpeg") #will also update ffmpeg if already installed
os.system("winget install ImageMagick.Q16")
ollama_url = "https://ollama.com/download/OllamaSetup.exe"
ollama_installer_path = "OllamaSetup.exe"
try:
    print("Downloading Ollama installer...")
    urllib.request.urlretrieve(ollama_url, ollama_installer_path)
    print("Running Ollama installer...")
    os.system(f"start /wait {ollama_installer_path}")
    print("Ollama installation completed.")
except Exception as e:
    print(f"Error downloading or installing Ollama: {e}")

with open("redditreader/main.py", "w") as f:
    f.write(request("https://raw.githubusercontent.com/aghastmuffin/reddit-reader-nightly/refs/heads/main/RedditReader.py"))
messagebox.showinfo("Installation Complete", "All necessary packages have been installed.")

root.mainloop()
