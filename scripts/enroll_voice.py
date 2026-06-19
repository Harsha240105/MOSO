"""
MOSO Voice Enrollment - Record voice samples for speaker verification.

Usage:
    python -m scripts.enroll_voice [--name owner] [--samples 3]

This script records your voice and creates a speaker profile
stored at ~/.moso/speakers/<name>.json
"""

import argparse
import logging
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("enroll_voice")


def parse_args():
    parser = argparse.ArgumentParser(description="MOSO Voice Enrollment")
    parser.add_argument("--name", default="owner", help="Speaker profile name (default: owner)")
    parser.add_argument("--samples", type=int, default=3,
                        help="Number of voice samples (default: 3, max: 5)")
    parser.add_argument("--duration", type=float, default=3.0,
                        help="Seconds per sample (default: 3.0)")
    parser.add_argument("--list", action="store_true", help="List enrolled profiles")
    parser.add_argument("--delete", type=str, default=None,
                        help="Delete an enrolled profile by name")
    return parser.parse_args()


def list_profiles():
    from moso_core.voice.speaker import SpeakerStore
    store = SpeakerStore()
    profiles = store.list_profiles()
    if not profiles:
        print("No enrolled speaker profiles found.")
    else:
        print("Enrolled speaker profiles:")
        for name in profiles:
            print(f"  - {name}")
    return profiles


def delete_profile(name: str):
    from moso_core.voice.speaker import SpeakerStore
    store = SpeakerStore()
    if store.delete_profile(name):
        print(f"Deleted profile: {name}")
    else:
        print(f"Profile not found: {name}")


def record_samples(
    num_samples: int,
    duration_per_sample: float,
    sample_rate: int = 16000,
) -> list:
    import numpy as np
    from moso_core.voice.input import AudioStream, AudioConfig

    config = AudioConfig(
        sample_rate=sample_rate,
        silence_duration_ms=int(duration_per_sample * 1000),
    )
    stream = AudioStream(config)
    stream.start()

    samples = []

    print(f"\n=== MOSO Voice Enrollment ===")
    print(f"Profile: {args.name}")
    print(f"Samples: {num_samples} x {duration_per_sample}s")
    print("\nSpeak clearly in a quiet environment.\n")

    try:
        for i in range(num_samples):
            input(f"Press Enter and speak sample {i + 1}/{num_samples}...")
            print("Recording...", end=" ", flush=True)

            chunks = []
            start_time = time.time()
            while time.time() - start_time < duration_per_sample:
                chunk = stream.read_audio(timeout=0.5)
                if chunk is not None:
                    chunks.append(chunk)

            if chunks:
                combined = np.concatenate(chunks)
                samples.append(combined)
                print(f"Done ({len(combined) / sample_rate:.1f}s)")
            else:
                print("No audio detected. Try again.")
                i -= 1

    finally:
        stream.stop()

    return samples


if __name__ == "__main__":
    args = parse_args()

    if args.list:
        list_profiles()
        sys.exit(0)

    if args.delete:
        delete_profile(args.delete)
        sys.exit(0)

    num_samples = min(max(args.samples, 1), 5)
    samples = record_samples(num_samples, args.duration)

    if not samples:
        print("No samples recorded. Aborting.")
        sys.exit(1)

    from moso_core.voice.speaker import SpeakerEmbedder, SpeakerVerifier

    print("\nGenerating speaker embedding...")
    embedder = SpeakerEmbedder()
    embedder.load_model()

    verifier = SpeakerVerifier(embedder=embedder)
    profile = verifier.enroll(samples, name=args.name)

    print(f"\nEnrollment complete!")
    print(f"  Name: {profile.name}")
    print(f"  Samples: {profile.enrollment_samples}")
    print(f"  Threshold: {profile.threshold}")
    print(f"\nYou can now use 'run_voice.py' for owner-only voice mode.\n")
