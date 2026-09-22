# -*- coding: utf-8 -*-
"""EP05 单集封面：心学狠人徐阶的潜伏术"""
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
f_pre = font(MS, 220)       # 顶层标题
f_title = font(MS, 460)     # 主标题
f_sub = font(MS, 105)       # 副题
f_seal = font(MS, 220)      # 印章字
f_host = font(MS, 96)       # 主播名

# 细边框（双线古籍装帧感）
d.rectangle([70, 70, W-70, H-70], outline=INK, width=8)
d.rectangle([110, 110, W-110, H-110], outline=INK, width=3)

# 台名角标
d.text((W//2, 280), "笑 谈 历 史 · EP05", font=f_brand, fill=GOLD, anchor="mm")

# 主标题：心学狠人的 + 潜伏反杀术
d.text((W//2, 700), "心学狠人的", font=f_pre, fill=INK, anchor="mm")
d.text((W//2, 1140), "潜伏反杀术", font=f_title, fill=INK, anchor="mm")

# 分隔线 + 菱形装饰
d.line([W//2-600, 1560, W//2-60, 1560], fill=RED, width=6)
d.line([W//2+60, 1560, W//2+600, 1560], fill=RED, width=6)
d.polygon([(W//2, 1530), (W//2+30, 1560), (W//2, 1590), (W//2-30, 1560)], fill=RED)

# 副题
d.text((W//2, 1770), "给严嵩装二十年孙子，王阳明心学到底有多硬核？", font=f_sub, fill=GOLD, anchor="mm")

# 朱砂印章：事上磨练（2x2，右下；从右列读起：事、上、磨、练）
seal_w = seal_h = 640
sx, sy = W - 170 - seal_w, H - 200 - seal_h
d.rounded_rectangle([sx, sy, sx+seal_w, sy+seal_h], radius=36, fill=RED)
pos = {"事": (0.72, 0.28), "上": (0.72, 0.72), "磨": (0.28, 0.28), "练": (0.28, 0.72)}
for ch, (fx, fy) in pos.items():
    d.text((sx + seal_w * fx, sy + seal_h * fy), ch, font=f_seal, fill=BG, anchor="mm")

# 左下主播名
d.text((360, H - 360), "主播：大开 × 小李", font=f_host, fill=INK, anchor="lm")

out = r"E:\AII_Gemini\LSBK\podcasts\EP05_心学狠人徐阶\EP05_封面.png"
img.save(out, "PNG")
print("EP05封面已生成:", out)
