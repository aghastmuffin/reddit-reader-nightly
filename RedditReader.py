import sys, requests, pyttsx3, sys, subprocess, yt_dlp, wave, os, threading
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt
from tkinter import messagebox
from moviepy.editor import *
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from vosk import SetLogLevel, KaldiRecognizer, Model
import ctypes
from ctypes import wintypes
import webbrowser
import logging
import inspect, json
from functools import partial
from ollama import chat
from ollama import ChatResponse

#inbuilt diagonostics
VER = "1.3.8-Nightly"
BUILD = "LAST EDIT 2025-1-18\nBUILD DATE 2024-1-20\n(Cython NaN)"
STATUS = "UNPAID, DIST, NIGHTLYDEV"

headers = {'User-Agent': r'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
a_accelerator = "libx264"
v_codec = "h264_nvenc"
saveas = "finalvideo.mp4"
gpu_num = 1
fps = 24
ollama_activate = False
#callback functions defined here
def setpythonashost():
    """Tell windows kernel that pythonw.exe is hosting the program, but not the program. Allows lower level access """
    #cite: @DamonJW https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/27872625#27872625
    myappid = 'redditreader.redditreader.Main.1-3-4-Nightly' # arbitrary string mycompany.myproduct.subproduct.version
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
def getfont():
    """i'm not gonna pretend to understand C code, chatgpt wrote this, it essentially analyzes the system and gets the current installed fonts on the SYSTEM PATH, which coincidentally moviepy can access, however doesn't have a scanning function built in?"""
    # Define necessary types
    LF_FACESIZE = 32
    LF_FULLFACESIZE = 64

    class LOGFONT(ctypes.Structure):
        _fields_ = [
            ("lfHeight", wintypes.LONG),
            ("lfWidth", wintypes.LONG),
            ("lfEscapement", wintypes.LONG),
            ("lfOrientation", wintypes.LONG),
            ("lfWeight", wintypes.LONG),
            ("lfItalic", wintypes.BYTE),
            ("lfUnderline", wintypes.BYTE),
            ("lfStrikeOut", wintypes.BYTE),
            ("lfCharSet", wintypes.BYTE),
            ("lfOutPrecision", wintypes.BYTE),
            ("lfClipPrecision", wintypes.BYTE),
            ("lfQuality", wintypes.BYTE),
            ("lfPitchAndFamily", wintypes.BYTE),
            ("lfFaceName", wintypes.WCHAR * LF_FACESIZE)
        ]

    # Define callback function
    def EnumFontFamiliesExProc(lpelfe, lpntme, FontType, lParam):
        fonts.append(lpelfe.contents.lfFaceName)
        return 1

    # Define function prototype
    EnumFontFamiliesExProcProto = ctypes.WINFUNCTYPE(
        wintypes.INT, ctypes.POINTER(LOGFONT), ctypes.POINTER(wintypes.LONG), wintypes.DWORD, wintypes.LPARAM
    )
    EnumFontFamiliesExProc = EnumFontFamiliesExProcProto(EnumFontFamiliesExProc)

    # Load gdi32.dll
    gdi32 = ctypes.WinDLL("gdi32")

    # Load user32.dll
    user32 = ctypes.WinDLL("user32")

    # Get device context
    hdc = user32.GetDC(None)

    # Prepare LOGFONT
    lf = LOGFONT()
    lf.lfCharSet = 1  # DEFAULT_CHARSET

    # Prepare list to store font names
    fonts = []

    # Enumerate fonts
    gdi32.EnumFontFamiliesExW(hdc, ctypes.byref(lf), EnumFontFamiliesExProc, 0, 0)

    # Release device context
    user32.ReleaseDC(None, hdc)

    return fonts


def generate_text_clip(text, duration):
    #return TextClip(text, fontsize=50, color='white', bg_color='black').set_duration(duration)
    selected_font = font_choice.currentText()
    if selected_font != None and selected_font != "":
        return TextClip(text, fontsize=50, color='grey', font=f"{selected_font}", bg_color="black").set_duration(duration)
    else:
        return TextClip(text, fontsize=50, color='grey', font="8514OEM", bg_color="black").set_duration(duration)

def ollama_init():
    if ollama_con() != 0:
        ollama_activate = True
    else:
        ollama_activate = False
def ollama_con():
    """Check if Ollama is running, checks with the default port for ollama, or 11434"""
    #messagebox.showerror("RedditReader Nightly Feature error", "Ollama is currently disabled, the UI infastructure is in place, however the 'backend' is currently not present. sorry for any inconvenience.")
    try:
        ollama = requests.get("http://localhost:11434/")
    except requests.exceptions.ConnectionError  or ConnectionRefusedError:
        messagebox.showerror("RedditReader ERROR", "Ollama is not running. Please start Ollama before continuing. (ERROR: localhost:11434 connection refused, this may be due to a mismaped port, OR Ollama is not running.)")
        return 0
    if ollama.status_code != 200:
        return 0
    else:
        if ollama.text.lower() != "ollama is running": #if not result isn't expected
            return 0
        else:
            olm_models = requests.get("http://localhost:11434/api/tags").json() #list of models
            olm_models = olm_models["models"]


def ollama_list():
    olm_models = requests.get("http://localhost:11434/api/tags").json() #list of models
    olm_models = olm_models["models"]


def query_ollama(query, model="llama3.2"):    
    response: ChatResponse = chat(model=model, messages=[
    {
        'role': 'user',
        'content': query,
    },
    ]) 
    return response['message']['content']

def stream_query_ollama(query, model="llama3.2"):
    stream = chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': 'Why is the sky blue?'}],
        stream=True,
    )
    for chunk in stream:
        return chunk['message']['content']

