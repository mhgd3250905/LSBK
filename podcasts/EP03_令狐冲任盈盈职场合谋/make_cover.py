# -*- coding: utf-8 -*-
"""EP03 单集封面：复用 EP02 标题主导版式（台名角标+大标题+朱砂印章）"""
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
f_pre = font(MS, 230)       # 令狐冲 × 任盈盈
f_title = font(MS, 500)     # 精准合谋
f_sub = font(MS, 100)       # 副题
f_seal = font(MS, 230)      # 印章字
f_host = font(MS, 96)       # 主播名

# 细边框（双线，古籍版式感）
d.rectangle([70, 70, W-70, H-70], outline=INK, width=8)
d.rectangle([110, 110, W-110, H-110], outline=INK, width=3)

# 台名角标（次要，顶部居中小字）
d.text((W//2, 280), "笑 谈 历 史 · EP03", font=f_brand, fill=GOLD, anchor="mm")

# 主标题
d.text((W//2, 700), "令狐冲 × 任盈盈", font=f_pre, fill=INK, anchor="mm")
d.text((W//2, 1140), "精准合谋", font=f_title, fill=INK, anchor="mm")

# 分隔线 + 菱形
d.line([W//2-520, 1560, W//2-60, 1560], fill=RED, width=6)
d.line([W//2+60, 1560, W//2+520, 1560], fill=RED, width=6)
d.polygon([(W//2, 1530), (W//2+30, 1560), (W//2, 1590), (W//2-30, 1560)], fill=RED)

# 副题
d.text((W//2, 1770), "职场退休大佬与大厂顶级职业经理人的精神赎身", font=f_sub, fill=GOLD, anchor="mm")

# 朱砂印章：体面离场（2x2，右下；从右列往下读：右列"体面"，左列"离场"）
seal_w = seal_h = 640
sx, sy = W - 170 - seal_w, H - 200 - seal_h
d.rounded_rectangle([sx, sy, sx+seal_w, sy+seal_h], radius=36, fill=RED)
pos = {"体": (0.72, 0.28), "面": (0.72, 0.72), "离": (0.28, 0.28), "场": (0.28, 0.72)}
for ch, (fx, fy) in pos.items():
    d.text((sx + seal_w * fx, sy + seal_h * fy), ch, font=f_seal, fill=BG, anchor="mm")

# 左下主播名
d.text((360, H - 360), "主播：大开 × 小李", font=f_host, fill=INK, anchor="lm")

out = r"E:\AII_Gemini\LSBK\podcasts\EP03_令狐冲任盈盈职场合谋\EP03_封面.png"
img.save(out, "PNG")
print("EP03封面已生成:", out)
