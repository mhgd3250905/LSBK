# -*- coding: utf-8 -*-
"""播客单幕文稿自动化质量自检脚本
用法: python scripts/verify_act_script.py <幕文稿.md> [--is-last-act]
"""
import argparse
import os
import re
import sys

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def check_script(filepath, is_last_act=False):
    if not os.path.exists(filepath):
        print(f"[错误] 文件不存在: {filepath}")
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    errors = []
    warnings = []
    
    # 提取所有正文对话行（排除标题行与空行）
    dialogue_lines = []
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue
        # 忽略 Markdown 标题行 (如 # 第一幕)
        if stripped.startswith("#"):
            continue
        dialogue_lines.append((idx, stripped))

    # 1. 严格检查直接引号（零容忍）
    quote_pattern = re.compile(r'[“”「」]')
    for idx, text in dialogue_lines:
        m = quote_pattern.search(text)
        if m:
            errors.append(f"第 {idx} 行发现直接引号 '{m.group()}': {text[:60]}...（豆包action=3易触发第三音色，必须一律第三人称转述）")

    # 2. 检查小李台词首句呼唤“大开，”（零容忍）
    dakai_pattern = re.compile(r'^\*\*小李\*\*.*?[:：\)]\s*大开[，,]')
    for idx, text in dialogue_lines:
        if dakai_pattern.search(text):
            errors.append(f"第 {idx} 行小李台词以'大开，'开头: {text[:60]}...（咪仔音色必卡顿重读，严禁句首呼唤）")

    # 3. 检查机械八股二元对仗句式（零容忍）
    antithesis_patterns = [
        re.compile(r'不是.*?而是'),
        re.compile(r'既不是.*?也不是'),
        re.compile(r'从来不是.*?恰恰是'),
    ]
    for idx, text in dialogue_lines:
        for p in antithesis_patterns:
            m = p.search(text)
            if m:
                errors.append(f"第 {idx} 行发现机械八股对仗句式 '{m.group()}': {text[:60]}...（改用自然口语单句陈述因果）")

    # 4. 检查廉价煽情与AI套话禁词（零容忍）
    ai_buzzwords = [
        "头皮发麻", "让人窒息", "脊背发凉", "细思极恐", "绝了", "魔幻",
        "这就太反常识了", "颠覆认知", "更绝的是", "真正让人不可思议的是",
        "等待着命运的裁决", "青史难书", "命运的齿轮", "做梦都想不到", "一点都没错"
    ]
    for idx, text in dialogue_lines:
        for bw in ai_buzzwords:
            if bw in text:
                errors.append(f"第 {idx} 行发现AI禁词/套话 '{bw}': {text[:60]}...")

    # 5. 检查剧本腔结构元词汇（零容忍）
    meta_words = ["伏笔", "彩蛋", "板块", "环节", "回收", "收束", "大纲", "脚本", "冷开场"]
    # 针对“幕”字特别处理（除夜幕/内幕/烟幕等自然名词外，严禁暴露剧本或旁白视角的“一幕/这一幕/下一幕/第X幕”）
    act_meta_pattern = re.compile(r'(第[一二三四1234]幕|这一幕|下一幕|上幕|前幕|四幕|本幕|落幕|谢幕|(?<!夜|内|烟)一幕)')
    for idx, text in dialogue_lines:
        for mw in meta_words:
            if mw in text:
                errors.append(f"第 {idx} 行发现剧本腔元词汇 '{mw}': {text[:60]}...")
        m_act = act_meta_pattern.search(text)
        if m_act:
            errors.append(f"第 {idx} 行发现暴露结构的'幕'词汇 '{m_act.group()}': {text[:60]}...")

    # 6. 检查机械串场报幕口癖（零容忍）
    robotic_patterns = [
        re.compile(r'接下来发生了什么'),
        re.compile(r'我们继续'),
        re.compile(r'接下来看'),
        re.compile(r'那后来呢[，,]我们接着说')
    ]
    for idx, text in dialogue_lines:
        for rp in robotic_patterns:
            m = rp.search(text)
            if m:
                errors.append(f"第 {idx} 行发现机械串场口癖 '{m.group()}': {text[:60]}...")

    # 7. 收尾完整性核验
    # 提取说话人发言轮次（将说话人标识与其后续所有正文段落正确合并）
    turns = []
    curr_spk = None
    curr_lines = []
    curr_idx = 0
    for idx, text in dialogue_lines:
        m_spk = re.match(r'^\*\*(大开|小李)\*\*', text)
        if m_spk:
            if curr_spk:
                turns.append((curr_idx, curr_spk, " ".join(curr_lines).strip()))
            curr_spk = m_spk.group(1)
            curr_lines = [text]
            curr_idx = idx
        else:
            if curr_spk:
                curr_lines.append(text)
    if curr_spk:
        turns.append((curr_idx, curr_spk, " ".join(curr_lines).strip()))

    if is_last_act:
        # 仅限全集最后一幕：必须检查末尾三轮闭环
        if len(turns) < 3:
            errors.append("末幕话轮少于3轮，无法满足双人闭环收口要求！")
        else:
            last_3 = turns[-3:]
            t_xiaoli_1, t_dakai, t_xiaoli_2 = last_3
            if t_xiaoli_1[1] != "小李":
                warnings.append(f"末幕倒数第3轮应为小李（主持回扣），实际为: {t_xiaoli_1[1]}")
            if t_dakai[1] != "大开":
                warnings.append(f"末幕倒数第2轮应为大开（深度历史注脚），实际为: {t_dakai[1]}")
            if t_xiaoli_2[1] != "小李":
                errors.append(f"末幕最后1轮必须为小李标志性电台告别语，实际为: {t_xiaoli_2[1]}")
            else:
                signoff_pattern = re.compile(r'感谢大家收听.*?笑谈历史.*?我们下期接着聊')
                if not signoff_pattern.search(t_xiaoli_2[2]):
                    errors.append(f"末幕最后1轮缺少标准电台告别语（'感谢大家收听本期的《笑谈历史》，我们下期接着聊。'）: {t_xiaoli_2[2][:60]}")
    else:
        # 前置各幕：严禁提前出现电台告别语或阶段总结
        for idx, spk, text in turns:
            if "感谢大家收听" in text or "下期接着聊" in text or "我们下期见" in text:
                errors.append(f"第 {idx} 行在前置幕中出现提前告别语: {text[:60]}...（前置各幕严禁提前收尾，事件必须无缝流动）")

    # 输出自检报告
    filename = os.path.basename(filepath)
    print(f"==================================================")
    print(f" 幕文稿自检报告: {filename}")
    print(f" 总行数: {len(lines)} | 对话行数: {len(dialogue_lines)} | 说话人轮次: {len(turns)}")
    print(f" 是否末幕(最后一幕): {'是' if is_last_act else '否'}")
    print(f"==================================================")

    if errors:
        print(f"❌ 发现 {len(errors)} 项严重违规，必须立即整改：")
        for err in errors:
            print(f"  - {err}")
    else:
        print("✅ 机械底线检查全部通过（零引号、零句首呼名、零八股对仗、零AI禁词、零元剧本词、零机械口癖）！")

    if warnings:
        print(f"⚠️ 发现 {len(warnings)} 项警告提示：")
        for w in warnings:
            print(f"  - {w}")

    print("==================================================\n")
    return len(errors) == 0

def main():
    parser = argparse.ArgumentParser(description="播客单幕文稿规范自检器")
    parser.add_argument("script_path", help="待检测的 Markdown 幕文件路径")
    parser.add_argument("--is-last-act", action="store_true", help="是否为全集最后一幕（第四幕）")
    args = parser.parse_args()

    ok = check_script(args.script_path, is_last_act=args.is_last_act)
    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
