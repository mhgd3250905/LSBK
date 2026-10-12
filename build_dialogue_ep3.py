#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成第 03 期《古代帝王“武力值”终极PK，第一竟不是李世民！》对话精修版
"""

import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

EP3_RULES = [
    (r'([伐的了啊呀这那嗯对说去])\1{4,}', r''),

    # 人名与帝王
    (r'成绩4S', '成吉思汗'),
    (r'成绩思汗', '成吉思汗'),
    (r'成吉思汉', '成吉思汗'),
    (r'玉石静德', '尉迟敬德'),
    (r'玉石敬德', '尉迟敬德'),
    (r'石大开', '石达开'),
    (r'亲宗', '钦宗'),
    (r'宋亲宗', '宋钦宗'),
    (r'照相鹰部', '招降英布'),
    (r'鹰部', '英布'),
    (r'刘秀', '刘秀'),
    (r'李世民', '李世民'),
    (r'朱元璋', '朱元璋'),
    (r'赵匡胤', '赵匡胤'),
    (r'赵构', '赵构'),
    (r'项羽', '项羽'),
    (r'韩信', '韩信'),
    (r'彭越', '彭越'),

    # 典故/事件/成语/冷兵器
    (r'尼玛度康王', '泥马渡康王'),
    (r'泥马度康王', '泥马渡康王'),
    (r'开疆拖土', '开疆拓土'),
    (r'长术', '长槊'),
    (r'弹兵作战', '单兵作战'),
    (r'伸手', '身手'),
    (r'把心', '靶心'),
    (r'命中了把心', '命中了靶心'),
    (r'一弹多的弓', '一石多的弓'),
    (r'一石五斗', '一石五斗'),
    (r'一龙分二虎', '一龙分二虎'),
    (r'三千破十万', '三千破十万'),
    (r'玄甲军', '玄甲军'),
    (r'虎牢关之战', '虎牢关之战'),
    (r'高筑墙[、，]广积粮[、，]缓称王', '高筑墙、广积粮、缓称王'),
    (r'跳水冠军', '跳水冠军'),
]

def clean_text(t: str) -> str:
    for p, r in EP3_RULES:
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
    src_file = Path(r"E:\AII_Gemini\LSBK\transcripts\03. [2026-09-02] 古代帝王“武力值”终极PK，第一竟不是李世民！.md")
    dst_file = Path(r"E:\AII_Gemini\LSBK\transcripts\03. [2026-09-02] 古代帝王“武力值”终极PK，第一竟不是李世民！_对话精修版.md")

    with open(src_file, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r'- \*\*`(\d{2}:\d{2}) - (\d{2}:\d{2})`\*\*\s+(.+)')
    raw_matches = pattern.findall(content)

    items = []
    for t1, t2, raw_text in raw_matches:
        txt = clean_text(raw_text)
        if txt and len(txt) > 1:
            items.append((t1, t2, txt))

    # 聚合连续语句
    merged = []
    curr_start = items[0][0]
    curr_end = items[0][1]
    curr_texts = [items[0][2]]

    for t1, t2, txt in items[1:]:
        s_sec = parse_time_sec(t1)
        e_prev_sec = parse_time_sec(curr_end)

        turn_cues = ["我是老罗", "我是斯派克", "我是张大夫", "张大夫", "罗老师", "二位", "你看"]
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

    # 三人对话分配 (老罗、斯派克、张大夫)
    dialogue_records = []
    for st, et, text in merged:
        if "我是张大夫" in text:
            spk = "张大夫"
        elif "我是斯派克" in text:
            spk = "斯派克"
        elif "我是老罗" in text:
            spk = "老罗"
        elif "罗老师" in text or "就像老罗说的" in text:
            spk = "斯派克" if (dialogue_records and dialogue_records[-1][0] != "斯派克") else "张大夫"
        elif "张大夫" in text or "大夫" in text:
            spk = "老罗" if (dialogue_records and dialogue_records[-1][0] != "老罗") else "斯派克"
        elif "我自己个人是把军事能力大约划分为" in text or "战略能力" in text or "制度建设能力" in text:
            spk = "老罗"
        elif "成吉思汗" in text or "三维评价" in text or "开疆拓土" in text:
            spk = "老罗"
        elif "一龙分二虎" in text or "泥马渡康王" in text:
            spk = "斯派克"
        elif "医学角度" in text or "单兵作战能力" in text or "射箭" in text:
            spk = "张大夫"
        elif len(text) > 85:
            spk = "老罗"
        else:
            last = dialogue_records[-1][0] if dialogue_records else "老罗"
            if last == "老罗":
                spk = "斯派克"
            elif last == "斯派克":
                spk = "张大夫"
            else:
                spk = "老罗"

        dialogue_records.append((spk, st, et, text))

    with open(dst_file, "w", encoding="utf-8") as f:
        f.write("# 03. [2026-09-02] 古代帝王“武力值”终极PK，第一竟不是李世民！（对话精修版）\n\n")
        f.write("> **节目主旨**：从个人武艺（单挑能力）到战略、战术、军队制度三维体系，对中国历代帝王军事武力值进行硬核大横评  \n")
        f.write("> **本期对谈嘉宾**：【老罗】（文化学者罗沙，提出军事三维评估模型）、【斯派克】（主持提问）、【张大夫】（特邀嘉宾）  \n")
        f.write(f"> **精修对话段落**：{len(dialogue_records)} 处  \n")
        f.write("> **纠错重点**：成吉思汗（非成绩4S）、尉迟敬德执槊李世民挽弓（非玉石静德）、宋高宗赵构神力比箭（泥马渡康王）、刘邦招降英布项羽彭越战略三角、李世民虎牢关三千破十万、朱元璋战略定力等。  \n\n")
        f.write("---\n\n## 🎙️ 节目完整对话精读实录\n\n")

        for spk, st, et, txt in dialogue_records:
            icon = "🧑‍🏫" if spk == "老罗" else ("🎙️" if spk == "斯派克" else "🩺")
            f.write(f"### {icon} **【{spk}】** `[{st} - {et}]`\n\n")
            f.write(f"{txt}\n\n")

    print(f"[√] 第 03 期精修完成！生成文件: {dst_file}")

if __name__ == "__main__":
    main()
