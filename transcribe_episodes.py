#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小宇宙播客《有啥说啥｜用历史解码当下》Whisper GPU 高速语音转写工具
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
import torch
import whisper

sys.stdout.reconfigure(encoding='utf-8')

DEFAULT_AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "episodes")
DEFAULT_TRANSCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "transcripts")
META_PATH = os.path.join(DEFAULT_AUDIO_DIR, "episodes_metadata.json")

def format_timestamp(seconds: float, srt_format: bool = False) -> str:
    """格式化时间戳"""
    total_sec = int(seconds)
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60
    millis = int((seconds - int(seconds)) * 1000)
    
    if srt_format:
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    else:
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

def load_metadata():
    """加载节目元数据以便提取主持人与主题词"""
    if os.path.exists(META_PATH):
        try:
            with open(META_PATH, 'r', encoding='utf-8') as f:
                return json.load(f).get('episodes', [])
        except Exception:
            pass
    return []

def get_initial_prompt(episode_title: str, metadata_list: list) -> str:
    """根据单集标题匹配对应的主持人与背景提示词，大幅提高专有名词识别率"""
    hosts = "老罗（罗沙）、王悠悠、斯派克"
    theme_keywords = ""
    for ep in metadata_list:
        if ep.get('title') in episode_title or episode_title in ep.get('title', ''):
            desc = ep.get('description', '')[:200]
            # 提取前200字简介作为语境提示
            theme_keywords = desc.replace('\n', ' ')
            break
    
    prompt = f"以下是中文播客《有啥说啥｜用历史解码当下》的节目音频，主要主持人包括：{hosts}。对话内容使用规范简体中文并带有标点符号。"
    if theme_keywords:
        prompt += f" 本期主题语境：{theme_keywords[:150]}"
    return prompt

def save_outputs(audio_name: str, result: dict, out_dir: str):
    """保存 Markdown、SRT 字幕以及纯文本文件"""
    base_name = os.path.splitext(audio_name)[0]
    segments = result.get("segments", [])
    
    # 1. 保存 SRT 字幕文件
    srt_path = os.path.join(out_dir, f"{base_name}.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, seg in enumerate(segments, 1):
            start_str = format_timestamp(seg['start'], srt_format=True)
            end_str = format_timestamp(seg['end'], srt_format=True)
            text = seg['text'].strip()
            f.write(f"{idx}\n{start_str} --> {end_str}\n{text}\n\n")
            
    # 2. 保存格式化 Markdown 文件（带有时间戳与段落划分）
    md_path = os.path.join(out_dir, f"{base_name}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {base_name}\n\n")
        f.write(f"> **转写时间**：{time.strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"> **总分段数**：{len(segments)}  \n")
        f.write(f"> **音频文件**：`{audio_name}`\n\n")
        f.write("---\n\n### 对话转写记录（时间戳）\n\n")
        
        # 将相邻断句聚合成适度段落（每隔 ~30秒 或按自然停顿聚合并带时间戳）
        for seg in segments:
            t_start = format_timestamp(seg['start'])
            t_end = format_timestamp(seg['end'])
            text = seg['text'].strip()
            f.write(f"- **`{t_start} - {t_end}`** {text}\n\n")
            
    # 3. 保存纯文本 TXT（便于阅读与全文检索）
    txt_path = os.path.join(out_dir, f"{base_name}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(f"[{format_timestamp(seg['start'])}] {seg['text'].strip()}\n")
            
    return md_path, srt_path, txt_path

def main():
    parser = argparse.ArgumentParser(description="使用 Whisper 转写播客音频")
    parser.add_argument("--model", default="large-v3-turbo", help="Whisper 模型名称 (默认: large-v3-turbo)")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu", help="计算设备")
    parser.add_argument("--audio_dir", default=DEFAULT_AUDIO_DIR, help="音频目录")
    parser.add_argument("--out_dir", default=DEFAULT_TRANSCRIPT_DIR, help="转写文本输出目录")
    parser.add_argument("--index", type=int, default=0, help="按序号指定单集 (例如: --index 3)")
    parser.add_argument("--limit", type=int, default=0, help="仅转写前 N 个音频文件 (0 表示全部)")
    parser.add_argument("--file", type=str, default="", help="指定单个音频文件名转写")
    parser.add_argument("--beam_size", type=int, default=1, help="Beam search 大小 (1 为快速贪婪解码约2-3分钟/期，5 为高精度约10分钟/期)")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    metadata_list = load_metadata()

    # 扫描待转写音频
    if args.index > 0:
        prefix = f"{args.index:02d}."
        matched = [p for p in Path(args.audio_dir).glob("*.m4a") if p.name.startswith(prefix)]
        if not matched:
            print(f"[!] 未找到以 {prefix} 开头的音频文件")
            return
        audio_files = matched
    elif args.file:
        full_path = os.path.join(args.audio_dir, args.file) if not os.path.isabs(args.file) else args.file
        if not os.path.exists(full_path):
            print(f"[!] 指定文件不存在: {full_path}")
            return
        audio_files = [Path(full_path)]
    else:
        audio_files = sorted(Path(args.audio_dir).glob("*.m4a"))
        if args.limit > 0:
            audio_files = audio_files[:args.limit]

    if not audio_files:
        print(f"[!] 未在 {args.audio_dir} 找到任何 .m4a 音频文件")
        return

    print("=" * 60)
    print(f"[*] 发现 {len(audio_files)} 个音频待处理")
    print(f"[*] 使用模型: {args.model} (设备: {args.device})")
    print(f"[*] 输出目录: {args.out_dir}")
    print("=" * 60)

    print(f"[*] 正在加载 Whisper 模型 `{args.model}`...")
    t_load = time.time()
    model = whisper.load_model(args.model, device=args.device)
    print(f"[√] 模型加载完成，耗时: {time.time() - t_load:.2f} 秒\n")

    for i, audio_path in enumerate(audio_files, 1):
        filename = audio_path.name
        base_name = audio_path.stem
        md_target = os.path.join(args.out_dir, f"{base_name}.md")
        
        # 检查是否已转写
        if os.path.exists(md_target) and os.path.getsize(md_target) > 500:
            print(f"[{i}/{len(audio_files)}] [已转写跳过] {filename}")
            continue

        print(f"[{i}/{len(audio_files)}] 正在转写: {filename}")
        t_start = time.time()
        initial_prompt = get_initial_prompt(base_name, metadata_list)
        
        try:
            result = model.transcribe(
                str(audio_path),
                language="zh",
                initial_prompt=initial_prompt,
                temperature=0.0,
                beam_size=args.beam_size,
                best_of=args.beam_size,
                verbose=False
            )
            elapsed = time.time() - t_start
            md_path, srt_path, txt_path = save_outputs(filename, result, args.out_dir)
            seg_count = len(result.get("segments", []))
            print(f"    [√] 转写完成 (用时 {elapsed:.1f}s, 分段数: {seg_count})")
            print(f"        -> Markdown: {os.path.basename(md_path)}")
            print(f"        -> 字幕 SRT: {os.path.basename(srt_path)}")
        except Exception as e:
            print(f"    [!] 转写出错: {e}")

    print("\n[√] 转写流程结束！")

if __name__ == "__main__":
    main()
