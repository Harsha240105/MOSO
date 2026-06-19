"""
MOSO Voice Models Downloader

Downloads the models needed for the voice pipeline:
- Whisper (STT) - Automatically downloaded by whisper library on first use
- Piper TTS voice models
- ECAPA-TDNN speaker verification model

Usage:
    python -m scripts.model-download.download_voice_models [--all] [--stt] [--tts] [--speaker]
"""

import argparse
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("download_voice_models")


MODELS_DIR = Path(os.path.join(os.path.expanduser("~"), ".moso", "models"))
SPEECH_DIR = MODELS_DIR / "speech"
TTS_DIR = SPEECH_DIR / "tts"
SPEAKER_DIR = MODELS_DIR / "speaker"


def parse_args():
    parser = argparse.ArgumentParser(description="Download MOSO voice models")
    parser.add_argument("--all", action="store_true", help="Download all voice models")
    parser.add_argument("--stt", action="store_true", help="Download Whisper STT model")
    parser.add_argument("--tts", action="store_true", help="Download Piper TTS model")
    parser.add_argument("--speaker", action="store_true", help="Download speaker verification model")
    parser.add_argument("--whisper-size", default="base",
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model size (default: base)")
    parser.add_argument("--tts-voice", default="en_US-lessac-medium",
                        help="Piper TTS voice (default: en_US-lessac-medium)")
    return parser.parse_args()


def download_whisper(model_size: str = "base"):
    logger.info("Downloading Whisper model '%s'...", model_size)
    try:
        import whisper
        model = whisper.load_model(model_size)
        logger.info("Whisper model '%s' loaded successfully", model_size)
        return True
    except Exception as e:
        logger.error("Failed to download Whisper model: %s", e)
        return False


def download_piper_tts(voice: str = "en_US-lessac-medium"):
    logger.info("Downloading Piper TTS voice '%s'...", voice)
    TTS_DIR.mkdir(parents=True, exist_ok=True)

    import urllib.request
    import json

    base_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/{voice}"
    voice_no_ext = voice.replace(".onnx", "")
    files = [
        (f"{voice_no_ext}.onnx", f"{base_url}/{voice_no_ext}.onnx"),
        (f"{voice_no_ext}.onnx.json", f"{base_url}/{voice_no_ext}.onnx.json"),
    ]

    success = True
    for filename, url in files:
        dest_path = TTS_DIR / filename
        if dest_path.exists():
            logger.info("  Already exists: %s", filename)
            continue
        logger.info("  Downloading %s...", filename)
        try:
            urllib.request.urlretrieve(url, dest_path)
            logger.info("  Downloaded: %s", filename)
        except Exception as e:
            logger.error("  Failed to download %s: %s", filename, e)
            success = False

    if success:
        logger.info("Piper TTS voice '%s' ready", voice)
    return success


def download_speaker_model():
    logger.info("Downloading speaker verification model...")
    SPEAKER_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from speechbrain.inference.speaker import SpeakerRecognition
        model = SpeakerRecognition.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir=str(SPEAKER_DIR),
        )
        logger.info("Speaker verification model downloaded")
        return True
    except Exception as e:
        logger.error("Failed to download speaker model: %s", e)
        return False


if __name__ == "__main__":
    args = parse_args()

    if not any([args.all, args.stt, args.tts, args.speaker]):
        args.all = True

    results = []

    if args.all or args.stt:
        results.append(("STT (Whisper)", download_whisper(args.whisper_size)))

    if args.all or args.tts:
        results.append(("TTS (Piper)", download_piper_tts(args.tts_voice)))

    if args.all or args.speaker:
        results.append(("Speaker (ECAPA-TDNN)", download_speaker_model()))

    print("\n=== Download Summary ===")
    all_ok = True
    for name, ok in results:
        status = "✓" if ok else "✗"
        print(f"  {status} {name}")
        all_ok = all_ok and ok

    if all_ok:
        print("\nAll voice models downloaded successfully!")
    else:
        print("\nSome downloads failed. Check logs above.")
        sys.exit(1)
