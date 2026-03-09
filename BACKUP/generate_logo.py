"""
Generate Velora AI Trading logo PNG for the mobile app.
Creates a clean white-background version suitable for use in the app header.
"""
import os
import sys

def main():
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               "mobile_app", "assets", "velora_logo.png")
    
    # Try using PIL/Pillow
    try:
        from PIL import Image, ImageDraw, ImageFont
        create_logo_pil(output_path)
        print(f"[OK] Logo created at {output_path}")
        return
    except ImportError:
        pass
    
    # Fallback: install Pillow then retry
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "-q"], check=True)
    from PIL import Image, ImageDraw, ImageFont
    create_logo_pil(output_path)
    print(f"[OK] Logo created at {output_path}")


def create_logo_pil(out_path):
    from PIL import Image, ImageDraw, ImageFont
    import math

    W, H = 512, 512
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)

    BLUE  = (0, 122, 255, 255)
    DARK  = (20,  20,  30, 255)
    MID   = (50,  60,  80, 255)

    # ── V shape ──────────────────────────────────────────────────────
    # Two thick arms of the "V"
    stroke = 28
    # Left arm: top-left down to bottom-center
    lx0, ly0 = 80,  70
    lx1, ly1 = 256, 310
    # Right arm: top-right to bottom-center  (but blended with A)
    rx0, ry0 = 432, 70
    rx1, ry1 = 256, 310

    def thick_line(draw, x0, y0, x1, y1, width, color):
        draw.line([(x0, y0), (x1, y1)], fill=color, width=width)

    thick_line(d, lx0, ly0, lx1, ly1, stroke, DARK)
    thick_line(d, rx0, ry0, rx1, ry1, stroke, DARK)

    # ── A shape over the V (using blue) ──────────────────────────────
    # "A" sits in the upper-right of the V
    a_left_x,  a_left_y  = 200, 70
    a_right_x, a_right_y = 390, 70
    a_apex_x,  a_apex_y  = 295, 240
    thick_line(d, a_left_x, a_left_y, a_apex_x, a_apex_y, 22, BLUE)
    thick_line(d, a_right_x, a_right_y, a_apex_x, a_apex_y, 22, BLUE)
    # Cross-bar of A
    d.rectangle([230, 175, 360, 197], fill=BLUE)

    # ── Circuit traces rising from inside the V gap ───────────────────
    cx, cy = 256, 175  # center base of traces
    trace_data = [
        # (offset_x, height, endpoint_x_offset)
        (-50, 100, -50),
        (-30, 120, -30),
        (-10, 130, -10),
        ( 10, 130,  10),
        ( 30, 120,  30),
        ( 50, 100,  50),
    ]
    for (ox, h, ex) in trace_data:
        x_start = cx + ox
        x_end   = cx + ex
        y_start = cy + 10
        y_end   = cy - h
        d.line([(x_start, y_start), (x_end, y_end)], fill=BLUE, width=3)
        # Terminal circle
        r = 5
        d.ellipse([x_end - r, y_end - r, x_end + r, y_end + r], fill=BLUE)
        # Small horizontal connection
        d.line([(x_end - 12, y_end), (x_end + 12, y_end)], fill=BLUE, width=3)

    # ── Mountain silhouette below the V ──────────────────────────────
    peak    = (256, 315)
    ml      = (160, 380)
    mr      = (352, 380)
    base_l  = (120, 390)
    base_r  = (392, 390)
    d.polygon([peak, ml, base_l, base_r, mr], fill=DARK)
    # Facets
    d.line([peak, (210, 355)], fill=MID, width=3)
    d.line([peak, (300, 360)], fill=MID, width=3)
    d.line([(210, 355), (180, 380)], fill=MID, width=2)

    # ── Text: VELORA ─────────────────────────────────────────────────
    # Try a font, fall back to default
    try:
        font_big  = ImageFont.truetype("arial.ttf", 72)
        font_sub  = ImageFont.truetype("arial.ttf", 28)
    except Exception:
        try:
            font_big  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
            font_sub  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        except Exception:
            font_big  = ImageFont.load_default()
            font_sub  = font_big

    # VELORA
    text1 = "VELORA"
    bbox1 = d.textbbox((0, 0), text1, font=font_big)
    tw1   = bbox1[2] - bbox1[0]
    d.text(((W - tw1) // 2, 405), text1, fill=DARK, font=font_big)

    # AI TRADING
    text2 = "AI TRADING"
    bbox2 = d.textbbox((0, 0), text2, font=font_sub)
    tw2   = bbox2[2] - bbox2[0]
    d.text(((W - tw2) // 2, 483), text2, fill=MID, font=font_sub)

    img.save(out_path, "PNG")


if __name__ == "__main__":
    main()
