# -*- coding: utf-8 -*-
"""EP09 单集封面：武侠男主炮轰襄阳城？重读凤歌《昆仑》"""
from PIL import Image, ImageDraw, ImageFont

W = H = 3000
BG = (245, 238, 226)        # 宣纸米色
INK = (45, 38, 32)          # 焦墨色
RED = (175, 48, 38)         # 故宫红/朱砂
GOLD = (156, 120, 60)       # 明制金泥

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

def font(path, size):
    return ImageFont.truetype(path, size)

MS = "C:/Windows/Fonts/msyhbd.ttc"
f_brand = font(MS, 96)      # 台名角标
f_pre = font(MS, 200)       # 顶层标题
f_title = font(MS, 380)     # 主标题
f_sub = font(MS, 96)        # 副题
f_seal = font(MS, 220)      # 印章字
f_host = font(MS, 96)       # 主播名

# 细边框（双线古籍装帧感）
d.rectangle([70, 70, W-70, H-70], outline=INK, width=8)
d.rectangle([110, 110, W-110, H-110], outline=INK, width=3)

# 台名角标
d.text((W//2, 280), "笑 谈 历 史 · EP09 · 武侠特别季", font=f_brand, fill=GOLD, anchor="mm")

# 顶层标题与主标题
d.text((W//2, 700), "武 侠 男 主 炮 轰 襄 阳 城 ？", font=f_pre, fill=RED, anchor="mm")
d.text((W//2, 1140), "重 读 凤 歌 《 昆 仑 》", font=f_title, fill=INK, anchor="mm")

# 分隔线 + 菱形装饰
d.line([W//2-600, 1560, W//2-60, 1560], fill=RED, width=6)
d.line([W//2+60, 1560, W//2+600, 1560], fill=RED, width=6)
d.polygon([(W//2, 1530), (W//2+30, 1560), (W//2, 1590), (W//2-30, 1560)], fill=RED)

# 副题
d.text((W//2, 1770), "算学神童还是自私巨婴？为什么二十年后我们不再原谅梁萧", font=f_sub, fill=GOLD, anchor="mm")

# 朱砂印章：侠之大者（2x2，右下；从右列读起：侠、之、大、者）
seal_w = seal_h = 640
sx, sy = W - 170 - seal_w, H - 200 - seal_h
d.rounded_rectangle([sx, sy, sx+seal_w, sy+seal_h], radius=36, fill=RED)
pos = {"侠": (0.72, 0.28), "之": (0.72, 0.72), "大": (0.28, 0.28), "者": (0.28, 0.72)}
for ch, (fx, fy) in pos.items():
    d.text((sx + seal_w * fx, sy + seal_h * fy), ch, font=f_seal, fill=BG, anchor="mm")

# 左下主播名
d.text((360, H - 360), "主播：大开 × 小李", font=f_host, fill=INK, anchor="lm")

out = r"e:\AII_Gemini\LSBK\podcasts\EP09_梁萧\EP09_封面.png"
img.save(out, "PNG")
print("EP09封面已生成:", out)