def get_assets():
    assets_hardcoded = ["https://raw.githubusercontent.com/aghastmuffin/reddit-reader/refs/heads/main/production/assets/youtube.png", "https://raw.githubusercontent.com/aghastmuffin/reddit-reader/refs/heads/main/production/assets/Logov2.png", "https://raw.githubusercontent.com/aghastmuffin/reddit-reader/refs/heads/main/production/assets/full_logo.png", "https://raw.githubusercontent.com/aghastmuffin/reddit-reader/refs/heads/main/production/assets/instagram.png", "https://raw.githubusercontent.com/aghastmuffin/reddit-reader/refs/heads/main/production/assets/tiktok_icon.png"]
    if not os.path.exists("assets"):
        os.makedirs("assets")
    logging.log(logging.INFO, "Downloading assets...")
    for url in assets_hardcoded:
        response = requests.get(url)
        if response.status_code == 200:
            save_path = os.path.join("assets", url.split("/")[-1]) #essientially save to current dir + assets + url.split("/")[len(url.split("/"))-1], considerably more efficent, though
            with open(save_path, 'wb') as file:
                file.write(response.content)
            print(f"Image successfully downloaded: {save_path}")
        else:
            print(f"Failed to download image. Status code: {response.status_code}")
    logging.log(logging.INFO, "function complete.")
    messagebox.showinfo("RedditReader Assets Downloaded", "The assets have been downloaded. These images will be used when the program restarts.")
def is_daemon():
    # Check if the process has a controlling terminal
    if os.getppid() == 1 or not sys.stdout.isatty():
        return True
    return False

def changevidsource(source:str):
    globaled = ["file_vid", "starttime", "endtime", "starttimelabel", "endtimelabel", "video_dur"]
    global video_dur
    for var in globaled:
        exec(f"global {var}")
    if source == "yt":
        if yt_url.text() != "":
            filechose.setEnabled(False)
    elif source == "file":
        if file_vid != "":
            yt_url.setEnabled(False)

    video_dur = int(getvideo_duration(source))
    starttime.setEnabled(True)
    endtime.setEnabled(True)
    starttime.setMaximum(video_dur)
    endtime.setMaximum(video_dur)
    updatestarttime() #call to populate endtime min
    starttime.valueChanged.connect(updatestarttime)
    endtime.valueChanged.connect(updateendtime)
