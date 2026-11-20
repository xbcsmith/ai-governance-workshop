#!/usr/bin/env python3
"""Generate the workshop "How it works" diagrams for the slide deck: a static PNG and a step-by-step GIF.

Same approach as the epr-workshop generator: Pillow, bundled fonts, a dark palette, an animated GIF
plus a PNG of the finished frame. Each diagram is built in steps. The GIF reveals one step at a time
with a short fade and a caption ("3/8  The tool-call gate checks the call before it runs").

  python generate_diagram_images.py                 # every diagram: PNG (1920x1080) and GIF (1280 wide)
  python generate_diagram_images.py --only 03       # one diagram (match on the file name)
  python generate_diagram_images.py --no-gif        # PNGs only
  python generate_diagram_images.py --no-title      # crop the title off, for slides that have their own
  python generate_diagram_images.py --bg F4F1EA     # match your slide background (light colours get dark text)
  python generate_diagram_images.py --bg 14171C --out ../images_deck   # write to a separate folder
  python generate_diagram_images.py --theme ./theme.json --out ../images   # colours from a theme file

Images are written to ../images. Colour means a role, and each role also carries a text tag,
so the diagrams still read in greyscale. These are the default colours; a theme file can change them:

  MODEL  purple   a language model writes something
  JUDGE  teal     the judge answers yes or no
  RULE   blue     a fixed rule or deterministic check, no model
  HUMAN  amber    a human decides
  red / green     blocked or flagged / passed or approved

Theme file (JSON, no extra packages). Every key is optional and colours are hex strings:

  {
    "background": "#eeeeee",
    "text": "#000000",
    "muted": "#595959",
    "soft": "#2d2d2d",
    "roles": {"model": "#212121", "judge": "#0097a7", "rule": "#4285f4",
              "human": "#ffab40", "ok": "#10b981", "block": "#ef4444"}
  }

With a theme, the title and label colours are derived from each role colour and nudged until they
reach a readable contrast on the background. --bg overrides the theme's background.
"""

import argparse
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "images")

MONO_B = os.path.join(HERE, "DejaVuSansMono-Bold.ttf")
MONO = os.path.join(HERE, "DejaVuSansMono.ttf")
SANS_B = os.path.join(HERE, "Poppins-Bold.ttf")
SANS = os.path.join(HERE, "Poppins-Medium.ttf")

# -- colour palette (same as the epr-workshop images) -------------------------------------------
# These are defaults. A --theme file replaces the role colours (PURPLE is the MODEL role, and so on).
BG = (10, 12, 16)
SURFACE = (17, 19, 24)
BORDER = (30, 34, 48)
TEXT = (226, 232, 240)
MUTED = (100, 116, 139)
BLUE = (59, 130, 246)
GREEN = (16, 185, 129)
AMBER = (245, 159, 11)
RED = (239, 68, 68)
PURPLE = (139, 92, 246)
L_BLUE = (147, 197, 253)
L_GREEN = (110, 231, 183)
L_RED = (252, 165, 165)
L_AMBER = (253, 230, 138)
L_PURP = (196, 181, 253)
TEAL = (20, 184, 166)
L_TEAL = (153, 246, 228)
SOFT = (148, 163, 184)

W, H = 1920, 1080
S = 2            # draw at 2x and scale down, so edges and text are smooth
TITLE_CROP = 148  # pixels removed from the top with --no-title

# role -> (line colour, light colour, tag text)
ROLES = {
    "model": (PURPLE, L_PURP, "MODEL"),
    "judge": (TEAL, L_TEAL, "JUDGE"),
    "rule": (BLUE, L_BLUE, "RULE"),
    "human": (AMBER, L_AMBER, "HUMAN"),
    "ok": (GREEN, L_GREEN, None),
    "block": (RED, L_RED, None),
    "plain": (MUTED, TEXT, None),
}



def parse_color(text):
    """'#14171C', '14171C' or '#abc' to an (r, g, b) tuple."""
    t = text.strip().lstrip("#")
    if len(t) == 3:
        t = "".join(c * 2 for c in t)
    if len(t) != 6 or any(c not in "0123456789abcdefABCDEF" for c in t):
        raise argparse.ArgumentTypeError(f"not a hex colour: {text!r} (use something like #14171C)")
    return tuple(int(t[i:i + 2], 16) for i in (0, 2, 4))


THEME_KEYS = {"background", "text", "muted", "soft", "roles"}
THEME_ROLES = {"model", "judge", "rule", "human", "ok", "block"}


def load_theme(path):
    """Read a theme JSON file into {'background': rgb, ..., 'roles': {role: rgb}}. Used as an argparse type."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        raise argparse.ArgumentTypeError(f"cannot read theme file {path!r}: {e.strerror}")
    except json.JSONDecodeError as e:
        raise argparse.ArgumentTypeError(f"{path!r} is not valid JSON: {e}")
    if not isinstance(data, dict):
        raise argparse.ArgumentTypeError(f"{path!r} must contain a JSON object")
    unknown = set(data) - THEME_KEYS
    roles = data.get("roles", {})
    if not isinstance(roles, dict):
        raise argparse.ArgumentTypeError("theme 'roles' must be an object")
    unknown_roles = set(roles) - THEME_ROLES
    if unknown or unknown_roles:
        bad = sorted(unknown) + [f"roles.{r}" for r in sorted(unknown_roles)]
        raise argparse.ArgumentTypeError(
            f"unknown theme key(s): {', '.join(bad)}. Allowed: {', '.join(sorted(THEME_KEYS))}; "
            f"roles: {', '.join(sorted(THEME_ROLES))}")
    theme = {k: parse_color(v) for k, v in data.items() if k != "roles"}
    theme["roles"] = {k: parse_color(v) for k, v in roles.items()}
    return theme


def luminance(c):
    """WCAG relative luminance of an (r, g, b) colour, 0 (black) to 1 (white)."""
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def readable(color, bg, ratio=4.5):
    """The role colour, nudged toward black (light bg) or white (dark bg) until it reads on its own tinted fill."""
    toward = (0, 0, 0) if luminance(bg) > 0.18 else (255, 255, 255)
    fill = mix(bg, color, 0.22)
    out = color
    for i in range(21):
        out = mix(color, toward, i / 20)
        if contrast(out, fill) >= ratio:
            break
    return out


def on_color(fill):
    """Text colour for labels drawn on a solid role colour: the background or the text colour, whichever reads better."""
    return BG if contrast(BG, fill) >= contrast(TEXT, fill) else TEXT


def apply_theme(theme, bg):
    """Install a theme's role colours, then set the background and the colours that depend on it."""
    global BLUE, GREEN, AMBER, RED, PURPLE, TEAL
    roles = theme.get("roles", {})
    PURPLE = roles.get("model", PURPLE)
    TEAL = roles.get("judge", TEAL)
    BLUE = roles.get("rule", BLUE)
    AMBER = roles.get("human", AMBER)
    GREEN = roles.get("ok", GREEN)
    RED = roles.get("block", RED)
    apply_background(bg, text=theme.get("text"), muted=theme.get("muted"), soft=theme.get("soft"), tint=bool(theme))


