#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性修复：以现役时间脚本txt为准，回写同步各幕md源稿台词。
背景：EP01手写txt与md出现措辞漂移，以txt（已合成v2的内容）为唯一正确版本。"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
TURN_RE = re.compile(r"^(\*\*.+?\*\*[（(]\d{1,2}:\d{2}(?::\d{2})?[）)][:：])\s*(.*)$")
INLINE_MD = re.compile(r"\*\*|\*|`")


def parse_txt(p):
    turns, cur = [], None
    for ln in open(p, encoding="utf-8"):
        ln = ln.rstrip()
        m = re.match(r"^\[\d+:\d+ - \d+:\d+\] (.+)$", ln)
        if m:
            cur = {"sp": m.group(1), "tx": ""}
            turns.append(cur)
        elif ln and cur is not None and not ln.startswith("=") and not ln.startswith("EP ") \
                and not ln.startswith("净台词") and not ln.startswith("说话人"):
            cur["tx"] += ln
    return turns


def sync(md_path, txt_path):
    turns = parse_txt(txt_path)
    lines = open(md_path, encoding="utf-8").read().split("\n")
    out, ti, skip = [], 0, False
    for ln in lines:
        s = ln.strip()
        m = TURN_RE.match(s)
        if m:
            if ti >= len(turns):
                print(f"[错误] {md_path}: md话轮多于txt({len(turns)})"); sys.exit(1)
            out.append(m.group(1))          # 保留原话轮头（说话人+时间戳）
            out.append("")                  # 空行
            out.append(INLINE_MD.sub("", turns[ti]["tx"]))  # txt台词整段
            ti += 1
            skip = True                      # 跳过旧正文直到结构行
            continue
        if skip:
            if s.startswith("#") or s.startswith(">") or s.startswith("---") or not s:
                if s.startswith(("#", ">", "---")):
                    skip = False
                    out.append(ln)
                # 空行在台词后已有一个，旧正文里的空行跳过
                continue
            continue                         # 旧正文行：跳过
        out.append(ln)
    if ti != len(turns):
        print(f"[错误] {md_path}: txt轮次{len(turns)} != md写入{ti}"); sys.exit(1)
    open(md_path, "w", encoding="utf-8").write("\n".join(out))
    print(f"{md_path}: {ti} 轮已同步")


for n in ["一", "二", "三", "四"]:
    sync(rf"E:\AII_Gemini\LSBK\podcasts\EP01_阳明心学\脚本_第{n}幕.md",
         rf"E:\AII_Gemini\LSBK\podcasts\EP01_阳明心学\第{n}幕_时间脚本.txt")
