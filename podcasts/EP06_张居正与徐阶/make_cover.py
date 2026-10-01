# -*- coding: utf-8 -*-
"""EP06 单集封面（AI电影级背景 + 3000x3000px 安全排版）"""
import os
from PIL import Image, ImageDraw, ImageFont

W = H = 3000
MS = "C:/Windows/Fonts/msyhbd.ttc"
DIR = os.path.dirname(os.path.abspath(__file__))

def get_font(size):
    return ImageFont.truetype(MS, size)

def add_top_gradient(base_img, height=1350, max_alpha=205):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(height):
        alpha = int(max_alpha * (1 - (y / height) ** 1.2))
        d.line([(0, y), (W, y)], fill=(12, 12, 18, alpha))
    return Image.alpha_composite(base_img.convert("RGBA"), overlay)

def add_bottom_gradient(base_img, start_y=2450, max_alpha=160):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(start_y, H):
        progress = (y - start_y) / (H - start_y)
        alpha = int(max_alpha * (progress ** 1.3))
        d.line([(0, y), (W, y)], fill=(12, 12, 18, alpha))
    return Image.alpha_composite(base_img.convert("RGBA"), overlay)

def draw_text_with_shadow(draw, pos, text, font, fill, shadow_color=(0, 0, 0, 230), offset=5, anchor="mm"):
    x, y = pos
    for dx in [-offset, 0, offset]:
        for dy in [-offset, 0, offset]:
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=shadow_color, anchor=anchor)
    draw.text((x, y), text, font=font, fill=fill, anchor=anchor)

def get_fitted_title_font(text, max_w=2150, start_sz=280, min_sz=160):
    for sz in range(start_sz, min_sz - 1, -10):
        f = ImageFont.truetype(MS, sz)
        bbox = f.getbbox(text)
        w = bbox[2] - bbox[0]
        if w <= max_w:
            return f, sz, w
    f = ImageFont.truetype(MS, min_sz)
    bbox = f.getbbox(text)
    return f, min_sz, bbox[2] - bbox[0]

def main():
    src_path = os.path.join(DIR, "cover_bg.jpg")
    out_path = os.path.join(DIR, "EP06_封面.png")
    
    img = Image.open(src_path).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    img = add_top_gradient(img, height=1350, max_alpha=205)
    img = add_bottom_gradient(img, start_y=2450, max_alpha=160).convert("RGB")
    d = ImageDraw.Draw(img)
    
    GOLD = (240, 205, 110)
    WHITE = (255, 255, 255)
    RED = (185, 45, 38)
    
    d.rectangle([60, 60, W-60, H-60], outline=(240, 205, 110, 190), width=6)
    d.rectangle([85, 85, W-85, H-85], outline=(255, 255, 255, 120), width=2)
    
    f_brand = get_font(96)
    f_pre = get_font(125)
    f_title, sz, tw = get_fitted_title_font("大明最强CEO张居正", max_w=2150, start_sz=280)
    f_sub = get_font(84)
    f_seal = get_font(210)
    f_host = get_font(92)
    
    draw_text_with_shadow(d, (W//2, 260), "笑 谈 历 史 · EP06", f_brand, GOLD, offset=5)
    draw_text_with_shadow(d, (W//2, 480), "铁血十年与身后深渊", f_pre, (240, 240, 245), offset=5)
    draw_text_with_shadow(d, (W//2, 800), "大明最强CEO张居正", f_title, WHITE, offset=8)
    
    d.line([W//2-500, 1020, W//2-40, 1020], fill=GOLD, width=5)
    d.line([W//2+40, 1020, W//2+500, 1020], fill=GOLD, width=5)
    d.polygon([(W//2, 1000), (W//2+20, 1020), (W//2, 1040), (W//2-20, 1020)], fill=GOLD)
    
    draw_text_with_shadow(d, (W//2, 1140), "从徐阶的得意门生，到万历帝国的总操盘手", f_sub, GOLD, offset=4)
    draw_text_with_shadow(d, (240, H - 240), "主播：大开 × 小李", f_host, WHITE, anchor="lm", offset=5)
    
    seal_w = seal_h = 560
    sx, sy = W - 180 - seal_w, H - 180 - seal_h
    d.rounded_rectangle([sx, sy, sx+seal_w, sy+seal_h], radius=30, fill=RED, outline=(240, 205, 110), width=5)
    chars = list("深心奉刹")
    pos = {chars[0]: (0.72, 0.28), chars[1]: (0.72, 0.72), chars[2]: (0.28, 0.28), chars[3]: (0.28, 0.72)}
    for ch, (fx, fy) in pos.items():
        d.text((sx + seal_w * fx, sy + seal_h * fy), ch, font=f_seal, fill=(250, 245, 235), anchor="mm")
        
    img.save(out_path, "PNG")
    print("EP06 封面已生成:", out_path)

if __name__ == "__main__":
    main()
