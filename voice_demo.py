#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音色试听样生成器：用同一句台词为多个候选音色各合成一段小样，供人工试听选型。
选型铁律：音色气质靠听不靠猜——让用户圈候选后各合成 15 秒小样对比定夺。

用法（在用户项目目录运行，复用同目录 doubao_podcast_pipeline.py 的 synthesize_batch）:
  python voice_demo.py --creds-file <凭据文件> --outdir 试听音色

适配新节目时改两处：
  1. LINE_HOST / LINE_COHOST —— 换成本节目的开场白（主讲/主持各一段，组内文本一致才好对比）
  2. CANDIDATES —— 换成圈定的候选音色（文件名, host|cohost, voice_type）
音色全库: https://www.volcengine.com/docs/6561/1257544
（预置 ICL_ 音色可直接用；_emo_ 多情感与 mix 音色不可用于播客 API）

断点续跑：已存在且 >100KB 的样片自动跳过；单个失败自动重试 1 次且不影响其余。
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doubao_podcast_pipeline import synthesize_batch

sys.stdout.reconfigure(encoding="utf-8")

# 试听台词（示例为《笑谈历史》；组内文本一致保证对比公平）
LINE_HOST = ("大家好，我是大开。今天咱们聊一个明朝狠人，王阳明。"
             "这人厉害到什么程度？临终的时候学生问他，先生还有什么遗言，"
             "他就留了八个字：此心光明，亦复何言。")
LINE_COHOST = ("哈喽大家好，我是小李，欢迎回到笑谈历史。"
               "大开今天要讲的这个故事信息量有点大，大家先坐稳，"
               "我去给各位倒杯茶，咱们慢慢聊。")

# 候选清单（2026-09 实测全部可用；播客配对音色 saturn 系列、通用 uranus 系列、预置 ICL 系列）
CANDIDATES = [
    ("01_刘飞_主讲",       "host",   "zh_male_liufei_v2_saturn_bigtts"),
    ("02_大壹_主讲",       "host",   "zh_male_dayixiansheng_v2_saturn_bigtts"),
    ("03_深夜播客2.0_主讲", "host",   "zh_male_shenyeboke_uranus_bigtts"),
    ("04_磁性解说男声_主讲", "host",  "zh_male_cixingjieshuonan_uranus_bigtts"),
    ("05_霸气青叔_主讲",    "host",   "zh_male_baqiqingshu_uranus_bigtts"),
    ("06_温润学者ICL_主讲", "host",   "ICL_uranus_zh_male_wenrunxuezhe_tob"),
    ("07_仗剑侠客ICL_主讲", "host",   "ICL_uranus_zh_male_zhangjianxiake_tob"),
    ("08_幽默大爷ICL_主讲", "host",   "ICL_uranus_zh_male_youmodaye_tob"),
    ("09_幽默叔叔ICL_主讲", "host",   "ICL_uranus_zh_male_youmoshushu_tob"),
    ("10_潇磊_主持",        "cohost", "zh_male_xiaolei_v2_saturn_bigtts"),
    ("11_清爽男大_主持",    "cohost", "zh_male_qingshuangnanda_uranus_bigtts"),
    ("12_开朗学长_主持",    "cohost", "zh_male_kailangxuezhang_uranus_bigtts"),
    ("13_率真小伙ICL_主持", "cohost", "ICL_uranus_zh_male_shuaizhenxiaohuo_tob"),
    ("14_机灵小伙ICL_主持", "cohost", "ICL_uranus_zh_male_jilingxiaohuo_tob"),
    ("15_咪仔_主持_女声",   "cohost", "zh_female_mizaitongxue_v2_saturn_bigtts"),
]


def load_creds(path):
    raw = open(path, encoding="utf-8").read().split()
    labels = {"APP", "ID", "ACCESS", "TOKEN"}
    vals = [v for v in raw if v.upper().strip("：:") not in labels]
    return vals[0], vals[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--creds-file", required=True)
    ap.add_argument("--outdir", default="试听音色")
    args = ap.parse_args()

    appid, token = load_creds(args.creds_file)
    os.makedirs(args.outdir, exist_ok=True)
    ok, fail = [], []

    for name, role, voice in CANDIDATES:
        text = LINE_HOST if role == "host" else LINE_COHOST
        out_path = os.path.join(args.outdir, f"{name}.mp3")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 100_000:
            print(f"[跳过] {name}（已存在）")
            ok.append(name)
            continue
        done = False
        for attempt in (1, 2):
            try:
                print(f"[合成] {name} -> {voice}（第{attempt}次）")
                audio, timeline, _ = synthesize_batch(
                    [{"speaker": "voice", "text": text}],
                    {"voice": voice}, appid, token,
                    head_music=False, tail_music=False, timeout=120, verbose=False)
                if len(audio) < 50_000:
                    raise RuntimeError(f"音频过小({len(audio)}B)，疑似失败")
                open(out_path, "wb").write(bytes(audio))
                dur = max((r.get("end_time", 0) for r in timeline), default=0)
                print(f"  完成: {len(audio)/1024:.0f}KB 约{dur:.0f}s -> {out_path}")
                ok.append(name)
                done = True
                break
            except Exception as e:
                print(f"  失败: {e}")
                time.sleep(2)
        if not done:
            fail.append(name)

    print("\n===== 汇总 =====")
    print(f"成功 {len(ok)}: {', '.join(ok)}")
    if fail:
        print(f"失败 {len(fail)}: {', '.join(fail)}")
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