def apply_background(bg, text=None, muted=None, soft=None, tint=False):
    """Set the background, and pick text and accent colours that stay readable on it.

    text, muted and soft override the automatic text colours. tint=True derives the light title colours
    from the role colours by contrast instead of using the fixed defaults.
    """
    global BG, TEXT, MUTED, SOFT, L_BLUE, L_GREEN, L_RED, L_AMBER, L_PURP, L_TEAL, ROLES
    BG = bg
    luminance = (0.2126 * bg[0] + 0.7152 * bg[1] + 0.0722 * bg[2]) / 255
    if luminance > 0.55:  # a light slide: dark text, and darker accents for titles
        TEXT, MUTED, SOFT = (15, 23, 42), (71, 85, 105), (51, 65, 85)
        dk = lambda c: tuple(int(v * 0.72) for v in c)
        L_BLUE, L_GREEN, L_RED, L_AMBER, L_PURP, L_TEAL = (dk(BLUE), dk(GREEN), dk(RED), dk(AMBER), dk(PURPLE), dk(TEAL))
    else:
        TEXT, MUTED, SOFT = (226, 232, 240), (100, 116, 139), (148, 163, 184)
        L_BLUE, L_GREEN, L_RED = (147, 197, 253), (110, 231, 183), (252, 165, 165)
        L_AMBER, L_PURP, L_TEAL = (253, 230, 138), (196, 181, 253), (153, 246, 228)
    TEXT = text or TEXT
    MUTED = muted or MUTED
    if soft:
        SOFT = soft
    elif text or muted:
        SOFT = mix(TEXT, MUTED, 0.5)
    if tint:
        L_BLUE, L_GREEN, L_RED, L_AMBER, L_PURP, L_TEAL = (readable(c, bg) for c in (BLUE, GREEN, RED, AMBER, PURPLE, TEAL))
    ROLES = {
        "model": (PURPLE, L_PURP, "MODEL"),
        "judge": (TEAL, L_TEAL, "JUDGE"),
        "rule": (BLUE, L_BLUE, "RULE"),
        "human": (AMBER, L_AMBER, "HUMAN"),
        "ok": (GREEN, L_GREEN, None),
        "block": (RED, L_RED, None),
        "plain": (MUTED, TEXT, None),
    }


def blend(color, a):
    return tuple(int(BG[i] + (color[i] - BG[i]) * a) for i in range(3))


class Canvas:
    """Records every draw call with the step it belongs to, then replays them.

    Step 0 is always visible (the header and the legend). cv.step("caption") starts the next step.
    stage(k) is the picture with steps 0..k drawn, and the GIF fades from stage(k-1) to stage(k).
    """

    def __init__(self):
        self.ops = []
        self.step_no = 0
        self.captions = [""]
        self._fonts = {}
        self._stages = {}

    def step(self, caption):
        self.step_no += 1
        self.captions.append(caption)

    def font(self, path, size):
        key = (path, size)
        if key not in self._fonts:
            self._fonts[key] = ImageFont.truetype(path, int(size * S))
        return self._fonts[key]

    def width(self, text, font):
        return font.getlength(text) / S

    # -- recording ----------------------------------------------------------------------------
    def rect(self, x, y, w, h, fill, outline=None, r=18, width=3):
        self.ops.append((self.step_no, "rect", (x, y, w, h, fill, outline, r, width)))

    def text(self, x, y, s, font, color=None, anchor="mm"):
        self.ops.append((self.step_no, "text", (x, y, s, font, TEXT if color is None else color, anchor)))

    def line(self, pts, color, width=4):
        self.ops.append((self.step_no, "line", (pts, color, width)))

    def poly(self, pts, color):
        self.ops.append((self.step_no, "poly", (pts, color)))

    # -- replay -------------------------------------------------------------------------------
    def stage(self, upto):
        if upto not in self._stages:
            img = Image.new("RGB", (W * S, H * S), BG)
            d = ImageDraw.Draw(img)
            for step_no, kind, a in self.ops:
                if step_no > upto:
                    continue
                if kind == "rect":
                    x, y, w, h, fill, outline, r, width = a
                    d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S], radius=r * S, fill=fill,
                                        outline=outline, width=int(width * S))
                elif kind == "text":
                    x, y, s_, font, color, anchor = a
                    d.text((x * S, y * S), s_, font=font, fill=color, anchor=anchor)
                elif kind == "line":
                    pts, color, width = a
                    d.line([(px * S, py * S) for px, py in pts], fill=color, width=int(width * S), joint="curve")
                elif kind == "poly":
                    pts, color = a
                    d.polygon([(px * S, py * S) for px, py in pts], fill=color)
            self._stages[upto] = img
        return self._stages[upto]

    def caption(self, img, k):
        """Draw 'k/N  caption' in the band under the title."""
        d = ImageDraw.Draw(img)
        f_chip, f_txt = self.font(MONO_B, 22), self.font(SANS_B, 28)
        label = f"{k}/{self.step_no}"
        cw = self.width(label, f_chip) + 26
        x, y = 60, 178
        d.rounded_rectangle([x * S, (y - 18) * S, (x + cw) * S, (y + 18) * S], radius=10 * S, fill=AMBER)
        d.text(((x + cw / 2) * S, y * S), label, font=f_chip, fill=on_color(AMBER), anchor="mm")
        d.text(((x + cw + 18) * S, y * S), self.captions[k], font=f_txt, fill=TEXT, anchor="lm")

    # -- output -------------------------------------------------------------------------------
    def _finish(self, img, size, crop_title):
        if crop_title:
            img = img.crop((0, TITLE_CROP * S, W * S, H * S))
        w = size
        return img.resize((w, round(w * img.size[1] / img.size[0])), Image.LANCZOS)

    def save_png(self, name, crop_title=False):
        img = self._finish(self.stage(self.step_no), W, crop_title)
        path = os.path.join(OUT, name)
        img.save(path, "PNG")
        report(path, f"{img.size[0]}x{img.size[1]}", "PNG")

    def save_gif(self, name, width=1280, hold=1600, crop_title=False):
        fades = (0.3, 0.6, 1.0)
        frames, durations = [], []

        def add(img, ms):
            frames.append(self._finish(img, width, crop_title))
            durations.append(ms)

        add(self.stage(0), 700)
        for k in range(1, self.step_no + 1):
            for i, a in enumerate(fades):
                img = Image.blend(self.stage(k - 1), self.stage(k), a)
                self.caption(img, k)
                last = i == len(fades) - 1
                add(img, (hold * 2.5 if k == self.step_no else hold) if last else 70)
        # one palette for the whole animation, taken from the finished frame, so colours do not flicker
        palette = frames[-1].quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
        path = os.path.join(OUT, name)
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=False)
        report(path, f"{frames[0].size[0]}x{frames[0].size[1]}, {len(frames)} frames", "GIF")


def report(path, detail, kind):
    shown = os.path.relpath(path, HERE)
    shown = path if shown.startswith(".." + os.sep + ".." + os.sep) else shown
    print(f"  wrote {shown}  ({kind}, {detail}, {os.path.getsize(path) // 1024}KB)")


def wrap(cv, text, font, maxw):
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w_ in words:
            trial = (cur + " " + w_).strip()
            if cv.width(trial, font) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w_
        lines.append(cur)
    return lines


class Box:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    def top(self, f=0.5):
        return (self.x + self.w * f, self.y)

    def bottom(self, f=0.5):
        return (self.x + self.w * f, self.y + self.h)

    def left(self, f=0.5):
        return (self.x, self.y + self.h * f)

    def right(self, f=0.5):
        return (self.x + self.w, self.y + self.h * f)


