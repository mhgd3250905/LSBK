#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成第 05 期《弑父，乱伦，吞子：《奥德赛》背后的那些古希腊抽象神话》对话精修版
"""

import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

EP5_RULES = [
    (r'([伐的了啊呀这那嗯对说去])\1{4,}', r''),

    # 希腊神话核心神祇与英雄
    (r'卡[俄恶]斯', '卡俄斯'),
    (r'盖[亚呀]', '盖亚'),
    (r'乌拉[诺若]斯', '乌拉诺斯'),
    (r'克[罗洛]诺斯', '克洛诺斯'),
    (r'波塞[冬东]', '波塞冬'),
    (r'哈[迪第]斯', '哈迪斯'),
    (r'雅典[娜那]', '雅典娜'),
    (r'赫[拉啦]', '赫拉'),
    (r'阿波[罗萝]', '阿波罗'),
    (r'奥德[修修]斯', '奥德修斯'),
    (r'奥德赛', '奥德赛'),
    (r'泰[坦叹]战争', '泰坦战争'),
    (r'十二泰[坦叹]', '十二泰坦'),
    (r'独眼巨人', '独眼巨人'),
    (r'百臂巨人', '百臂巨人'),
    (r'塞[壬仁]', '塞壬'),
    (r'荷马[史诗]', '荷马史诗'),
    (r'伊利亚[特德]', '伊利亚特'),
    (r'斯拜克', '斯派克'),
]

def clean_text(t: str) -> str:
    for p, r in EP5_RULES:
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
    src_file = Path(r"E:\AII_Gemini\LSBK\transcripts\05. [2026-08-19] 弑父，乱伦，吞子：《奥德赛》背后的那些古希腊抽象神话.md")
    dst_file = Path(r"E:\AII_Gemini\LSBK\transcripts\05. [2026-08-19] 弑父，乱伦，吞子：《奥德赛》背后的那些古希腊抽象神话_对话精修版.md")

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

    merged = []
    curr_start = items[0][0]
    curr_end = items[0][1]
    curr_texts = [items[0][2]]

    for t1, t2, txt in items[1:]:
        s_sec = parse_time_sec(t1)
        e_prev_sec = parse_time_sec(curr_end)

        turn_cues = ["我是老罗", "我是斯派克", "罗老师", "二位", "你看", "对对"]
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

    dialogue_records = []
    for st, et, text in merged:
        if "我是斯派克" in text or "我是斯拜克" in text:
            spk = "斯派克"
        elif "我是老罗" in text:
            spk = "老罗"
        elif "罗老师" in text or "就像老罗说的" in text:
            spk = "斯派克"
        elif "卡俄斯" in text or "泰坦战争" in text or "乌拉诺斯" in text or "奥德修斯" in text:
            spk = "老罗"
        elif len(text) > 85:
            spk = "老罗"
        else:
            last = dialogue_records[-1][0] if dialogue_records else "老罗"
            spk = "斯派克" if last == "老罗" else "老罗"

        dialogue_records.append((spk, st, et, text))

    with open(dst_file, "w", encoding="utf-8") as f:
        f.write("# 05. [2026-08-19] 弑父，乱伦，吞子：《奥德赛》背后的那些古希腊抽象神话（对话精修版）\n\n")
        f.write("> **节目主旨**：从诺兰电影《奥德赛》切入，剥开史诗外衣直击古希腊神谱的“原始内核”——从卡俄斯、盖亚与乌拉诺斯，到克洛诺斯阉割弑父吞子、宙斯发动十年泰坦战争，以及奥德修斯归家历险背后的生存理性与残暴智慧  \n")
        f.write("> **主要对话人**：【老罗】（文化学者罗沙，深度解析神话内核演变与西方文化基因）、【斯派克】（主持互动）  \n")
        f.write(f"> **精修对话段落**：{len(dialogue_records)} 处  \n")
        f.write("> **纠错重点**：卡俄斯、乌拉诺斯、克洛诺斯弑父吞子、宙斯联手独眼巨人与百臂巨人发动泰坦之战、雅典娜破头而生、塞壬妖歌、奥德修斯刺瞎波塞冬之子谎称“无人”等神话专名。  \n\n")
        f.write("---\n\n## 🎙️ 节目完整对话精读实录\n\n")

        for spk, st, et, txt in dialogue_records:
            icon = "🧑‍🏫" if spk == "老罗" else "🎙️"
            f.write(f"### {icon} **【{spk}】** `[{st} - {et}]`\n\n")
            f.write(f"{txt}\n\n")

    print(f"[√] 第 05 期精修完成！生成文件: {dst_file}")

if __name__ == "__main__":
    main()
