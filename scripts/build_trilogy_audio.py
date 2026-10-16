# -*- coding: utf-8 -*-
"""
build_trilogy_audio.py — 《笑谈历史》李自成三部曲（EP30/31/32）全自动顺序合成总控脚本
================================================================================
顺序执行：
1. EP30_李自成上（从下岗驿卒到商洛山：四幕合成 + 完整版拼接 + ffmpeg体检）
2. EP31_李自成中（一呼百万：四幕合成 + 完整版拼接 + ffmpeg体检）
3. EP32_李自成下（四十二天皇帝与九宫山谜案：四幕合成 + 完整版拼接 + ffmpeg体检）

按顺序推进，遇到失败立即中断并报告。
"""
import os
import subprocess
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PODCASTS_DIR = os.path.join(ROOT_DIR, "podcasts")

episodes = [
    ("EP30_李自成上", "李自成上：戴死囚大枷、破窑拔刀杀人，一个穷汉是如何熬死大明十面罗网的？"),
    ("EP31_李自成中", "李自成中：吓跪三百斤福王、一句口号卷走中原，流民巨兽是如何把大明逼到悬崖的？"),
    ("EP32_李自成下", "李自成终局：当了一天皇帝、一把火烧了紫禁城，一代闯王为何最终死在一条烂泥沟里？"),
]

def run_episode_synthesis(ep_folder, title):
    print(f"\n{'='*70}")
    print(f"🎙️  开始生产单集音频: {ep_folder} —— 《{title}》")
    print(f"{'='*70}")
    start_time = time.time()
    
    script_path = os.path.join(PODCASTS_DIR, ep_folder, "run_synthesis.py")
    if not os.path.exists(script_path):
        print(f"❌ 找不到合成脚本: {script_path}")
        return False
        
    cmd = [sys.executable, script_path]
    proc = subprocess.run(cmd, cwd=os.path.join(PODCASTS_DIR, ep_folder))
    if proc.returncode != 0:
        print(f"\n❌ {ep_folder} 合成流水线执行失败，退出码: {proc.returncode}")
        return False
        
    elapsed = time.time() - start_time
    m, s = divmod(int(elapsed), 60)
    print(f"\n✅ {ep_folder} 生产完成！耗时: {m}分{s}秒")
    return True

def main():
    print("======================================================================")
    print(" 开始推进《笑谈历史》大明终局·李自成三部曲 音频全自动化顺序生产")
    print("======================================================================")
    
    total_start = time.time()
    results = {}
    
    for ep_folder, title in episodes:
        success = run_episode_synthesis(ep_folder, title)
        results[ep_folder] = success
        if not success:
            print(f"\n⚠️  由于 {ep_folder} 失败，按规范暂停后续单集生产，等待排查。")
            sys.exit(1)
            
    total_elapsed = time.time() - total_start
    tm, ts = divmod(int(total_elapsed), 60)
    
    print("\n" + "="*70)
    print("🎉🎉 李自成三部曲（EP30 / EP31 / EP32）全部 12 幕音频生产圆满收官！🎉🎉")
    print(f"总计耗时: {tm}分{ts}秒")
    print("="*70)
    for ep_folder, title in episodes:
        out_mp3 = os.path.join(PODCASTS_DIR, ep_folder, "output", "完整版.mp3")
        out_srt = os.path.join(PODCASTS_DIR, ep_folder, "output", "完整版.srt")
        mp3_size = os.path.getsize(out_mp3) / 1024 / 1024 if os.path.exists(out_mp3) else 0
        srt_lines = len(open(out_srt, encoding='utf-8').readlines()) if os.path.exists(out_srt) else 0
        print(f"- {ep_folder} 《{title}》: MP3 {mp3_size:.1f} MB | SRT {srt_lines} 行")

if __name__ == "__main__":
    main()