def get_video_duration_ffmpeg(file_vid):
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        file_vid
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    duration = json.loads(result.stdout)['format']['duration']
    
    return float(duration)

def getvideo_duration(source):
    globaled = ["file_vid", "starttime", "endtime", "starttimelabel", "endtimelabel"]
    for var in globaled:
        exec(f"global {var}")

    if source == "yt":
        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(yt_url.text(), download=False)
            duration = info_dict.get('duration', None)  # Duration in seconds
            return duration
    elif source == "file":
        return get_video_duration_ffmpeg(file_vid)
    else:
        print('unexpected media type::could not get duration')
def updatestarttime():
    globaled = ["file_vid", "starttime", "endtime", "starttimelabel", "endtimelabel", "video_dur"]
    for var in globaled:
        exec(f"global {var}")
    global video_dur

    starttimelabel.setText(f"Start at ({starttime.value()}): ")
    endtimelabel.setText(f"End at ({endtime.value()}): ")
    if starttime.value() < video_dur:
        endtime.setMinimum(int(starttime.value() + 1))
    else:
        endtime.setMinimum(int(starttime.value()))

def updateendtime():
    globaled = ["file_vid", "starttime", "endtime", "starttimelabel", "endtimelabel"]
    for var in globaled:
        exec(f"global {var}")
    endtimelabel.setText(f"End at ({endtime.value()}): ")


def setcodec(codec):
    global a_accelerator
    #a_accelerator = codec_pick.currentText()
    a_accelerator = codec
    print("Succesfully changed accelerator: ", a_accelerator)

def updatesettings(codec, v_codec1, cheaders, csaveas, cgpu_num, cfps):
    global headers, saveas, gpu_num, fps, v_codec
    
    if cheaders:
        headers = dict(cheaders)
        print("Succesfully changed headers:", headers)
    if csaveas:
        saveas = str(csaveas)
        print("Succesfully changed saveas:", saveas)
    if cgpu_num:
        gpu_num = int(cgpu_num)
        print("Succesfully changed gpunum:", gpu_num)
    if v_codec1:
        v_codec = str(v_codec1)
        print("Succesfully changed v_codec:", v_codec)
    if cfps > 60:
        messagebox.showwarning("Reddit Reader WARN", "FPS being higher than 60 can result in VERY LONG compile times, extreme usage, and large video sizes, before starting the program, please confirm that these are the fps settings you'd like to procede with!")
        return
    fps = int(cfps)
    if codec:
        setcodec(codec)

    

