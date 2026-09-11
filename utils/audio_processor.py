# import yt_dlp
# from pydub import AudioSegment
# import os

# DOWNLOAD_DIR = "downloads"
# os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# def download_youtube_audio(url: str) -> str:
#     output_path = os.path.join(
#         DOWNLOAD_DIR,
#         "%(title)s.%(ext)s"
#     )

#     ydl_opts = {
#         "format": "bestaudio/best",

#         "outtmpl": output_path,

#         "extractor_args": {
#             "youtube": {
#                 "player_client": ["mweb"]
#             },
#             "youtubepot-bgutilscript": {
#                 "script_path": os.path.expanduser(
#                     "~/bgutil-ytdlp-pot-provider/server/build/generate_once.js"
#                 )
#             }
#         },

#         "postprocessors": [
#             {
#                 "key": "FFmpegExtractAudio",
#                 "preferredcodec": "wav",
#                 "preferredquality": "192",
#             }
#         ],

#         "quiet": False,
#         "no_warnings": False,
#     }

#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(url, download=True)

#         filename = (
#             ydl.prepare_filename(info)
#             .replace(".webm", ".wav")
#             .replace(".m4a", ".wav")
#         )

#     return filename

# def convert_to_wav(input_path: str) -> str:
#     """Convert any audio/video file to WAV format using pydub."""
#     output_path = os.path.splitext(input_path)[0] + "_converted.wav"
#     audio = AudioSegment.from_file(input_path)
#     audio = audio.set_channels(1).set_frame_rate(16000) #16khz
#     audio.export(output_path, format="wav")
#     return output_path

# def chunk_audio(wav_path: str, chunk_minutes: int=10) -> list:
#     audio = AudioSegment.from_wav(wav_path)
#     chunk_ms = chunk_minutes * 60 * 1000
    
#     chunks=[]
    
#     for i , start in enumerate(range(0,len(audio), chunk_ms)):
#         chunk = audio[start: start + chunk_ms]
#         chunk_path = f"{wav_path}_chunk_{i}.wav"
#         chunk.export(chunk_path, format="wav")
        
#         chunks.append(chunk_path)
#     return chunks

# def process_input(source: str) -> list:
#     if source.startswith("http://") or source.startswith("https://"):
#         print("Detected YouTube URL. Downloading audio...")
#         wav_path = download_youtube_audio(source)
#     else:
#         print("Detected local file. Converting to WAV...")
#         wav_path = convert_to_wav(source)

#     print("Chunking audio...")
#     chunks = chunk_audio(wav_path)
#     print(f"Audio ready — {len(chunks)} chunk(s) created.")
#     return chunks

import os
import subprocess
import time
from pathlib import Path

import requests
import yt_dlp
from pydub import AudioSegment


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# BgUtils PO-token provider
BGUTIL_VERSION = "2.0.0"
BGUTIL_DIR = Path.home() / "bgutil-ytdlp-pot-provider"
BGUTIL_SERVER_DIR = BGUTIL_DIR / "server"
BGUTIL_URL = "http://127.0.0.1:4416"

_bgutil_process = None


