import qrcode
from pathlib import Path
from PIL import Image, ImageDraw

def generate_qr_code(data: str) -> Image.Image:
    """Generate a QR code image from the provided data."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    # Convert to RGB if in RGBA mode
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    return img

def _detect_photo_square_bbox(template_rgba: Image.Image) -> tuple[int, int, int, int] | None:
    """Detect the top photo square region inside the ticket border.

    Returns (left, top, right, bottom) in image coordinates, or None if not detected.
    Heuristic tuned for the provided ticket template: find the inner border bbox, then
    locate the first sustained bright (light) band that begins the text/control area.
    """
    import numpy as np

    rgb = template_rgba.convert("RGB")
    arr = np.asarray(rgb)
    if arr.ndim != 3 or arr.shape[2] != 3:
        return None

    gray = (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]).astype("float32")
    black = gray < 40
    row_score = black.mean(axis=1)
    col_score = black.mean(axis=0)

    r = np.where(row_score > 0.08)[0]
    c = np.where(col_score > 0.08)[0]
    if len(r) < 2 or len(c) < 2:
        return None

    # Outer border bbox
    x0, y0, x1, y1 = int(c[0]), int(r[0]), int(c[-1]), int(r[-1])

    # Shrink into inner content bbox (exclude border thickness)
    crop_gray = gray[y0 : y1 + 1, x0 : x1 + 1]
    crop_black = crop_gray < 40
    rs = crop_black.mean(axis=1)
    cs = crop_black.mean(axis=0)
    top = int(np.argmax(rs < 0.05))
    bottom = int(len(rs) - 1 - np.argmax(rs[::-1] < 0.05))
    left = int(np.argmax(cs < 0.05))
    right = int(len(cs) - 1 - np.argmax(cs[::-1] < 0.05))

    ix0, iy0, ix1, iy1 = x0 + left, y0 + top, x0 + right, y0 + bottom
    if ix1 <= ix0 or iy1 <= iy0:
        return None

    inner = gray[iy0 : iy1 + 1, ix0 : ix1 + 1]
    row_mean = inner.mean(axis=1)

    # Find first sustained bright region (text/control area) below the photo.
    thr = 215.0
    consec = 10
    start = min(40, max(0, len(row_mean) - consec - 1))
    split = None
    for i in range(start, len(row_mean) - consec):
        if (row_mean[i : i + consec] > thr).all():
            split = i
            break
    if split is None or split < 20:
        return None

    photo_top = iy0
    photo_bottom = iy0 + split - 1
    photo_left = ix0
    photo_right = ix1

    # Convert photo rectangle into an inscribed square (centered horizontally).
    photo_w = photo_right - photo_left
    photo_h = photo_bottom - photo_top
    side = int(min(photo_w, photo_h))
    if side < 50:
        return None
    sq_left = int(photo_left + (photo_w - side) / 2)
    sq_top = int(photo_top + (photo_h - side) / 2)
    return (sq_left, sq_top, sq_left + side, sq_top + side)

def generate_branded_ticket_image(
    data: str,
    template_path: str | Path,
    *,
    fit_mode: str = "legacy",
    qr_scale: float = 0.27,
    qr_center_x: float = 0.5,
    qr_center_y: float = 0.39,
    qr_padding_scale: float = 0.08,
    photo_square_inset_scale: float = 0.04,
    photo_square_inset_top_scale: float | None = None,
    photo_square_offset_y_scale: float = 0.0,
) -> Image.Image:
    """Place a scannable QR code into the ticket template.

    qr_scale is relative to min(width, height). qr_center_x/qr_center_y are
    normalized template coordinates (0..1) describing the QR "card" center.
    """
    template = Image.open(template_path).convert("RGBA")
    width, height = template.size

    fit_mode = (fit_mode or "legacy").strip().lower()

    # photo_square: fill the inner photo square area with a QR (with minimal padding).
    if fit_mode in {"photo_square", "inner_square", "photo"}:
        bbox = _detect_photo_square_bbox(template)
        if bbox is not None:
            left, top, right, bottom = bbox
            side = max(1, right - left)
            inset = max(2, int(side * float(photo_square_inset_scale)))
            top_inset_scale = photo_square_inset_scale if photo_square_inset_top_scale is None else float(photo_square_inset_top_scale)
            inset_top = max(2, int(side * top_inset_scale))
            inset_bottom = inset
            inset_left = inset
            inset_right = inset

            side_w = max(1, side - (inset_left + inset_right))
            side_h = max(1, side - (inset_top + inset_bottom))
            side = max(1, min(side_w, side_h))

            # Center the square within the inset area (keeps it visually centered even if
            # top inset differs from other sides).
            left += inset_left + max(0, int((side_w - side) / 2))
            top += inset_top + max(0, int((side_h - side) / 2))

            # Optional: shift the whole white box down a bit within the photo square.
            offset_y = int(side * float(photo_square_offset_y_scale))
            top += offset_y

            # Use a rounded white backing card that fills the square, then the QR inside it.
            padding = max(2, int(side * float(qr_padding_scale)))
            card = Image.new("RGBA", (side, side), (255, 255, 255, 245))
            mask = Image.new("L", (side, side), 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle(
                (0, 0, side - 1, side - 1),
                radius=max(10, int(side * 0.08)),
                fill=255,
            )
            card.putalpha(mask)

            qr_side = max(1, side - (padding * 2))
            qr_img = generate_qr_code(data).convert("RGBA").resize(
                (qr_side, qr_side),
                Image.Resampling.NEAREST,
            )
            card.alpha_composite(qr_img, (padding, padding))
            template.alpha_composite(card, (left, top))
            return template.convert("RGB")

    qr_scale = float(qr_scale)
    qr_center_x = float(qr_center_x)
    qr_center_y = float(qr_center_y)
    qr_size = int(min(width, height) * qr_scale)
    qr_img = generate_qr_code(data).convert("RGBA").resize(
        (qr_size, qr_size),
        Image.Resampling.NEAREST,
    )

    padding = max(6, int(qr_size * float(qr_padding_scale)))
    card_size = qr_size + (padding * 2)
    card = Image.new("RGBA", (card_size, card_size), (255, 247, 247, 245))
    mask = Image.new("L", (card_size, card_size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        (0, 0, card_size - 1, card_size - 1),
        radius=max(12, int(card_size * 0.08)),
        fill=255,
    )
    card.putalpha(mask)
    card.alpha_composite(qr_img, (padding, padding))

    # Place the QR "card" by normalized center coordinates.
    x = int(width * qr_center_x - card_size / 2)
    y = int(height * qr_center_y - card_size / 2)
    template.alpha_composite(card, (x, y))
    return template.convert("RGB")
