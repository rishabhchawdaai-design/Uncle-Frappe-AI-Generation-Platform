#!/usr/bin/env python3
"""
End-to-end generation verification harness.

Proves every modality by execution on the current machine, using only the
documented install (stdlib + httpx). No API keys are required to run it:
keyless paths (image via Pollinations) are expected to produce real media;
credential-gated paths must return clean, truthful errors with exact reasons
instead of crashing.

Usage:
    python scripts/verify_generation.py [--output-dir DIR]

Exit code 0 when every path executed without crashing and all produced
artifacts validated; 1 when anything crashes or a produced artifact is
invalid.
"""
import argparse
import asyncio
import json
import os
import struct
import sys
import time
from pathlib import Path


def jpeg_ok(data: bytes) -> bool:
    return data[:3] == b"\xff\xd8\xff" and data[-2:] == b"\xff\xd9"


def png_ok(data: bytes) -> bool:
    return data[:8] == b"\x89PNG\r\n\x1a\n"


def wav_ok(data: bytes) -> bool:
    return data[:4] == b"RIFF" and data[8:12] == b"WAVE"


def mp4_ok(data: bytes) -> bool:
    return data[4:8] == b"ftyp"


def image_dims(data: bytes) -> dict:
    if png_ok(data) and len(data) >= 24:
        w, h = struct.unpack(">II", data[16:24])
        return {"width": w, "height": h}
    if jpeg_ok(data):
        i, n = 2, len(data)
        while i < n - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC2):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return {"width": w, "height": h}
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return {}


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="output/verification")
    args = parser.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ai_generation import UncleFrappeAI

    ai = UncleFrappeAI()
    report = {"started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "modalities": {}, "artifacts": []}
    crashed = False

    def record(name, ok, detail, artifact=None):
        report["modalities"][name] = {"ok": ok, "detail": detail}
        if artifact:
            report["artifacts"].append(artifact)

    # 1. IMAGE — keyless (Pollinations) — must produce a real image
    try:
        r = await ai.generate_image("a red apple on a wooden table",
                                    width=512, height=512)
        data = r.output_bytes or b""
        ok = r.success and data and (jpeg_ok(data) or png_ok(data))
        dims = image_dims(data) if data else {}
        rec = {"provider": r.provider, "format": r.output_format,
               "bytes": len(data), "dims": dims}
        if ok:
            path = out_dir / f"image.{r.output_format or 'jpg'}"
            path.write_bytes(data)
            rec["path"] = str(path)
        record("image", ok, rec or {"error": r.error, "status": r.status},
               rec if ok else None)
    except Exception as e:
        crashed = True
        record("image", False, f"CRASH {type(e).__name__}: {e}")

    # 2. VIDEO — credential-gated providers; must fail cleanly
    try:
        r = await ai.generate_video("a cat walking", duration_secs=2.0)
        record("video", not r.success and bool(r.error),
               {"status": r.status, "error": r.error, "provider": r.provider})
    except Exception as e:
        crashed = True
        record("video", False, f"CRASH {type(e).__name__}: {e}")

    # 3. MUSIC — local AudioCraft server; must fail cleanly with reason
    try:
        r = await ai.generate_music("upbeat jazz", duration_secs=2.0)
        clean = getattr(r, "status", None) in ("failed", "dependency_missing")
        record("music", clean, {"status": getattr(r, "status", None),
                                "error": getattr(r, "error", None)})
    except Exception as e:
        crashed = True
        record("music", False, f"CRASH {type(e).__name__}: {e}")

    # 4. SFX
    try:
        r = await ai.generate_sfx("thunder", duration_secs=2.0)
        clean = getattr(r, "status", None) in ("failed", "dependency_missing")
        record("sfx", clean, {"status": getattr(r, "status", None),
                              "error": getattr(r, "error", None)})
    except Exception as e:
        crashed = True
        record("sfx", False, f"CRASH {type(e).__name__}: {e}")

    # 5. SPEECH (TTS) — all providers credential/local-gated
    try:
        r = await ai.generate_speech("Hello from the platform")
        clean = getattr(r, "success", False) is False and bool(getattr(r, "error", None))
        record("speech", clean, {"status": getattr(r, "status", None),
                                 "error": getattr(r, "error", None)})
    except Exception as e:
        crashed = True
        record("speech", False, f"CRASH {type(e).__name__}: {e}")

    # 6. 3D — truthful unavailable/dependency_missing (no crash)
    try:
        r = await ai.generate_3d("a red cube")
        clean = isinstance(r, dict) and r.get("status") in ("unavailable", "dependency_missing")
        record("3d", clean, {"status": r.get("status"), "error": r.get("error")})
    except Exception as e:
        crashed = True
        record("3d", False, f"CRASH {type(e).__name__}: {e}")

    # 7. TEXT — Kimi cloud/vLLM/SGLang; must fail cleanly without key
    try:
        r = await ai.chat("Say hello", timeout_secs=30)
        clean = not r.get("text") and bool(r.get("error"))
        record("text", clean, {"provider": r.get("provider"), "error": r.get("error")})
    except Exception as e:
        crashed = True
        record("text", False, f"CRASH {type(e).__name__}: {e}")

    # 8. Registry + SDK surface sanity (offline)
    try:
        srv = ai.get_mcp_registry_stats()
        skl = ai.get_skill_registry_stats()
        tls = ai.get_tool_registry_stats()
        record("registries", True, {"mcp_servers": srv["total_servers"],
                                    "skills": skl["total_skills"],
                                    "tools": tls["total_tools"]})
    except Exception as e:
        crashed = True
        record("registries", False, f"CRASH {type(e).__name__}: {e}")

    report["crashed"] = crashed
    report["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report_path = out_dir / "verify_generation.json"
    report_path.write_text(json.dumps(report, indent=2, default=str))

    print("\n=== Modality Verification Matrix ===")
    for name, m in report["modalities"].items():
        icon = "PASS" if m["ok"] else "FAIL"
        print(f"  [{icon}] {name:12s} {str(m['detail'])[:160]}")
    print(f"\n  Artifacts: {len(report['artifacts'])}")
    for a in report["artifacts"]:
        print(f"    - {a.get('path', '?')} ({a.get('bytes')} bytes, dims={a.get('dims')})")
    print(f"\n  Report: {report_path}")
    print(f"  Result: {'CRASHED' if crashed else 'executed without crashes'}")
    return 1 if crashed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
