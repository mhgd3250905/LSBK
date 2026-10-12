# -*- coding: utf-8 -*-
"""EP23 shownotes.md -> v2 HTML（沿用 convert_shownotes_ep22_s2e01_s2e07.py 规则，对齐 EP13~EP22 基线），输出 SHA-256 校验文件。
路径按脚本所在目录解析，Windows 与 Linux 均可运行。"""
import base64, hashlib, io, json, os, re, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))


def bold(s):
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)


def convert(md_path, html_path):
    lines = open(md_path, encoding='utf-8').read().splitlines()
    ps = []
    for ln in lines:
        t = ln.strip()
        if not t or t == '---':
            continue
        if t.startswith('# '):
            continue
        if t.startswith('## '):
            ps.append(f"<p><strong>{t[3:].strip()}</strong></p>")
        elif t.startswith('- '):
            ps.append(f"<p>{bold(t[2:].strip())}</p>")
        elif re.match(r'^[•\*] ', t):
            body = t[2:].strip()
            m = re.match(r'^\*\*(.+?)\*\*[：:](.*)$', body)
            if m:
                ps.append(f"<p>• <strong>{m.group(1)}</strong>：{m.group(2)}</p>")
            else:
                ps.append(f"<p>• {bold(body)}</p>")
        else:
            ps.append(f"<p>{bold(t)}</p>")
    html = ''.join(ps)
    open(html_path, 'w', encoding='utf-8').write(html)
    b64 = base64.b64encode(html.encode('utf-8')).decode('ascii')
    sha = hashlib.sha256(html.encode('utf-8')).hexdigest()
    meta = {'html_path': os.path.relpath(html_path, BASE), 'html_chars': len(html),
            'b64_chars': len(b64), 'sha256': sha}
    with open(html_path + '.meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, ensure_ascii=False, indent=1, fp=f)
    return meta


if __name__ == '__main__':
    ep = 'EP23_唐伯虎科场案'
    d = os.path.join(BASE, ep)
    r = convert(os.path.join(d, 'shownotes.md'), os.path.join(d, 'shownotes_v2.html'))
    print(json.dumps({'ep': ep, 'html_chars': r['html_chars'], 'sha256': r['sha256']}, ensure_ascii=False))
