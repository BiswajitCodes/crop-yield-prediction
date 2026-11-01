"""Generates the bundled illustrations (no internet needed).
To use real photographs instead, drop your own files into assets/:
  assets/farm_banner.jpg            (wide landscape, ~1600x520)
  assets/crop_images/<name>.png|jpg (rice, wheat, maize, cotton, sugarcane, other)
The app prefers your files; this script only overwrites files with the same names."""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

A = Path(__file__).parent / "assets"
(A / "crop_images").mkdir(parents=True, exist_ok=True)
S = 4  # supersampling


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def banner():
    random.seed(7)
    W, H = 1600 * 1, 520
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    horizon = 300
    for y in range(horizon + 40):
        d.line([(0, y), (W, y)], fill=lerp((96, 160, 222), (214, 234, 244), y / (horizon + 40)))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([980, 40, 1300, 360], fill=(255, 240, 200))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.blend(img, Image.composite(glow, img, glow.convert("L")), 0.0)
    img = Image.eval(img, lambda v: v)  # no-op
    from PIL import ImageChops
    img = ImageChops.add(img, glow.point(lambda v: int(v * .55)))
    # clouds
    cl = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    cd = ImageDraw.Draw(cl)
    for cx, cy, sc in [(250, 90, 1.2), (700, 60, 1.0), (1150, 120, 1.3), (1450, 70, .9)]:
        for _ in range(9):
            ox, oy = random.randint(-90, 90) * sc, random.randint(-14, 14) * sc
            r = random.randint(34, 62) * sc
            cd.ellipse([cx + ox - r * 1.5, cy + oy - r * .55, cx + ox + r * 1.5, cy + oy + r * .55], fill=(255, 255, 255, 120))
    cl = cl.filter(ImageFilter.GaussianBlur(14))
    img.paste(cl, (0, 0), cl)
    d = ImageDraw.Draw(img)

    def ridge(base, amp, color, seed, step=14):
        random.seed(seed)
        pts = [(0, H)]
        ph = [random.random() * 6 for _ in range(4)]
        for x in range(0, W + step, step):
            y = base - amp * (0.55 * math.sin(x / 210 + ph[0]) + 0.3 * math.sin(x / 90 + ph[1]) + 0.15 * math.sin(x / 41 + ph[2]))
            pts.append((x, y))
        pts.append((W, H))
        d.polygon(pts, fill=color)

    ridge(250, 95, (150, 185, 205), 1)
    ridge(275, 70, (96, 150, 150), 2)
    ridge(295, 45, (64, 125, 90), 3)
    # field with perspective rows
    for y in range(horizon, H):
        t = (y - horizon) / (H - horizon)
        d.line([(0, y), (W, y)], fill=lerp((120, 178, 70), (28, 112, 48), t))
    vx = 900
    for i in range(-40, 60):
        x_bot = vx + i * 70
        shade = (70, 150, 58) if i % 2 else (96, 168, 64)
        d.polygon([(vx + i * 4, horizon), (vx + i * 4 + 3, horizon), (x_bot + 34, H), (x_bot - 34, H)], fill=shade)
    # plants: many small blades, bigger toward the bottom
    random.seed(11)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for _ in range(9000):
        t = random.random() ** 1.8
        y = horizon + 6 + t * (H - horizon - 6)
        x = random.randint(-20, W + 20)
        hgt = 5 + 38 * t
        lean = random.uniform(-.35, .35) * hgt
        c = lerp((150, 205, 80), (44, 140, 52), random.random())
        ld.line([(x, y), (x + lean, y - hgt)], fill=c + (230,), width=max(1, int(1 + 2.2 * t)))
        if random.random() < .12 and t > .3:
            ld.ellipse([x + lean - 2 * t * 3, y - hgt - 2, x + lean + 2 * t * 3, y - hgt + 6 * t], fill=(214, 200, 90, 220))
    img.paste(layer, (0, 0), layer)
    # soft haze at horizon + left shade for text legibility
    haze = Image.new("RGBA", (W, H), (235, 245, 235, 0))
    hd = ImageDraw.Draw(haze)
    for y in range(horizon - 30, horizon + 60):
        a = int(70 * (1 - abs(y - horizon) / 60)) if abs(y - horizon) < 60 else 0
        hd.line([(0, y), (W, y)], fill=(235, 245, 235, max(a, 0)))
    haze = haze.filter(ImageFilter.GaussianBlur(10))
    img.paste(haze, (0, 0), haze)
    img.save(A / "farm_banner.jpg", quality=88, optimize=True)


