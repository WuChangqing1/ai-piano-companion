"""Run basic-pitch audio transcription on test2 video."""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from basic_pitch.inference import predict_and_save
import basic_pitch

AUDIO_PATH = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'test2', 'test_audio.wav')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'test2', 'basic_pitch_output')

# Use the built-in ONNX model (no TensorFlow needed)
MODEL_PATH = os.path.join(os.path.dirname(basic_pitch.__file__), 'saved_models', 'icassp_2022', 'nmp.onnx')

os.makedirs(OUTPUT_DIR, exist_ok=True)

t0 = time.time()
print(f"Transcribing: {AUDIO_PATH}")
print(f"Model: {MODEL_PATH}")
predict_and_save(
    [AUDIO_PATH],
    OUTPUT_DIR,
    save_midi=True,
    sonify_midi=False,
    save_model_outputs=False,
    save_notes=False,
    model_or_model_path=MODEL_PATH,
)
elapsed = time.time() - t0
print(f"Transcription complete in {elapsed:.1f}s")
print(f"Output: {OUTPUT_DIR}")
