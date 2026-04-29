---
name: vibevoice
description: Microsoft open-source frontier Voice AI — ASR (speech-to-text) and TTS (text-to-speech). Handles 60-min audio, multilingual, speaker diarization.
---

# VibeVoice

Microsoft open-source frontier Voice AI from https://github.com/microsoft/VibeVoice (44k stars)

## Models

| Model | Description | Quick Try |
|-------|-------------|-----------|
| VibeVoice-ASR-7B | Speech-to-text, 60-min audio, speaker diarization | [Playground](https://aka.ms/vibevoice-asr) |
| VibeVoice-TTS-1.5B | Text-to-speech (disabled) | N/A |
| VibeVoice-Realtime-0.5B | Real-time streaming TTS | [Colab](https://colab.research.google.com/github/microsoft/VibeVoice/blob/main/demo/vibevoice_realtime_colab.ipynb) |

## Key Features

### VibeVoice-ASR
- **60-minute single-pass** — Processes long audio without chunking
- **Rich transcription** — Who (Speaker), When (Timestamps), What (Content)
- **Multilingual** — 50+ languages supported
- **Custom hotwords** — Domain-specific terminology support
- **Hugging Face Transformers** — Native HF integration

### VibeVoice-Realtime
- **Streaming text input** — Real-time TTS
- **Multilingual voices** — DE, FR, IT, JP, KR, NL, PL, PT, ES
- **11 English styles** — Different voice characteristics

## Installation

```bash
# Clone
git clone https://github.com/microsoft/VibeVoice
cd VibeVoice

# Install
pip install -e .
```

## Usage

### ASR (Speech Recognition)
```python
from transformers import pipeline

asr = pipeline(
    "automatic-speech-recognition",
    model="microsoft/VibeVoice-ASR"
)
result = asr("audio_file.wav")
print(result["text"])
```

### Fine-tuning ASR
```bash
cd finetuning-asr
# See finetuning-asr/README.md for details
```

### vLLM Inference (Faster)
```bash
# See docs/vibevoice-vllm-asr.md
```

## Requirements
- Python 3.8+
- PyTorch
- GPU recommended for inference
- Transformers library

## Resources
- [Documentation](docs/vibevoice-asr.md)
- [Hugging Face](https://huggingface.co/microsoft/VibeVoice-ASR)
- [ASR Paper](https://arxiv.org/pdf/2601.18184)
- [TTS Paper](https://openreview.net/pdf?id=FihSkzyxdv)

## Location
Installed at: /opt/VibeVoice