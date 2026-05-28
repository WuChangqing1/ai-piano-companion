"""Run basic-pitch on test3 audio."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import basic_pitch
from basic_pitch.inference import predict_and_save

AUDIO_PATH = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'test3', 'test_audio.wav')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'test3', 'basic_pitch_output')
MODEL_PATH = os.path.join(os.path.dirname(basic_pitch.__file__), 'saved_models', 'icassp_2022', 'nmp.onnx')

os.makedirs(OUTPUT_DIR, exist_ok=True)
t0 = time.time()
print(f"Transcribing: {AUDIO_PATH}")
predict_and_save([AUDIO_PATH], OUTPUT_DIR, save_midi=True, sonify_midi=False,
                 save_model_outputs=False, save_notes=False, model_or_model_path=MODEL_PATH)
print(f"Done in {time.time()-t0:.1f}s → {OUTPUT_DIR}")
