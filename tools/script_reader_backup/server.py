"""
笑谈历史播客 · 智能审稿工作台后端服务
支持实时读取各集脚本、大纲、质检报告、大主角分析，并在本地启动审稿网页
新增：实时比对 Git 修改，提供“修改高亮”与“修改导航”功能
"""

import http.server
import socketserver
import json
import os
import glob
import re
import urllib.parse
import sys
import subprocess
import difflib

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
PORT = 8520

def parse_markdown_metadata(lines):
    meta = {}
    for line in lines:
        s = line.strip()
        if s.startswith('>'):
            cleaned = s.lstrip('>').strip()
            matches = re.findall(r'\*\*([^*]+)\*\*[：:\s]*([^*]+)', cleaned)
            for k, v in matches:
                meta[k.strip()] = v.strip().rstrip('；;，,')
        elif s.startswith('---'):
            break
    return meta

def parse_script_dialogues(content):
    lines = content.split('\n')
    meta = parse_markdown_metadata(lines)
    
    dialogues = []
    current_sp = None
    current_time = ""
    current_text = []

    dialogue_pattern = re.compile(r'^\*\*(大开|小李)\*\*[（\(](.*?)[）\)]：?\s*(.*)$')

    for line in lines:
        s = line.strip()
        m = dialogue_pattern.match(s)
        if m:
            if current_sp:
                dialogues.append({
                    "speaker": current_sp,
                    "time": current_time,
                    "text": "\n".join(current_text).strip()
                })
            current_sp = m.group(1)
            current_time = m.group(2)
            first_text = m.group(3).strip()
            current_text = [first_text] if first_text else []
        elif current_sp is not None:
            if not s.startswith('#') and not s.startswith('>') and not s.startswith('---'):
                if s:
                    current_text.append(s)

    if current_sp:
        dialogues.append({
            "speaker": current_sp,
            "time": current_time,
            "text": "\n".join(current_text).strip()
        })

    return meta, dialogues

def get_git_base_content(rel_file_path):
    """获取 HEAD 中指定文件的原始内容"""
    try:
        norm_path = rel_file_path.replace('\\', '/')
        cmd = ['git', 'show', f'HEAD:{norm_path}']
        out = subprocess.check_output(cmd, cwd=BASE_DIR, stderr=subprocess.DEVNULL)
        return out.decode('utf-8')
    except Exception:
        return None

def compute_dialogue_diff(old_text, new_text):
    """计算单个话轮的增删字词，生成高亮 HTML"""
    matcher = difflib.SequenceMatcher(None, old_text, new_text)
    html_parts = []
    has_change = False
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            html_parts.append(new_text[j1:j2])
        elif tag == 'replace':
            has_change = True
            deleted = old_text[i1:i2]
            added = new_text[j1:j2]
            html_parts.append(f'<span class="line-through text-red-500 bg-red-100 dark:bg-red-950/50 px-1 rounded mx-0.5 text-xs">{deleted}</span><span class="font-bold text-emerald-700 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-950/60 px-1 rounded shadow-xs">{added}</span>')
        elif tag == 'delete':
            has_change = True
            deleted = old_text[i1:i2]
            html_parts.append(f'<span class="line-through text-red-500 bg-red-100 dark:bg-red-950/50 px-1 rounded mx-0.5 text-xs">{deleted}</span>')
        elif tag == 'insert':
            has_change = True
            added = new_text[j1:j2]
            html_parts.append(f'<span class="font-bold text-emerald-700 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-950/60 px-1 rounded shadow-xs">{added}</span>')
            
    return "".join(html_parts), has_change

def get_all_episodes():
    episodes = []
    
    # S2 Song Series
    song_dirs = sorted(glob.glob(os.path.join(BASE_DIR, 'podcasts', '宋朝系列', 'S*')))
    for p in song_dirs:
        if os.path.isdir(p):
            dirname = os.path.basename(p)
            parts = dirname.split('_', 1)
            ep_id = parts[0]
            title = parts[1] if len(parts) > 1 else dirname
            
            scripts = glob.glob(os.path.join(p, '脚本_第*.md'))
            has_report = os.path.exists(os.path.join(p, '质检报告.md'))
            has_outline = os.path.exists(os.path.join(p, '大纲.md'))
            has_fact = os.path.exists(os.path.join(p, '史料核对.md'))
            
            episodes.append({
                "id": f"S2{ep_id}",
                "series": "第二季·大宋篇",
                "folder": os.path.relpath(p, BASE_DIR).replace('\\', '/'),
                "title": title,
                "display_name": f"S2{ep_id} {title}",
                "act_count": len(scripts),
                "has_report": has_report,
                "has_outline": has_outline,
                "has_fact": has_fact
            })
            
    # S1 Ming Series
    ming_dirs = sorted(glob.glob(os.path.join(BASE_DIR, 'podcasts', 'EP*')))
    for p in ming_dirs:
        if os.path.isdir(p):
            dirname = os.path.basename(p)
            parts = dirname.split('_', 1)
            ep_id = parts[0]
            title = parts[1] if len(parts) > 1 else dirname
            
            scripts = glob.glob(os.path.join(p, '脚本_第*.md'))
            has_report = os.path.exists(os.path.join(p, '质检报告.md')) or os.path.exists(os.path.join(p, '文稿质检报告.md'))
            has_outline = os.path.exists(os.path.join(p, '大纲.md'))
            has_fact = os.path.exists(os.path.join(p, '史料核对.md'))
            
            episodes.append({
                "id": ep_id,
                "series": "第一季·大明篇",
                "folder": os.path.relpath(p, BASE_DIR).replace('\\', '/'),
                "title": title,
                "display_name": f"{ep_id} {title}",
                "act_count": len(scripts),
                "has_report": has_report,
                "has_outline": has_outline,
                "has_fact": has_fact
            })
            
    return episodes

