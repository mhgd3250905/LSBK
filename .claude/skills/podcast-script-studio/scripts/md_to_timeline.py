#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md_to_timeline.py — 脚本_第N幕.md → 第N幕_时间脚本.txt
单一真相源原则：台词修改只改 md，本工具负责生成合成用 txt。

用法:
  python md_to_timeline.py 脚本_第一幕.md [-o 第一幕_时间脚本.txt] [--act 第一幕] [--cpm 290]

自动处理：
- 时间戳归零（减去幕内首个话轮时间）
- 过滤：---- 分隔线、> 引用块（生产笔记）、# 标题、（…完…）尾注行
- 剥离内容中的舞台提示不属于本工具职责（合成时 pipeline 再剥离），保留供人读
"""
import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

TURN_RE = re.compile(r"^\*\*(.+?)\*\*[（(](\d{1,2}:\d{2}(?::\d{2})?)[）)][:：]\s*(.*)$")


def t2s(t):
    parts = [int(x) for x in t.split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return parts[0] * 60 + parts[1]


def s2t(s):
    m, sec = divmod(int(s), 60)
    return f"{m:02d}:{sec:02d}"


def convert(md_path, out_path=None, act_name=None, chars_per_minute=400):
    lines = open(md_path, encoding="utf-8").read().split("\n")
    title = act_name or os.path.splitext(os.path.basename(md_path))[0].replace("脚本_", "")
    turns, cur = [], None
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("#"):          # 各级标题：不入台词（幕名已单独取）
            continue
        if s.startswith(">"):          # 引用块=生产笔记
            continue
        if s.startswith("---"):
            continue
        if re.match(r"^（.+完.*）$", s) or s.startswith("（本幕完"):  # 尾注行严禁入文本
            continue
        m = TURN_RE.match(s)
        if m:
            cur = {"speaker": m.group(1).strip(), "t": t2s(m.group(2)),
                   "text": re.sub(r"\*\*|\*|`", "", m.group(3).strip())}
            turns.append(cur)
            continue
        if cur is not None:
            cur["text"] += re.sub(r"\*\*|\*|`", "", s)
    if not turns:
        print(f"[错误] 未解析到话轮: {md_path}")
        sys.exit(1)

    base = turns[0]["t"]
    total_chars = sum(len(t["text"]) for t in turns)
    header = [
        f"EP 时间脚本（{title}）",
        f"净台词约 {total_chars} 字（按合成语速每分钟约 {chars_per_minute} 字估算，成品约 {round(total_chars / chars_per_minute)} 分钟）",
        f"说话人：{'、'.join(dict.fromkeys(t['speaker'] for t in turns))}",
        "=" * 80,
    ]
    out = []
    for i, t in enumerate(turns):
        start = t["t"] - base
        if i + 1 < len(turns):
            end = turns[i + 1]["t"] - base
        else:
            end = start + max(10, len(t["text"]) // 5)
        out.append(f"[{s2t(start)} - {s2t(end)}] {t['speaker']}\n{t['text']}\n")

    out_path = out_path or os.path.join(os.path.dirname(os.path.abspath(md_path)),
                                        f"{title.replace('第', '第')}_时间脚本.txt")
    open(out_path, "w", encoding="utf-8").write("\n".join(header) + "\n\n" + "\n".join(out))
    print(f"{len(turns)} 个话轮 → {out_path}（净台词 {total_chars} 字）")
    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("-o", "--out")
    ap.add_argument("--act", help="幕名（默认从文件名提取）")
    ap.add_argument("--cpm", type=int, default=400, help="每分钟估算汉字数（默认 400；可按本期试听语速校准）")
    a = ap.parse_args()
    if a.cpm <= 0:
        ap.error("--cpm 必须是正整数")
    convert(a.md, a.out, a.act, a.cpm)
