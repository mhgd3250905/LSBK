#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成第 04 期《古希腊历史和文化》对话精修版
"""

import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

EP4_RULES = [
    (r'([伐的了啊呀这那嗯对说去])\1{4,}', r''),

    # 古希腊历史人物与考古学家
    (r'谢里[慢曼漫]', '谢里曼'),
    (r'修[西夕]底德', '修昔底德'),
    (r'休昔底德', '修昔底德'),
    (r'修昔底德陷[井阱]', '修昔底德陷阱'),
    (r'伯里克[利里]', '伯里克利'),
    (r'苏格拉[底第]', '苏格拉底'),
    (r'亚里士多[德得]', '亚里士多德'),
    (r'柏拉[图土]', '柏拉图'),
    (r'伊巴密浓[达大]', '伊巴密浓达'),

    # 古希腊城邦、文明与地理
    (r'米诺[斯私]', '米诺斯'),
    (r'[麦迈]锡尼', '迈锡尼'),
    (r'克里[特忒]', '克里特'),
    (r'特洛[伊依]', '特洛伊'),
    (r'[博伯]罗奔尼[撒萨]', '伯罗奔尼撒'),
    (r'[底迪]比斯', '底比斯'),
    (r'底比斯圣[队对]', '底比斯圣队'),
    (r'斯巴[达大]', '斯巴达'),
    (r'雅[典点]', '雅典'),
    (r'[希西]波战争', '希波战争'),
    (r'温泉[关官]', '温泉关'),
    (r'萨拉米[斯私]', '萨拉米斯'),
    (r'爱琴[海嗨]', '爱琴海'),
    (r'马其[顿栋]', '马其顿'),

    # 常见误听词与口语
    (r'西方伪史[论伦]', '西方伪史论'),
    (r'斯拜克', '斯派克'),
    (r'线形文字', '线形文字'),
]

def clean_text(t: str) -> str:
    for p, r in EP4_RULES:
        t = re.sub(p, r, t)
    t = t.replace(' ,', '，').replace(',', '，').replace('?', '？').replace('!', '！')
    t = re.sub(r'[\ufffd\x00-\x08\x0b\x0c\x0e-\x1f]', '', t).strip()
    return t

def parse_time_sec(t_str: str) -> int:
    parts = t_str.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0

def main():
    src_file = Path(r"E:\AII_Gemini\LSBK\transcripts\04. [2026-08-26] 古希腊历史和文化.md")
    dst_file = Path(r"E:\AII_Gemini\LSBK\transcripts\04. [2026-08-26] 古希腊历史和文化_对话精修版.md")

    if not src_file.exists():
        print(f"[!] 待转写文件尚未生成: {src_file}")
        return

    with open(src_file, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r'- \*\*`(\d{2}:\d{2}) - (\d{2}:\d{2})`\*\*\s+(.+)')
    raw_matches = pattern.findall(content)

    items = []
    for t1, t2, raw_text in raw_matches:
        txt = clean_text(raw_text)
        if txt and len(txt) > 1:
            items.append((t1, t2, txt))

    if not items:
        print("[!] 没有提取到有效文本")
        return

    # 聚合连续语句
    merged = []
    curr_start = items[0][0]
    curr_end = items[0][1]
    curr_texts = [items[0][2]]

    for t1, t2, txt in items[1:]:
        s_sec = parse_time_sec(t1)
        e_prev_sec = parse_time_sec(curr_end)

        turn_cues = ["我是老罗", "我是斯派克", "我是悠悠", "罗老师", "悠悠", "二位", "你看"]
        is_turn = any(cue in txt for cue in turn_cues)

        if (s_sec - e_prev_sec > 2.5) or len("".join(curr_texts)) > 110 or is_turn:
            merged.append((curr_start, curr_end, "".join(curr_texts)))
            curr_start = t1
            curr_end = t2
            curr_texts = [txt]
        else:
            curr_end = t2
            curr_texts.append(txt)

    if curr_texts:
        merged.append((curr_start, curr_end, "".join(curr_texts)))

    # 对话人分配 (老罗与斯派克/悠悠)
    dialogue_records = []
    for st, et, text in merged:
        if "我是悠悠" in text or "我是王悠悠" in text:
            spk = "王悠悠"
        elif "我是斯派克" in text or "我是斯拜克" in text:
            spk = "斯派克"
        elif "我是老罗" in text:
            spk = "老罗"
        elif "罗老师" in text or "就像老罗说的" in text:
            spk = "斯派克"
        elif "谢里曼" in text or "米诺斯" in text or "修昔底德陷阱" in text or "西方伪史论" in text:
            spk = "老罗"
        elif len(text) > 85:
            spk = "老罗"
        else:
            last = dialogue_records[-1][0] if dialogue_records else "老罗"
            spk = "斯派克" if last == "老罗" else "老罗"

        dialogue_records.append((spk, st, et, text))

    with open(dst_file, "w", encoding="utf-8") as f:
        f.write("# 04. [2026-08-26] 古希腊历史和文化（对话精修版）\n\n")
        f.write("> **节目主旨**：摒弃极端“西方伪史论”，以审视中国古史的严谨眼光，重新辨伪爱琴海文明（米诺斯与迈锡尼）、希波战争真相、伯罗奔尼撒内耗与修昔底德陷阱  \n")
        f.write("> **主要对话人**：【老罗】（文化学者罗沙，主讲文明辨伪与历史规律）、【斯派克】（主持互动）  \n")
        f.write(f"> **精修对话段落**：{len(dialogue_records)} 处  \n")
        f.write("> **纠错重点**：谢里曼（毁掉特洛伊遗址）、克里特迷宫、米诺斯与迈锡尼文明、希波战争温泉关与萨拉米斯海战、伯罗奔尼撒战争、底比斯圣队、修昔底德陷阱等。  \n\n")
        f.write("---\n\n## 🎙️ 节目完整对话精读实录\n\n")

        for spk, st, et, txt in dialogue_records:
            icon = "🧑‍🏫" if spk == "老罗" else "🎙️"
            f.write(f"### {icon} **【{spk}】** `[{st} - {et}]`\n\n")
            f.write(f"{txt}\n\n")

    print(f"[√] 第 04 期精修完成！生成文件: {dst_file}")

if __name__ == "__main__":
    main()
