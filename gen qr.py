from PIL import Image, ImageDraw, ImageFont
import qrcode

data = [
    'QD1-1985',
    'QD1-1998',
    'QD1-2001',
    'QD1-2073',
    'QC5-9973',
    'QC7-7957',
    'QC4-9336',
    'FE3-8546',
    '4A3-5526',
    'QC7-2413',
    'QC7-7956-000',
    'QC5-9110-000',
    'QC5-9113-000',
    'QC7-7990-000',
    'QD1-1988-000',
    'FE4-1624-000',
    'QC8-0996-000',
]

dpi = 300
px_per_mm = dpi / 25.4

QR_MM = 11.0
QR_PX = int(round(QR_MM * px_per_mm))

LABEL_MM = 6  # ความสูงพื้นที่ label
LABEL_PX = int(round(LABEL_MM * px_per_mm))
LABEL_PAD_PX = int(round(1.0 * px_per_mm))  # padding ซ้าย/ขวาของข้อความ

FRAME_PAD_MM = 8.0  # ช่องว่างระหว่างกรอบกับเนื้อใน
FRAME_PAD_PX = int(round(FRAME_PAD_MM * px_per_mm))
FRAME_WIDTH_PX = 3

A4_W = int(round(210 * px_per_mm))
A4_H = int(round(297 * px_per_mm))

COLS = 7
MARGIN_PX = int(round(8 * px_per_mm))
ROW_GAP_PX = int(round(1 * px_per_mm))


# ---------------- Helpers ----------------
def load_font(pt):
    for name in ("DejaVuSans.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, pt)
        except:
            pass
    return ImageFont.load_default()


def text_bbox(draw, text, font):
    try:
        return draw.textbbox((0, 0), text, font=font)
    except AttributeError:
        w, h = draw.textsize(text, font=font)
        return (0, 0, w, h)


def fit_font_binary(draw, text, max_w_px, px_per_mm, lo_mm=3.5, hi_mm=4.4):
    # binary search mm -> px
    for _ in range(16):
        mid = (lo_mm + hi_mm) / 2
        font = load_font(int(round(mid * px_per_mm)))
        x0, y0, x1, y1 = text_bbox(draw, text, font)
        w = x1 - x0
        if w <= max_w_px:
            lo_mm = mid
        else:
            hi_mm = mid
    return load_font(int(round(lo_mm * px_per_mm)))


# ---------------- Layout sizes ----------------
CELL_INNER_W = QR_PX
CELL_INNER_H = QR_PX + LABEL_PX
CELL_W = CELL_INNER_W + 2 * FRAME_PAD_PX
CELL_H = CELL_INNER_H + 2 * FRAME_PAD_PX - 50
SPACE_X = (A4_W - 2 * MARGIN_PX - COLS * CELL_W) // (COLS - 1)

# ---------------- Stage 1: place all QR on A4 ----------------
a4 = Image.new("RGB", (A4_W, A4_H), "white")
page = ImageDraw.Draw(a4)

# เก็บตำแหน่งไว้สำหรับวาด label และกรอบในภายหลัง
cells = []  # dict: {code, qr_xy, label_box(x,y,w,h), frame_box(x0,y0,x1,y1)}

x, y = MARGIN_PX, MARGIN_PX
for i, code in enumerate(data):
    # กรอบนอก (ยังไม่วาด)
    fx0, fy0 = x, y
    fx1, fy1 = x + CELL_W, y + CELL_H

    # พื้นที่เนื้อใน
    ix0, iy0 = fx0 + FRAME_PAD_PX, fy0 + FRAME_PAD_PX

    # วาง QR (เท่านั้นในสเตจนี้)
    qr = qrcode.QRCode(border=0)
    qr.add_data(code)
    qr.make(fit=True)
    qim = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qim = qim.resize((QR_PX, QR_PX), Image.NEAREST)
    a4.paste(qim, (ix0, iy0))

    # เก็บตำแหน่ง label
    label_box = (ix0, iy0 + QR_PX, QR_PX, LABEL_PX)
    cells.append({
        "code": code,
        "qr_xy": (ix0, iy0),
        "label_box": label_box,
        "frame_box": (fx0, fy0, fx1, fy1),
    })

    # เดินตำแหน่งไปช่องถัดไป
    x += CELL_W + SPACE_X
    if (i + 1) % COLS == 0:
        x = MARGIN_PX
        y += CELL_H + ROW_GAP_PX

# ---------------- Stage 2: draw labels afterwards ----------------
for c in cells:
    code = c["code"]
    lx, ly, lw, lh = c["label_box"]
    # เคลียร์พื้น label เป็นขาวก่อน
    page.rectangle([lx, ly, lx + lw, ly + lh], fill="white")

    # ย่อฟอนต์ให้พอดีกว้าง (ภายใน padding)
    max_w = lw - 2 * LABEL_PAD_PX
    # วัดด้วย context แยก (หลีกเลี่ยงการวัดโดยมี offset)
    temp_img = Image.new("RGB", (lw, lh), "white")
    tdraw = ImageDraw.Draw(temp_img)
    font = fit_font_binary(tdraw, code, max_w, px_per_mm)

    # คำนวณตำแหน่งจริงด้วย bbox และชดเชย left/top bearing
    x0, y0, x1, y1 = text_bbox(tdraw, code, font)
    w, h = x1 - x0, y1 - y0
    tx = lx + LABEL_PAD_PX + (max_w - w) // 2 - x0
    ty = ly + (lh - h) // 2 - y0

    # วาดข้อความลงบน A4 (ไม่ใช้ stroke เพื่อไม่ให้ล้น)
    page.text((tx, ty), code, font=font, fill="black")

# ---------------- Stage 3: draw frames at the end ----------------
for c in cells:
    page.rectangle(c["frame_box"], outline="black", width=FRAME_WIDTH_PX)

# ---------------- Save ----------------
a4.save("qrcodes_a4.png", dpi=(dpi, dpi))
print("✅ Saved as qrcodes_a4.png")
