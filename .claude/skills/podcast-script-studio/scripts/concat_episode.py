#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拼接各幕音频与字幕为完整一期。
用法: python concat_episode.py --dir <output目录> --out <输出名> <幕1前缀> <幕2前缀> ...
时间戳自动按各幕时长偏移。"""
import argparse
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ap = argparse.ArgumentParser()
ap.add_argument("--dir", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("acts", nargs="+")
a = ap.parse_args()

durs = []
for act in a.acts:
    tl = json.load(open(os.path.join(a.dir, f"{act}_时间轴.json"), encoding="utf-8"))
    durs.append(max(r["end_time"] for r in tl))

merged = bytearray()
for act in a.acts:
    merged.extend(open(os.path.join(a.dir, f"{act}_合并.mp3"), "rb").read())
open(os.path.join(a.dir, f"{a.out}.mp3"), "wb").write(bytes(merged))


def parse_ts(s):
    h, m, rest = s.split(":")
    sec, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def fmt_ts(t):
    ms = int(round(t * 1000))
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


blocks, offset, idx = [], 0.0, 0
for act, dur in zip(a.acts, durs):
    text = open(os.path.join(a.dir, f"{act}.srt"), encoding="utf-8").read()
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.strip().split("\n")
        if len(lines) < 2 or "-->" not in lines[1]:
            continue
        t1, t2 = lines[1].split(" --> ")
        idx += 1
        blocks.append(f"{idx}\n{fmt_ts(parse_ts(t1) + offset)} --> {fmt_ts(parse_ts(t2) + offset)}\n" + "\n".join(lines[2:]))
    offset += dur

open(os.path.join(a.dir, f"{a.out}.srt"), "w", encoding="utf-8").write("\n\n".join(blocks) + "\n")
print(f"各幕时长(秒): {[round(d, 1) for d in durs]} | 总时长 {sum(durs) / 60:.1f} 分钟")
print(f"音频: {os.path.join(a.dir, a.out + '.mp3')} ({len(merged) / 1024 / 1024:.1f} MB)")
print(f"字幕: {os.path.join(a.dir, a.out + '.srt')} ({idx} 条)")
