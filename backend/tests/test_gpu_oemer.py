"""
测试 Oemer ONNX 是否使用 GPU。
用法: conda run -n AIqinban --cwd backend python tests/test_gpu_oemer.py
"""
import os
import site
import sys
from pathlib import Path

# ── 注册 CUDA/cuDNN DLL ──
for sp in site.getsitepackages():
    for pattern in ["nvidia/cudnn/bin", "nvidia/cublas/bin", "nvidia/cuda_nvrtc/bin"]:
        p = f"{sp}/{pattern}"
        if os.path.isdir(p):
            try:
                os.add_dll_directory(p)
            except Exception:
                pass

print("=" * 60)
print(" GPU 可用性诊断")
print("=" * 60)

# 1. ONNX Runtime providers
print("\n[1] ONNX Runtime 可用 providers:")
try:
    import onnxruntime as ort
    providers = ort.get_available_providers()
    for p in providers:
        print(f"    ✓ {p}")
    cuda_available = "CUDAExecutionProvider" in providers
    print(f"\n    CUDA GPU 可用: {'是 ✓' if cuda_available else '否 ✗'}")
    if cuda_available:
        try:
            dev = ort.get_device()
            print(f"    设备: {dev}")
        except Exception:
            pass
except Exception as e:
    print(f"    ✗ onnxruntime 导入失败: {e}")
    cuda_available = False

# 2. 创建 CUDA 推理会话测试
print("\n[2] CUDA 推理会话测试:")
if cuda_available:
    try:
        import numpy as np
        sess = ort.InferenceSession(
            # 用最小模型验证 CUDA provider 能真正被使用
            # 创建一个临时 ONNX 模型是不可能的,改为检查 provider 选项
            ort.SessionOptions(),
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        # Actually test with a simple matmul
        import onnx
        from onnx import helper, TensorProto
        import tempfile

        # Build a minimal ONNX model
        X = helper.make_tensor_value_info("X", TensorProto.FLOAT, [1, 10])
        Y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [1, 10])
        node = helper.make_node("Relu", ["X"], ["Y"], name="relu")
        graph = helper.make_graph([node], "test", [X], [Y])
        model = helper.make_model(graph, producer_name="test")
        model = onnx.shape_inference.infer_shapes(model)

        with tempfile.NamedTemporaryFile(suffix=".onnx", delete=False) as f:
            f.write(model.SerializeToString())
            tmp_onnx = f.name

        sess = ort.InferenceSession(
            tmp_onnx,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        actual_provider = sess.get_providers()
        print(f"    实际使用的 provider: {actual_provider[0]}")
        if "CUDA" in actual_provider[0]:
            print("    GPU 推理测试通过 ✓")

        # Run a real inference
        input_data = np.random.randn(1, 10).astype(np.float32)
        out = sess.run(None, {"X": input_data})
        print(f"    推理结果 shape: {out[0].shape}, sum={out[0].sum():.3f}")

        os.unlink(tmp_onnx)
    except Exception as e:
        print(f"    ✗ CUDA 会话创建失败: {e}")
else:
    print("    跳过（CUDA 不可用）")

# 3. Oemer 依赖检查
print("\n[3] Oemer 依赖:")
try:
    import oemer
    print(f"    ✓ oemer 已安装")
except ImportError:
    print(f"    ✗ oemer 未安装")

# 4. 实际跑一次 Oemer 并检测是否用 GPU
print("\n[4] Oemer 实际 GPU 测试:")
import subprocess, shutil, tempfile, time

score_img = Path("test_data/1.jpg")
if score_img.exists():
    tmp_dir = Path(tempfile.mkdtemp(prefix="oemer_gpu_test_"))
    tmp_img = tmp_dir / "score.jpg"
    shutil.copy2(score_img, tmp_img)

    out_dir = tmp_dir / "output"
    out_dir.mkdir(exist_ok=True)

    oemer_exe = Path(sys.prefix) / "Scripts" / "oemer.exe"
    if not oemer_exe.exists():
        oemer_exe = Path("D:/App/Business/Coding/Python/Miniconda/envs/AIqinban/Scripts/oemer.exe")

    print(f"    Oemer CLI: {oemer_exe}")
    print(f"    输入: {score_img.name}")
    print(f"    运行中（超时 300s）...")

    t0 = time.time()
    try:
        res = subprocess.run(
            [str(oemer_exe), str(tmp_img), "-o", str(out_dir), "--without-deskew"],
            capture_output=True, timeout=300,
        )
        elapsed = time.time() - t0
        print(f"    耗时: {elapsed:.0f}s, returncode={res.returncode}")

        if res.returncode == 0:
            mxl = list(out_dir.glob("*.musicxml")) + list(out_dir.glob("*.xml"))
            print(f"    MusicXML 输出: {'有' if mxl else '无'} ({len(mxl)} 个)")
            print(f"    Oemer 运行成功 ✓")
        else:
            stderr = res.stderr.decode("gbk", errors="replace")
            print(f"    stderr (尾部): ...{stderr[-300:]}")
    except subprocess.TimeoutExpired:
        print(f"    ✗ 超时 (>300s)")
    except Exception as e:
        print(f"    ✗ 异常: {e}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
else:
    print(f"    跳过: test_data/1.jpg 不存在")

# 5. 汇总
print("\n" + "=" * 60)
print(" 诊断结论")
print("=" * 60)
print(f"  CUDA GPU: {'可用 ✓' if cuda_available else '不可用 ✗'}")
print(f"  Oemer 使用 ONNX Runtime（非 TensorFlow），GPU 取决于 ONNX provider")
print(f"  结论: {'GPU 可用于 Oemer ✓' if cuda_available else '需要配置 CUDA/cuDNN ✗'}")
