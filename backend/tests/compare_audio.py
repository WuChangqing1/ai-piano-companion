"""Compare basic-pitch transcribed MIDI with standard score MIDI (Oemer OMR).

Detects: correct notes, wrong notes, missing notes, extra notes, timing errors.
Auto-aligns start offset between the two MIDIs.
"""
import os
import sys
import json
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pretty_midi
import numpy as np

# Paths
TRANSCRIBED_MIDI = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'test2', 'basic_pitch_output', 'test_audio_basic_pitch.mid')
STANDARD_MIDI = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'test2', 'oemer_output', 'standard_score.mid')
OUTPUT_JSON = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'test2', 'audio_comparison.json')

# Tolerance for matching
TIME_TOLERANCE = 0.5  # seconds
PITCH_TOLERANCE = 0   # semitones, 0 = exact pitch
OCTAVE_TOLERANCE = False  # if True, also match ±12 semitones


def extract_notes(midi_path, label):
    """Extract all notes from a MIDI file."""
    pm = pretty_midi.PrettyMIDI(midi_path)
    notes = []
    for inst in pm.instruments:
        for note in inst.notes:
            notes.append({
                'pitch': note.pitch,
                'start': note.start,
                'end': note.end,
                'duration': note.end - note.start,
                'velocity': note.velocity,
                'note_name': pretty_midi.note_number_to_name(note.pitch),
            })
    notes.sort(key=lambda n: n['start'])
    print(f"[{label}] {len(notes)} notes, {len(pm.instruments)} instrument(s), end time: {notes[-1]['end']:.1f}s" if notes else f"[{label}] 0 notes")
    return notes, pm


def find_best_offset(transcribed_notes, standard_notes, max_offset=5.0, step=0.05):
    """Find the time offset that maximizes pitch matches (modulo octave)."""
    best_offset = 0.0
    best_count = 0
    for offset in np.arange(0, max_offset + step, step):
        count = 0
        std_idx = 0
        for tn in transcribed_notes:
            tn_time = tn['start'] - offset
            if tn_time < 0:
                continue
            # Find nearest standard note in time
            while std_idx < len(standard_notes) and standard_notes[std_idx]['start'] < tn_time - TIME_TOLERANCE:
                std_idx += 1
            # Check window around tn_time
            si = std_idx
            while si < len(standard_notes) and standard_notes[si]['start'] <= tn_time + TIME_TOLERANCE:
                pitch_diff = abs(tn['pitch'] - standard_notes[si]['pitch'])
                if pitch_diff <= PITCH_TOLERANCE or pitch_diff % 12 == 0:
                    count += 1
                    break
                si += 1
        if count > best_count:
            best_count = count
            best_offset = offset
    print(f"Best start offset: {best_offset:.2f}s (matched {best_count} notes with octave equivalence)")
    return round(best_offset, 2)


def compare_notes(transcribed_notes, standard_notes, time_tolerance=0.5, pitch_tolerance=0, start_offset=0.0, octave_tolerance=False):
    """Compare two sets of notes, finding matches, errors, omissions."""
    matched_std = set()
    matched_trans = set()
    correct = []
    pitch_errors = []
    octave_errors = []

    for ti, tn in enumerate(transcribed_notes):
        tn_time = tn['start'] - start_offset
        if tn_time < 0:
            continue

        best_dist = float('inf')
        best_si = -1
        for si, sn in enumerate(standard_notes):
            if si in matched_std:
                continue
            time_diff = abs(tn_time - sn['start'])
            if time_diff > time_tolerance:
                continue
            pitch_diff = abs(tn['pitch'] - sn['pitch'])
            # Weighted: time is primary, pitch secondary
            dist = time_diff / time_tolerance + pitch_diff / 12.0
            if dist < best_dist:
                best_dist = dist
                best_si = si

        if best_si >= 0:
            matched_trans.add(ti)
            matched_std.add(best_si)
            sn = standard_notes[best_si]
            time_diff = abs(tn_time - sn['start'])
            pitch_diff = abs(tn['pitch'] - sn['pitch'])
            if pitch_diff <= pitch_tolerance:
                correct.append({
                    'pitch': tn['pitch'],
                    'note_name': tn['note_name'],
                    'std_start': sn['start'],
                    'trans_start': tn['start'],
                    'time_diff': round(time_diff, 3),
                })
            elif octave_tolerance and pitch_diff % 12 == 0:
                octave_errors.append({
                    'expected_pitch': sn['pitch'],
                    'expected_name': sn['note_name'],
                    'played_pitch': tn['pitch'],
                    'played_name': tn['note_name'],
                    'pitch_diff': pitch_diff,
                    'std_start': sn['start'],
                    'trans_start': tn['start'],
                    'time_diff': round(time_diff, 3),
                })
            else:
                pitch_errors.append({
                    'expected_pitch': sn['pitch'],
                    'expected_name': sn['note_name'],
                    'played_pitch': tn['pitch'],
                    'played_name': tn['note_name'],
                    'pitch_diff': pitch_diff,
                    'std_start': sn['start'],
                    'trans_start': tn['start'],
                    'time_diff': round(time_diff, 3),
                })

    missing_notes = [standard_notes[si] for si in range(len(standard_notes)) if si not in matched_std]
    extra_notes = [transcribed_notes[ti] for ti in range(len(transcribed_notes)) if ti not in matched_trans]

    return {
        'correct': correct,
        'pitch_errors': pitch_errors,
        'octave_errors': octave_errors,
        'missing_notes': missing_notes,
        'extra_notes': extra_notes,
    }