def box(cv, x, y, w, title, lines=(), role="plain", h=0, tsize=30, lsize=24, align="center", tag=True, mono=False, vcenter=True):
    col, light, tagtxt = ROLES[role]
    f_t = cv.font(SANS_B, tsize)
    f_l = cv.font(MONO if mono else SANS, lsize)
    pad = 24
    t_lines = wrap(cv, title, f_t, w - 2 * pad)
    l_lines = []
    for ln in lines:
        l_lines += wrap(cv, ln, f_l, w - 2 * pad)
    t_h = len(t_lines) * tsize * 1.3
    l_h = len(l_lines) * lsize * 1.45
    need = pad + t_h + (12 if l_lines else 0) + l_h + pad
    h = max(h, need)
    cv.rect(x, y, w, h, blend(col, 0.14), col)
    cy = y + pad + tsize * 0.65 + ((h - need) / 2 if vcenter else 0)
    for ln in t_lines:
        cv.text(x + w / 2 if align == "center" else x + pad, cy, ln, f_t, light,
                "mm" if align == "center" else "lm")
        cy += tsize * 1.3
    cy += 12 - tsize * 0.65 + lsize * 0.72
    for ln in l_lines:
        cv.text(x + w / 2 if align == "center" else x + pad, cy, ln, f_l, TEXT if align == "left" else SOFT,
                "mm" if align == "center" else "lm")
        cy += lsize * 1.45
    if tag and tagtxt:
        f_tag = cv.font(MONO_B, 17)
        tw = cv.width(tagtxt, f_tag) + 26
        cv.rect(x + 20, y - 15, tw, 30, col, None, r=8)
        cv.text(x + 20 + tw / 2, y, tagtxt, f_tag, on_color(col))
    return Box(x, y, w, h)


def chip(cv, x, y, text, role, size=22, w=None):
    col, light, _ = ROLES[role]
    f = cv.font(MONO_B, size)
    tw = w or cv.width(text, f) + 34
    cv.rect(x, y, tw, size * 1.9, blend(col, 0.22), col, r=12, width=2)
    cv.text(x + tw / 2, y + size * 0.95, text, f, light)
    return tw


def arrow(cv, pts, color=None, width=4, label=None, seg=None, off=(0, -20), dashed=False, head=16, lsize=20, lbg=True):
    default_color = color is None
    color = SOFT if default_color else color
    if dashed:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            length = math.hypot(x1 - x0, y1 - y0)
            ux, uy = (x1 - x0) / max(length, 1), (y1 - y0) / max(length, 1)
            t, on = 0.0, True
            while t < length:
                t2 = min(t + (14 if on else 9), length)
                if on:
                    cv.line([(x0 + ux * t, y0 + uy * t), (x0 + ux * t2, y0 + uy * t2)], color, width)
                t, on = t2, not on
    else:
        cv.line(pts, color, width)
    (x0, y0), (x1, y1) = pts[-2], pts[-1]
    length = max(math.hypot(x1 - x0, y1 - y0), 1)
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    px, py = -uy, ux
    cv.poly([(x1, y1), (x1 - head * ux + head * 0.5 * px, y1 - head * uy + head * 0.5 * py),
             (x1 - head * ux - head * 0.5 * px, y1 - head * uy - head * 0.5 * py)], color)
    if label:
        if seg is None:
            seg = max(range(len(pts) - 1), key=lambda i: math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]))
        (a, b), (c, d) = pts[seg], pts[seg + 1]
        mx, my = (a + c) / 2 + off[0], (b + d) / 2 + off[1]
        f = cv.font(SANS, lsize)
        if lbg:
            tw = cv.width(label, f)
            cv.rect(mx - tw / 2 - 8, my - lsize * 0.8, tw + 16, lsize * 1.6, BG, None, r=6, width=0)
        cv.text(mx, my, label, f, MUTED if default_color else color)


def header(cv, eyebrow, title):
    cv.text(60, 62, eyebrow, cv.font(MONO_B, 22), MUTED, "lm")
    cv.text(60, 118, title, cv.font(SANS_B, 46), TEXT, "lm")


def legend(cv, roles):
    keep, cv.step_no = cv.step_no, 0  # the legend is part of step 0: always visible
    x, y = 60, 1030
    notes = {"model": "a model writes", "judge": "the judge says yes or no", "rule": "a fixed rule, no model",
             "human": "a human decides"}
    f = cv.font(SANS, 20)
    for role in roles:
        col, light, tagtxt = ROLES[role]
        cv.rect(x, y - 13, 24, 26, col, None, r=6)
        cv.text(x + 36, y, f"{tagtxt}: {notes[role]}", f, MUTED, "lm")
        x += 36 + cv.width(f"{tagtxt}: {notes[role]}", f) + 40
    cv.step_no = keep


def new(eyebrow, title):
    cv = Canvas()
    header(cv, eyebrow, title)
    return cv


# ================================================================================================
# 00  The map: before, during, after
# ================================================================================================
def col_header(cv, name, x, w=540):
    cv.text(x + w / 2, 238, name, cv.font(SANS_B, 34), TEXT)
    cv.line([(x, 268), (x + w, 268)], MUTED, 3)


def d_map():
    cv = new("00 · OVERVIEW", "Nine controls around the agents, and one that tests them all")
    w = 432
    k = dict(h=160, tsize=28, lsize=22)  # two-line boxes: keep the rows clear of each other
    c1, c2, c3, c4 = 60, 516, 972, 1428  # four columns; the number in each title is the chapter
    cv.step("Before the agent runs: vet the tools, shrink permissions, compile the policy")
    col_header(cv, "BEFORE it runs", c1, w)
    box(cv, c1, 300, w, "04 · Vet the tools", ["Judge definitions, pin them with a hash"], "judge", **k)
    box(cv, c1, 480, w, "05 · Shrink permissions", ["Learn least privilege from audited traces"], "rule", **k)
    box(cv, c1, 660, w, "06 · Compile the policy", ["Turn written policy into tested criteria"], "model", **k)
    cv.step("While it runs: guard four gates, keep a human on approvals, and box the code")
    col_header(cv, "DURING the run", c2, w)
    box(cv, c2, 300, w, "02 · Guard four gates", ["input · tool call · tool result · output"], "judge", **k)
    box(cv, c2, 480, w, "03 · Triage approvals", ["AI explains and sorts, a human decides"], "human", **k)
    box(cv, c2, 660, w, "09 · Box the code", ["Parse it and allowlist it, judge it second"], "rule", **k)
    cv.step("Between agents: sign the messages, and contain a mistake that spreads")
    col_header(cv, "BETWEEN agents", c3, w)
    box(cv, c3, 300, w, "10 · Sign the messages", ["Verify, authorize, then judge the text"], "rule", **k)
    box(cv, c3, 480, w, "11 · Contain a cascade", ["Contract, budget, breaker, provenance"], "rule", **k)
    cv.step("After the run: audit the whole trace")
    col_header(cv, "AFTER it ran", c4, w)
    box(cv, c4, 300, w, "08 · Audit the traces", ["Goal, policy, faithfulness, first deviation"], "judge", **k)
    cv.text(c4 + w / 2, 560, "Gates stop things.", cv.font(SANS_B, 28), L_AMBER)
    cv.text(c4 + w / 2, 604, "Audits find what the gates", cv.font(SANS, 24), MUTED)
    cv.text(c4 + w / 2, 640, "did not check or could not see.", cv.font(SANS, 24), MUTED)
    cv.step("And always: attack the judge, because it is one layer, not a guarantee")
    box(cv, 60, 850, 1800, "07 · ALWAYS: red-team the judge",
        ["A model attacks the judge, benign look-alikes measure false positives, every miss becomes a regression test"],
        "model", h=130)
    legend(cv, ["model", "judge", "rule", "human"])
    return cv


