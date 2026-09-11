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
import base64
import tempfile
import subprocess
import tarfile
import urllib.request

import streamlit as st
import yt_dlp
from pydub import AudioSegment


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def get_node_binary() -> str:
    """
    Get a Node.js 22+ binary for yt-dlp.

    Streamlit Community Cloud may provide an older system Node.js
    version. Current yt-dlp EJS requires Node.js 22 or newer.

    This function downloads a portable Node.js 22 binary into the
    user's cache directory if it is not already available.
    """

    NODE_VERSION = "22.22.2"

    node_base_dir = os.path.join(
        os.path.expanduser("~"),
        ".cache",
        "nodejs"
    )

    node_dir = os.path.join(
        node_base_dir,
        f"node-v{NODE_VERSION}"
    )

    node_binary = os.path.join(
        node_dir,
        "bin",
        "node"
    )

    # ---------------------------------------------------------
    # 1. Check whether Node.js 22 is already installed
    # ---------------------------------------------------------

    if os.path.exists(node_binary):
        print("Using cached Node.js 22:")
        print("Node path:", node_binary)

        return node_binary

    # ---------------------------------------------------------
    # 2. Create cache directory
    # ---------------------------------------------------------

    os.makedirs(
        node_base_dir,
        exist_ok=True
    )

    # ---------------------------------------------------------
    # 3. Download Node.js 22
    # ---------------------------------------------------------

    archive_name = (
        f"node-v{NODE_VERSION}-linux-x64.tar.xz"
    )

    archive_path = os.path.join(
        tempfile.gettempdir(),
        archive_name
    )

    node_url = (
        f"https://nodejs.org/dist/v{NODE_VERSION}/"
        f"{archive_name}"
    )

    print(
        "Node.js 22 not found."
    )

    print(
        "Downloading Node.js 22..."
    )

    try:

        urllib.request.urlretrieve(
            node_url,
            archive_path
        )

    except Exception as e:

        raise RuntimeError(
            "Failed to download Node.js 22. "
            f"URL: {node_url}. "
            f"Error: {e}"
        ) from e

    # ---------------------------------------------------------
    # 4. Extract Node.js
    # ---------------------------------------------------------

    print(
        "Extracting Node.js 22..."
    )

    try:

        with tarfile.open(
            archive_path,
            mode="r:xz"
        ) as tar:

            tar.extractall(
                path=node_base_dir,
                filter="data"
            )

    except Exception as e:

        raise RuntimeError(
            "Failed to extract Node.js 22. "
            f"Error: {e}"
        ) from e

    finally:

        if os.path.exists(archive_path):

            os.remove(
                archive_path
            )

    # ---------------------------------------------------------
    # 5. Verify Node.js binary
    # ---------------------------------------------------------

    if not os.path.exists(node_binary):

        raise RuntimeError(
            "Node.js 22 installation completed, "
            "but the Node binary was not found at: "
            f"{node_binary}"
        )

    # ---------------------------------------------------------
    # 6. Check Node version
    # ---------------------------------------------------------

    node_result = subprocess.run(
        [
            node_binary,
            "--version"
        ],
        capture_output=True,
        text=True,
        check=True
    )

    print(
        "Node path:",
        node_binary
    )

    print(
        "Node version:",
        node_result.stdout.strip()
    )

    return node_binary


