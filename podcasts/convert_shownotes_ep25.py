# -*- coding: utf-8 -*-
"""EP25 shownotes.md -> v2 HTML（沿用 convert_shownotes_ep22_s2e01_s2e07.py 规则，对齐EP13~EP22基线），输出 SHA-256 校验文件。
路径按本脚本所在目录（podcasts/）相对解析，Windows 工作机与 Linux 沙箱均可直接运行。"""
import base64, hashlib, json, os, re, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def bold(s):
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)

def convert(md_path, html_path):
    lines = open(md_path, encoding='utf-8').read().splitlines()
    ps = []
    for ln in lines:
        t = ln.strip()
        if not t or t == '---':
            continue
        if t.startswith('# '):        # 文件标题行，不注入
            continue
        if t.startswith('## '):       # 小节头
            head = t[3:].strip()
            ps.append(f"<p><strong>{head}</strong></p>")
        elif t.startswith('- '):      # 列表项（时间轴 mm:ss 行首留空格供平台识别章节）
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
    open(html_path, 'w', encoding='utf-8').write(html)
    b64 = base64.b64encode(html.encode('utf-8')).decode('ascii')
    sha = hashlib.sha256(html.encode('utf-8')).hexdigest()
    meta = {'html_path': html_path, 'html_chars': len(html), 'b64_chars': len(b64),
            'sha256': sha}
    with open(html_path + '.meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, ensure_ascii=False, indent=1, fp=f)
    return meta

base = os.path.dirname(os.path.abspath(__file__))
ep = 'EP25_宋濂_送东阳马生序'
r = convert(os.path.join(base, ep, 'shownotes.md'), os.path.join(base, ep, 'shownotes_v2.html'))
print(json.dumps({'ep': ep, 'html_chars': r['html_chars'], 'sha256': r['sha256']}, ensure_ascii=False))
