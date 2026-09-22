# -*- coding: utf-8 -*-
"""EP02 单集封面 v2：本集标题为主角，台名退居角落，"偏要勉强"朱砂印章点睛"""
from PIL import Image, ImageDraw, ImageFont

W = H = 3000
BG = (243, 236, 222)        # 宣纸米色
INK = (51, 43, 36)          # 墨色
RED = (178, 54, 43)         # 朱砂红
GOLD = (156, 124, 66)       # 淡金

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

def font(path, size):
    return ImageFont.truetype(path, size)

MS = "C:/Windows/Fonts/msyhbd.ttc"
f_brand = font(MS, 96)      # 台名角标
f_pre = font(MS, 230)       # 赵敏的
f_title = font(MS, 500)     # 恋爱心理学
f_sub = font(MS, 110)       # 副题
f_seal = font(MS, 230)      # 印章字
f_host = font(MS, 96)       # 主播名

# 细边框（双线，古籍版式感）
d.rectangle([70, 70, W-70, H-70], outline=INK, width=8)
d.rectangle([110, 110, W-110, H-110], outline=INK, width=3)

# 台名角标（次要，顶部居中小字）
d.text((W//2, 280), "笑 谈 历 史 · EP02", font=f_brand, fill=GOLD, anchor="mm")

# 主标题：赵敏的 + 恋爱心理学
d.text((W//2, 700), "赵敏的", font=f_pre, fill=INK, anchor="mm")
d.text((W//2, 1140), "恋爱心理学", font=f_title, fill=INK, anchor="mm")

# 分隔线 + 菱形
d.line([W//2-520, 1560, W//2-60, 1560], fill=RED, width=6)
d.line([W//2+60, 1560, W//2+520, 1560], fill=RED, width=6)
d.polygon([(W//2, 1530), (W//2+30, 1560), (W//2, 1590), (W//2-30, 1560)], fill=RED)

# 副题
d.text((W//2, 1770), "为什么说她是金庸宇宙最高段位的沟通大师", font=f_sub, fill=GOLD, anchor="mm")

# 朱砂印章：偏要勉强（2x2，右下；印章从右列往下读：右列"偏要"，左列"勉强"）
seal_w = seal_h = 640
sx, sy = W - 170 - seal_w, H - 200 - seal_h
d.rounded_rectangle([sx, sy, sx+seal_w, sy+seal_h], radius=36, fill=RED)
pos = {"偏": (0.72, 0.28), "要": (0.72, 0.72), "勉": (0.28, 0.28), "强": (0.28, 0.72)}
for ch, (fx, fy) in pos.items():
    d.text((sx + seal_w * fx, sy + seal_h * fy), ch, font=f_seal, fill=BG, anchor="mm")

# 左下主播名
d.text((360, H - 360), "主播：大开 × 小李", font=f_host, fill=INK, anchor="lm")

out = r"E:\AII_Gemini\LSBK\podcasts\EP02_赵敏恋爱小巧思\EP02_封面.png"
img.save(out, "PNG")
print("封面v2已生成:", out)
