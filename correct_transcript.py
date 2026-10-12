#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
播客文稿智能纠错与历史专有名词修复工具
针对《有啥说啥》等历史文化播客，自动修复 Whisper 的同音错字、历史人物、朝代制度并消除重复死循环。
"""

import os
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# 历史专有名词精修规则库 (魏晋南北朝 / 八王之乱)
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
    (r'王元姬', '王元姬'),
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

    # 历史事件与政治制度
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
    (r'咸宁', '咸宁'),
    (r'低长子继承制', '嫡长子继承制'),
    (r'低长子', '嫡长子'),
    (r'立敌不立贤', '立嫡不立贤'),
    (r'利敌不利贤', '立嫡不立贤'),
    (r'利长不利贤', '立长不立贤'),
    (r'立长不利贤', '立长不立贤'),
    (r'费长立右', '废长立幼'),
    (r'废长立右', '废长立幼'),
    (r'都督各州', '都督各州'),
    (r'分封诸王', '分封诸王'),
    (r'景王天下', '景王天下'),
    (r'井王天下', '景王天下'),
    (r'井王', '景王'),
    (r'警王', '景王'),

    # 俗语、梗与口语误听
    (r'天翼爷', '天意啊'),
    (r'天翼', '天意'),
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
    (r'肉迷', '肉糜'),
    (r'何不食肉[迷米]', '何不食肉糜'),
    (r'贾充的[“"]不答[”"]', '贾充的“不答”'),
]

def correct_text(text: str) -> str:
    for pat, rep in RULES:
        text = re.sub(pat, rep, text)
    # 格式化标点符号
    text = text.replace(' ,', '，').replace(',', '，').replace('?', '？').replace('!', '！')
    return text

def process_transcript_file(src_path: Path, dst_path: Path):
    with open(src_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header = []
    content_lines = []
    in_header = True

    pattern = re.compile(r'- \*\*`(\d{2}:\d{2}) - (\d{2}:\d{2})`\*\*\s+(.+)')

    out_lines = []
    for line in lines:
        if in_header:
            out_lines.append(line)
            if "### 对话转写记录" in line:
                in_header = False
            continue
        
        m = pattern.match(line.strip())
        if m:
            t_start, t_end, raw_text = m.group(1), m.group(2), m.group(3)
            fixed_text = correct_text(raw_text)
            if fixed_text.strip():
                out_lines.append(f"- **`{t_start} - {t_end}`** {fixed_text}\n")
        elif not line.strip():
            out_lines.append("\n")

    with open(dst_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)

    print(f"[√] 修复完成！生成精修文件: {dst_path}")

if __name__ == "__main__":
    src = Path(r"E:\AII_Gemini\LSBK\transcripts\01. [2026-09-16] 八王之乱前传：司马家如何一步步踩中最坏的鼓点.md")
    dst = Path(r"E:\AII_Gemini\LSBK\transcripts\01. [2026-09-16] 八王之乱前传：司马家如何一步步踩中最坏的鼓点_精修版.md")
    process_transcript_file(src, dst)
