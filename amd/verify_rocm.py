"""Run inside the AMD AI Notebook, before starting vLLM, to confirm ROCm/
PyTorch/vLLM actually see the GPU. Prints only non-secret diagnostic
information (no environment-variable dump, no tokens).

    python amd/verify_rocm.py
"""

import shutil
import subprocess


def _run(cmd: list[str]) -> str:
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return (completed.stdout or completed.stderr).strip()
    except FileNotFoundError:
        return f"<{cmd[0]} not found on PATH>"
    except Exception as exc:  # noqa: BLE001 - diagnostic script, report and continue
        return f"<error running {' '.join(cmd)}: {exc}>"


def main() -> None:
    print("=" * 60)
    print("ClipContext AMD ROCm / vLLM diagnostic")
    print("=" * 60)

    print("\n--- rocminfo (GPU agent / name) ---")
    if shutil.which("rocminfo"):
        for line in _run(["rocminfo"]).splitlines():
            stripped = line.strip()
            if "Marketing Name" in stripped or "Agent" in stripped or "gfx" in stripped:
                print(stripped)
    else:
        print("rocminfo not found on PATH")

    print("\n--- rocm-smi (VRAM) ---")
    if shutil.which("rocm-smi"):
        print(_run(["rocm-smi", "--showproductname", "--showmeminfo", "vram"]))
    else:
        print("rocm-smi not found on PATH")

    print("\n--- PyTorch / HIP ---")
    try:
        import torch

        print(f"torch.__version__: {torch.__version__}")
        print(f"torch.version.hip: {torch.version.hip}")
        print(f"torch.cuda.is_available(): {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            print(f"torch.cuda.device_count(): {torch.cuda.device_count()}")
            print(f"torch.cuda.get_device_name(0): {torch.cuda.get_device_name(0)}")
            props = torch.cuda.get_device_properties(0)
            print(f"total_memory_gb: {props.total_memory / (1024 ** 3):.1f}")
        else:
            print("NO GPU visible to PyTorch")
    except ImportError:
        print("torch is not importable in this environment")

    print("\n--- vLLM ---")
    try:
        import vllm

        print(f"vllm.__version__: {vllm.__version__}")
    except ImportError:
        print("vllm is not importable in this environment")

    print("\n--- Python ---")
    import sys

    print(sys.version)

    print("\n--- Disk ---")
    print(_run(["df", "-h", "."]))

    print("\n--- RAM ---")
    print(_run(["free", "-h"]))

    print("\nDone. Paste this full output back to continue AMD model selection.")


if __name__ == "__main__":
    main()