# ================================================================================================
# 01  The idea
# ================================================================================================
def d_idea():
    cv = new("01 · INTRO", "A second model that answers yes or no")
    hh = 210
    cv.step("An agent reads text it cannot fully trust")
    t = box(cv, 60, 230, 360, "UNTRUSTED TEXT", ["user message", "tool results", "the model's own output"], "plain", h=hh)
    a = box(cv, 520, 230, 300, "AGENT", ["reads text,", "calls tools"], "model", h=hh)
    arrow(cv, [t.right(), a.left()])
    cv.step("It calls tools, and tools have real effects")
    c = box(cv, 920, 230, 360, "TOOL CALLS", ["read a ticket", "open a file", "send an email"], "plain", h=hh)
    e = box(cv, 1380, 230, 480, "REAL EFFECTS", ["data read, data sent,", "actions taken"], "block", h=hh)
    arrow(cv, [a.right(), c.left()])
    arrow(cv, [c.right(), e.left()])
    cv.step("A judge reads one piece of text and answers yes or no")
    j = box(cv, 420, 540, 520, "JUDGE", ["one piece of text", "one plain-English criterion", "one answer: yes or no"], "judge", h=200)
    arrow(cv, [(640, a.bottom()[1]), (640, j.y)], MUTED, label="is this OK?", off=(-95, 0), dashed=True)
    arrow(cv, [(780, j.y), (780, a.bottom()[1])], L_TEAL, label="yes / no", off=(80, 0))
    cv.step("You decide what a flag does: block, warn, log or ask a human")
    d = box(cv, 1100, 540, 760, "YOU DECIDE WHAT A FLAG DOES", [], "human", h=200, vcenter=False)
    x = 1140
    for txt, role in [("block", "block"), ("warn", "human"), ("log", "plain"), ("ask a human", "human")]:
        x += chip(cv, x, 650, txt, role) + 18
    arrow(cv, [j.right(), d.left()], L_TEAL, label="flag", off=(0, -24))
    cv.step("Two rules for every judge: read the polarity, and fail closed")
    box(cv, 60, 820, 870, "READ THE POLARITY", ["Risk criterion: yes is bad.", "Requirement criterion: no is bad."], "rule", tag=False, h=170)
    box(cv, 990, 820, 870, "FAIL CLOSED", ["A verdict we cannot parse counts as a flag."], "rule", tag=False, h=170)
    legend(cv, ["model", "judge", "rule", "human"])
    return cv


# ================================================================================================
# 02  Four gates
# ================================================================================================
def d_gates():
    cv = new("02 · AGENT-JUDGE · HOW IT WORKS", "Guard the agent at every boundary")
    ya, yb, ha, hb = 240, 620, 240, 210
    cv.step("A user message reaches the input gate, which checks for a jailbreak")
    u = box(cv, 60, ya, 230, "USER MESSAGE", [], "plain", h=ha)
    ig = box(cv, 390, ya, 300, "INPUT GATE", ["jailbreak?", "(pre-baked)"], "judge", h=ha)
    arrow(cv, [u.right(), ig.left()])
    chip(cv, ig.x + 40, ig.y + ig.h + 24, "flag: BLOCK", "block", 20)
    cv.step("The agent decides it wants to call a tool")
    ag = box(cv, 790, ya, 260, "AGENT", ["Granite 4.1 8B", "wants a tool call"], "model", h=ha)
    arrow(cv, [ig.right(), ag.left()])
    cv.step("The tool-call gate checks the call before it runs")
    cg = box(cv, 1150, ya, 330, "TOOL-CALL GATE", ["hallucinated call?", "(pre-baked)", "authorized action?", "(custom)"], "judge", h=ha)
    tl = box(cv, 1580, ya, 280, "TOOL", ["get_ticket", "read_file", "send_email"], "plain", h=ha)
    arrow(cv, [ag.right(), cg.left()])
    arrow(cv, [cg.right(), tl.left()])
    chip(cv, cg.x + 60, cg.y + cg.h + 24, "flag: BLOCK", "block", 20)
    cv.step("The tool result is checked before the agent reads it")
    rg = box(cv, 1500, yb, 360, "TOOL-RESULT GATE", ["instructions aimed", "at the AI?", "(custom)"], "judge", h=hb)
    arrow(cv, [(1720, tl.bottom()[1]), (1720, rg.y)], label="result", off=(50, 0))
    arrow(cv, [rg.left(), (990, rg.left()[1]), (990, ag.bottom()[1])], label="result goes back to the agent", off=(10, 28), seg=0)
    chip(cv, rg.x + 20, rg.y + rg.h + 24, "warns · --strict blocks", "human", 20)
    cv.step("When the agent answers, the output gate checks for secrets")
    og = box(cv, 400, yb, 330, "OUTPUT GATE", ["secrets in the answer?", "(custom)"], "judge", h=hb)
    ans = box(cv, 60, yb, 230, "ANSWER TO USER", [], "plain", h=hb)
    arrow(cv, [(860, ag.bottom()[1]), (860, og.left()[1]), og.right()], label="final answer", off=(-85, 0), seg=0)
    arrow(cv, [og.left(), ans.right()])
    cv.step("A flag at any gate blocks the request. The next gate stops what the last one warned about")
    cv.text(960, 985, "A flag at any gate blocks the request. The tool-result gate only warns, and the next gate stops the damage.",
            cv.font(SANS, 24), MUTED)
    legend(cv, ["model", "judge"])
    return cv