def advancedwin():
    window.setWindowTitle('little itsy bitsy Reddit Reader')
    adv = QDialog()
    adv.setWindowTitle("RedditReader Advanced Settings")
    adv.setGeometry(100, 100, 200, 200)
    layout = QVBoxLayout()
    info = QLabel(f"VERSION: {VER}\nBUILD: {BUILD}\nStatus: {STATUS}")
    ollama = QCheckBox("Enable Ollama (AI)")
    beta_videotiming = QCheckBox("Enable start/stop video timings")
    beta_videotiming.setCheckState(Qt.CheckState.Checked)
    ok = QPushButton("Save Changes (TextBox Only)")
    report = QPushButton("Report an Error")
    #codec_pick = QComboBox()
    #codecs = [c.split()[-1] for c in subprocess.Popen(['ffmpeg', '-codecs'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0].decode('utf-8').split("\n") if c.strip()] 
    #codec_pick.addItems(codecs)
    #codec_pick.currentIndexChanged.connect(lambda: setcodec(codec_pick))
    l_codec_pick = QLabel("(A) Codec:")
    codec_pick = QLineEdit()
    l_vcodec_pick = QLabel("(V) Codec:")
    vcodec_pick = QLineEdit()
    l_cheaders = QLabel("Headers:")
    cheaders = QLineEdit()
    l_csaveas = QLabel("Save As:")
    csaveas = QLineEdit()
    l_cgpu_num = QLabel("GPU Number:")
    cgpu_num = QSpinBox()
    l_cfps = QLabel("FPS:")
    cfps = QSpinBox()
    cgpu_num.setRange(0, 100)
    cfps.setRange(1, 1000)
    codec_pick.setPlaceholderText(a_accelerator)
    vcodec_pick.setPlaceholderText(v_codec)
    cheaders.setPlaceholderText(str(headers)) 
    csaveas.setPlaceholderText(saveas)
    cgpu_num.setValue(gpu_num)
    cfps.setValue(fps)
    if UIMG == 0:
        getasset = QPushButton("Assets Missing!! Click to download.")
        getasset.clicked.connect(get_assets)
    else:
        getasset = QPushButton("Looks like you have the required assets!")
        getasset.setDisabled(True)
    ok.clicked.connect(lambda: (updatesettings(codec_pick.text(), vcodec_pick.text(), cheaders.text(), csaveas.text(), cgpu_num.value(), cfps.value()), adv.close()))
    report.clicked.connect(adv.close)
    report.clicked.connect(reperr)
    ollama.clicked.connect(ollama_init)
    beta_videotiming.stateChanged.connect(on_beta_videotiming_checked)
    #diagbar
    layout.addWidget(info)
    #settings
    layout.addWidget(ollama)
    layout.addWidget(beta_videotiming)
    layout.addWidget(l_codec_pick)
    layout.addWidget(codec_pick)
    layout.addWidget(l_vcodec_pick)
    layout.addWidget(vcodec_pick)
    layout.addWidget(l_cheaders)
    layout.addWidget(cheaders)
    layout.addWidget(l_csaveas)
    layout.addWidget(csaveas)
    layout.addWidget(l_cgpu_num)
    layout.addWidget(cgpu_num)
    layout.addWidget(l_cfps)
    layout.addWidget(cfps)
    if UIMG == 0:
        layout.addWidget(getasset)
    #bottombar
    layout.addWidget(report)
    layout.addWidget(ok)


    adv.setLayout(layout)
    adv.exec()
    window.setWindowTitle('Reddit Reader (UNPAID)')

def on_beta_videotiming_checked(state):
    global setcustomtimings
    if state == 2: #for whatever reason, the function is getting an INT, not a Qt.CheckState, so update Qt.CheckState.Checked to 2
        logging.log(logging.INFO, "Beta Video Timing Shown")
        starttime.show()
        endtime.show()
        setcustomtimings = True
    else:
        logging.log(logging.INFO, "Beta Video Timing Hidden")
        starttime.hide()
        endtime.hide()
        setcustomtimings = False 
            

class Word:
    ''' A class representing a word from the JSON format for vosk speech recognition API '''

    def __init__(self, dict):
        '''
        Parameters:
          dict (dict) dictionary from JSON, containing:
            conf (float): degree of confidence, from 0 to 1
            end (float): end time of the pronouncing the word, in seconds
            start (float): start time of the pronouncing the word, in seconds
            word (str): recognized word
        '''

        self.conf = dict["conf"]
        self.end = dict["end"]
        self.start = dict["start"]
        self.word = dict["word"]

    def to_string(self):
        ''' Returns a string describing this instance '''
        return "{:20} from {:.2f} sec to {:.2f} sec, confidence is {:.2f}%".format(
            self.word, self.start, self.end, self.conf*100)
    def times(self):
        ''' Returns a tuple with start and end times '''
        return (self.start, self.end)
    def word(self):
        ''' Returns the recognized word '''
        return self.word
    def all(self):
        return self.word, self.start, self.end, self.conf*100

def filechoose():
    global file_vid
    global reset_file
    file_vid, _ = QFileDialog.getOpenFileName(window, "Select Video File", "", "Video Files (*.mp4)")
    if file_vid:
        filechose.setText("File Chosen")
        filechose.setEnabled(False)
        reset_file = QPushButton("Slect a different file")
        reset_file.clicked.connect(reset_filechoose)
        layout.insertRow(layout.rowCount() - 5, reset_file)  # Insert reset_button before the last row (start button)
        changevidsource("file")