def get_episode_data(folder_path):
    full_path = os.path.join(BASE_DIR, folder_path)
    if not os.path.exists(full_path):
        return None
        
    act_names = ["第一幕", "第二幕", "第三幕", "第四幕"]
    acts = []
    total_words = 0
    total_turns = 0
    dk_turns = 0
    xl_turns = 0
    total_changed_turns = 0
    
    for i, an in enumerate(act_names):
        md_file = os.path.join(full_path, f"脚本_{an}.md")
        rel_file = os.path.relpath(md_file, BASE_DIR)
        
        if os.path.exists(md_file):
            new_content = open(md_file, encoding='utf-8').read()
            meta, dialogues = parse_script_dialogues(new_content)
            
            # 读取 HEAD 旧版本以对比变更
            old_content = get_git_base_content(rel_file)
            old_dialogues = []
            if old_content:
                _, old_dialogues = parse_script_dialogues(old_content)
                
            act_words = 0
            act_changed_count = 0
            
            for idx, d in enumerate(dialogues):
                w = len(d['text'].replace(' ', '').replace('\n', ''))
                act_words += w
                if d['speaker'] == '大开':
                    dk_turns += 1
                else:
                    xl_turns += 1
                    
                # 检查修改
                is_changed = False
                old_d_text = ""
                diff_html = d['text']
                
                if idx < len(old_dialogues):
                    old_d_text = old_dialogues[idx]['text']
                    if old_d_text != d['text'] or old_dialogues[idx]['speaker'] != d['speaker']:
                        is_changed = True
                        diff_html, _ = compute_dialogue_diff(old_d_text, d['text'])
                else:
                    # 新增的话轮
                    is_changed = True
                    diff_html = f'<span class="font-bold text-emerald-700 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-950/60 px-1 rounded shadow-xs">{d["text"]}</span>'
                    
                if is_changed:
                    act_changed_count += 1
                    total_changed_turns += 1
                    
                d['is_changed'] = is_changed
                d['diff_html'] = diff_html
                d['old_text'] = old_d_text
                
            total_words += act_words
            total_turns += len(dialogues)
                    
            acts.append({
                "act_index": i + 1,
                "act_name": an,
                "title": meta.get("幕名", f"第{i+1}幕"),
                "protagonist": meta.get("主角", ""),
                "timeline": meta.get("时间线", ""),
                "core_task": meta.get("核心任务", ""),
                "meta": meta,
                "dialogues": dialogues,
                "word_count": act_words,
                "turn_count": len(dialogues),
                "changed_count": act_changed_count,
                "est_duration": f"{round(act_words / 320, 1)} 分钟"
            })
            
    report_content = ""
    for rname in ["质检报告.md", "文稿质检报告.md"]:
        rpath = os.path.join(full_path, rname)
        if os.path.exists(rpath):
            report_content = open(rpath, encoding='utf-8').read()
            break
            
    outline_content = ""
    opath = os.path.join(full_path, "大纲.md")
    if os.path.exists(opath):
        outline_content = open(opath, encoding='utf-8').read()
        
    fact_content = ""
    fpath = os.path.join(full_path, "史料核对.md")
    if os.path.exists(fpath):
        fact_content = open(fpath, encoding='utf-8').read()
        
    topic_content = ""
    tpath = os.path.join(full_path, "选题卡.md")
    if os.path.exists(tpath):
        topic_content = open(tpath, encoding='utf-8').read()
        
    return {
        "folder": folder_path,
        "title": os.path.basename(folder_path),
        "total_words": total_words,
        "total_turns": total_turns,
        "dk_turns": dk_turns,
        "xl_turns": xl_turns,
        "total_changed_turns": total_changed_turns,
        "est_total_duration": f"{round(total_words / 320, 1)} 分钟",
        "acts": acts,
        "report_md": report_content,
        "outline_md": outline_content,
        "fact_md": fact_content,
        "topic_md": topic_content
    }

class ScriptViewerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        
        if path == '/' or path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html_path = os.path.join(os.path.dirname(__file__), 'index.html')
            with open(html_path, 'rb') as f:
                self.wfile.write(f.read())
            return
            
        elif path == '/api/episodes':
            eps = get_all_episodes()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(eps, ensure_ascii=False).encode('utf-8'))
            return
            
        elif path == '/api/episode':
            qs = urllib.parse.parse_qs(url.query)
            folder = qs.get('folder', [''])[0]
            data = get_episode_data(folder)
            if data:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
            return
            
        else:
            super().do_GET()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ScriptViewerHandler) as httpd:
        print(f"======================================================")
        print(f" 《笑谈历史》智能审稿工作台 (增补修订高亮功能) 已就绪！")
        print(f" 请在浏览器打开: http://localhost:{PORT}")
        print(f"======================================================")
        sys.stdout.flush()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n正在关闭审稿工作台服务...")

if __name__ == '__main__':
    run_server()
