#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_ep04.py — 第四幕三处女声补丁：切割原音频、插入单句合成补丁、修正时间轴、重建字幕"""
import copy
import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

DIR = r"E:\AII_Gemini\LSBK\podcasts\EP04_明朝中期皇帝反常识\output"
ACT = "第四幕_时间脚本"
FFMPEG = "ffmpeg"
PATCHES = [(9, "test_句A_合并.mp3"), (13, "test_句B_合并.mp3"), (21, "test_句C_合并.mp3")]


def dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", p], capture_output=True, text=True)
    return float(out.stdout.strip())


tl = json.load(open(f"{DIR}\\{ACT}_时间轴.json", encoding="utf-8"))
orig = copy.deepcopy(tl)
rounds = {r["round_id"]: r for r in tl if r.get("round_id") is not None}
total = max(r["end_time"] for r in orig if r.get("round_id") is not None)

# 1) 切原音频为保留段，与补丁交错拼接
cuts, prev = [], 0.0
for rid, _ in PATCHES:
    r = next(x for x in orig if x.get("round_id") == rid)
    cuts.append((prev, r["start_time"]))
    prev = r["end_time"]
cuts.append((prev, total))

seg_files = []
for i, (s, e) in enumerate(cuts):
    out = f"{DIR}\\patch_seg{i}.mp3"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", f"{DIR}\\{ACT}_合并.mp3",
                    "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-c", "copy", out], check=True)
    seg_files.append(out)

lst = f"{DIR}\\patch_concat.txt"
with open(lst, "w", encoding="utf-8") as f:
    for i, (_, patch) in enumerate(PATCHES):
        f.write(f"file '{seg_files[i]}'\nfile '{DIR}\\{patch}'\n")
    f.write(f"file '{seg_files[-1]}'\n")
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                "-i", lst, "-c", "copy", f"{DIR}\\{ACT}_合并.mp3"], check=True)

# 2) 时间轴重算：补丁轮用补丁实际时长，其后所有轮累计平移
shift = 0.0
for rid, patch in PATCHES:
    r = next(x for x in orig if x.get("round_id") == rid)
    new_len = dur(f"{DIR}\\{patch}")
    shift += new_len - (r["end_time"] - r["start_time"])

shift = 0.0
for r_orig, r_new in zip(orig, tl):
    rid = r_orig.get("round_id")
    patch_len = None
    for pid, patch in PATCHES:
        if pid == rid:
            patch_len = dur(f"{DIR}\\{patch}")
    if rid is None:  # 音乐轮（9999）：尾音乐，跟随平移
        r_new["start_time"] = r_orig["start_time"] + shift
        r_new["end_time"] = r_orig["end_time"] + shift
        continue
    if patch_len is not None:  # 补丁轮
        r_new["start_time"] = r_orig["start_time"] + shift
        r_new["end_time"] = r_new["start_time"] + patch_len
        shift += patch_len - (r_orig["end_time"] - r_orig["start_time"])
    else:  # 普通轮
        r_new["start_time"] = r_orig["start_time"] + shift
        r_new["end_time"] = r_orig["end_time"] + shift

json.dump(tl, open(f"{DIR}\\{ACT}_时间轴.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 3) 重建字幕
subprocess.run([sys.executable, r"E:\AII_Gemini\LSBK\rebuild_srt.py",
                f"{DIR}\\{ACT}_时间轴.json", f"{DIR}\\{ACT}.srt"], check=True)

new_total = max(r["end_time"] for r in tl)
print(f"补丁完成：新第四幕总时长 {new_total:.3f}s（原 {total:.3f}s，偏移 +{shift:.3f}s）")
