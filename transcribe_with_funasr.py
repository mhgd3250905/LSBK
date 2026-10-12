#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小宇宙播客《有啥说啥｜用历史解码当下》FunASR + CAM++ 说话人自动分离转写工具
自带阿里达摩院声纹识别 (CAM++)，可精准区分老罗、王悠悠、斯派克等不同主持人发言。
"""

import os
import re
import sys
import time
import json
import argparse
from pathlib import Path
import torch

sys.stdout.reconfigure(encoding='utf-8')

# 本地 ModelScope 模型缓存目录
MODELSCOPE_CACHE = Path(r"E:\AII\TUI\.cache\modelscope")
MODEL_BASE = MODELSCOPE_CACHE / "models" / "iic"

MODEL_ASR = MODEL_BASE / "speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
MODEL_VAD = MODEL_BASE / "speech_fsmn_vad_zh-cn-16k-common-pytorch"
MODEL_PUNC = MODEL_BASE / "punc_ct-transformer_zh-cn-common-vocab272727-pytorch"
MODEL_SPK = MODEL_BASE / "speech_campplus_sv_zh-cn_16k-common"

DEFAULT_AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "episodes")
DEFAULT_TRANSCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "transcripts_diarized")
META_PATH = os.path.join(DEFAULT_AUDIO_DIR, "episodes_metadata.json")

def format_time(ms: int, srt: bool = False) -> str:
    """毫秒时间转可读格式"""
    total_sec = ms / 1000.0
    hrs = int(total_sec // 3600)
    mins = int((total_sec % 3600) // 60)
    secs = int(total_sec % 60)
    millis = int((total_sec - int(total_sec)) * 1000)
    if srt:
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

def identify_speaker_names(sentences: list, fallback_names: list = None) -> dict:
    """
    智能分析自我介绍识别说话人姓名（例如“我是老罗” -> Speaker 0 为老罗）
    """
    speaker_map = {}
    known_hosts = ["老罗", "斯巴克", "斯派克", "王悠悠", "悠悠", "张大夫"]
    
    # 扫描前 5 分钟的句子看是否有自我介绍
    for s in sentences:
        if s.get("start", 0) > 300000:  # 超过5分钟停止扫描介绍
            break
        text = s.get("text", "")
        spk = s.get("spk")
        if spk not in speaker_map:
            for host in known_hosts:
                # 匹配：我是老罗、老罗在这、大家好我是xxx
                if f"我是{host}" in text or f"我{host}" in text or f"叫{host}" in text:
                    formal_name = "斯派克" if host == "斯巴克" else ("王悠悠" if host == "悠悠" else host)
                    speaker_map[spk] = formal_name
                    break

    # 未能识别出的 speaker 赋予规范称呼
    all_spks = sorted({s.get("spk", 0) for s in sentences})
    for idx, spk in enumerate(all_spks):
        if spk not in speaker_map:
            speaker_map[spk] = f"说话人_{idx+1}"

    return speaker_map

def merge_consecutive_utterances(sentences: list, speaker_map: dict) -> list:
    """将同一个人连续说的短句合并为一个完整语段"""
    if not sentences:
        return []
    
    merged = []
    curr = {
        "speaker": speaker_map.get(sentences[0].get("spk", 0), "说话人"),
        "start": sentences[0].get("start", 0),
        "end": sentences[0].get("end", 0),
        "texts": [sentences[0].get("text", "").strip()]
    }
    
    for s in sentences[1:]:
        spk_name = speaker_map.get(s.get("spk", 0), "说话人")
        start = s.get("start", 0)
        end = s.get("end", 0)
        text = s.get("text", "").strip()
        
        # 如果是同一个人，且停顿间隔在 2.5 秒以内，合并语段
        if spk_name == curr["speaker"] and (start - curr["end"] < 2500):
            curr["end"] = end
            if text:
                curr["texts"].append(text)
        else:
            if curr["texts"]:
                merged.append(curr)
            curr = {
                "speaker": spk_name,
                "start": start,
                "end": end,
                "texts": [text] if text else []
            }
            
    if curr["texts"]:
        merged.append(curr)
        
    return merged

def save_transcript_outputs(base_name: str, merged_dialogues: list, out_dir: str):
    """保存 Markdown 剧本格式与 SRT 字幕"""
    md_path = os.path.join(out_dir, f"{base_name}.md")
    srt_path = os.path.join(out_dir, f"{base_name}.srt")
    txt_path = os.path.join(out_dir, f"{base_name}.txt")

    # 1. 保存 Markdown 对话录
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {base_name}\n\n")
        f.write(f"> **转写引擎**：FunASR + CAM++ 声纹说话人分离  \n")
        f.write(f"> **生成时间**：{time.strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"> **总轮换段落数**：{len(merged_dialogues)}  \n\n")
        f.write("---\n\n### 🎙️ 节目对话实录（已标注说话人）\n\n")
        
        for item in merged_dialogues:
            t_start = format_time(item['start'])
            t_end = format_time(item['end'])
            spk = item['speaker']
            full_text = "".join(item['texts'])
            f.write(f"**【{spk}】** `[{t_start} - {t_end}]`  \n{full_text}\n\n")

    # 2. 保存带说话人名字的 SRT 字幕
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, item in enumerate(merged_dialogues, 1):
            s_str = format_time(item['start'], srt=True)
            e_str = format_time(item['end'], srt=True)
            spk = item['speaker']
            full_text = "".join(item['texts'])
            f.write(f"{idx}\n{s_str} --> {e_str}\n[{spk}] {full_text}\n\n")

    # 3. 纯文本
    with open(txt_path, "w", encoding="utf-8") as f:
        for item in merged_dialogues:
            t_start = format_time(item['start'])
            spk = item['speaker']
            full_text = "".join(item['texts'])
            f.write(f"[{t_start}] 【{spk}】: {full_text}\n")

    return md_path, srt_path

def main():
    parser = argparse.ArgumentParser(description="FunASR + CAM++ 说话人自动分离与语音转写")
    parser.add_argument("--audio_dir", default=DEFAULT_AUDIO_DIR, help="音频目录")
    parser.add_argument("--out_dir", default=DEFAULT_TRANSCRIPT_DIR, help="输出目录")
    parser.add_argument("--file", type=str, default="", help="指定单个音频文件名处理")
    parser.add_argument("--limit", type=int, default=0, help="仅转写前 N 个文件")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    os.environ["MODELSCOPE_CACHE"] = str(MODELSCOPE_CACHE)

    print("=" * 65)
    print(" 阿里 FunASR + CAM++ 说话人识别与语音转写系统")
    print(f"[*] 音频源目录: {args.audio_dir}")
    print(f"[*] 输出目录  : {args.out_dir}")
    print("=" * 65)

    from funasr import AutoModel
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"[*] 正在加载 FunASR 本地模型 (设备: {device})...")
    t0 = time.time()
    model = AutoModel(
        model=str(MODEL_ASR),
        vad_model=str(MODEL_VAD),
        punc_model=str(MODEL_PUNC),
        spk_model=str(MODEL_SPK),
        device=device,
        disable_update=True,
    )
    print(f"[√] 模型就绪！耗时: {time.time() - t0:.2f} 秒\n")

    if args.file:
        audio_files = [Path(os.path.join(args.audio_dir, args.file))]
    else:
        audio_files = sorted(Path(args.audio_dir).glob("*.m4a"))
        if args.limit > 0:
            audio_files = audio_files[:args.limit]

    print(f"[*] 待处理音频文件数: {len(audio_files)}")

    for idx, audio_path in enumerate(audio_files, 1):
        if not audio_path.exists():
            continue
        base_name = audio_path.stem
        target_md = os.path.join(args.out_dir, f"{base_name}.md")
        if os.path.exists(target_md) and os.path.getsize(target_md) > 1000:
            print(f"[{idx}/{len(audio_files)}] [已完成跳过] {audio_path.name}")
            continue

        print(f"\n[{idx}/{len(audio_files)}] 正在识别与分离说话人: {audio_path.name}")
        t_start = time.time()
        try:
            res = model.generate(input=str(audio_path))
            sentence_info = res[0].get("sentence_info", [])
            
            # 智能映射说话人真实姓名
            speaker_map = identify_speaker_names(sentence_info)
            print(f"    [*] 说话人检测映射结果: {speaker_map}")

            # 合并同说话人连续语句
            merged = merge_consecutive_utterances(sentence_info, speaker_map)
            md_path, srt_path = save_transcript_outputs(base_name, merged, args.out_dir)
            
            elapsed = time.time() - t_start
            print(f"    [√] 转写与角色分离完成！耗时: {elapsed:.1f} 秒，共生成 {len(merged)} 处对话轮换")
            print(f"        -> Markdown 剧本文档: {os.path.basename(md_path)}")
            print(f"        -> 带角色字幕文件  : {os.path.basename(srt_path)}")
        except Exception as e:
            print(f"    [!] 处理失败: {e}")

if __name__ == "__main__":
    main()