# ================================================================================================
# 03  Approval triage
# ================================================================================================
def d_triage():
    cv = new("03 · APPROVAL-TRIAGE · HOW IT WORKS", "Help the reviewer decide, without deciding for them")
    r1 = 230
    cv.step("Nine pending actions, each one a block of JSON")
    p = box(cv, 60, r1, 330, "9 PENDING ACTIONS", ["user request", "context", "proposed action"], "plain", h=240)
    cv.step("The judge answers four yes/no questions about each item")
    s_ = box(cv, 470, r1, 500, "SIGNALS", ["request-match · policy", "sensitive-data · injected-text", "4 yes/no checks per item"], "judge", h=240)
    arrow(cv, [p.right(), s_.left()])
    cv.step("A fixed rule turns the signals into a level. No model is involved")
    lv = box(cv, 1050, r1, 810, "LEVEL: a fixed rule, no model", [], "rule", h=240, vcenter=False)
    f = cv.font(MONO, 22)
    for i, (txt, role, cond) in enumerate([("DENY", "block", "injected-text + any other flag"),
                                            ("REVIEW", "human", "any flag"), ("ROUTINE", "ok", "no flags")]):
        yy = r1 + 88 + i * 48
        chip(cv, 1085, yy, txt, role, 20, w=150)
        cv.text(1260, yy + 19, cond, f, TEXT, "lm")
    arrow(cv, [s_.right(), lv.left()])
    r2, h2 = 600, 200
    cv.step("A model writes the card. It explains, and it cannot change the level")
    card = box(cv, 60, r2, 450, "CARD (Granite 8B)", ["writes the explanation only", "cannot change the level"], "model", h=h2)
    arrow(cv, [(720, s_.bottom()[1]), (720, 540), (285, 540), (285, card.y)], label="signals and level", off=(0, -22), seg=1)
    cv.step("The exact action is always shown verbatim, so the reviewer can check the facts")
    act = box(cv, 60, r2 + h2 + 40, 450, "ACTION, VERBATIM", ["the reviewer checks the facts"], "plain", h=130)
    cv.step("The judge verifies the card against the action, so a lying card fails")
    v = box(cv, 620, r2, 440, "VERIFY", ["does the card match", "the action?", "fail: the card says ignore it"], "judge", h=h2)
    arrow(cv, [card.right(), v.left()], label="card", off=(0, -24))
    arrow(cv, [act.right(), (840, act.y + act.h / 2), (840, v.bottom()[1])], MUTED, label="action", off=(-30, -22), seg=0)
    cv.step("Risky items go to the top of the triaged queue, routine ones are grouped")
    q = box(cv, 1160, r2, 320, "TRIAGED QUEUE", ["DENY first, then REVIEW,", "ROUTINE grouped"], "plain", h=h2)
    arrow(cv, [v.right(), q.left()])
    arrow(cv, [(1320, lv.bottom()[1]), (1320, q.y)], label="level", off=(46, 0))
    cv.step("A human decides, and every override is logged. Nothing is auto-approved")
    hm = box(cv, 1560, r2, 300, "HUMAN DECIDES", ["approve · deny · skip", "overrides logged"], "human", h=h2)
    arrow(cv, [q.right(), hm.left()])
    cv.text(1710, hm.y + hm.h + 34, "decisions.jsonl", cv.font(MONO, 22), MUTED)
    legend(cv, ["model", "judge", "rule", "human"])
    return cv


# ================================================================================================
# 04  Tool vetting
# ================================================================================================
def d_vetting():
    cv = new("04 · TOOL-VETTING · HOW IT WORKS", "Vet tools before the agent sees them")
    r1, h1 = 240, 210
    cv.step("A tool server publishes definitions. The description is text the agent will read")
    sv = box(cv, 60, r1, 300, "TOOL SERVER", ["publishes tools"], "plain", h=h1)
    df = box(cv, 440, r1, 360, "TOOL DEFINITION", ["name · description", "parameters"], "plain", h=h1)
    arrow(cv, [sv.right(), df.left()])
    cv.step("The judge vets each definition with three checks")
    vt = box(cv, 880, r1, 480, "VET", ["hidden instructions", "scope · shadowing", "any flag quarantines the tool"], "judge", h=h1)
    arrow(cv, [df.right(), vt.left()])
    cv.step("Any flag quarantines the tool. A clean one is approved")
    qr = box(cv, 1500, r1 - 10, 360, "QUARANTINE", [], "block", h=90)
    ap = box(cv, 1500, r1 + 130, 360, "APPROVE", [], "ok", h=90)
    arrow(cv, [(vt.x + vt.w, r1 + 50), (1500, r1 + 35)], label="flag", off=(0, -22))
    arrow(cv, [(vt.x + vt.w, r1 + 160), (1500, r1 + 175)], label="clean", off=(0, 24))
    r2 = 640
    cv.step("Approved definitions are pinned with a hash, like a lockfile")
    pn = box(cv, 880, r2, 480, "PIN", ["sha256 of each approved definition", "like a lockfile for dependencies"], "rule", h=170)
    arrow(cv, [ap.bottom(), (1680, 540), (1120, 540), (1120, pn.y)], label="approved", off=(0, -22), seg=1)
    cv.step("The agent sees only the approved tools")
    agt = box(cv, 1500, r2, 360, "AGENT", ["sees only approved tools"], "model", h=170)
    arrow(cv, [pn.right(), agt.left()])
    cv.step("Later, a server changes an approved tool: a rug pull")
    dr = box(cv, 60, r2, 640, "LATER: A SERVER CHANGES THE TOOL", ["hash mismatch: the pinned version stays in use", "the new definition is vetted again"], "block", h=170, tag=False)
    arrow(cv, [pn.left(), dr.right()], label="hash check", off=(0, -24))
    cv.step("The hash mismatch sends it back to be vetted. A hash shows change, not harm")
    arrow(cv, [(380, dr.y), (380, 500), (1000, 500), (1000, vt.y + vt.h)], label="re-vet", off=(0, -22), seg=1)
    cv.text(960, 930, "The judge reads what a definition says. It cannot see what the server code does.", cv.font(SANS, 24), MUTED)
    legend(cv, ["judge", "rule", "model"])
    return cv


# ================================================================================================
# 05  Least privilege
# ================================================================================================
def d_privilege():
    cv = new("05 · LEAST-PRIVILEGE · HOW IT WORKS", "Learn least privilege from audited traces")
    r1, h1 = 220, 175
    cv.step("Start with logged agent runs, and audit each one with the judge")
    tr = box(cv, 60, r1, 260, "14 LOGGED TRACES", [], "plain", h=h1)
    au = box(cv, 400, r1, 420, "AUDIT", ["goal aligned?", "injected text?"], "judge", h=h1)
    arrow(cv, [tr.right(), au.left()])
    cv.step("Only clean runs survive. Learning from a hijacked run would whitelist the attack")
    cl = box(cv, 900, r1, 380, "CLEAN TRACES ONLY", ["hijacked runs excluded"], "ok", h=h1)
    arrow(cv, [au.right(), cl.left()])
    cv.step("Mine what the agent actually used: tools, file paths, email domains")
    mn = box(cv, 1360, r1, 500, "MINE USAGE", ["tools · file paths · email domains", "plain counts, no model"], "rule", h=h1)
    arrow(cv, [cl.right(), mn.left()])
    r2, h2 = 440, 140
    cv.step("Two candidate policies: plain rules, and a model that may generalize a little")
    bl = box(cv, 980, r2, 420, "BASELINE", ["smallest policy that covers", "observed use"], "rule", h=h2)
    pr = box(cv, 1480, r2, 380, "PROPOSE", ["may generalize a little:", "path to directory"], "model", h=h2)
    arrow(cv, [(1500, mn.bottom()[1]), (1500, 410), (1190, 410), (1190, bl.y)])
    arrow(cv, [(1670, mn.bottom()[1]), (1670, pr.y)])
    r3, h3 = 650, 200
    cv.step("Deterministic checks verify the proposal. The model proposes, rules decide")
    vf = box(cv, 1360, r3, 500, "VERIFY", ["valid JSON, known tools", "covers every clean action", "denies canaries the baseline denies"], "rule", h=h3)
    arrow(cv, [pr.bottom(0.5), (1670, vf.y)])
    cv.step("A verified proposal is used. If it fails, fall back to the baseline")
    pu = box(cv, 880, r3, 400, "POLICY USED", ["verified proposal,", "or the baseline"], "ok", h=h3)
    arrow(cv, [bl.bottom(), (bl.x + 210, pu.y)], label="fails: fallback", off=(-100, 0))
    arrow(cv, [(vf.x, r3 + h3 / 2), (pu.x + pu.w, r3 + h3 / 2)], label="passes", off=(0, -38))
    cv.step("Replay the policy on every trace using our labels, not the judge's")
    rp = box(cv, 60, r3, 640, "REPLAY ON ALL TRACES", ["using OUR labels, not the judge's", "legit · malicious · canaries"], "rule", h=h3)
    arrow(cv, [pu.left(), rp.right()])
    cv.step("A human reviews the proposal. Nothing is approved automatically")
    rv = box(cv, 60, 910, 1800, "REPORT, THEN HUMAN REVIEW  ·  approved: false until a human says otherwise", [], "human", h=80, tsize=26, tag=False)
    arrow(cv, [(380, rp.bottom()[1]), (380, rv.y)])
    legend(cv, ["judge", "rule", "model", "human"])
    return cv


