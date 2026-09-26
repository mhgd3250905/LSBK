# -*- coding: utf-8 -*-
"""EP09 单集封面：大明最不装的首辅：张居正的豪华房车与四百年贪名"""
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
f_title = font(MS, 420)     # 主标题
f_sub = font(MS, 92)        # 副题
f_seal = font(MS, 220)      # 印章字
f_host = font(MS, 96)       # 主播名

# 细边框（双线古籍装帧感）
d.rectangle([70, 70, W-70, H-70], outline=INK, width=8)
d.rectangle([110, 110, W-110, H-110], outline=INK, width=3)

# 台名角标
d.text((W//2, 280), "笑 谈 历 史 · EP09", font=f_brand, fill=GOLD, anchor="mm")

# 主标题：大明最不装的首辅 · 四百年贪名
d.text((W//2, 700), "大明最不装的首辅", font=f_pre, fill=INK, anchor="mm")
d.text((W//2, 1140), "四 百 年 贪 名", font=f_title, fill=INK, anchor="mm")

# 分隔线 + 菱形装饰
d.line([W//2-600, 1560, W//2-60, 1560], fill=RED, width=6)
d.line([W//2+60, 1560, W//2+600, 1560], fill=RED, width=6)
d.polygon([(W//2, 1530), (W//2+30, 1560), (W//2, 1590), (W//2-30, 1560)], fill=RED)

# 副题
d.text((W//2, 1770), "被骂巨贪的人，抄家时为什么没抄出多少银子？", font=f_sub, fill=GOLD, anchor="mm")

# 朱砂印章：工于谋国（2x2，右下；从右列读起：工、于、谋、国）
seal_w = seal_h = 640
sx, sy = W - 170 - seal_w, H - 200 - seal_h
d.rounded_rectangle([sx, sy, sx+seal_w, sy+seal_h], radius=36, fill=RED)
pos = {"工": (0.72, 0.28), "于": (0.72, 0.72), "谋": (0.28, 0.28), "国": (0.28, 0.72)}
for ch, (fx, fy) in pos.items():
    d.text((sx + seal_w * fx, sy + seal_h * fy), ch, font=f_seal, fill=BG, anchor="mm")

# 左下主播名
d.text((360, H - 360), "主播：大开 × 小李", font=f_host, fill=INK, anchor="lm")

out = r"e:\AII_Gemini\LSBK\podcasts\EP09_张居正的另一面\EP09_封面.png"
img.save(out, "PNG")
print("EP09封面已生成:", out)
