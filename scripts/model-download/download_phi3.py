# MOSO AI Model Download Script

import argparse
import os
import requests

MODELS = {
    "phi-3-mini-4k-instruct-q4": {
        "url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf",
        "path": "models/llm/phi3/",
        "description": "Phi-3 Mini 3.8B - Q4 quantized GGUF",
    },
    "gemma-2b-it-q4": {
        "url": "https://huggingface.co/google/gemma-2b-it-gguf/resolve/main/gemma-2b-it-q4.gguf",
        "path": "models/llm/gemma/",
        "description": "Gemma 2B Instruct - Q4 quantized GGUF",
    },
}


def download_model(model_name: str):
    if model_name not in MODELS:
        print(f"Unknown model: {model_name}")
        print("Available models:")
        for name, info in MODELS.items():
            print(f"  {name}: {info['description']}")
        return

    info = MODELS[model_name]
    os.makedirs(info["path"], exist_ok=True)
    filepath = os.path.join(info["path"], os.path.basename(info["url"]))

    if os.path.exists(filepath):
        print(f"Model already exists at {filepath}")
        return

    print(f"Downloading {model_name}...")
    response = requests.get(info["url"], stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                percent = (downloaded / total_size) * 100
                print(f"\rProgress: {percent:.1f}% ({downloaded / 1e9:.2f}GB)", end="")

    print(f"\nDownloaded to {filepath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download MOSO AI models")
    parser.add_argument("--model", required=True, help="Model name to download")
    args = parser.parse_args()
    download_model(args.model)
