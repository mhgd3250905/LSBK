#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小宇宙播客《有啥说啥｜用历史解码当下》全量音频批量下载工具
"""

import os
import re
import sys
import json
import time
import urllib.request
import urllib.parse
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

# 播客官方 RSS 源 (来自 Apple Podcasts 索引)
FEED_URL = "https://www.ximalaya.com/album/103041959.xml"
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "episodes")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.xiaoyuzhoufm.com/'
}

def sanitize_filename(name: str) -> str:
    """清理 Windows 文件名非法字符"""
    clean = re.sub(r'[\\/*?:"<>|]', '_', name)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def fetch_feed_episodes(feed_url: str):
    """解析播客 RSS 订阅源获取所有单集信息"""
    print(f"[*] 正在拉取播客订阅源: {feed_url}")
    req = urllib.request.Request(feed_url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        xml_data = resp.read()

    root = ET.fromstring(xml_data)
    channel = root.find('channel')
    podcast_title = channel.find('title').text.strip() if channel.find('title') is not None else "有啥说啥"

    items = channel.findall('item')
    episodes = []

    for i, item in enumerate(items):
        title = item.find('title').text.strip() if item.find('title') is not None else f"Episode_{i+1}"
        pub_date_str = item.find('pubDate').text.strip() if item.find('pubDate') is not None else ""
        
        # 格式化日期为 YYYY-MM-DD
        date_formatted = ""
        if pub_date_str:
            try:
                dt = parsedate_to_datetime(pub_date_str)
                date_formatted = dt.strftime('%Y-%m-%d')
            except Exception:
                date_formatted = pub_date_str[:10]
        
        # 提取时长
        duration = ""
        for child in item:
            if 'duration' in child.tag.lower() and child.text:
                duration = child.text.strip()
                break

        # 提取音频链接
        enc = item.find('enclosure')
        enc_url = enc.get('url') if enc is not None else ""
        enc_len = int(enc.get('length', 0)) if enc is not None and enc.get('length') else 0
        
        # 如果包含腾讯云 COS 直链参数 jt，优先直接使用直链加速下载
        direct_url = enc_url
        if 'jt=' in enc_url:
            parsed = urllib.parse.urlparse(enc_url)
            qs = urllib.parse.parse_qs(parsed.query)
            if 'jt' in qs and qs['jt']:
                direct_url = qs['jt'][0]

        # 节目描述
        desc = item.find('description').text if item.find('description') is not None else ""
        
        episodes.append({
            'index': i + 1,
            'title': title,
            'safe_title': sanitize_filename(title),
            'date': date_formatted,
            'duration': duration,
            'url': direct_url,
            'orig_url': enc_url,
            'size_bytes': enc_len,
            'description': desc
        })

    return podcast_title, episodes

def download_file(ep: dict, output_dir: str, max_retries: int = 3):
    """单文件下载，支持断点与重试"""
    filename = f"{ep['index']:02d}. [{ep['date']}] {ep['safe_title']}.m4a"
    dest_path = os.path.join(output_dir, filename)

    # 检查是否已下载完毕
    if os.path.exists(dest_path):
        current_size = os.path.getsize(dest_path)
        if current_size > 1024 * 1024:  # 大于 1MB
            return ep['index'], f"[已存在跳过] {filename} ({current_size/1024/1024:.1f} MB)"

    url = ep['url']
    tmp_path = dest_path + ".tmp"

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp, open(tmp_path, 'wb') as out_f:
                total_size = int(resp.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 1024 * 256  # 256KB
                
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    out_f.write(chunk)
                    downloaded += len(chunk)

            # 下载完成后原子替换临时文件
            if os.path.exists(dest_path):
                os.remove(dest_path)
            os.rename(tmp_path, dest_path)
            
            final_size_mb = os.path.getsize(dest_path) / (1024 * 1024)
            return ep['index'], f"[成功] {filename} ({final_size_mb:.1f} MB)"
            
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            if attempt == max_retries:
                # 尝试备用原链接
                if url != ep['orig_url']:
                    try:
                        req = urllib.request.Request(ep['orig_url'], headers=HEADERS)
                        with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, 'wb') as out_f:
                            while True:
                                chunk = resp.read(1024 * 256)
                                if not chunk:
                                    break
                                out_f.write(chunk)
                        final_size_mb = os.path.getsize(dest_path) / (1024 * 1024)
                        return ep['index'], f"[成功(备用源)] {filename} ({final_size_mb:.1f} MB)"
                    except Exception as err2:
                        return ep['index'], f"[失败] {filename}: {err2}"
                return ep['index'], f"[失败] {filename}: {e}"
            time.sleep(2)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="小宇宙播客音频下载器")
    parser.add_argument("--dir", default=DEFAULT_OUTPUT_DIR, help="音频保存目录")
    parser.add_argument("--workers", type=int, default=4, help="并发下载线程数")
    parser.add_argument("--limit", type=int, default=0, help="仅下载前 N 期 (0 表示全部)")
    args = parser.parse_args()

    os.makedirs(args.dir, exist_ok=True)

    podcast_title, episodes = fetch_feed_episodes(FEED_URL)
    print(f"[*] 播客: {podcast_title}")
    print(f"[*] 共解析到 {len(episodes)} 期节目")
    print(f"[*] 保存目录: {args.dir}")

    # 保存元数据列表
    meta_path = os.path.join(args.dir, "episodes_metadata.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump({
            'podcast': podcast_title,
            'source_feed': FEED_URL,
            'total_episodes': len(episodes),
            'episodes': episodes
        }, f, ensure_ascii=False, indent=2)
    print(f"[*] 节目清单已保存至: {meta_path}")

    to_download = episodes[:args.limit] if args.limit > 0 else episodes
    print(f"[*] 开始下载 {len(to_download)} 期音频 (并发线程数: {args.workers})...\n")

    start_time = time.time()
    completed_count = 0

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(download_file, ep, args.dir): ep for ep in to_download}
        for future in as_completed(futures):
            idx, msg = future.result()
            completed_count += 1
            print(f"[{completed_count}/{len(to_download)}] {msg}")

    total_time = time.time() - start_time
    print(f"\n[√] 全部任务完成！耗时: {total_time:.1f} 秒，文件存放在: {args.dir}")

if __name__ == "__main__":
    main()
