# -*- coding: utf-8 -*-
"""EP22 与 S2E01~S2E07 shownotes.md -> v2 HTML（对齐EP13~EP21基线），输出 SHA-256 校验文件。"""
import base64, hashlib, json, re, sys, io

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

eps = [
    (r'EP22_张璁_六年首辅',),
    (r'宋朝系列\S01_范仲淹百官图_岳阳楼记',),
    (r'宋朝系列\S02_欧阳修张甥案_醉翁亭记',),
    (r'宋朝系列\S03_狄青平南_面涅将军',),
    (r'宋朝系列\S04_欧阳修论狄青',),
    (r'宋朝系列\S05_濮议',),
    (r'宋朝系列\S06_阿云之狱',),
    (r'宋朝系列\S07_乌台诗案_沈括之谜',),
]
base = r'E:\AII_Gemini\LSBK\podcasts'
for (ep,) in eps:
    r = convert(rf'{base}\{ep}\shownotes.md', rf'{base}\{ep}\shownotes_v2.html')
    print(json.dumps({'ep': ep, 'html_chars': r['html_chars'], 'sha256': r['sha256']}, ensure_ascii=False))
