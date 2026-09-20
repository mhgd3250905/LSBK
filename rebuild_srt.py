#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从时间轴json重建单幕SRT（时间轴里每轮带有RoundStart返回的文本）。
用法: python rebuild_srt.py <时间轴.json> <输出.srt>"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
from doubao_podcast_pipeline import fmt_ts

json_path, srt_path = sys.argv[1], sys.argv[2]
tl = json.load(open(json_path, encoding="utf-8"))
out, n = [], 0
for r in tl:
    rid = r.get("round_id")
    if rid in (-1, 9999, None):
        continue  # 头尾音乐轮
    text = (r.get("text") or "").strip()
    if not text:
        continue
    n += 1
    out.append(f"{n}\n{fmt_ts(r['start_time'])} --> {fmt_ts(r['end_time'])}\n{r.get('speaker', '')}: {text}")
open(srt_path, "w", encoding="utf-8").write("\n\n".join(out) + "\n")
print(f"{srt_path}: {n} 条")
