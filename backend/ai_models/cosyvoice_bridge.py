"""
CosyVoice 桥接脚本 —— 在独立的 conda 环境中运行。
用法:
  python cosyvoice_bridge.py --text "文本" --output output.wav --voice "中文女"
  [--ref-audio ref.wav --ref-text "参考文本"]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def synthesize_edge_fallback(text: str, output: Path) -> None:
    """CosyVoice 不可用时的 edge-tts 兜底。"""
    import asyncio
    import edge_tts
    mp3_out = output.with_suffix(".mp3")
    asyncio.run(
        edge_tts.Communicate(text=text, voice="zh-CN-XiaoxiaoNeural").save(str(mp3_out))
    )
    print(f"FALLBACK: {mp3_out}")


def synthesize_cosyvoice(
    text: str, output: Path, voice: str = "中文女",
    ref_audio: str | None = None, ref_text: str = "",
) -> None:
    """使用 CosyVoice 进行 Zero-shot TTS。"""
    try:
        from cosyvoice.cli.cosyvoice import CosyVoice
        from cosyvoice.utils.file_utils import load_wav
        import torchaudio

        cosyvoice = CosyVoice("pretrained_models/CosyVoice-300M-SFT")

        if ref_audio and Path(ref_audio).exists():
            # Zero-shot 模式:用参考音频克隆音色
            prompt_speech_16k = load_wav(ref_audio, 16000)
            output_gen = cosyvoice.inference_zero_shot(
                text, ref_text, prompt_speech_16k, stream=False,
            )
        else:
            # 预置音色模式
            output_gen = cosyvoice.inference_sft(text, voice, stream=False)

        for i, wav_data in enumerate(output_gen):
            torchaudio.save(str(output), wav_data["tts_speech"], 22050)
            print(f"OK: {output}")
            return

    except ImportError:
        print("CosyVoice not installed, falling back to edge-tts")
        synthesize_edge_fallback(text, output)
    except Exception as e:
        print(f"CosyVoice error: {e}")
        synthesize_edge_fallback(text, output)


def main():
    parser = argparse.ArgumentParser(description="CosyVoice TTS Bridge")
    parser.add_argument("--text", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--voice", default="中文女")
    parser.add_argument("--ref-audio", default=None)
    parser.add_argument("--ref-text", default="")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    synthesize_cosyvoice(
        text=args.text,
        output=output_path,
        voice=args.voice,
        ref_audio=args.ref_audio,
        ref_text=args.ref_text,
    )


if __name__ == "__main__":
    main()
