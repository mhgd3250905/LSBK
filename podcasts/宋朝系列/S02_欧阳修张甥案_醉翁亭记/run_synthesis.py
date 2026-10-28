# -*- coding: utf-8 -*-
"""S2E02 豆包播客全自动合成与拼接流水线"""
import os
import subprocess
import sys

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(DIR, "..", "..", ".."))
CREDS = os.path.join(ROOT, "豆包api.txt")
PIPELINE = os.path.join(ROOT, ".agents", "skills", "podcast-script-studio", "scripts", "doubao_podcast_pipeline.py")
CONCAT = os.path.join(ROOT, ".agents", "skills", "podcast-script-studio", "scripts", "concat_episode.py")
OUTDIR = os.path.join(DIR, "output")
os.makedirs(OUTDIR, exist_ok=True)

acts = [
    ("第一幕_时间脚本.txt", ["--no-tail-music"]),
    ("第二幕_时间脚本.txt", ["--no-head-music", "--no-tail-music"]),
    ("第三幕_时间脚本.txt", ["--no-head-music", "--no-tail-music"]),
    ("第四幕_时间脚本.txt", ["--no-head-music"]),
]

print("=== 开始合成 S2E02 欧阳修张甥案与醉翁亭记 四幕音频 ===")
for act_file, extra_args in acts:
    script_path = os.path.join(DIR, act_file)
    print(f"\n>>> 正在合成: {act_file} ...")
    cmd = [
        sys.executable, PIPELINE, script_path,
        "--creds-file", CREDS,
        "--outdir", OUTDIR
    ] + extra_args
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"[错误] {act_file} 合成失败，退出码 {res.returncode}")
        sys.exit(res.returncode)

print("\n=== 四幕音频合成完毕，开始拼接完整版 ===")
concat_cmd = [
    sys.executable, CONCAT,
    "--dir", OUTDIR,
    "--out", "完整版",
    "第一幕_时间脚本",
    "第二幕_时间脚本",
    "第三幕_时间脚本",
    "第四幕_时间脚本"
]
res = subprocess.run(concat_cmd)
if res.returncode != 0:
    print(f"[错误] 拼接失败，退出码 {res.returncode}")
    sys.exit(res.returncode)

print("\n=== 检查完整版音频解码与时长 ===")
out_mp3 = os.path.join(OUTDIR, "完整版.mp3")
probe_cmd = ["ffmpeg", "-v", "error", "-i", out_mp3, "-f", "null", "-"]
res = subprocess.run(probe_cmd, capture_output=True, text=True)
if res.returncode == 0 and not res.stderr.strip():
    print("✅ ffmpeg 解码验证通过：零坏帧、零解码错误！")
else:
    print(f"⚠️ 解码告警: {res.stderr.strip()}")

print(f"\n🎉 S2E02 全部合成完成！成品文件保存在: {OUTDIR}")
