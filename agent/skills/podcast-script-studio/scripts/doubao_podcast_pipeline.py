#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
豆包播客语音流水线：时间脚本.txt → 豆包播客API(action=3) → MP3 + SRT字幕
=================================================================
用法:
  # 干跑（不调API，只验证解析与切分，输出请求JSON预览）
  python doubao_podcast_pipeline.py 第一幕_时间脚本.txt --dry-run

  # 正式合成（凭据用环境变量，避免明文）
  set VOLC_APP_ID=xxx
  set VOLC_ACCESS_TOKEN=xxx
  python doubao_podcast_pipeline.py 第一幕_时间脚本.txt --outdir 输出目录

协议依据: 《播客API-websocket-v3协议》PDF（action=3 指定对话文本直接合成，不改写内容）
关键限制: 单轮<=300字符 / 单次调用总量<=10000字符（本脚本自动切分与分批）
"""
import argparse
import gzip
import json
import os
import random
import string
import struct
import sys
import time
import uuid

try:
    import websocket  # websocket-client
except ImportError:
    print("缺少依赖: pip install websocket-client")
    sys.exit(1)

sys.stdout.reconfigure(encoding="utf-8")

# ---------------- 协议常量（与文档字节举例一致） ----------------
WS_URL = "https://openspeech.bytedance.com/api/v3/sami/podcasttts"
RESOURCE_ID = "volc.service_type.10050"
APP_KEY = "aGjiRDfUWi"  # 文档固定值

EVENT_START_SESSION = 1
EVENT_FINISH_CONNECTION = 2
# 下行事件
EVT_SESSION_STARTED = 150
EVT_ROUND_START = 360
EVT_ROUND_AUDIO = 361
EVT_ROUND_END = 362
EVT_PODCAST_END = 363
EVT_SESSION_FINISHED = 152
EVT_USAGE = 154
EVT_CONNECTION_FINISHED = 52

# 默认音色映射（按项目 podcasts/节目档案.md；示例为《笑谈历史》：大开=刘飞，小李=咪仔女声；可用 --map 覆盖）
DEFAULT_VOICE_MAP = {
    "大开": "zh_male_liufei_v2_saturn_bigtts",
    "小李": "zh_female_mizaitongxue_v2_saturn_bigtts",
}

MAX_CHARS_PER_ROUND = 280   # 官方上限300，留余量
MAX_CHARS_PER_CALL = 9500   # 官方上限10000，留余量


# ---------------- 1. 时间脚本解析 ----------------
def parse_time_script(path):
    """解析 [mm:ss - mm:ss] 说话人 + 台词 格式，返回轮次列表。"""
    turns = []
    cur = None
    with open(path, encoding="utf-8") as f:
        for raw in f.readlines():
            line = raw.rstrip("\n").strip()
            if not line:
                continue
            if line.startswith("====") or (line.startswith("（") and line.endswith("）")):
                continue  # 分隔线与"（第X幕完…）"类尾注行，禁止进入合成文本
            if line.startswith("[") and "]" in line:
                import re
                m = re.match(r"\[\s*(\d+:\d+)\s*-\s*(\d+:\d+)\s*\]\s*(.*)", line)
                if m:
                    rest = m.group(3).strip()
                    parts = rest.split(None, 1)
                    speaker = parts[0] if parts else ""
                    inline_text = parts[1].strip() if len(parts) > 1 else ""
                    cur = {"speaker": speaker, "start": m.group(1), "text": inline_text}
                    turns.append(cur)
                continue
            if line.startswith("EP") or line.startswith("净台词") or line.startswith("说话人") or line.startswith("总时长"):
                continue  # 头部元信息
            if cur is not None:
                cur["text"] += ("" if not cur["text"] else " ") + line
            # 形如"（第一幕完…）"的尾注行会被并入上一轮文本，下面统一清洗
    # 清洗：剥离舞台提示（（笑）（停顿）（停顿两秒）等）与尾注行
    import re
    for t in turns:
        t["text"] = re.sub(r"（[^）]{0,12}）", "", t["text"])  # 短舞台提示
        t["text"] = re.sub(r"\([^)]{0,12}\)", "", t["text"])
        t["text"] = t["text"].replace("（第一幕完", "").strip()
    turns = [t for t in turns if t["text"]]
    return turns


# ---------------- 2. 长轮切分与分批 ----------------
def split_long_rounds(turns, limit=MAX_CHARS_PER_ROUND):
    out = []
    for t in turns:
        text = t["text"]
        if len(text) <= limit:
            out.append({**t, "text": text})
            continue
        # 按句末标点切，尽量接近 limit
        import re
        sentences = re.split(r"(?<=[。！？!?；;])", text)
        buf = ""
        for s in sentences:
            if len(buf) + len(s) > limit and buf:
                out.append({**t, "text": buf})
                buf = s
            else:
                buf += s
        if buf:
            out.append({**t, "text": buf})
    return out


def chunk_into_batches(turns, limit=MAX_CHARS_PER_CALL):
    batches, cur, size = [], [], 0
    for t in turns:
        if size + len(t["text"]) > limit and cur:
            batches.append(cur)
            cur, size = [], 0
        cur.append(t)
        size += len(t["text"])
    if cur:
        batches.append(cur)
    return batches


# ---------------- 3. 二进制协议（对齐官方 agentkit-samples 实现） ----------------
MSG_FULL_CLIENT = 0b0001  # FullClientRequest
FLAG_WITH_EVENT = 0b0100


def build_frame(event, payload: bytes, session_id: str = None):
    """官方时序: StartConnection(event=1,无sid) / StartSession(event=100,带sid)
    / FinishSession(event=102,带sid) / FinishConnection(event=2,无sid)。"""
    header = bytes([0x11, (MSG_FULL_CLIENT << 4) | FLAG_WITH_EVENT, 0x10, 0x00])
    frame = header + struct.pack(">i", event)
    if session_id is not None:  # 连接类事件(1/2)不写session_id，会话类(100/102)写
        sid = session_id.encode()
        frame += struct.pack(">I", len(sid)) + sid
    frame += struct.pack(">I", len(payload)) + payload
    return frame


def parse_frame(data):
    """解析下行帧: 返回 (event, payload_bytes)。"""
    if len(data) < 4:
        return None, None
    msg_type_flags = data[1]
    ser, comp = (data[2] >> 4) & 0xF, data[2] & 0xF
    pos = 4
    event = None
    flags = msg_type_flags & 0xF
    if flags & 0x4:  # 带 event number
        if len(data) < pos + 4:
            return None, None
        event = struct.unpack(">I", data[pos:pos + 4])[0]
        pos += 4
        # session_id
        if len(data) < pos + 4:
            return event, b""
        sid_len = struct.unpack(">I", data[pos:pos + 4])[0]
        pos += 4 + sid_len
    # payload size + payload
    if len(data) >= pos + 4:
        plen = struct.unpack(">I", data[pos:pos + 4])[0]
        pos += 4
        payload = data[pos:pos + plen] if plen else b""
    else:
        payload = b""
    if comp == 1 and payload:
        try:
            payload = gzip.decompress(payload)
        except OSError:
            pass
    return event, payload


# ---------------- 4. 单批合成 ----------------
def synthesize_batch(turns, voice_map, appid, token, head_music=False, tail_music=False,
                     timeout=900, verbose=True):
    """调用豆包播客API合成一批轮次（官方时序）。
    时序: StartConnection(1)→<50→StartSession(100)→<150→FinishSession(102)→收流→FinishConnection(2)"""
    session_id = str(uuid.uuid4())
    speakers = sorted({voice_map[t["speaker"]] for t in turns if t["speaker"] in voice_map})
    req = {
        "input_id": "podcast_input",
        "action": 3,
        "nlp_texts": [{"speaker": voice_map[t["speaker"]], "text": t["text"]} for t in turns],
        "audio_config": {"format": "mp3", "sample_rate": 24000, "speech_rate": 0},
        "speaker_info": {"random_order": False, "speakers": speakers},  # 指哪打哪：顺序由脚本决定
        "use_head_music": head_music,
        "use_tail_music": tail_music,
        "input_info": {"return_audio_url": True},
    }
    payload = json.dumps(req, ensure_ascii=False).encode("utf-8")

    ws = websocket.create_connection(
        WS_URL.replace("https", "wss"),
        header=[f"X-Api-App-Id: {appid}", f"X-Api-Access-Key: {token}",
                f"X-Api-Resource-Id: {RESOURCE_ID}", f"X-Api-App-Key: {APP_KEY}"],
        timeout=timeout,
    )

    audio, timeline, audio_url = bytearray(), [], None
    cur_round = {}
    ws.settimeout(timeout)

    def recv_msg():
        """收一帧，返回 (event, payload_bytes)；连接断开抛异常。"""
        while True:
            data = ws.recv()
            if isinstance(data, str):
                continue
            event, payload_bytes = parse_frame(data)
            if event is not None:
                return event, payload_bytes

    try:
        # 1) StartConnection（event=1，无 session_id）
        ws.send_binary(build_frame(1, b"{}"))
        ev, _ = recv_msg()
        if ev != 50:
            print(f"  [warn] 期望ConnectionStarted(50)，实际 event={ev}")
        elif verbose:
            print("  握手成功(ConnectionStarted)")

        # 2) StartSession（event=100，带 session_id + 任务payload）
        ws.send_binary(build_frame(100, payload, session_id))
        ev, _ = recv_msg()
        if ev != 150:
            print(f"  [warn] 期望SessionStarted(150)，实际 event={ev}")
        elif verbose:
            print("  任务已接受(SessionStarted)")

        # 3) FinishSession（event=102，带 session_id）
        ws.send_binary(build_frame(102, b"{}", session_id))

        # 4) 接收音频流与事件
        while True:
            try:
                event, payload_bytes = recv_msg()
            except websocket.WebSocketConnectionClosedException:
                print("  [warn] 连接被服务端关闭（流未完成）")
                break
            if event == EVT_ROUND_START:
                try:
                    cur_round = json.loads(payload_bytes.decode("utf-8"))
                except Exception:
                    cur_round = {}
            elif event == EVT_ROUND_AUDIO:
                audio.extend(payload_bytes)
            elif event == EVT_ROUND_END:
                try:
                    info = json.loads(payload_bytes.decode("utf-8"))
                    if info.get("is_error"):
                        print(f"  [错误] 轮次失败: {info}")
                    cur_round.update(info)
                    timeline.append(dict(cur_round))
                except Exception:
                    pass
                if verbose:
                    print(f"  轮次完成: round_id={cur_round.get('round_id')} "
                          f"speaker={cur_round.get('speaker', '?')[:34]} "
                          f"{cur_round.get('start_time', 0):.1f}s-{cur_round.get('end_time', 0):.1f}s")
            elif event == EVT_PODCAST_END:
                try:
                    audio_url = json.loads(payload_bytes.decode("utf-8")).get("meta_info", {}).get("audio_url")
                except Exception:
                    pass
            elif event in (EVT_SESSION_FINISHED, EVT_CONNECTION_FINISHED):
                if verbose:
                    print("  会话合成完成(SessionFinished)")
                break
    finally:
        try:
            ws.send_binary(build_frame(2, b"{}"))  # FinishConnection（event=2，无sid）
            ws.close()
        except Exception:
            pass
    return bytes(audio), timeline, audio_url


# ---------------- 5. SRT ----------------
def fmt_ts(sec):
    ms = int(round(sec * 1000))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def make_srt(timeline, texts_by_round, offset, path):
    """timeline: API返回轮次; texts_by_round: {round_id: text}; offset: 批前累计秒数"""
    n = 0
    with open(path, "a", encoding="utf-8") as f:
        for r in timeline:
            rid = r.get("round_id")
            if rid in (-1, 9999) or rid is None:
                continue  # 跳过头尾音乐轮
            text = texts_by_round.get(rid, "")
            if not text:
                continue
            n += 1
            f.write(f"{n}\n{fmt_ts(r['start_time'] + offset)} --> {fmt_ts(r['end_time'] + offset)}\n"
                    f"{r.get('speaker', '')}: {text}\n\n")
    return n


# ---------------- 主流程 ----------------
def main():
    import re
    ap = argparse.ArgumentParser()
    ap.add_argument("script", help="时间脚本txt路径")
    ap.add_argument("--outdir", default=None, help="输出目录（默认脚本同目录下 output）")
    ap.add_argument("--map", action="append", default=[],
                    help="说话人=音色 映射，如 周老师=zh_male_xiaolei_v2_saturn_bigtts（可多次）")
    ap.add_argument("--dry-run", action="store_true", help="只解析与切分，输出请求JSON预览，不调用API")
    ap.add_argument("--appid", default=os.environ.get("VOLC_APP_ID"))
    ap.add_argument("--token", default=os.environ.get("VOLC_ACCESS_TOKEN"))
    ap.add_argument("--creds-file", default=None,
                    help="凭据文件路径（支持 'APP ID/标签行+值行' 或纯 'id token' 两行）")
    ap.add_argument("--speech-rate", type=int, default=0, help="语速[-50,100]")
    ap.add_argument("--no-head-music", action="store_true", help="不加片头音乐（拼接整期时中间幕用）")
    ap.add_argument("--no-tail-music", action="store_true", help="不加片尾音乐（拼接整期时中间幕用）")
    args = ap.parse_args()

    if args.creds_file and not (args.appid and args.token):
        raw = open(args.creds_file, encoding="utf-8").read().split()
        labels = {"APP", "ID", "ACCESS", "TOKEN", "APIKEY", "API", "KEY", "TOKEN：", "ID："}
        vals = [v for v in raw if v.upper().strip("：:") not in labels]
        if len(vals) >= 2:
            args.appid, args.token = vals[0], vals[1]

    voice_map = dict(DEFAULT_VOICE_MAP)
    for m in args.map:
        k, _, v = m.partition("=")
        voice_map[k.strip()] = v.strip()

    turns = parse_time_script(args.script)
    print(f"解析到 {len(turns)} 个话轮")
    missing = {t['speaker'] for t in turns if t['speaker'] not in voice_map}
    if missing:
        print(f"[错误] 以下说话人没有音色映射，请用 --map 指定: {missing}")
        sys.exit(1)

    turns = split_long_rounds(turns)
    batches = chunk_into_batches(turns)
    print(f"切分后 {len(turns)} 轮（单轮<= {MAX_CHARS_PER_ROUND} 字符），分为 {len(batches)} 批调用")

    outdir = args.outdir or os.path.join(os.path.dirname(os.path.abspath(args.script)), "output")
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.script))[0]

    if args.dry_run:
        preview = {"action": 3, "nlp_texts": [{"speaker": voice_map[t["speaker"]], "text": t["text"]} for t in batches[0][:5]],
                   "批次数": len(batches), "每批轮数": [len(b) for b in batches],
                   "speaker_info": {"random_order": False, "speakers": sorted({voice_map[s] for s in voice_map if any(t['speaker']==s for t in turns)})}}
        p = os.path.join(outdir, f"{base}_请求预览.json")
        open(p, "w", encoding="utf-8").write(json.dumps(preview, ensure_ascii=False, indent=2))
        print(f"[干跑] 请求预览已写入 {p}")
        return

    if not args.appid or not args.token:
        print("[错误] 缺少凭据：设置环境变量 VOLC_APP_ID / VOLC_ACCESS_TOKEN，或用 --appid/--token")
        sys.exit(1)

    srt_path = os.path.join(outdir, f"{base}.srt")
    open(srt_path, "w", encoding="utf-8").close()  # 每次运行先清空字幕，防止多次运行追加旧条目
    timeline_path = os.path.join(outdir, f"{base}_时间轴.json")
    merged = bytearray()
    all_timeline, offset = [], 0.0
    for i, batch in enumerate(batches):
        print(f"\n===== 批次 {i + 1}/{len(batches)}（{len(batch)} 轮）=====")
        audio, timeline, audio_url = synthesize_batch(
            batch, voice_map, args.appid, args.token,
            head_music=(i == 0) and not args.no_head_music,
            tail_music=(i == len(batches) - 1) and not args.no_tail_music)
        p_mp3 = os.path.join(outdir, f"{base}_批{i + 1}.mp3")
        open(p_mp3, "wb").write(audio)
        print(f"  音频 {len(audio) / 1024:.0f} KB → {p_mp3}")
        if audio_url:
            print(f"  官方完整音频URL(1小时内有效): {audio_url[:100]}...")
        merged.extend(audio)
        texts_by_round = {j: t["text"] for j, t in enumerate(batch)}
        role_of_voice = {v: k for k, v in voice_map.items()}
        for r in timeline:  # SRT/时间轴中把音色ID换回角色名
            r["speaker"] = role_of_voice.get(r.get("speaker", ""), r.get("speaker", ""))
        n = make_srt(timeline, texts_by_round, offset, srt_path)
        for r in timeline:
            r["_batch"] = i + 1
        all_timeline.extend(timeline)
        last_end = max((r.get("end_time", 0) for r in timeline), default=0)
        offset += last_end + 0.5
        print(f"  字幕 {n} 条已追加；批末时间 {last_end:.1f}s")

    merged_path = os.path.join(outdir, f"{base}_合并.mp3")
    open(merged_path, "wb").write(bytes(merged))
    open(timeline_path, "w", encoding="utf-8").write(json.dumps(all_timeline, ensure_ascii=False, indent=2))
    print(f"\n完成：\n  合并音频: {merged_path}（{len(merged)/1024/1024:.1f} MB，MP3流直接拼接）\n"
          f"  字幕: {srt_path}\n  时间轴: {timeline_path}")


if __name__ == "__main__":
    main()
