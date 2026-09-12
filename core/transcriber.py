import torch
import whisper
import os
import numpy as np
import requests
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

# Sarvam's sync STT-translate API rejects audio longer than 30s.
# We slice each chunk into 25s pieces (with a 5s safety margin) before sending.
SARVAM_PIECE_SECONDS = 25


WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")


SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

_model = None


def load_model():
    global _model

    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"Loading Whisper model: {WHISPER_MODEL} on {device} ...")

        _model = whisper.load_model(
            WHISPER_MODEL,
            device=device
        )

        print("Whisper model loaded.")

    return _model


def transcribe_chunk_whisper(chunk_path: str) -> str:
    """
    Transcribe one WAV chunk using Whisper.
    Validates the audio file and decoded samples before transcription.
    """

    print(f"\nWhisper input file: {chunk_path}")

    if not os.path.exists(chunk_path):
        print(f"Skipping missing chunk: {chunk_path}")
        return ""

    try:
        file_size = os.path.getsize(chunk_path)
        print(f"Audio file size: {file_size} bytes")

        if file_size == 0:
            print(f"Skipping zero-byte audio chunk: {chunk_path}")
            return ""

        audio = AudioSegment.from_file(chunk_path)

    except Exception as e:
        print(f"Could not read audio file {chunk_path}: {e}")
        return ""

    print(
        f"Original audio: "
        f"{len(audio) / 1000:.2f}s | "
        f"Channels: {audio.channels} | "
        f"Frame rate: {audio.frame_rate} | "
        f"Sample width: {audio.sample_width}"
    )

    if len(audio) <= 0:
        print(f"Skipping empty audio chunk: {chunk_path}")
        return ""

    # Convert audio into Whisper-compatible format
    audio = (
        audio
        .set_channels(1)
        .set_sample_width(2)
        .set_frame_rate(16000)
    )

    samples = np.array(
        audio.get_array_of_samples(),
        dtype=np.int16
    )

    print(
        f"Processed audio: "
        f"{len(audio) / 1000:.2f}s | "
        f"Samples: {samples.size}"
    )

    if samples.size == 0:
        print(f"Skipping zero-sample audio chunk: {chunk_path}")
        return ""

    if not np.isfinite(samples).all():
        print(f"Skipping invalid audio samples: {chunk_path}")
        return ""

    # Convert int16 PCM samples to float32 in the range [-1, 1]
    audio_float32 = samples.astype(np.float32) / 32768.0

    if audio_float32.size == 0:
        print(f"Skipping empty float32 audio: {chunk_path}")
        return ""

    model = load_model()

    print("Sending audio to Whisper...")

    result = model.transcribe(
        audio_float32,
        task="transcribe",
        fp16=False
    )

    text = result.get("text", "").strip()

    print(f"Whisper result: {text[:100]}")

    return text


def _send_to_sarvam(piece_path: str) -> str:
    """Send one ≤30s WAV file to Sarvam and return the English transcript."""
    headers = {"api-subscription-key": SARVAM_API_KEY}

    with open(piece_path, "rb") as f:
        files = {"file": (os.path.basename(piece_path), f, "audio/wav")}
        data = {"model": SARVAM_MODEL, "with_diarization": "false"}
        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    if not response.ok:
        print(f"\n Sarvam returned {response.status_code}")
        print(f"Response body: {response.text}\n")
        response.raise_for_status()

    return response.json().get("transcript", "")


def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """
    Sarvam sync API only accepts ≤30s audio. We split this chunk into
    25-second pieces, send each separately, and join the transcripts.
    """
    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000

    full_text = ""
    total_pieces = (len(audio) + piece_ms - 1) // piece_ms

    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start: start + piece_ms]
        piece_path = f"{chunk_path}_sv_{i}.wav"
        piece.export(piece_path, format="wav")

        try:
            print(f"  → Sarvam piece {i + 1}/{total_pieces} ...")
            full_text += _send_to_sarvam(piece_path) + " "
        finally:
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return full_text.strip()


def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    Route one chunk to Whisper or Sarvam depending on language choice.
    - english  → Whisper (local model)
    - hinglish → Sarvam (translates to English while transcribing)
    """
    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path)
    return transcribe_chunk_whisper(chunk_path)


def transcribe_all(chunks: list, language: str = "english") -> str:
    full_transcript = ""

    engine = "Sarvam AI" if language.lower() == "hinglish" else "Whisper"
    print(f"Using {engine} for transcription.")

    for i, chunk in enumerate(chunks):  
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")

        try:
            text = transcribe_chunk(chunk, language=language)
        except Exception as e:
            print(f"Failed to transcribe chunk {chunk}: {e}")
            continue

        if text.strip():
            full_transcript += text.strip() + " "

        print("Transcription complete.")

    return full_transcript.strip()  