def reperr():
    dlg = QDialog()
    dlg.setWindowTitle("Report an Error!")
    dlg.setGeometry(100, 100, 1, 1)
    layout = QVBoxLayout()
    label = QLabel("If you have encountered an error, please report it on the github page. \nYou can do this by making a Github Account, then pressing \nNew Issue on the link you will be brought to \nafter pressing X to close this window and continue,\nor pressing OK.")
    ok = QPushButton("OK")
    ok.clicked.connect(dlg.close)
    layout.addWidget(label)
    layout.addWidget(ok)
    dlg.setLayout(layout)
    dlg.exec()

    webbrowser.open("https://github.com/aghastmuffin/reddit-reader/issues")
    

def reset_filechoose():
    global file_vid
    global reset_file
    filechose.setText("Select File")
    filechose.setEnabled(True)
    layout.removeRow(reset_file)
    file_vid = None
    starttime.setDisabled(True)
    endtime.setDisabled(True)


def valid_chk():
    global file_vid
    global setcustomtimings #responsible for the config window to communicate to this function
    if reddit_url.text() == "" or not (reddit_url.text().startswith("https://reddit.com") or reddit_url.text().startswith("https://www.reddit.com")):
        messagebox.showerror("Reddit Reader ERROR", "Naming Schema: Please enter a valid Reddit URL, starting with https://reddit.com")
        return
    if len(yt_url.text()) < 1 and 'file_vid' not in globals():
        messagebox.showerror("Reddit Reader ERROR", "Naming Schema: Please enter either a Youtube URL or select a file, not both.")
        return
    if yt_url.text() != "" and (yt_url.text().startswith("https://youtube.com") or yt_url.text().startswith("https://www.youtube.com")):
        file_vid = yt_url.text()
        print("set ytdwnload to true because", "yt_url.text() is: '" + yt_url.text() + "'")
        yt_download = True
    elif yt_url.text() == "":
        yt_download = False
    else:
        messagebox.showerror("Reddit Reader ERROR", "Naming Schema: Please enter a valid Youtube URL, starting with https://youtube.com, or provide a valid file.")
        return
    url = requests.get(f"{reddit_url.text()}.json", headers=headers) #replace with reddit_url.text()
    if url.status_code == 200: #success
        tts = pyttsx3.init()
        story = str(url.json()[0]['data']['children'][0]['data']['selftext'])
        #query ollama to provide a written response of the reddit post
        if ollama_activate:
            commentary = query_ollama("You are a narrator (that reads reddit) respond to the following reddit post, remember to introduce yourself, however the story has already been read, you are respond to it, so just be like I thought/Wow this is... : " + story)
            tts.save_to_file(f"{url.json()[0]['data']['children'][0]['data']['selftext']} {commentary}", "voiceover.mp3") #potentially see if I can store this content in a variable, not a file.
        else:
            tts.save_to_file(f"{url.json()[0]['data']['children'][0]['data']['selftext']}", "voiceover.mp3")
        tts.runAndWait()
    else:
        print(url.status_code)
        print("^ Unexpected Code from reddit.com")
        if url.status_code.starttswith("4") or url.status_code.starttswith("5"): #client or server error
            print("You may have been banned from reddit.com. Please try again later. Or you entered a malformed URL.")
        sys.exit()
    #handle the downloading of the youtube video
    print(yt_download)
    if yt_download:
        yt_url1 = yt_url.text()
        ydl_opts = {
            'outtmpl': 'output' #webm
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(yt_url1)
            subprocess.Popen(f"ffmpeg -i output.webm -c:v {v_codec} -c:a aac output.mp4")
            videoclip = VideoFileClip("output.mp4")
    else:
        if setcustomtimings:
            fullvideoclip = VideoFileClip(file_vid) #this is defined as EITHER the youtube OR file location (set when file selected)
            videoclip = fullvideoclip.subclip(starttime.value(), endtime.value())
        else:
            videoclip = VideoFileClip(file_vid)
    if videoclip is None:
        logging.log(logging.ERROR, "videoclip is None")
    #concatenate the video clips
    audioclip = AudioFileClip("voiceover.mp3")
    if videoclip is not None and audioclip is not None:
        vdur = videoclip.duration
        adur = audioclip.duration
        print(vdur, adur)
    """if vdur == adur or vdur+5 == adur: #why 
        new_audioclip = CompositeAudioClip([audioclip])
        videoclip.audio = new_audioclip
        #videoclip.write_videofile("pvideo.mp4")"""
    if vdur >= adur:
        #audioclip = CompositeAudioClip([audioclip, audioclip.subclip(adur - 1)])
        new_audioclip = CompositeAudioClip([audioclip])
        videoclip.audio = new_audioclip
        #videoclip.write_videofile("pvideo.mp4")
    os.system("ffmpeg -y -i voiceover.mp3 -ac 1 -ar 22050 voiceover.wav")
    audio_filename = "voiceover.wav"
    custom_Word = Word
    model = Model(lang="en-us")
    wf = wave.open(audio_filename, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)

    results = []
    # recognize speech using vosk model
    while True:
        import json  # python for some reason doesn't recognize that this was previously imported. Glitch.
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            part_result = json.loads(rec.Result())
            results.append(part_result)
    part_result = json.loads(rec.FinalResult())
    results.append(part_result)
    list_of_Words = []
    for sentence in results:
        if len(sentence) == 1:
            # sometimes there are bugs in recognition 
            # and it returns an empty dictionary
            # {'text': ''}
            continue
        for obj in sentence['result']:
            w = custom_Word(obj)  # create custom Word object
            list_of_Words.append(w)  # and add it to list
    maindict = {}
    wf.close()  # close audiofile
    from collections import OrderedDict
    import json
    list_of_Words = []
    for sentence in results:
        if len(sentence) == 1:
            continue
        for obj in sentence['result']:
            w = custom_Word(obj)  # create custom Word object
            list_of_Words.append(w)  # and add it to list

    wf.close()  # close audiofile
    timestamped = []
    """
    with open('timestamped.txt', 'w') as f:
        for word in list_of_Words:
            theword = word.all()
            # f.write(', '.join(map(str, theword)))
            f.write(f"{theword[0]},{theword[1]},{theword[2]}")
            f.write('\n')
        f.close()
    """
    for word in list_of_Words:
        theword = word.all()
        timestamped.append(f"{theword[0]}, {theword[1]}, {theword[2]}")
    #start 3

    # Define the text and its timings
    text_clips = []

    for line in timestamped:
        try:
            lsplit = line.split(",")
            word = str(lsplit[0])
            stime = float(lsplit[1])
            etime = float(lsplit[2])
            text_clips.append({"text": word, "start": stime, "end": etime})
        except IndexError:
            pass
        except:
            print("unexpected error")
            pass
    clips = []
    last_end = 0

    # Group the words into chunks of 4
    for i in range(0, len(text_clips) - 3, 4):
        clip1 = text_clips[i]
        clip2 = text_clips[i + 1]
        clip3 = text_clips[i + 2]
        clip4 = text_clips[i + 3]

        # Combine the words and timings
        combined_text = " ".join([clip1["text"], clip2["text"], clip3["text"], clip4["text"]])
        combined_start = clip1["start"]
        combined_end = clip4["end"]

        # Cut the videoclip into a small clip
        try:
            video_clip = videoclip.subclip(last_end, combined_end)
        except ValueError:
            messagebox.showerror("Reddit Reader ERROR", f"The video you've selected (clip or general videosize) is too short to fit the voiceover, please select a new one or extend the clip length, and press start again to restart the process. {last_end}, {combined_end}")
            return
        last_end = combined_end

        # Generate the text clip
        text_clip = generate_text_clip(combined_text, combined_end - combined_start)
        text_clip = text_clip.set_start(0).set_position('center')

        # Add the text to the videoclip clip
        video_clip_with_text =  CompositeVideoClip([video_clip, text_clip])

        clips.append(video_clip_with_text)

    # Concatenate the clips back together
    videoclip_with_text = concatenate_videoclips(clips)

    # Write the videoclip to a file
    if not os.path.exists("finalvideoclip.mp4"):
        videoclip_with_text.write_videofile("finalvideoclip.mp4", codec=f'{v_codec}', fps=fps, ffmpeg_params=["-gpu", f"{gpu_num}"])
    else:
        from tkinter import simpledialog
        new_f_name = simpledialog.askstring("File Exists Error", "The default name of finalvideoclip.mp4 already exists. Please provide an alternate name, including .mp4 at the end. Press ok when done.")
        if new_f_name != None and new_f_name != "" and not os.path.exists(new_f_name):
            videoclip_with_text.write_videofile(f"{new_f_name}", codec=f'{v_codec}', fps=fps, ffmpeg_params=["-gpu", f"{gpu_num}"])
        else:
            while True:
                new_f_name = simpledialog.askstring("File Exists Error", f"The default name of {new_f_name}.mp4 already exists. Please provide an alternate name, including .mp4 at the end. Press ok when done.")
                if new_f_name != None and new_f_name != "" and not os.path.exists(new_f_name):
                    videoclip_with_text.write_videofile(f"{new_f_name}", codec=f'{a_accelerator}', fps=fps, ffmpeg_params=["-gpu", f"{gpu_num}"])
                    break

setpythonashost()
app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle('Reddit Reader (UNPAID)')
window.setGeometry(100, 100, 280, 320)
font_types = getfont()
UIMG = 0
if os.path.exists("assets"):
    UIMG = 1
    logo_pathf = os.path.join(os.path.dirname(__file__), "assets", "full_logo.png")
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "Logov2.png")
    pixmap_unc = QPixmap(logo_pathf)
    logo = QLabel()
    pixmap_unc = pixmap_unc.scaled(window.width(), 100, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)  # 1 is Qt.AspectRatioMode.KeepAspectRatio
    logo.setPixmap(pixmap_unc)
