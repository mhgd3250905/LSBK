#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拼接各幕音频与字幕为完整一期。
用法: python concat_episode.py --dir <output目录> --out <输出名> <幕1前缀> <幕2前缀> ...
时间戳自动按各幕时长偏移（用 ffprobe 实测各幕 mp3 时长——json 的 max end_time 与实际
音频存在秒级偏差，EP04 实测三幕累积 +5.2s，会造成后续幕字幕整体错位）。"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")


def strip_embedded_id3(data):
    """Remove valid ID3v2 tags emitted between streamed MP3 speech rounds.

    The podcast API can put an ID3v2 tag before every round. A raw byte join
    leaves those tags inside the MP3 frame stream, where decoders report bad
    frames. Keep the audio frames byte-for-byte and drop only validated tags.
    """
    out = bytearray()
    pos = 0
    removed = 0
    while True:
        i = data.find(b"ID3", pos)
        if i < 0:
            out.extend(data[pos:])
            break

        if i + 10 > len(data):
            out.extend(data[pos:])
            break

        header = data[i:i + 10]
        version = header[3]
        size_bytes = header[6:10]
        if version not in (2, 3, 4) or any(byte & 0x80 for byte in size_bytes):
            out.extend(data[pos:i + 1])
            pos = i + 1
            continue

        tag_size = ((size_bytes[0] & 0x7f) << 21) | ((size_bytes[1] & 0x7f) << 14) \
            | ((size_bytes[2] & 0x7f) << 7) | (size_bytes[3] & 0x7f)
        footer_size = 10 if version == 4 and (header[5] & 0x10) else 0
        end = i + 10 + tag_size + footer_size
        next_is_mpeg_frame = end + 1 < len(data) and data[end] == 0xff and (data[end + 1] & 0xe0) == 0xe0
        if end > len(data) or (end < len(data) and not next_is_mpeg_frame):
            out.extend(data[pos:i + 1])
            pos = i + 1
            continue

        out.extend(data[pos:i])
        pos = end
        removed += 1

    return bytes(out), removed

ap = argparse.ArgumentParser()
ap.add_argument("--dir", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("acts", nargs="+")
a = ap.parse_args()

clean_acts, durs, stripped_counts = [], [], []
with tempfile.TemporaryDirectory(prefix="concat_episode_") as temp_dir:
    for index, act in enumerate(a.acts):
        source = os.path.join(a.dir, f"{act}_合并.mp3")
        raw = open(source, "rb").read()
        clean, removed = strip_embedded_id3(raw)
        clean_acts.append(clean)
        stripped_counts.append(removed)

        probe_path = os.path.join(temp_dir, f"act_{index + 1}.mp3")
        with open(probe_path, "wb") as f:
            f.write(clean)
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", probe_path],
            capture_output=True, text=True, check=True)
        durs.append(float(probe.stdout.strip()))

merged = b"".join(clean_acts)
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
if any(stripped_counts):
    print(f"各幕已去除内嵌 ID3 标签: {stripped_counts}")
print(f"音频: {os.path.join(a.dir, a.out + '.mp3')} ({len(merged) / 1024 / 1024:.1f} MB)")
print(f"字幕: {os.path.join(a.dir, a.out + '.srt')} ({idx} 条)")