def start_bgutil_server():
    """
    Install/build/start the BgUtils PO-token HTTP server if it
    is not already running.

    Uses Node.js. No Deno is required.
    """

    global _bgutil_process

    # ---------------------------------------------------------
    # 1. Check whether the server is already running
    # ---------------------------------------------------------
    try:
        response = requests.get(
            f"{BGUTIL_URL}/",
            timeout=2
        )

        if response.status_code < 500:
            print("BgUtils PO-token server is already running.")
            return

    except requests.RequestException:
        pass

    # ---------------------------------------------------------
    # 2. Clone BgUtils if it isn't present
    # ---------------------------------------------------------
    if not BGUTIL_SERVER_DIR.exists():

        print("Installing BgUtils PO-token provider...")

        subprocess.run(
            [
                "git",
                "clone",
                "--single-branch",
                "--branch",
                BGUTIL_VERSION,
                "https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git",
                str(BGUTIL_DIR),
            ],
            check=True,
        )

    # ---------------------------------------------------------
    # 3. Install Node dependencies
    # ---------------------------------------------------------
    package_json = BGUTIL_SERVER_DIR / "package.json"
    node_modules = BGUTIL_SERVER_DIR / "node_modules"

    if package_json.exists() and not node_modules.exists():

        print("Installing BgUtils Node dependencies...")

        subprocess.run(
            ["npm", "ci"],
            cwd=str(BGUTIL_SERVER_DIR),
            check=True,
        )

    # ---------------------------------------------------------
    # 4. Build TypeScript server
    # ---------------------------------------------------------
    build_file = BGUTIL_SERVER_DIR / "build" / "main.js"

    if not build_file.exists():

        print("Building BgUtils PO-token server...")

        subprocess.run(
            ["npx", "tsc"],
            cwd=str(BGUTIL_SERVER_DIR),
            check=True,
        )

    # ---------------------------------------------------------
    # 5. Start HTTP server
    # ---------------------------------------------------------
    print("Starting BgUtils PO-token server...")

    _bgutil_process = subprocess.Popen(
        [
            "node",
            "build/main.js",
            "--host",
            "127.0.0.1",
            "--port",
            "4416",
        ],
        cwd=str(BGUTIL_SERVER_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # ---------------------------------------------------------
    # 6. Wait until server becomes available
    # ---------------------------------------------------------
    for _ in range(30):

        try:
            response = requests.get(
                f"{BGUTIL_URL}/",
                timeout=2
            )

            if response.status_code < 500:
                print("BgUtils PO-token server started successfully.")
                return

        except requests.RequestException:
            pass

        time.sleep(1)

    raise RuntimeError(
        "BgUtils PO-token server failed to start."
    )


def download_youtube_audio(url: str) -> str:
    import tempfile
    import streamlit as st

    cookie_file = None

    try:
        # Get YouTube cookies from Streamlit Secrets
        cookies = st.secrets.get("YOUTUBE_COOKIES")

        if not cookies:
            raise RuntimeError(
                "YOUTUBE_COOKIES is not configured in Streamlit Secrets."
            )

        # Create temporary cookies.txt
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8"
        ) as f:
            f.write(cookies)
            cookie_file = f.name

        output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,

            # YouTube authentication
            "cookiefile": cookie_file,

            # JavaScript challenge solving
            "js_runtimes": {
                "node": {}
            },

            # Download EJS challenge solver from GitHub
            "remote_components": {
                "ejs": ["github"]
            },

            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }],

            "quiet": False,
            "no_warnings": False,
            "retries": 3,
            "fragment_retries": 3,
        }

        print("Downloading YouTube audio...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        filename = (
            filename
            .replace(".webm", ".wav")
            .replace(".m4a", ".wav")
            .replace(".mp4", ".wav")
        )

        if not os.path.exists(filename):
            raise FileNotFoundError(
                f"Downloaded WAV file was not found: {filename}"
            )

        print(f"YouTube audio downloaded: {filename}")

        return filename

    finally:
        # Delete temporary cookie file
        if cookie_file and os.path.exists(cookie_file):
            os.remove(cookie_file)


def convert_to_wav(input_path: str) -> str:
    """
    Convert any audio/video file to mono 16-kHz WAV.
    """

    output_path = (
        os.path.splitext(input_path)[0]
        + "_converted.wav"
    )

    print("Converting input file to WAV...")

    audio = AudioSegment.from_file(input_path)

    audio = (
        audio
        .set_channels(1)
        .set_frame_rate(16000)
    )

    audio.export(
        output_path,
        format="wav"
    )

    return output_path


def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10
) -> list:
    """
    Split WAV audio into chunks.
    """

    print("Chunking audio...")

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = chunk_minutes * 60 * 1000

    chunks = []

    for i, start in enumerate(
        range(0, len(audio), chunk_ms)
    ):

        chunk = audio[
            start:start + chunk_ms
        ]

        chunk_path = (
            f"{wav_path}_chunk_{i}.wav"
        )

        chunk.export(
            chunk_path,
            format="wav"
        )

        chunks.append(chunk_path)

    print(
        f"Audio ready — {len(chunks)} chunk(s) created."
    )

    return chunks


def process_input(source: str) -> list:
    """
    Process either a YouTube URL or a local file.
    """

    if (
        source.startswith("http://")
        or source.startswith("https://")
    ):

        print(
            "Detected YouTube URL."
        )

        wav_path = download_youtube_audio(
            source
        )

    else:

        print(
            "Detected local file."
        )

        wav_path = convert_to_wav(
            source
        )

    return chunk_audio(wav_path)