def tempo_analysis(transcribed_midi, standard_midi):
    """Analyze tempo differences."""
    std_tempo = standard_midi.estimate_tempo()
    trans_tempo = transcribed_midi.estimate_tempo()
    return {
        'standard_tempo_bpm': round(std_tempo, 1),
        'transcribed_tempo_bpm': round(trans_tempo, 1),
        'tempo_ratio': round(trans_tempo / std_tempo, 3) if std_tempo > 0 else 1.0,
    }


def main():
    print("=" * 60)
    print("MIDI Comparison: Transcribed vs Standard Score")
    print("=" * 60)

    trans_notes, trans_midi = extract_notes(TRANSCRIBED_MIDI, "Transcribed")
    std_notes, std_midi = extract_notes(STANDARD_MIDI, "Standard Score")

    if not trans_notes or not std_notes:
        print("ERROR: Empty MIDI!")
        return

    # Step 1: Find best start offset
    print("\n--- Auto-aligning start offset ---")
    start_offset = find_best_offset(trans_notes, std_notes, max_offset=5.0)

    # Step 2: Compare with alignment
    print(f"\n--- Comparing (time tolerance={TIME_TOLERANCE}s, offset={start_offset}s) ---")
    result = compare_notes(trans_notes, std_notes, TIME_TOLERANCE, PITCH_TOLERANCE, start_offset, OCTAVE_TOLERANCE)
    tempo = tempo_analysis(trans_midi, std_midi)

    n_correct = len(result['correct'])
    n_pitch_err = len(result['pitch_errors'])
    n_octave_err = len(result['octave_errors'])
    n_missing = len(result['missing_notes'])
    n_extra = len(result['extra_notes'])
    n_std = len(std_notes)
    n_trans = len(trans_notes)
    n_matched = n_correct + n_pitch_err + n_octave_err

    print(f"Standard score notes:   {n_std}")
    print(f"Transcribed notes:      {n_trans}")
    print(f"Time-matched notes:     {n_matched}")
    print(f"  Correct (exact):      {n_correct}")
    print(f"  Pitch errors:         {n_pitch_err}")
    print(f"  Octave errors:        {n_octave_err}")
    print(f"Missing (std unmatched):{n_missing}")
    print(f"Extra (trans unmatched):{n_extra}")

    # Accuracy metrics
    precision = n_correct / n_trans * 100 if n_trans > 0 else 0
    recall = n_correct / n_std * 100 if n_std > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    # Time-matched rate: how many notes found a time partner
    match_rate = n_matched / max(n_std, n_trans) * 100 if max(n_std, n_trans) > 0 else 0

    print(f"\n--- Metrics ---")
    print(f"Time-match rate:  {match_rate:.1f}%")
    print(f"Precision:        {precision:.1f}%")
    print(f"Recall:           {recall:.1f}%")
    print(f"F1 Score:         {f1:.1f}%")

    print(f"\n--- Tempo Analysis ---")
    print(f"Standard tempo:    {tempo['standard_tempo_bpm']} BPM")
    print(f"Transcribed tempo: {tempo['transcribed_tempo_bpm']} BPM")

    tempo_diff = abs(tempo['standard_tempo_bpm'] - tempo['transcribed_tempo_bpm'])
    tempo_score = max(0, 100 - tempo_diff * 2)
    print(f"Tempo score:       {tempo_score:.0f}/100")

    # Scoring
    pitch_score = round(recall * 0.7 + precision * 0.3)
    overall_score = round(pitch_score * 0.5 + tempo_score * 0.5)

    print(f"\n--- Scores ---")
    print(f"Pitch accuracy score:  {pitch_score}/100")
    print(f"Tempo score:           {tempo_score:.0f}/100")
    print(f"Overall audio score:   {overall_score}/100")

    # Pitch error distribution
    pitch_err_dist = {}
    for pe in result['pitch_errors']:
        semitone_diff = pe['pitch_diff']
        bucket = f"{semitone_diff}半音" if semitone_diff <= 7 else ">7半音"
        pitch_err_dist[bucket] = pitch_err_dist.get(bucket, 0) + 1

    # Save results
    output = {
        'start_offset': start_offset,
        'standard_note_count': n_std,
        'transcribed_note_count': n_trans,
        'time_matched_count': n_matched,
        'correct_count': n_correct,
        'pitch_error_count': n_pitch_err,
        'octave_error_count': n_octave_err,
        'missing_count': n_missing,
        'extra_count': n_extra,
        'time_match_rate': round(match_rate, 1),
        'precision': round(precision, 1),
        'recall': round(recall, 1),
        'f1_score': round(f1, 1),
        'pitch_score': pitch_score,
        'tempo_score': round(tempo_score),
        'overall_audio_score': overall_score,
        'tempo': tempo,
        'pitch_error_distribution': dict(sorted(pitch_err_dist.items())),
        'pitch_errors_detail': result['pitch_errors'][:30],
        'octave_errors_detail': result['octave_errors'][:20],
        'missing_notes_detail': [{'pitch': n['pitch'], 'note_name': n['note_name'], 'start': round(n['start'], 2)} for n in result['missing_notes'][:30]],
        'extra_notes_detail': [{'pitch': n['pitch'], 'note_name': n['note_name'], 'start': round(n['start'], 2)} for n in result['extra_notes'][:30]],
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {OUTPUT_JSON}")

    return output


if __name__ == '__main__':
    main()
