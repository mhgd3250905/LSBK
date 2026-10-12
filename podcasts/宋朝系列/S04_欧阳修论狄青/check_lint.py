import re
import glob

banned_patterns = [
    (r'[“”「」"\']', '直接引号'),
    (r'不是.*?而是', '不是……而是……二元对仗'),
    (r'既不是.*?也不是.*?而是', '既不是……也不是……而是……'),
    (r'头皮发麻', 'AI煽情:头皮发麻'),
    (r'细思极恐', 'AI煽情:细思极恐'),
    (r'[让人令人]窒息', 'AI煽情:窒息'),
    (r'脊背发凉', 'AI煽情:脊背发凉'),
    (r'可以说是', 'AI套话:可以说是'),
    (r'(?<![婉回])绝了', 'AI套话:绝了'),
    (r'一点都没错', 'AI套话:一点都没错'),
    (r'这就太反常识了', 'AI标签:这就太反常识了'),
    (r'颠覆认知', 'AI标签:颠覆认知'),
    (r'大开[，,]', '小李句首大开呼名重读'),
    (r'(大纲|脚本)', '元剧本词汇')
]

all_files = sorted(glob.glob('podcasts/宋朝系列/S04_欧阳修论狄青/脚本_*.md')) + sorted(glob.glob('podcasts/宋朝系列/S04_欧阳修论狄青/*_时间脚本.txt'))
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
    print('ALL CLEAN! 100% passed mechanical linting!')