# ================================================================================================
# 06  Policy compiler
# ================================================================================================
def d_compiler():
    cv = new("06 · POLICY-COMPILER · HOW IT WORKS", "From written policy to reviewable criteria")
    r1, h = 230, 180
    r2 = 530
    cv.step("A model reads the policy and splits it into rules, picking a checkpoint for each")
    pt = box(cv, 60, r1, 320, "POLICY TEXT", ["seven numbered rules", "plain English"], "plain", h=h)
    ex = box(cv, 460, r1, 400, "EXTRACT", ["split into enforceable rules", "pick a checkpoint for each"], "model", h=h)
    arrow(cv, [pt.right(), ex.left()])
    cv.step("It drafts one criterion per rule, true when the text complies")
    dr = box(cv, 940, r1, 440, "DRAFT", ["one criterion per rule", "TRUE when the text complies"], "model", h=h)
    arrow(cv, [ex.right(), dr.left()])
    cv.step("It writes compliant and violating examples for each rule")
    ts = box(cv, 1460, r1, 400, "TEST", ["compliant and violating", "examples for each rule"], "model", h=h)
    arrow(cv, [dr.right(), ts.left()])
    cv.step("The judge applies each criterion to its tests, in both directions")
    vl = box(cv, 1460, r2, 400, "VALIDATE", ["violations caught?", "compliant text left alone?"], "judge", h=h)
    arrow(cv, [ts.bottom(), vl.top()])
    cv.step("Weak criteria are rewritten and compared with the old one on fresh tests")
    rp = box(cv, 940, r2, 440, "REPAIR (--repair)", ["rewrite weak criteria", "compare on FRESH tests"], "model", h=h)
    arrow(cv, [vl.left(), rp.right()])
    cv.step("Everything is exported as a draft, marked approved: false")
    xp = box(cv, 460, r2, 400, "EXPORT", ["criteria.json, approved: false", "review_sheet.md"], "rule", h=h)
    arrow(cv, [rp.left(), xp.right()])
    cv.step("A human reads the review sheet and approves what they accept")
    hm = box(cv, 60, r2, 320, "HUMAN", ["reads the sheet", "sets approved: true"], "human", h=h)
    arrow(cv, [xp.left(), hm.right()])
    cv.step("Only approved criteria are ever applied. The model drafts, the judge checks, the human decides")
    ap = box(cv, 60, 830, 1050, "APPLY", ["--apply judges text against ONLY the criteria a human approved"], "judge", h=130)
    arrow(cv, [hm.bottom(), (hm.x + hm.w / 2, ap.y)], label="approved only", off=(110, 0))
    cv.text(1500, 880, "The model drafts. The judge checks.", cv.font(SANS_B, 28), L_AMBER)
    cv.text(1500, 926, "The human decides.", cv.font(SANS_B, 28), L_AMBER)
    legend(cv, ["model", "judge", "rule", "human"])
    return cv


# ================================================================================================
# 07  Red team
# ================================================================================================
def d_redteam():
    cv = new("07 · RED-TEAM · HOW IT WORKS", "A model attacks the judge")
    r1, h1 = 280, 190
    cv.step("A model writes attacks in eight categories, and the judge checks them")
    at = box(cv, 60, r1, 400, "ATTACKER", ["Granite 8B writes attacks", "in eight categories"], "model", h=h1)
    jd = box(cv, 700, r1, 420, "JUDGE AT A GATE", ["input gate", "tool-result gate"], "judge", h=h1)
    arrow(cv, [at.right(), jd.left()], label="attack text", off=(0, -26))
    cv.step("Each attack is caught or missed")
    cg = box(cv, 1300, r1 - 10, 560, "CAUGHT", [], "ok", h=90)
    ms = box(cv, 1300, r1 + 110, 560, "MISSED", [], "block", h=90)
    arrow(cv, [jd.right(0.3), (1210, r1 + 47), (1210, r1 + 35), cg.left()])
    arrow(cv, [jd.right(0.75), (1210, r1 + 142), (1210, r1 + 155), ms.left()])
    cv.step("Round two: the attacker sees what was caught, and rewrites. It never sees the judge's reasoning")
    arrow(cv, [cg.top(0.5), (1580, 248), (260, 248), (260, at.y)], label="round 2: these were caught, rewrite them (no judge reasoning shared)", off=(0, -22), seg=1)
    cv.step("Misses are saved. Each one becomes a regression test")
    sv = box(cv, 1300, 580, 560, "MISSES SAVED", ["the regression set"], "plain", h=170)
    arrow(cv, [ms.bottom(), (1580, sv.y)])
    cv.step("A human tightens the criterion, from what they saw")
    tg = box(cv, 700, 580, 460, "TIGHTEN THE CRITERION", ["v1 to v2, from what you saw"], "human", h=170)
    arrow(cv, [sv.left(), tg.right()])
    cv.step("Replay the misses under the new criterion: what was recovered, what regressed?")
    rpl = box(cv, 60, 580, 480, "REPLAY", ["recovered? regressed?", "new false positives?"], "judge", h=170)
    arrow(cv, [tg.left(), rpl.right()])
    cv.step("Benign look-alikes measure false positives. A guardrail that flags everything is an outage")
    bn = box(cv, 60, 800, 560, "BENIGN LOOK-ALIKES", ["harmless text from the same attacker", "tickets that mention passwords"], "model", h=200)
    fp = box(cv, 800, 800, 600, "FALSE POSITIVES", ["harmless text wrongly flagged", "a guardrail that flags", "everything is an outage"], "block", h=200)
    arrow(cv, [bn.right(), fp.left()], label="same gates", off=(0, -26))
    cv.step("Measure both directions. Replaying old misses proves little: attack the new criteria afresh")
    cv.text(1650, 875, "Measure both directions.", cv.font(SANS_B, 28), L_AMBER)
    cv.text(1650, 925, "Replaying old misses proves little:", cv.font(SANS, 22), MUTED)
    cv.text(1650, 957, "attack the new criteria afresh.", cv.font(SANS, 22), MUTED)
    legend(cv, ["model", "judge", "human"])
    return cv


