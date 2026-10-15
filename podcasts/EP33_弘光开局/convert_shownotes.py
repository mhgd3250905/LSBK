# -*- coding: utf-8 -*-
"""EP33 shownotes.md -> v2 HTML 并生成 base64 + SHA-256 校验元数据"""
import base64
import hashlib
import json
import os
import re

DIR = os.path.dirname(os.path.abspath(__file__))
md_path = os.path.join(DIR, "shownotes.md")
html_path = os.path.join(DIR, "shownotes_v2.html")

def bold(s):
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)

def convert(md_file, html_file, chunk=700):
    lines = open(md_file, encoding='utf-8').read().splitlines()
    ps = []
    for ln in lines:
        t = ln.strip()
        if not t or t == '---':
            continue
        if t.startswith('# '):        # 文件大标题，不注入
            continue
        if t.startswith('## '):       # 小节头
            head = t[3:].strip()
            ps.append(f"<p><strong>{head}</strong></p>")
        elif t.startswith('- '):      # 列表项
            item = t[2:].strip()
            ps.append(f"<p>{bold(item)}</p>")
        elif re.match(r'^[•\*] ', t):  # 要点行 -> • **标题**：正文
            body = t[2:].strip()
            m = re.match(r'^\*\*(.+?)\*\*[：:](.*)$', body)
            if m:
                ps.append(f"<p>• <strong>{m.group(1)}</strong>：{m.group(2)}</p>")
            else:
                ps.append(f"<p>• {bold(body)}</p>")
        elif re.match(r'^\d+\. ', t):  # 编号项
            ps.append(f"<p>{bold(t)}</p>")
        else:                          # 普通段落
            ps.append(f"<p>{bold(t)}</p>")
    html = ''.join(ps)
    open(html_file, 'w', encoding='utf-8').write(html)
    b64 = base64.b64encode(html.encode('utf-8')).decode('ascii')
    sha = hashlib.sha256(html.encode('utf-8')).hexdigest()
    chunks = [b64[i:i+chunk] for i in range(0, len(b64), chunk)]
    meta = {
        'html_path': 'podcasts/EP33_弘光开局/shownotes_v2.html',
        'html_chars': len(html),
        'b64_chars': len(b64),
        'sha256': sha,
        'n_chunks': len(chunks),
        'chunk_lens': [len(c) for c in chunks]
    }
    with open(html_file + '.b64chunks.json', 'w', encoding='utf-8') as f:
        json.dump({'sha256': sha, 'chunks': chunks}, ensure_ascii=False, fp=f)
    with open(html_file + '.meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, ensure_ascii=False, indent=1, fp=f)
    print("Conversion successful!")
    print(json.dumps(meta, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    convert(md_path, html_path)
