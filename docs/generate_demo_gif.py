#!/usr/bin/env python3
"""Generate docs/demo.gif — animated terminal demo for BunkerVM README."""

from PIL import Image, ImageDraw, ImageFont
import os

# ── Config ──────────────────────────────────────────────────────────────
W, H = 820, 520
BG       = (12, 12, 18)
HEADER   = (18, 18, 28)
GRAY     = (107, 107, 128)
WHITE    = (232, 232, 240)
GREEN    = (52, 211, 153)
CYAN     = (34, 211, 238)
PINK     = (244, 114, 182)
RED      = (248, 113, 113)
YELLOW   = (251, 191, 36)
DOT_G    = (52, 211, 153)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_SIZE = 13
TITLE_SIZE = 12

# ── Lines to render (color, text) ──────────────────────────────────────
LINES = [
    # (color, text, y_position)
    (GREEN,  "$ ", WHITE, "pip install bunkervm",                                  68),
    (GREEN,  "✓ Installed bunkervm-0.6.0", None, None,                             90),
    (GREEN,  "$ ", WHITE, "bunkervm demo",                                        118),
    (CYAN,   "⚡ Booting Firecracker MicroVM...", None, None,                      140),
    (GREEN,  "✓ VM ready in 2.3s — KVM hardware isolation active", None, None,    162),
    (GRAY,   "  Kernel: 6.1.102 │ OS: Alpine Linux │ Python: 3.12", None, None,   184),
    (GRAY,   "  Running code inside sandbox...", None, None,                       212),
    (PINK,   "  Prime numbers under 100:", None, None,                             250),
    (PINK,   "  2  3  5  7  11  13  17  19  23  29  31  37  41  43  47", None, None, 272),
    (PINK,   "  53  59  61  67  71  73  79  83  89  97", None, None,              294),
    (GREEN,  "✓ Code ran safely inside a Firecracker microVM", None, None,        332),
    (GREEN,  "✓ Full Linux environment (not a container)", None, None,            354),
    (GREEN,  "✓ Hardware-level isolation via KVM", None, None,                    376),
    (GREEN,  "✓ VM destroyed after demo", None, None,                             398),
    (CYAN,   "🧹 Destroying sandbox...", None, None,                               436),
    (GREEN,  "Done. ✓ Demo completed in 3.6s", None, None,                        458),
    (GREEN,  "Your host was never touched.", None, None,                           472),
]

# Timing: delay in ms before each line appears
DELAYS = [300, 400, 500, 400, 700, 400, 400, 500, 400, 400, 500, 400, 400, 400, 600, 400, 400]

# How long to hold the final frame
FINAL_HOLD = 3000

def make_base(font, title_font):
    """Draw the terminal chrome (static parts)."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rounded_rectangle([(1, 1), (W - 2, 39)], radius=12, fill=HEADER)
    draw.rectangle([(1, 28), (W - 2, 39)], fill=BG)

    # Traffic lights
    draw.ellipse([(14, 13), (26, 25)], fill=RED)
    draw.ellipse([(34, 13), (46, 25)], fill=YELLOW)
    draw.ellipse([(54, 13), (66, 25)], fill=DOT_G)

    # Title
    title = "bunkervm — demo"
    bbox = title_font.getbbox(title)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, 10), title, fill=GRAY, font=title_font)

    return img


def draw_line(draw, font, line_data):
    """Draw a single line onto the image."""
    c1, t1, c2, t2, y = line_data
    x = 20
    draw.text((x, y), t1, fill=c1, font=font)
    if c2 is not None and t2 is not None:
        # Prompt + command on same line
        bbox = font.getbbox(t1)
        prompt_w = bbox[2] - bbox[0]
        draw.text((x + prompt_w, y), t2, fill=c2, font=font)


def main():
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    title_font = ImageFont.truetype(FONT_PATH, TITLE_SIZE)

    frames = []
    durations = []

    # Initial empty terminal frame (brief pause)
    base = make_base(font, title_font)
    frames.append(base.copy())
    durations.append(500)

    # Build up frames line by line
    canvas = base.copy()
    for i, line_data in enumerate(LINES):
        draw = ImageDraw.Draw(canvas)
        draw_line(draw, font, line_data)
        frames.append(canvas.copy())
        durations.append(DELAYS[i] if i < len(DELAYS) else 400)

    # Hold final frame
    durations[-1] = FINAL_HOLD

    # Add a "replay" hint frame
    final = canvas.copy()
    draw = ImageDraw.Draw(final)
    hint = "↻ replay"
    bbox = font.getbbox(hint)
    hw = bbox[2] - bbox[0]
    draw.text(((W - hw) // 2, H - 18), hint, fill=(107, 107, 128, 128), font=title_font)
    frames.append(final)
    durations.append(1500)

    # Save GIF
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo.gif")
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    print(f"✓ Saved {out_path} ({len(frames)} frames, {os.path.getsize(out_path) // 1024} KB)")


if __name__ == "__main__":
    main()