def canvas():
    im = Image.new("RGBA", (240 * S, 240 * S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def finish(im, name):
    im.resize((240, 240), Image.LANCZOS).save(A / "crop_images" / f"{name}.png", optimize=True)


def leaf(d, x0, y0, x1, y1, w, fill):
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L * w, dx / L * w
    pts = []
    for i in range(21):
        t = i / 20
        k = math.sin(math.pi * t)
        pts.append((x0 + dx * t + nx * k, y0 + dy * t + ny * k))
    for i in range(20, -1, -1):
        t = i / 20
        k = math.sin(math.pi * t)
        pts.append((x0 + dx * t - nx * k, y0 + dy * t - ny * k))
    d.polygon(pts, fill=fill)


def rice():
    im, d = canvas()
    G, GD, GOLD = (86, 160, 50), (52, 118, 40), (226, 190, 70)
    for ox, bend, hh in [(-46, -40, 150), (0, 10, 175), (48, 46, 150)]:
        base = (120 + ox * .25, 215)
        pts = [(base[0] + (ox * .3) * (t) + bend * (t ** 2) * .9, base[1] - hh * t) for t in [i / 24 for i in range(25)]]
        d.line([(x * S, y * S) for x, y in pts], fill=GD, width=5 * S)
        x, y = pts[-1]
        for k in range(9):
            t = k / 8
            gx, gy = x + (t * 26) + 4, y + t * 40
            d.ellipse([(gx - 5) * S, (gy - 8) * S, (gx + 5) * S, (gy + 8) * S], fill=GOLD)
            d.ellipse([(gx - 16 + 4) * S, (gy - 8) * S, (gx - 6 + 4) * S, (gy + 8) * S], fill=(210, 176, 60))
    for sx, ex, ey in [(118, 60, 70), (125, 190, 80), (120, 40, 120), (122, 205, 130)]:
        leaf(d, sx * S, 215 * S, ex * S, ey * S + 40 * S, 7 * S, G)
    finish(im, "rice")


def wheat():
    im, d = canvas()
    for ox, rot in [(-38, -12), (0, 0), (38, 12)]:
        bx, by = 120 + ox * .5, 222
        tx, ty = bx + math.sin(math.radians(rot)) * 150, by - math.cos(math.radians(rot)) * 150
        d.line([bx * S, by * S, tx * S, ty * S], fill=(176, 150, 60), width=4 * S)
        for i in range(8):
            t = .35 + i * .08
            cx, cy = bx + (tx - bx) * (t + .25), by + (ty - by) * (t + .25)
            if i == 7:
                continue
            for side in (-1, 1):
                gx, gy = cx + side * 9 + (ox * .1), cy - 10
                leaf(d, (cx) * S, (cy + 6) * S, gx * S, (gy - 14) * S, 6 * S, (232, 184, 60) if side == 1 else (216, 164, 48))
        leaf(d, tx * S, (ty + 12) * S, (tx + math.sin(math.radians(rot)) * 14) * S, (ty - 22) * S, 6 * S, (236, 190, 64))
    finish(im, "wheat")


def maize():
    im, d = canvas()
    G, GD = (92, 168, 52), (60, 128, 42)
    leaf(d, 120 * S, 215 * S, 36 * S, 70 * S, 26 * S, GD)
    leaf(d, 120 * S, 215 * S, 204 * S, 70 * S, 26 * S, GD)
    d.ellipse([84 * S, 36 * S, 156 * S, 196 * S], fill=(248, 206, 56))
    for r in range(10):
        for c in range(5):
            x = 96 + c * 12 + (6 if r % 2 else 0)
            y = 50 + r * 14
            d.ellipse([(x - 5) * S, (y - 5) * S, (x + 5) * S, (y + 5) * S], fill=(255, 226, 96), outline=(214, 164, 30), width=S)
    leaf(d, 120 * S, 222 * S, 66 * S, 90 * S, 30 * S, G)
    leaf(d, 120 * S, 222 * S, 174 * S, 90 * S, 30 * S, (108, 184, 62))
    leaf(d, 120 * S, 222 * S, 120 * S, 120 * S, 22 * S, (124, 196, 72))
    finish(im, "maize")


def cotton():
    im, d = canvas()
    d.line([120 * S, 222 * S, 120 * S, 120 * S], fill=(110, 86, 52), width=5 * S)
    leaf(d, 120 * S, 190 * S, 40 * S, 150 * S, 16 * S, (76, 150, 56))
    leaf(d, 120 * S, 190 * S, 200 * S, 150 * S, 16 * S, (76, 150, 56))
    for cx, cy in [(88, 96), (152, 96), (120, 62)]:
        pts = [(120 + (cx - 120) * 0.0, 124)]
        d.polygon([(cx - 26) * S if False else (cx - 26) * S, (cy + 30) * S, (cx + 26) * S, (cy + 30) * S, cx * S, (cy + 4) * S], fill=(120, 92, 56))
        for ox, oy, r in [(-16, 0, 22), (16, 0, 22), (0, -14, 24), (-6, 8, 20), (8, 10, 20), (0, -2, 24)]:
            d.ellipse([(cx + ox - r) * S, (cy + oy - r) * S, (cx + ox + r) * S, (cy + oy + r) * S], fill=(252, 252, 250), outline=(214, 220, 226), width=S)
        for k in range(4):
            ang = k * math.pi / 2 + .6
            d.line([(cx) * S, (cy + 22) * S, (cx + 24 * math.cos(ang)) * S, (cy + 22 + 14 * math.sin(ang)) * S], fill=(120, 92, 56), width=3 * S)
    finish(im, "cotton")


def sugarcane():
    im, d = canvas()
    for x0, shade in [(86, (120, 170, 60)), (120, (96, 150, 52)), (154, (132, 180, 66))]:
        d.rectangle([(x0 - 11) * S, 50 * S, (x0 + 11) * S, 226 * S], fill=shade)
        for y in range(70, 226, 30):
            d.rectangle([(x0 - 13) * S, y * S, (x0 + 13) * S, (y + 5) * S], fill=(58, 100, 40))
            d.line([(x0 - 6) * S, (y + 8) * S, (x0 - 6) * S, (y + 24) * S], fill=(166, 206, 98), width=2 * S)
    for ex, ey, sx in [(34, 40, 98), (206, 44, 142), (70, 14, 120), (170, 14, 120)]:
        leaf(d, sx * S, 58 * S, ex * S, ey * S + 26 * S, 9 * S, (82, 160, 52))
    finish(im, "sugarcane")


def other():
    im, d = canvas()
    d.line([120 * S, 222 * S, 120 * S, 120 * S], fill=(90, 140, 60), width=6 * S)
    leaf(d, 120 * S, 130 * S, 32 * S, 56 * S, 34 * S, (82, 170, 60))
    leaf(d, 120 * S, 130 * S, 208 * S, 56 * S, 34 * S, (106, 190, 70))
    leaf(d, 120 * S, 190 * S, 60 * S, 150 * S, 18 * S, (70, 148, 52))
    leaf(d, 120 * S, 190 * S, 182 * S, 150 * S, 18 * S, (70, 148, 52))
    finish(im, "other")


if __name__ == "__main__":
    banner()
    for f in (rice, wheat, maize, cotton, sugarcane, other):
        f()
    print("assets written to", A)
