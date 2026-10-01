#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_voice.py — 双人播客音色纯度体检（EP05 第三音色排查工具）
================================================================
原理：大开（男声刘飞）与小李（女声咪仔）基频(f0)区间差异明显；
      任何"第三个音色"或段内变声都会表现为 f0 异常。
用法：
  # mp3 解码慢，先用 ffmpeg 转 wav（快），再体检：
  ffmpeg -y -i 完整版.mp3 -ac 1 -ar 16000 -f wav 完整版_体检用.wav
  python audit_voice.py 完整版_体检用.wav 完整版.srt --out 报告.json
输出：每条字幕的 f0 统计 + 可疑段清单（声部错位 / 段内双声部）
判定：
  A. 声部错位：段中位 f0 相对该说话人全局中位偏离 >45%（约半gender距离）
  B. 段内双声部：voiced f0 两簇中心比 >1.45 且小簇帧占比 >15%

⚠️ 结果解读（EP05 实战经验，2026-09-21）：
  1. "段内双声部"绝大多数是自相关的谐波误报（高簇≈2×或3×低簇：
     小李段高簇~370Hz≈2×185，大开段高簇~390Hz≈3×130），**不是异常**。
  2. 唯一硬指标是"声部错位"，且要交叉验证：对嫌疑段跑谐波间隔法
     （FFT 强峰间隔=基频，见 EP05 修复记录），或看低簇是否落在对方性别区间。
  3. 结尾 1 秒告别短段（拜拜/再见）的声部错位多为升调短句的正常上扬。
  4. 确认真异常后：微调该句 md 消除触发源（角色场景类比/引语/叹号密集），
     重录该幕。注意 API 非确定性——同句重录可能复发，改文案才根治。