# ================================================================================================
# 08  Trace audit
# ================================================================================================
def d_audit():
    cv = new("08 · TRACE-AUDIT · HOW IT WORKS", "Review the whole run, after the fact")
    cv.step("A recorded run is rendered as a transcript the judge can read")
    tr = box(cv, 60, 230, 340, "RECORDED TRACE", ["goal · steps", "results · final message"], "plain", h=300)
    rd = box(cv, 480, 230, 320, "RENDER", ["as a transcript", "the judge can read"], "rule", h=300)
    arrow(cv, [tr.right(), rd.left()])
    cv.step("The judge answers four questions about the whole run")
    jd = box(cv, 880, 230, 980, "THE JUDGE ANSWERS FOUR QUESTIONS", [], "judge", h=300, align="left", vcenter=False)
    rows = [("goal", "every action needed for the user's goal?", "fail if no", "block"),
            ("policy", "actions comply with the written policy?", "fail if no", "block"),
            ("faithful", "final message matches the tool results?", "fail if no", "block"),
            ("injection", "a tool result addressed the AI?", "context only", "human")]
    f1, f2 = cv.font(MONO_B, 24), cv.font(SANS, 24)
    for i, (k, q, flag, role) in enumerate(rows):
        yy = 330 + i * 52
        cv.text(915, yy, k, f1, L_TEAL, "lm")
        cv.text(1070, yy, q, f2, TEXT, "lm")
        chip(cv, 1660, yy - 20, flag, role, 18, w=180)
    arrow(cv, [rd.right(), jd.left()])
    r2, h2 = 630, 180
    cv.step("A run fails if goal, policy or faithfulness is violated. Injection is only context")
    dc = box(cv, 880, r2, 420, "GOAL OR POLICY FAILED?", ["no: the problem is in", "the final message"], "rule", h=h2)
    arrow(cv, [(1090, jd.bottom()[1]), (1090, dc.y)])
    cv.step("If the actions were wrong, replay the run one step at a time")
    rp = box(cv, 1440, r2, 420, "REPLAY STEP BY STEP", ["is the last action needed", "and compliant?"], "judge", h=h2)
    arrow(cv, [dc.right(), rp.left()], label="yes", off=(0, -24))
    cv.step("The first step the judge rejects is the first deviating step. It is a heuristic")
    fd = box(cv, 1440, 870, 420, "FIRST DEVIATING STEP", [], "ok", h=90)
    arrow(cv, [rp.bottom(), fd.top()])
    cv.step("Everything goes into a report for a human. A pass is not proof the run was safe")
    rpt = box(cv, 60, r2, 640, "REPORT FOR A HUMAN", ["audit_report.md · audit_results.jsonl", "a pass is not proof the run was safe"], "human", h=h2)
    arrow(cv, [dc.left(), rpt.right()], label="no", off=(0, -24))
    arrow(cv, [fd.left(), (380, fd.left()[1]), (380, rpt.bottom()[1])], dashed=True)
    legend(cv, ["judge", "rule", "human"])
    return cv


# ================================================================================================
# 09  Code execution (ASI05)
# ================================================================================================
def d_code():
    cv = new("09 · CODE-EXECUTION · HOW IT WORKS", "Keep agent-written code in a box")
    gk = dict(h=160, tsize=28, lsize=22)  # four boxes plus the gaps must clear the legend
    cv.step("Unexpected code reaches the agent three ways: the user, the data, or the model itself")
    s1 = box(cv, 60, 230, 380, "THE USER ASKS", ["asks for code that reaches", "files or the network"], "plain", h=150)
    s2 = box(cv, 60, 420, 380, "THE DATA CARRIES IT", ["a poisoned ticket says", "run this snippet"], "plain", h=150)
    s3 = box(cv, 60, 610, 380, "THE MODEL REACHES", ["a legitimate request, and the", "model writes more than needed"], "plain", h=150)
    cv.step("The agent decides to run Python, and one tool call can do what every other tool does")
    ag = box(cv, 540, 330, 300, "AGENT", ["Granite 4.1 8B", "calls run_python"], "model", h=250)
    arrow(cv, [s1.right(), (490, s1.right()[1]), (490, 400), (540, 400)])
    arrow(cv, [s2.right(), (540, s2.right()[1])])
    arrow(cv, [s3.right(), (490, s3.right()[1]), (490, 560), (540, 560)])
    cv.step("Gate 1 parses the code and allows only listed imports, builtins and attributes")
    g1 = box(cv, 960, 225, 480, "1. ALLOWLIST", ["parse the code, do not search it", "imports · builtins · attributes"], "rule", **gk)
    arrow(cv, [ag.right(), (900, ag.right()[1]), (900, g1.left()[1]), g1.left()])
    box(cv, 1540, g1.y + 15, 320, "BLOCK", ["not on the list"], "block", h=130)
    arrow(cv, [g1.right(), (1540, g1.right()[1])])
    cv.step("Gate 2 applies budget rules to code that is made only of allowed parts")
    g2 = box(cv, 960, 405, 480, "2. BUDGET RULES", ["never ends, or a huge loop", "or list: exact rules"], "rule", **gk)
    arrow(cv, [g1.bottom(), g2.top()])
    box(cv, 1540, g2.y + 15, 320, "BLOCK", ["abuse the list missed"], "block", h=130)
    arrow(cv, [g2.right(), (1540, g2.right()[1])])
    cv.step("Gate 3 is the judge. It can ask a human to review, and it can never allow what a rule blocked")
    g3 = box(cv, 960, 585, 480, "3. JUDGE", ["a second opinion on the code", "a guess, so only stricter"], "judge", **gk)
    arrow(cv, [g2.bottom(), g3.top()])
    box(cv, 1540, g3.y + 15, 320, "REVIEW", ["a human decides"], "human", h=130)
    arrow(cv, [g3.right(), (1540, g3.right()[1])])
    cv.step("Allowed code reaches an interpreter. A real one also needs a sandbox")
    mi = box(cv, 960, 790, 480, "INTERPRETER", ["returns an exit status", "and no output"], "plain", **gk)
    arrow(cv, [g3.bottom(), mi.top()], label="allow", off=(46, 0))
    sb = box(cv, 1540, 790, 320, "SANDBOX", ["not built: no network,", "no secrets, time limits"], "plain", tag=False, **gk)
    arrow(cv, [mi.right(), sb.left()], dashed=True)
    cv.step("Parse the code, do not search it. The judge can only make a decision stricter")
    cv.text(60, 880, "Parse the code. Do not search it.", cv.font(SANS_B, 28), L_AMBER, "lm")
    cv.text(60, 930, "The judge can only make a decision stricter.", cv.font(SANS, 24), MUTED, "lm")
    legend(cv, ["model", "judge", "rule", "human"])
    return cv