def download_youtube_audio(url: str) -> str:
    """
    Download audio from a YouTube URL.

    Uses:
    - YouTube cookies stored in Streamlit Secrets
    - Node.js 22 for JavaScript execution
    - yt-dlp EJS challenge solver from GitHub
    """

    cookie_file = None

    try:

        # =====================================================
        # 1. Get Node.js 22
        # =====================================================

        node_path = get_node_binary()

        # =====================================================
        # 2. Get YouTube cookies from Streamlit Secrets
        # =====================================================

        cookies_b64 = st.secrets.get(
            "YOUTUBE_COOKIES_B64"
        )

        if not cookies_b64:

            raise RuntimeError(
                "YOUTUBE_COOKIES_B64 is not configured "
                "in Streamlit Secrets."
            )

        # =====================================================
        # 3. Decode cookies
        # =====================================================

        try:

            cookie_bytes = base64.b64decode(
                cookies_b64,
                validate=True
            )

        except Exception as e:

            raise RuntimeError(
                "YOUTUBE_COOKIES_B64 is not valid Base64."
            ) from e

        # =====================================================
        # 4. Recreate original cookies.txt
        # =====================================================

        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".txt",
            delete=False
        ) as f:

            f.write(
                cookie_bytes
            )

            cookie_file = f.name

        print(
            "Cookie file:",
            cookie_file
        )

        print(
            "Cookie file exists:",
            os.path.exists(cookie_file)
        )

        print(
            "Cookie file size:",
            os.path.getsize(cookie_file)
        )

        # =====================================================
        # 5. Configure output
        # =====================================================

        output_path = os.path.join(
            DOWNLOAD_DIR,
            "%(title)s.%(ext)s"
        )

        # =====================================================
        # 6. Configure yt-dlp
        # =====================================================

        ydl_opts = {

            "format": "bestaudio/best",

            "outtmpl": output_path,

            # -------------------------------------------------
            # YouTube authentication
            # -------------------------------------------------

            "cookiefile": cookie_file,

            # -------------------------------------------------
            # JavaScript runtime
            # -------------------------------------------------

            "js_runtimes": {
                "node": {
                    "path": node_path
                }
            },

            # -------------------------------------------------
            # EJS challenge solver
            # -------------------------------------------------

            "remote_components": [
                "ejs:github"
            ],

            # -------------------------------------------------
            # Convert downloaded audio to WAV
            # -------------------------------------------------

            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],

            # -------------------------------------------------
            # Retry settings
            # -------------------------------------------------

            "retries": 3,

            "fragment_retries": 3,

            # -------------------------------------------------
            # Logging
            # -------------------------------------------------

            "quiet": False,

            "no_warnings": False,
        }

        # =====================================================
        # 7. Download
        # =====================================================

        print(
            "Downloading YouTube audio..."
        )

        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            filename = ydl.prepare_filename(
                info
            )

        # =====================================================
        # 8. Determine resulting WAV filename
        # =====================================================

        filename = (
            filename
            .replace(".webm", ".wav")
            .replace(".m4a", ".wav")
            .replace(".mp4", ".wav")
        )

        # =====================================================
        # 9. Verify download
        # =====================================================

        if not os.path.exists(filename):

            raise FileNotFoundError(
                "Downloaded WAV file was not found: "
                f"{filename}"
            )

        print(
            "YouTube audio downloaded:",
            filename
        )

        return filename

    finally:

        # =====================================================
        # 10. Delete temporary cookie file
        # =====================================================

        if (
            cookie_file
            and os.path.exists(cookie_file)
        ):

            os.remove(
                cookie_file
            )

            print(
                "Temporary cookie file removed."
            )


def convert_to_wav(
    input_path: str
) -> str:
    """
    Convert any audio/video file to
    mono 16-kHz WAV.
    """

    output_path = (
        os.path.splitext(input_path)[0]
        + "_converted.wav"
    )

    print(
        "Converting input to WAV..."
    )

    audio = AudioSegment.from_file(
        input_path
    )

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

    print(
        "Chunking audio..."
    )

    audio = AudioSegment.from_wav(
        wav_path
    )

    chunk_ms = (
        chunk_minutes
        * 60
        * 1000
    )

    chunks = []

    for i, start in enumerate(
        range(
            0,
            len(audio),
            chunk_ms
        )
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

        chunks.append(
            chunk_path
        )

    print(
        f"Audio ready — "
        f"{len(chunks)} chunk(s) created."
    )

    return chunks


def process_input(
    source: str
) -> list:
    """
    Process either a YouTube URL
    or a local audio/video file.
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

    return chunk_audio(
        wav_path
    )