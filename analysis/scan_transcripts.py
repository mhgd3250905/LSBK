#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全景量化扫描：对全部 56 期对话精修版做结构化统计
输出：
  1. analysis/stats.csv           每期统计（时长/话轮/话轮长度/问句/感叹等）
  2. analysis/headtails.md        每期开场(前3个话轮)+结尾(后4个话轮)集中提取
"""
import re
import csv
from pathlib import Path

SRC = Path(r"E:\AII_Gemini\LSBK\transcripts")
OUT = Path(r"E:\AII_Gemini\LSBK\analysis")
OUT.mkdir(exist_ok=True)

# 话轮头模式: ### 🧑‍🏫 **【老罗】** `[00:00 - 00:30]`
TURN_RE = re.compile(r"^###\s*\S*\s*\*\*【(.+?)】\*\*\s*`\[(\d+:\d+)(?:\s*-\s*(\d+:\d+))?\]`", re.M)

def t2s(t: str) -> int:
    parts = [int(x) for x in t.split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return parts[0] * 60 + parts[1]

rows = []
headtail = ["# 全部 56 期：开场 + 结尾集中提取\n"]

files = sorted(SRC.glob("*_对话精修版.md"))
for f in files:
    text = f.read_text(encoding="utf-8")
    # 去掉文件头部元信息块（第一个 ### 之前）
    first_m = TURN_RE.search(text)
    body = text[first_m.start():] if first_m else text
    matches = list(TURN_RE.finditer(body))
    turns = []
    for i, m in enumerate(matches):
        start_s = t2s(m.group(2))
        end_s = t2s(m.group(3)) if m.group(3) else start_s
        seg = body[m.end():matches[i + 1].start()] if i + 1 < len(matches) else body[m.end():]
        seg = seg.strip()
        turns.append({"who": m.group(1), "start": start_s, "end": end_s, "text": seg})

    if not turns:
        continue

    total_sec = max(t["end"] for t in turns)
    speakers = {}
    for t in turns:
        speakers.setdefault(t["who"], {"n": 0, "chars": 0})
        speakers[t["who"]]["n"] += 1
        speakers[t["who"]]["chars"] += len(t["text"])
    all_text = "".join(t["text"] for t in turns)
    n_question = len(re.findall(r"[?？]", all_text))
    n_exclaim = len(re.findall(r"[!！]", all_text))
    # 相邻同说话人合并后的"有效交锋轮"
    effective = 1
    for i in range(1, len(turns)):
        if turns[i]["who"] != turns[i - 1]["who"]:
            effective += 1
    # 每分钟话轮切换次数
    sw_per_min = effective / (total_sec / 60) if total_sec else 0
    # 平均话轮时长
    avg_turn_sec = total_sec / len(turns) if turns else 0

    name = f.name.replace("_对话精修版.md", "")
    spk_str = "; ".join(f"{k}:{v['n']}轮/{v['chars']}字" for k, v in sorted(speakers.items(), key=lambda x: -x[1]["n"]))
    rows.append({
        "file": name,
        "total_min": round(total_sec / 60, 1),
        "turns": len(turns),
        "effective_switches": effective,
        "switch_per_min": round(sw_per_min, 2),
        "avg_turn_sec": round(avg_turn_sec, 1),
        "questions": n_question,
        "q_per_min": round(n_question / (total_sec / 60), 2) if total_sec else 0,
        "exclaims": n_exclaim,
        "speakers": spk_str,
    })

    headtail.append(f"\n---\n\n## {name}\n")
    headtail.append(f"时长 {total_sec//60} 分钟 | {spk_str}\n")
    headtail.append("\n### 开场（前3话轮）\n")
    for t in turns[:3]:
        headtail.append(f"**[{t['who']} {t['start']//60}:{t['start']%60:02d}]** {t['text'][:600]}\n")
    headtail.append("\n### 结尾（后4话轮）\n")
    for t in turns[-4:]:
        headtail.append(f"**[{t['who']} {t['start']//60}:{t['start']%60:02d}]** {t['text'][-600:]}\n")

with open(OUT / "stats.csv", "w", encoding="utf-8-sig", newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

(OUT / "headtails.md").write_text("".join(headtail), encoding="utf-8")

# 控制台摘要
print(f"共扫描 {len(rows)} 期")
ts = [r["total_min"] for r in rows]
print(f"时长: min={min(ts)}, max={max(ts)}, avg={sum(ts)/len(ts):.0f} 分钟")
sw = [r["switch_per_min"] for r in rows]
print(f"话轮切换/分钟: min={min(sw)}, max={max(sw)}, avg={sum(sw)/len(sw):.2f}")
q = [r["q_per_min"] for r in rows]
print(f"问句/分钟: min={min(q)}, max={max(q)}, avg={sum(q)/len(q):.2f}")
allspk = {}
for r in rows:
    for p in r["speakers"].split("; "):
        k = p.split(":")[0]
        if k:
            allspk[k] = allspk.get(k, 0) + int(p.split(":")[1].split("轮")[0])
print("说话人出场期数:", allspk)