# ================================================================================================
# 10  Agent messaging (ASI07)
# ================================================================================================
def d_messaging():
    cv = new("10 · AGENT-MESSAGING · HOW IT WORKS", "A message that says who it is from proves nothing")
    r1, r2, h = 230, 620, 210
    cv.step("Agents send each other signed envelopes. The receiver trusts none of the text")
    sd = box(cv, 60, r1, 320, "SENDING AGENTS", ["triage · orchestrator", "or someone pretending"], "plain", h=h)
    cv.step("Verify first: signature, recipient, clock and message id, before any agent reads it")
    vf = box(cv, 470, r1, 380, "1. VERIFY", ["signature · recipient", "clock · message id"], "rule", h=h)
    arrow(cv, [sd.right(), vf.left()])
    chip(cv, vf.x + 20, r1 + h + 24, "forged or replayed: BLOCK", "block", 20)
    cv.step("Then authorize: is this sender allowed to ask for this, with these arguments?")
    az = box(cv, 940, r1, 380, "2. AUTHORIZE", ["may THIS sender ask", "for THIS? deny by default"], "rule", h=h)
    arrow(cv, [vf.right(), az.left()])
    chip(cv, az.x + 20, r1 + h + 24, "outside its role: BLOCK", "block", 20)
    cv.step("A compromised peer signs with its real key, so the judge reads the free-text reason for orders")
    jd = box(cv, 1410, r1, 450, "3. JUDGE", ["reads only the free-text reason:", "does it give orders to the agent?"], "judge", h=h)
    arrow(cv, [az.right(), jd.left()])
    chip(cv, jd.x + 20, r1 + h + 24, "gives orders: REVIEW", "human", 20)
    cv.step("Only messages that got through reach the ops agent")
    ops = box(cv, 1410, r2, 450, "OPS AGENT", ["Granite 4.1 8B", "reads only what got through"], "model", h=h)
    arrow(cv, [jd.bottom(0.8), ops.top(0.8)], label="allow", off=(46, 0))
    cv.step("Every tool call is checked again, with the SENDER's authority and not the agent's own")
    tg = box(cv, 940, r2, 380, "TOOL GATE", ["every call checked with", "the SENDER's authority"], "rule", h=h)
    tl = box(cv, 470, r2, 380, "TOOLS", ["rotate_key", "grant_access · post_note"], "plain", h=h)
    arrow(cv, [ops.left(), tg.right()])
    arrow(cv, [tg.left(), tl.right()])
    chip(cv, tg.x + 20, r2 + h + 24, "beyond the sender: BLOCK", "block", 20)
    cv.step("A signature says who sent it. It does not say the sender is trustworthy")
    cv.text(960, 945, "A signature says who sent it. It does not say the sender is trustworthy.", cv.font(SANS_B, 28), L_AMBER)
    cv.text(960, 990, "A compromised agent signs its poisoned messages with its own real key.", cv.font(SANS, 22), MUTED)
    legend(cv, ["model", "judge", "rule", "human"])
    return cv


# ================================================================================================
# 11  Cascading failures (ASI08)
# ================================================================================================
def d_cascade():
    cv = new("11 · CASCADING-FAILURES · HOW IT WORKS", "One mistake becomes many")
    r1, h1 = 230, 200
    r2, h2 = 560, 200
    r3, h3 = 820, 150
    cv.step("A ticket enters the pipeline")
    tk = box(cv, 60, r1, 300, "TICKET", ["restart stg-api", "or hidden text"], "plain", h=h1)
    cv.step("Intake, an agent, turns the ticket into a work order")
    ik = box(cv, 440, r1, 340, "INTAKE", ["Granite 4.1 8B", "files one work order"], "model", h=h1)
    arrow(cv, [tk.right(), ik.left()])
    cv.step("The planner expands one field into many services: stg-* becomes eight")
    pl = box(cv, 860, r1, 440, "PLANNER", ["expands the target", "one name or a wildcard"], "rule", h=h1)
    arrow(cv, [ik.right(), pl.left()])
    cv.step("The executor restarts every one of them")
    ex = box(cv, 1380, r1, 480, "EXECUTOR", ["restarts the services", "a fleet of twelve"], "plain", h=h1)
    arrow(cv, [pl.right(), ex.left()])
    cv.step("Monitoring files new tickets about what broke, so the pipeline feeds itself")
    mo = box(cv, 1380, r3, 480, "MONITORING", ["a restart fails its dependents", "and files a ticket for each"], "plain", h=h3)
    arrow(cv, [ex.bottom(), mo.top()], label="dependents fail", off=(90, 0))
    cv.step("At the boundary, an exact contract and the scope and budget rules")
    cv.text(60, 508, "AT THE BOUNDARY: the strictest decision wins", cv.font(SANS_B, 26), L_AMBER, "lm")
    cx = box(cv, 60, r2, 350, "CONTRACT", ["one known action,", "one known service", "else BLOCK"], "rule", h=h2, lsize=22)
    sc = box(cv, 440, r2, 350, "SCOPE · BUDGET", ["prod and critical need", "a human, max 3 restarts", "REVIEW"], "rule", h=h2, lsize=22)
    cv.step("The judge reads the ticket and the order together: does the order match?")
    jd = box(cv, 820, r2, 350, "JUDGE", ["does the order match", "the ticket?", "can only add a REVIEW"], "judge", h=h2, lsize=22)
    cv.step("Provenance and a circuit breaker break the feedback loop, two ways")
    pv = box(cv, 1200, r2, 350, "PROVENANCE", ["a ticket we caused is", "not acted on", "REVIEW"], "rule", h=h2, lsize=22)
    br = box(cv, 800, r3, 480, "CIRCUIT BREAKER", ["a restart that raises 2 alerts", "stops the line"], "rule", h=h3)
    arrow(cv, [mo.left(), br.right()])
    arrow(cv, [br.left(), (30, br.left()[1]), (30, tk.left()[1]), tk.left()], label="new tickets: the loop feeds itself", seg=0, off=(0, -26))
    cv.step("Limit the blast radius first. A budget and a breaker work when you did not predict the failure")
    legend(cv, ["model", "judge", "rule"])
    return cv


DIAGRAMS = [
    ("00_map_before_during_after", d_map),
    ("01_judge_idea", d_idea),
    ("02_four_gates", d_gates),
    ("03_approval_triage", d_triage),
    ("04_tool_vetting", d_vetting),
    ("05_least_privilege", d_privilege),
    ("06_policy_compiler", d_compiler),
    ("07_red_team", d_redteam),
    ("08_trace_audit", d_audit),
    ("09_code_execution", d_code),
    ("10_agent_messaging", d_messaging),
    ("11_cascading_failures", d_cascade),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="only diagrams whose file name contains this text")
    ap.add_argument("--no-gif", action="store_true", help="write the PNGs only")
    ap.add_argument("--gif-width", type=int, default=1280, help="GIF width in pixels (default 1280)")
    ap.add_argument("--hold", type=int, default=1600, help="milliseconds each step stays on screen (default 1600)")
    ap.add_argument("--no-title", action="store_true", help="crop the title off (files get a _notitle suffix)")
    ap.add_argument("--bg", type=parse_color, default=None, metavar="HEX",
                    help="background colour to match your slides, e.g. 14171C or #F4F1EA. Light colours switch to dark text. "
                         "Overrides the theme's background")
    ap.add_argument("--theme", type=load_theme, default=None, metavar="JSON",
                    help="theme file (JSON) with background, text colours and role colours. See the top of this file")
    ap.add_argument("--out", default=None, help="output folder (default: ../images)")
    args = ap.parse_args()
    theme = args.theme or {}
    apply_theme(theme, args.bg or theme.get("background") or BG)
    global OUT
    OUT = os.path.abspath(args.out) if args.out else OUT
    os.makedirs(OUT, exist_ok=True)
    for name, fn in DIAGRAMS:
        if args.only and args.only not in name:
            continue
        stem = name + ("_notitle" if args.no_title else "")
        cv = fn()
        cv.save_png(stem + ".png", crop_title=args.no_title)
        if not args.no_gif:
            cv.save_gif(stem + ".gif", width=args.gif_width, hold=args.hold, crop_title=args.no_title)


if __name__ == "__main__":
    main()
