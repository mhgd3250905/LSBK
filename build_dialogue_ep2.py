#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成第 02 期《七分真三分假？揭密〈三国演义〉与真实历史的异同》对话精修版
"""

import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

EP2_RULES = [
    (r'([伐的了啊呀这那嗯对说去])\1{4,}', r''),

    # 人名与评书/红学大家
    (r'成功', '陈宫'),
    (r'斯拜克', '斯派克'),
    (r'圆阔重', '袁阔成'),
    (r'施南安', '施耐庵'),
    (r'罗惯中', '罗贯中'),
    (r'毛中岗', '毛宗岗'),
    (r'毛忠岗', '毛宗岗'),
    (r'张学成', '章学诚'),
    (r'章学成', '章学诚'),
    (r'许楚', '许褚'),
    (r'点为', '典韦'),
    (r'江博约', '姜伯约'),
    (r'姜博约', '姜伯约'),
    (r'中会', '钟会'),
    (r'邓爱', '邓艾'),
    (r'吉川英子', '吉川英治'),
    (r'周日昂', '周汝昌'),
    (r'于平博', '俞平伯'),
    (r'刘新武', '刘心武'),

    # 文化与版本概念
    (r'小幻形', '小浣熊'),
    (r'水狐', '水浒'),
    (r'百亚讲坛', '百家讲坛'),
    (r'百家讲台', '百家讲坛'),
    (r'成高本', '程高本'),
    (r'支批本', '脂批本'),
    (r'支援斋', '脂砚斋'),
    (r'鬼友本', '癸酉本'),
    (r'石头记', '石头记'),
    (r'光荣游戏', '光荣特库摩游戏'),

    # 典故/事件/成语
    (r'白油光', '白月光'),
    (r'过五万斩流向', '过五关斩六将'),
    (r'过五关斩流向', '过五关斩六将'),
    (r'唱马破', '长坂坡'),
    (r'长板坡', '长坂坡'),
    (r'近期期出', '七擒七纵'),
    (r'近期七出', '七擒七纵'),
    (r'六出旗山', '六出祁山'),
    (r'明金受兵', '鸣金收兵'),
    (r'鸣金受兵', '鸣金收兵'),
    (r'水五[乱传]', '水浒传'),
    (r'吃剧子', '斥巨资'),
    (r'并利', '并列'),
    (r'少儿不移', '少儿不宜'),
    (r'状诸葛多智而近夭', '状诸葛多智而近妖'),
    (r'状诸葛多智而近[要妖]', '状诸葛多智而近妖'),
    (r'一计害三[贤闲]', '一计害三贤'),
    (r'可食天水', '可知天水'),
    (r'老将军可食', '老将军可知'),
    (r'九宫八卦战争', '九宫八卦阵'),
    (r'九宫八卦阵[争法]', '九宫八卦阵'),
    (r'七实三虚', '七实三虚'),
    (r'七分真三分假', '七分真三分假'),
    (r'白门楼', '白门楼'),
    (r'三英战吕布', '三英战吕布'),
    (r'一吕二赵三典韦', '一吕二赵三典韦'),
    (r'云大怒', '云大怒'),
]

def fix_contextual(text: str) -> str:
    text = re.sub(r'关于张飞', '关羽张飞', text)
    text = re.sub(r'关于、张飞', '关羽、张飞', text)
    text = re.sub(r'关于和张飞', '关羽和张飞', text)
    text = re.sub(r'关于跟张飞', '关羽跟张飞', text)
    text = re.sub(r'关于赵云', '关羽赵云', text)
    text = re.sub(r'关于的身高', '关羽的身高', text)
    text = re.sub(r'关于斩颜良', '关羽斩颜良', text)
    text = re.sub(r'关于温酒', '关羽温酒', text)
    text = re.sub(r'关于千里', '关羽千里', text)
    text = re.sub(r'关于大意', '关羽大意', text)
    text = re.sub(r'关于走麦城', '关羽走麦城', text)
    text = re.sub(r'关于二哥', '关羽二哥', text)
    text = re.sub(r'关于跟刘备', '关羽跟刘备', text)
    return text

def clean_text(t: str) -> str:
    t = fix_contextual(t)
    for p, r in EP2_RULES:
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
    src_file = Path(r"E:\AII_Gemini\LSBK\transcripts\02. [2026-09-08] 七分真三分假？揭密《三国演义》与真实历史的异同.md")
    dst_file = Path(r"E:\AII_Gemini\LSBK\transcripts\02. [2026-09-08] 七分真三分假？揭密《三国演义》与真实历史的异同_对话精修版.md")

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

        turn_cues = ["我是老罗", "我是斯派克", "我是张大夫", "张大夫", "罗老师", "二位", "你说"]
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
    current_speaker = "老罗"

    for st, et, text in merged:
        if "我是张大夫" in text:
            spk = "张大夫"
        elif "我是斯派克" in text or "我是斯拜克" in text:
            spk = "斯派克"
        elif "我是老罗" in text:
            spk = "老罗"
        elif "罗老师" in text or "就像老罗说的" in text:
            spk = "斯派克" if (dialogue_records and dialogue_records[-1][0] != "斯派克") else "张大夫"
        elif "张大夫" in text or "大夫" in text:
            spk = "老罗" if (dialogue_records and dialogue_records[-1][0] != "老罗") else "斯派克"
        elif "章学诚" in text or "毛宗岗" in text or "嘉靖本" in text or "七实三虚" in text or "战略眼光" in text:
            spk = "老罗"
        elif "三英战吕布" in text or "水浒传是我拥有的第一本" in text or "吃剧子" in text or "斥巨资" in text:
            spk = "斯派克"
        elif "从医学角度" in text or "云大怒" in text or "白月光" in text:
            spk = "张大夫"
        elif len(text) > 80:
            spk = "老罗"
        else:
            # 轮流切换
            last = dialogue_records[-1][0] if dialogue_records else "老罗"
            if last == "老罗":
                spk = "斯派克"
            elif last == "斯派克":
                spk = "张大夫"
            else:
                spk = "老罗"

        dialogue_records.append((spk, st, et, text))

    with open(dst_file, "w", encoding="utf-8") as f:
        f.write("# 02. [2026-09-08] 七分真三分假？揭密《三国演义》与真实历史的异同（对话精修版）\n\n")
        f.write("> **节目主旨**：从章学诚“七实三虚”、毛宗岗批本与嘉靖本差异、鲁迅“状诸葛多智而近妖”，深度拆解《三国演义》文学虚构与真实三国史的边界  \n")
        f.write("> **本期对谈嘉宾**：【老罗】（主讲文化学者）、【斯派克】（主持互动）、【张大夫】（特邀金牌书迷嘉宾）  \n")
        f.write(f"> **精修对话段落**：{len(dialogue_records)} 处  \n")
        f.write("> **纠错重点**：陈宫（曹操白月光）、袁阔成评书、章学诚（七实三虚）、毛宗岗本 vs 嘉靖本、长坂坡（非唱马破）、过五关斩六将、七擒七纵、一计害三贤、鸣金收兵、许褚典韦战力、日本光荣三国志等。  \n\n")
        f.write("---\n\n## 🎙️ 节目完整对话精读实录\n\n")

        for spk, st, et, txt in dialogue_records:
            icon = "🧑‍🏫" if spk == "老罗" else ("🎙️" if spk == "斯派克" else "🩺")
            f.write(f"### {icon} **【{spk}】** `[{st} - {et}]`\n\n")
            f.write(f"{txt}\n\n")

    print(f"[√] 第 02 期精修完成！生成文件: {dst_file}")

if __name__ == "__main__":
    main()
