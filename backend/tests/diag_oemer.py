"""Oemer diagnostic script."""
import subprocess, sys, os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Oemer diagnostic")
print("=" * 50)
oemer_exe = "D:/App/Business/Coding/Python/Miniconda/envs/AIqinban/Scripts/oemer.exe"
result = subprocess.run(
    [oemer_exe, "test_data/1.jpg", "-o", "test_data/omr_test_output", "--without-deskew"],
    capture_output=True, timeout=300,
)
print(f"Return code: {result.returncode}")
print(f"\n--- STDOUT ---")
print(result.stdout.decode("utf-8", errors="replace"))
print(f"\n--- STDERR ---")
print(result.stderr.decode("utf-8", errors="replace"))
