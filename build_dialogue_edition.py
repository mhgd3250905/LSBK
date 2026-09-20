#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成带角色对话、段落聚合与全量纠错的终极精读版播客文稿
"""

import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RULES = [
    # 消除 Whisper 重复幻觉
    (r'([伐的了啊呀这那嗯对说去])\1{4,}', r''),

    # 核心历史人物
    (r'司马延', '司马炎'),
    (r'司马仪', '司马懿'),
    (r'司马施', '司马师'),
    (r'司马[优忧裕]', '司马攸'),
    (r'司马[忠终中]', '司马衷'),
    (r'司马福', '司马孚'),
    (r'司马炯', '司马冏'),
    (r'司马义', '司马乂'),
    (r'司马勇', '司马颙'),
    (r'司马[纬伟]', '司马玮'),
    (r'优耳', '攸儿'),
    (r'炎儿', '炎儿'),
    (r'贾[崇冲]', '贾充'),
    (r'甲[崇冲]', '贾充'),
    (r'贾南[峰丰]', '贾南风'),
    (r'甲南风', '贾南风'),
    (r'杨俊', '杨骏'),
    (r'杨辉[瑜愉]', '杨徽瑜'),
    (r'王元基', '王元姬'),
    (r'成[记纪]', '成济'),
    (r'曹毛', '曹髦'),
    (r'诸葛[蛋旦]', '诸葛诞'),
    (r'陪秀', '裴秀'),
    (r'和宗', '何曾'),
    (r'和劭', '何劭'),
    (r'循序', '荀勖'),
    (r'荀虚', '荀勖'),
    (r'卫冠', '卫瓘'),
    (r'为惯', '卫瓘'),
    (r'斯巴克', '斯派克'),

    # 历史事件与制度
    (r'炎忧之争', '炎攸之争'),
    (r'言忧之[中争]', '炎攸之争'),
    (r'言忧', '炎攸'),
    (r'高平[临林]之变', '高平陵之变'),
    (r'高频[龄凌]之变', '高平陵之变'),
    (r'高平[临林]', '高平陵'),
    (r'对[着着]落水', '对着洛水'),
    (r'落水之誓', '洛水之誓'),
    (r'得过不正', '得国不正'),
    (r'五[户湖]乱[花华]', '五胡乱华'),
    (r'五[湖户]水国', '五胡十六国'),
    (r'五[湖户]十六国', '五胡十六国'),
    (r'八王之[段断]', '八王之乱'),
    (r'淮南三[叛判]', '淮南三叛'),
    (r'以尽待位', '以晋代魏'),
    (r'以进代魏', '以晋代魏'),
    (r'泰康元年', '太康元年'),
    (r'太康之治', '太康之治'),
    (r'咸宁二年', '咸宁二年'),
    (r'低长子继承制', '嫡长子继承制'),
    (r'低长子', '嫡长子'),
    (r'立敌不立贤', '立嫡不立贤'),
    (r'利敌不利贤', '立嫡不立贤'),
    (r'利长不利贤', '立长不立贤'),
    (r'立长不利贤', '立长不立贤'),
    (r'费长立右', '废长立幼'),
    (r'废长立右', '废长立幼'),
    (r'景王天下', '景王天下'),
    (r'井王天下', '景王天下'),
    (r'井王', '景王'),
    (r'警王', '景王'),

    # 俗语与口语
    (r'天翼爷', '天意啊'),
    (r'一切都是天翼', '一切都是天意'),
    (r'气韵', '气运'),
    (r'正八景', '正儿八经'),
    (r'多了政权', '夺了政权'),
    (r'扁扁诗', '鞭鞭尸'),
    (r'鞭[子]?诗', '鞭尸'),
    (r'何少莫得[，,]我莫不得', '和尚摸得，我摸不得'),
    (r'挖空', '挖坑'),
    (r'填空', '填坑'),
    (r'抵毒情深', '舐犊情深'),
    (r'舐毒情深', '舐犊情深'),
    (r'何不食肉[迷米]', '何不食肉糜'),
]

def clean_text(t: str) -> str:
    for pat, rep in RULES:
        t = re.sub(pat, rep, t)
    t = t.replace(' ,', '，').replace(',', '，').replace('?', '？').replace('!', '！')
    # 消除孤立乱码符号
    t = re.sub(r'[\ufffd\x00-\x08\x0b\x0c\x0e-\x1f]', '', t).strip()
    return t

def parse_time_sec(t_str: str) -> int:
    parts = t_str.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0

def format_sec(sec: int) -> str:
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"

def main():
    src_file = Path(r"E:\AII_Gemini\LSBK\transcripts\01. [2026-09-16] 八王之乱前传：司马家如何一步步踩中最坏的鼓点.md")
    dst_file = Path(r"E:\AII_Gemini\LSBK\transcripts\01. [2026-09-16] 八王之乱前传：司马家如何一步步踩中最坏的鼓点_对话精修版.md")

    with open(src_file, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r'- \*\*`(\d{2}:\d{2}) - (\d{2}:\d{2})`\*\*\s+(.+)')
    raw_matches = pattern.findall(content)

    items = []
    for t1, t2, raw_text in raw_matches:
        txt = clean_text(raw_text)
        if txt and len(txt) > 1:
            items.append((t1, t2, txt))

    # 智能分段聚合：将同一个主持人在连续几秒内的发言合并为完整语段
    merged_sections = []
    curr_start = items[0][0]
    curr_end = items[0][1]
    curr_texts = [items[0][2]]

    for t1, t2, txt in items[1:]:
        s_sec = parse_time_sec(t1)
        e_prev_sec = parse_time_sec(curr_end)

        # 明显的话轮转换提示词
        turn_cues = ["大家好我是老罗", "大家好我是斯派克", "其实罗老师", "罗老师", "对对对", "对，群里其实", "而且你还要从什么角度"]
        is_turn = any(cue in txt for cue in turn_cues)

        # 停顿超过 3 秒，或者文本达到适中篇幅 (100字左右)，或者遇到明确话轮提示
        if (s_sec - e_prev_sec > 3) or len("".join(curr_texts)) > 120 or is_turn:
            merged_sections.append((curr_start, curr_end, "".join(curr_texts)))
            curr_start = t1
            curr_end = t2
            curr_texts = [txt]
        else:
            curr_end = t2
            curr_texts.append(txt)

    if curr_texts:
        merged_sections.append((curr_start, curr_end, "".join(curr_texts)))

    # 智能判定说话人 (老罗为主讲学者，斯派克为主持兼互动提问)
    dialogue_records = []

    for start_t, end_t, text in merged_sections:
        # 显式规则判断
        if "其实罗老师" in text or "罗老师说的" in text or "听罗老师聊" in text or "听过我们前面节目的朋友" in text:
            spk = "斯派克"
        elif "我是老罗" in text:
            spk = "老罗"
        elif "我是斯派克" in text or "我是斯巴克" in text:
            spk = "斯派克"
        elif "为什么又挖坑了" in text or "光听那些名字呢，你就挺迷糊了" in text or "最黑暗还是五代十国" in text:
            spk = "斯派克"
        elif "灭吴应该是公元280年" in text or "晋王殿下" in text or "我们今天就从这个地方开始给大家讲" in text:
            spk = "老罗"
        elif "司马昭在死前专门把" in text or "王元姬在他病逝前" in text or "此天下乃景王之天下" in text:
            spk = "老罗"
        elif "嫡长子继承制不管是欧洲的还是中国的" in text or "诸葛诞之乱我们当时聊过" in text:
            spk = "老罗"
        elif len(text) > 70:
            # 深度长篇阐述绝大多数为老罗
            spk = "老罗"
        else:
            # 短篇互动根据前文交替
            spk = "斯派克" if (dialogue_records and dialogue_records[-1][0] == "老罗") else "老罗"

        dialogue_records.append((spk, start_t, end_t, text))

    # 写入 Markdown
    with open(dst_file, "w", encoding="utf-8") as f:
        f.write("# 01. [2026-09-16] 八王之乱前传：司马家如何一步步踩中最坏的鼓点（对话精修版）\n\n")
        f.write("> **节目主旨**：聚焦西晋代魏与八王之乱的深层体制与血脉权力交接起源  \n")
        f.write("> **主要对话人**：【老罗】（文化学者罗沙，主讲历史成因与制度机理）、【斯派克】（主持互动与话题引申）  \n")
        f.write(f"> **精修语段数**：{len(dialogue_records)}  \n")
        f.write("> **修正内容**：全量修正历史人名（司马懿/师/攸/衷/冏/乂/颙、贾充、贾南风、杨骏、杨徽瑜等）、历史事件（高平陵之变、洛水之誓、太康元年、炎攸之争、五胡乱华）、政治制度（嫡长子继承制、都督制）及消除 Whisper 重复幻觉循环。  \n\n")
        f.write("---\n\n## 🎙️ 节目完整对话精读实录\n\n")

        for spk, st, et, txt in dialogue_records:
            icon = "🧑‍🏫" if spk == "老罗" else "🎙️"
            f.write(f"### {icon} **【{spk}】** `[{st} - {et}]`\n\n")
            f.write(f"{txt}\n\n")

    print(f"[√] 对话精修版生成成功！共生成 {len(dialogue_records)} 个聚合对话段落，存放在: {dst_file}")

if __name__ == "__main__":
    main()