else:
    if messagebox.askokcancel("RedditReader Assets Missing", "The assets folder is missing. Please ensure the assets folder is in the same directory as this program. The program will still proceede with execution, however it may be glitchy due to the aforementioned bug."):
        threading.Thread(target=get_assets).start()

setcustomtimings = True
layout = QFormLayout()
# Add widgets to the layout
reddit_url = QLineEdit()
font_choice = QComboBox()
font_choice.addItems(font_types)
yt_url = QLineEdit()
filechose = QPushButton("Select File")
starttime = QSlider(Qt.Orientation.Horizontal)
starttime.setDisabled(True)
endtime = QSlider(Qt.Orientation.Horizontal)
endtime.setDisabled(True)
endtime_minimum = 0
advanced = QPushButton("Config")
start = QPushButton("Start Video Generation")
ollama = QCheckBox("Connect")
infostart = QLabel("Set Custom start/end Timings")
starttimelabel = QLabel("Start at (Nodata): ")
endtimelabel = QLabel("End at (Nodata): ")
#layout.setVerticalSpacing(20)
if UIMG == 1:
    layout.addRow(logo)
layout.addRow("Reddit URL:", reddit_url)
layout.addRow("Font:", font_choice)
layout.addRow("Youtube URL:", yt_url)
layout.addRow("Select your own .mp4", filechose)
layout.addRow("Advanced Settings", advanced)
layout.addRow(infostart)
layout.addRow(starttimelabel, starttime)
layout.addRow(endtimelabel, endtime)
layout.addRow(start)
window.setLayout(layout)
#add signals/callbacks to onchange functions
filechose.clicked.connect(filechoose)
advanced.clicked.connect(advancedwin)
#yt_url.textChanged.connect(lambda: filechose.setEnabled(False))
yt_url.textChanged.connect(partial(changevidsource, "yt"))
#start.clicked.connect(valid_chk)
start.clicked.connect(lambda: threading.Thread(valid_chk()).start())

if UIMG == 1:
    window.setWindowIcon(QIcon(logo_path))
    app.setWindowIcon(QIcon(logo_path))
window.show()
sys.exit(app.exec())
