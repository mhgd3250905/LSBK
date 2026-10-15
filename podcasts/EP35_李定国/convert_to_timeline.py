# -*- coding: utf-8 -*-
"""EP35 Markdown 脚本转时间脚本转换器"""
import os
import re

DIR = os.path.dirname(os.path.abspath(__file__))

def s2t(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"

def process_act(act_num_cn, act_title):
    md_file = os.path.join(DIR, f"脚本_第{act_num_cn}幕.md")
    txt_file = os.path.join(DIR, f"第{act_num_cn}幕_时间脚本.txt")
    
    with open(md_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    turns = []
    curr_spk = None
    curr_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(">"):
            continue
        m = re.match(r"^\*\*(大开|小李)\*\*.*?[:：]\s*(.*)", stripped)
        if m:
            if curr_spk and curr_lines:
                turns.append((curr_spk, " ".join(curr_lines).strip()))
            curr_spk = m.group(1)
            text_part = m.group(2).strip()
            curr_lines = [text_part] if text_part else []
        else:
            if curr_spk:
                curr_lines.append(stripped)
                
    if curr_spk and curr_lines:
        turns.append((curr_spk, " ".join(curr_lines).strip()))
        
    total_chars = sum(len(text) for spk, text in turns)
    cpm = 360  # 约每分钟 360 字
    
    header = [
        f"EP 时间脚本（第{act_num_cn}幕）",
        f"净台词约 {total_chars} 字（按合成语速每分钟约 {cpm} 字估算，成品约 {round(total_chars / cpm)} 分钟）",
        f"说话人：大开、小李",
        "=" * 80,
        ""
    ]
    
    cur_time = 0.0
    out_blocks = []
    for spk, text in turns:
        dur = max(3.0, len(text) / (cpm / 60.0))
        start_str = s2t(cur_time)
        end_str = s2t(cur_time + dur)
        out_blocks.append(f"[{start_str} - {end_str}] {spk}\n{text}\n")
        cur_time += dur
        
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("\n".join(header) + "\n".join(out_blocks))
        
    print(f"第{act_num_cn}幕转换完成: {len(turns)} 话轮, {total_chars} 字 -> {txt_file}")
    return total_chars

def main():
    acts = [("一", "流贼变义军，西南擎天柱"),
            ("二", "两蹶名王，天下震动"),
            ("三", "同室操戈与十八先生之狱"),
            ("四", "磨盘山血战与战神绝唱")]
    total = 0
    for cn, title in acts:
        total += process_act(cn, title)
    print(f"\n四幕总字数: {total} 字")

if __name__ == "__main__":
    main()