"""
import argparse
import json
import re
import sys

import numpy as np
import librosa

sys.stdout.reconfigure(encoding="utf-8")


def parse_srt(path):
    # concat_episode.py writes one trailing newline, not an extra blank line.
    # Normalize EOF so the final cue is parsed just like every earlier block.
    srt = open(path, encoding="utf-8").read().rstrip() + "\n\n"
    blocks = re.findall(
        r"(\d+)\n(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})\n(.+?)\n\n",
        srt, re.S)
    out = []
    for b in blocks:
        idx = int(b[0])
        start = int(b[1]) * 3600 + int(b[2]) * 60 + int(b[3]) + int(b[4]) / 1000
        end = int(b[5]) * 3600 + int(b[6]) * 60 + int(b[7]) + int(b[8]) / 1000
        text = b[9].strip()
        speaker = text.split(":", 1)[0] if ":" in text else "?"
        out.append({"idx": idx, "start": start, "end": end,
                    "speaker": speaker, "text": text})
    return out


def seg_f0(y, sr, start, end):
    """FFT 自相关基频估计（纯 numpy，避开 librosa.yin 在部分环境的性能问题）。
    帧 40ms/hop 10ms；lag 搜索范围 65-420Hz；归一化自相关峰 >0.45 判 voiced。"""
    s = max(0, int(start * sr) - int(0.05 * sr))
    e = min(len(y), int(end * sr) + int(0.05 * sr))
    if e - s < int(0.3 * sr):
        return None
    seg = y[s:e].astype(np.float64)
    frame, hop = int(0.04 * sr), int(0.01 * sr)
    lag_min, lag_max = int(sr / 420), int(sr / 65)
    n_frames = max(0, (len(seg) - frame) // hop + 1)
    if n_frames == 0:
        return None
    idx = np.arange(frame)[None, :] + hop * np.arange(n_frames)[:, None]
    frames = seg[idx]
    win = np.hanning(frame)
    fw = frames * win
    nfft = 1
    while nfft < 2 * frame:
        nfft *= 2
    spec = np.fft.rfft(fw, nfft, axis=1)
    ac = np.fft.irfft(spec * np.conj(spec), nfft, axis=1)[:, :frame]
    power = (fw ** 2).sum(axis=1)
    ac = ac / np.maximum(power[:, None], 1e-12)
    lags = np.arange(lag_min, lag_max + 1)
    cand = ac[:, lags]
    best = cand.argmax(axis=1)
    peak = cand[np.arange(n_frames), best]
    voiced = peak > 0.45
    lag = lags[best][voiced]
    if len(lag) == 0:
        return None
    return sr / lag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mp3")
    ap.add_argument("srt")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    print(f"加载音频 {args.mp3} ...")
    try:
        import soundfile as sf
        y, sr = sf.read(args.mp3, dtype="float32", always_2d=True)
        y = y.mean(axis=1)  # mono
        if sr != 16000:  # 罕见：非16k时重采样
            y = librosa.resample(y, orig_sr=sr, target_sr=16000)
            sr = 16000
    except Exception as e:
        print(f"soundfile 读取失败（{e}），回退 librosa.load ...")
        y, sr = librosa.load(args.mp3, sr=16000, mono=True)
    dur = len(y) / sr
    print(f"时长 {dur/60:.1f} 分钟，sr={sr}")

    blocks = parse_srt(args.srt)
    print(f"字幕 {len(blocks)} 条；逐段测基频（pyin）...")

    results = []
    for i, b in enumerate(blocks):
        v = seg_f0(y, sr, b["start"], b["end"])
        if v is None or len(v) < 5:
            results.append({**b, "n_voiced": 0 if v is None else len(v)})
            continue
        med = float(np.median(v))
        p10, p90 = np.percentile(v, [10, 90])
        results.append({**b, "n_voiced": int(len(v)), "f0_med": round(med, 1),
                        "f0_p10": round(float(p10), 1), "f0_p90": round(float(p90), 1),
                        "_f0": v.tolist()})
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{len(blocks)} 段...")

    # 全局每说话人中位
    glob = {}
    for spk in ("大开", "小李"):
        meds = [r["f0_med"] for r in results if r.get("speaker") == spk and "f0_med" in r]
        if meds:
            glob[spk] = float(np.median(meds))
    print(f"全局中位 f0: {glob}")

    # 异常判定
    suspicious = []
    for r in results:
        spk = r.get("speaker")
        if "f0_med" not in r or spk not in glob:
            continue
        g = glob[spk]
        flags = []
        ratio = r["f0_med"] / g
        if ratio < 0.55 or ratio > 1.45:
            flags.append(f"声部错位(段中位{r['f0_med']}Hz vs {spk}全局{g:.0f}Hz, 比值{ratio:.2f})")
        v = np.array(r.pop("_f0"))
        # 段内双声部：2-means
        lo, hi = v.min(), v.max()
        if hi / lo > 1.45 and len(v) >= 10:
            c = np.array([lo, hi], float)
            for _ in range(30):
                d = np.abs(v[:, None] - c[None, :])
                lab = d.argmin(1)
                newc = np.array([v[lab == k].mean() if (lab == k).any() else c[k] for k in (0, 1)])
                if np.allclose(newc, c):
                    break
                c = newc
            minor = min((lab == k).mean() for k in (0, 1))
            if minor > 0.15 and c[1] / c[0] > 1.45:
                flags.append(f"段内双声部(簇{c[0]:.0f}Hz/{c[1]:.0f}Hz, 小簇占比{minor:.0%})")
        if flags:
            suspicious.append({
                "idx": r["idx"], "start": r["start"], "end": r["end"],
                "speaker": spk, "text": r["text"][:60],
                "f0_med": r.get("f0_med"), "flags": flags})

    print(f"\n===== 可疑段 {len(suspicious)} 条 =====")
    for s in suspicious:
        m, sec = divmod(s["start"], 60)
        print(f"[{int(m):02d}:{sec:05.2f}] #{s['idx']} {s['speaker']} f0={s['f0_med']}Hz | "
              f"{'; '.join(s['flags'])} | {s['text']}")

    if args.out:
        json.dump({"global_median_f0": glob, "suspicious": suspicious,
                   "segments": [{k: v for k, v in r.items() if k != "_f0"} for r in results]},
                  open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"报告已写入 {args.out}")


if __name__ == "__main__":
    main()
