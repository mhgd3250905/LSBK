# -*- coding: utf-8 -*-
import re
import glob
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

banned_patterns = [
    (r'[“”「」"\']', '直接引号'),
    (r'不是.*?而是', '不是……而是……二元对仗'),
    (r'既不是.*?也不是.*?而是', '既不是……也不是……而是……'),
    (r'从来不是.*?恰恰是', '从来不是……恰恰是……'),
    (r'头皮发麻', 'AI煽情:头皮发麻'),
    (r'细思极恐', 'AI煽情:细思极恐'),
    (r'[让人令人]窒息', 'AI煽情:窒息'),
    (r'脊背发凉', 'AI煽情:脊背发凉'),
    (r'可以说是', 'AI套话:可以说是'),
    (r'(?<![婉回])绝了', 'AI套话:绝了'),
    (r'一点都没错', 'AI套话:一点都没错'),
    (r'这就太反常识了', 'AI标签:这就太反常识了'),
    (r'颠覆认知', 'AI标签:颠覆认知'),
    (r'(?<!脑洞)大开[，,]', '小李句首大开呼名重读'),
    (r'(大纲|脚本|冷开场)', '元剧本词汇'),
    (r'(刚才|刚刚|前面|上一幕)(咱们|我们)?(提到|说到|聊到|讲到)', '机械回溯串场'),
    (r'在(很多|大家|不少)人的?印象[里中]', '做作问卷垫话'),
    (r'极其', 'AI程度副词口癖:极其'),
    (r'绞肉机|絞肉机', '现代翻译腔:绞肉机'),
    (r'何止是', '机械接茬口癖:何止是')
]

all_files = sorted(glob.glob('podcasts/宋朝系列/S08A_王安石上_天变不足畏/脚本_*.md')) + sorted(glob.glob('podcasts/宋朝系列/S08A_王安石上_天变不足畏/*_时间脚本.txt'))
all_clean = True
for fpath in all_files:
    lines = open(fpath, encoding='utf-8').readlines()
    for idx, line in enumerate(lines, 1):
        if idx == 1 or line.startswith('#') or line.startswith('>'):
            continue
        for pat, desc in banned_patterns:
            m = re.search(pat, line)
            if m:
                print(f'[{desc}] {fpath}:{idx} -> {line.strip()}')
                all_clean = False

if all_clean:
    print('ALL CLEAN! 100% passed mechanical linting across all MD script and TXT timeline files in S2E08A!')
else:
    sys.exit(1)
