# -*- coding: utf-8 -*-
"""EP23 单集封面：大明篇·唐伯虎科场案（AI 电影级贡院夜景背景 + 3000x3000px 自适应排版）

字体：优先 Windows 微软雅黑粗体；不存在时依次回退到环境变量 LSBK_CJK_FONT、
常见 Linux/macOS 的 Noto/Source Han CJK 字体路径，便于在 Windows 与沙箱两处运行。
"""
import os
from PIL import Image, ImageDraw, ImageFont

W = H = 3000
DIR = os.path.dirname(os.path.abspath(__file__))

FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyhbd.ttc",
    os.environ.get("LSBK_CJK_FONT", ""),
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Bold.otf",
    "/usr/share/fonts/adobe-source-han-sans/SourceHanSansSC-Bold.otf",
    "/System/Library/Fonts/PingFang.ttc",
    "/workspace/work/fonts/NotoSansCJKsc-Bold.otf",
]


def pick_font_path():
    for p in FONT_CANDIDATES:
        if p and os.path.exists(p):
            return p
    raise SystemExit("未找到中文字体：请安装微软雅黑或 Noto Sans CJK，或设置环境变量 LSBK_CJK_FONT")


MS = pick_font_path()


def get_font(size):
    return ImageFont.truetype(MS, size)


def add_top_gradient(base_img, height=1350, max_alpha=190):
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


def get_fitted_font(text, max_w=2150, start_sz=240, min_sz=60):
    for sz in range(start_sz, min_sz - 1, -4):
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
    out_path = os.path.join(DIR, "EP23_封面.png")
    print("字体:", MS)

    img = Image.open(src_path).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    img = add_top_gradient(img, height=1350, max_alpha=190)
    img = add_bottom_gradient(img, start_y=2450, max_alpha=160).convert("RGB")
    d = ImageDraw.Draw(img)

    GOLD = (240, 205, 110)
    WHITE = (255, 255, 255)
    RED = (185, 45, 38)

    # 双线边框
    d.rectangle([60, 60, W - 60, H - 60], outline=(240, 205, 110), width=6)
    d.rectangle([85, 85, W - 85, H - 85], outline=(255, 255, 255), width=2)

    f_brand = get_font(96)
    f_pre = get_font(120)

    title_text = "唐 伯 虎 科 场 案"
    f_title, sz, tw = get_fitted_font(title_text, max_w=2150, start_sz=240, min_sz=160)
    print(f"Title '{title_text}': sz={sz}, width={tw}px (margins: {(W - tw) // 2}px)")

    sub_text = "卷子都没被录取，为什么还是因作弊坐了牢？"
    f_sub, ssz, sw = get_fitted_font(sub_text, max_w=2150, start_sz=96, min_sz=60)
    print(f"Sub: sz={ssz}, width={sw}px")

    f_seal = get_font(210)
    f_host = get_font(92)

    draw_text_with_shadow(d, (W // 2, 260), "笑 谈 历 史 · EP23", f_brand, GOLD, offset=5)
    draw_text_with_shadow(d, (W // 2, 480), "大 明 篇 · 弘 治 十 二 年", f_pre, (240, 240, 245), offset=5)
    draw_text_with_shadow(d, (W // 2, 800), title_text, f_title, WHITE, offset=8)

    # 分隔线
    d.line([W // 2 - 500, 1020, W // 2 - 40, 1020], fill=GOLD, width=5)
    d.line([W // 2 + 40, 1020, W // 2 + 500, 1020], fill=GOLD, width=5)
    d.polygon([(W // 2, 1000), (W // 2 + 20, 1020), (W // 2, 1040), (W // 2 - 20, 1020)], fill=GOLD)

    draw_text_with_shadow(d, (W // 2, 1140), sub_text, f_sub, GOLD, offset=4)

    # 底部：主播名
    draw_text_with_shadow(d, (240, H - 240), "主播：大开 × 小李", f_host, WHITE, anchor="lm", offset=5)

    # 印章：李下整冠（古法右列先读：李、下；左列：整、冠）
    seal_w = seal_h = 560
    sx, sy = W - 180 - seal_w, H - 180 - seal_h
    d.rounded_rectangle([sx, sy, sx + seal_w, sy + seal_h], radius=30, fill=RED, outline=(240, 205, 110), width=5)
    pos = {"李": (0.72, 0.28), "下": (0.72, 0.72), "整": (0.28, 0.28), "冠": (0.28, 0.72)}
    for ch, (fx, fy) in pos.items():
        d.text((sx + seal_w * fx, sy + seal_h * fy), ch, font=f_seal, fill=(250, 245, 235), anchor="mm")

    img.save(out_path, "PNG")
    print("EP23 封面已生成:", out_path)


if __name__ == "__main__":
    main()
