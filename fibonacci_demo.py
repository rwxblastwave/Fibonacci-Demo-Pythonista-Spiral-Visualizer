# Pythonista 3 — Fibonacci Poster (flipped arc orientation: +90° CCW)
# Exact 34×21 tiling, distinct colors, notch-safe layout
# Origin: (24, 6) with 270° (down) initial tangent

import ui, math
from objc_util import ObjCClass, on_main_thread

# ===== Appearance =====
MARGIN = 18
GRID_ALPHA = 0.20
BORDER_COLOR = (0.14, 0.18, 0.45)
SPIRAL_COLOR = (1.00, 0.45, 0.10)
LABEL_COLOR  = (1.00, 0.45, 0.10)
TITLE_COLOR  = (0.05, 0.20, 0.45)
FONT_TITLE   = ('<System-Bold>', 28)
FONT_LABEL   = ('<System>', 20)
FONT_SERIES  = ('<System-Bold>', 20)
SPIRAL_WIDTH_PT = 4.0

SHOW_GRID = False
SHOW_START_ARROW = False
SHOW_TINY_1x1_LABELS = True

TINTS = {
    1:  (0.98, 0.90, 0.60, 0.75),
    2:  (0.95, 0.70, 0.50, 0.75),
    3:  (0.70, 0.85, 0.98, 0.75),
    5:  (0.80, 0.95, 0.80, 0.75),
    8:  (0.95, 0.85, 0.95, 0.75),
    13: (0.90, 0.95, 0.99, 0.75),
    21: (0.99, 0.98, 0.80, 0.70),
}

# ===== Exact tiling on a 34×21 grid (y-up) =====
# (name, size, x_ll, y_ll)
SQUARES = [
    ('21', 21,  0,  0),
    ('13', 13, 21,  8),
    ('8',   8, 26,  0),
    ('5',   5, 21,  0),
    ('3',   3, 21,  5),
    ('2',   2, 24,  6),
    ('1a',  1, 24,  5),
    ('1b',  1, 25,  5),
]
W, H = 34, 21

# ===== Safe-area =====
@on_main_thread
def _ios_safe_insets():
    try:
        UIApplication = ObjCClass('UIApplication')
        app = UIApplication.sharedApplication()
        win = app.keyWindow() or app.windows().lastObject()
        if win:
            ins = win.safeAreaInsets()
            return float(ins.top), float(ins.left), float(ins.bottom), float(ins.right)
    except Exception:
        pass
    return 0.0, 0.0, 0.0, 0.0

def _fallback_insets(w, h):
    return (44.0,0.0,34.0,0.0) if h>w else (20.0,0.0,0.0,0.0)

# ===== Grid→screen mapper (math y-up → UIKit y-down) =====
class Map:
    def __init__(self, frame, safe_top=0.0, safe_bottom=0.0):
        vw, vh = frame[2], frame[3]
        top_pad    = 18 + safe_top + 12
        bottom_pad = 18 + safe_bottom + 6
        sx = (vw - 2*MARGIN) / float(W)
        sy = (vh - (MARGIN + bottom_pad) - (MARGIN + top_pad)) / float(H)
        self.k  = min(sx, sy)
        self.ox = MARGIN + (vw - 2*MARGIN - W*self.k) * 0.5
        self.oy = MARGIN + top_pad + (vh - (2*MARGIN + top_pad + bottom_pad) - H*self.k) * 0.5
    def rect_ll(self, x, y, s):
        return (self.ox + x*self.k, self.oy + (H-(y+s))*self.k, s*self.k, s*self.k)
    def pt(self, gx, gy):
        return self.ox + gx*self.k, self.oy + (H-gy)*self.k
    def x_to_px(self, gx): return self.ox + gx*self.k
    def y_to_py(self, gy): return self.oy + (H-gy)*self.k

# ===== Golden spiral geometry (flipped to +90° CCW) =====
# Centers at appropriate corners for CCW orientation:
C1   = (25,  6)   # 1×1 (TR for 1a, TL for 1b)
C2   = (24,  6)   # 2×2 (BL)
C3   = (24,  5)   # 3×3 (BR)
C5   = (26,  5)   # 5×5 (TR)
C8   = (26,  8)   # 8×8 (TL)
C13  = (21,  8)   # 13×13 (BL)
C21  = (21,  0)   # 21×21 (BR)

# Same waypoint chain; each arc now sweeps +90° (counter-clockwise)
SPIRAL_ARCS = [
    (C1,  (24, 6), +90),  # 1×1: left   → bottom   (start tangent = 270°)
    (C1,  (25, 5), +90),  # 1×1: bottom → right
    (C2,  (26, 6), +90),  # 2×2: right  → top
    (C3,  (24, 8), +90),  # 3×3: top    → left
    (C5,  (21, 5), +90),  # 5×5: left   → bottom
    (C8,  (26, 0), +90),  # 8×8: bottom → right
    (C13, (34, 8), +90),  # 13×13: right→ top
    (C21, (21,21), +90),  # 21×21: top  → left (ends at (0,0))
]

def arc_poly(mapper, center, start, sweep_deg, px_per_seg=6.0):
    cx, cy = center; sx, sy = start
    r  = math.hypot(sx-cx, sy-cy)
    a0 = math.atan2(sy-cy, sx-cx)             # math-space angle
    a1 = a0 + math.radians(sweep_deg)         # +90° = CCW quarter
    segs = max(64, int((r * mapper.k) / px_per_seg))
    pts = []
    for i in range(segs + 1):
        t  = a0 + (a1 - a0) * (i / segs)
        gx = cx + r * math.cos(t)
        gy = cy + r * math.sin(t)
        pts.append(mapper.pt(gx, gy))
    return pts

def build_spiral(mapper):
    path = ui.Path()
    start_dir = None
    first = True
    for center, start, sweep in SPIRAL_ARCS:
        seg = arc_poly(mapper, center, start, sweep)
        if first:
            start_dir = seg[:2]     # for arrowhead direction
        for i, (x, y) in enumerate(seg):
            if first and i == 0:
                path.move_to(x, y)
            else:
                if i == 0:  # avoid double vertex
                    continue
                path.line_to(x, y)
        first = False
    return path, start_dir

def draw_arrowhead(p0, p1, size=10.0):
    x0, y0 = p0; x1, y1 = p1
    vx, vy = x1-x0, y1-y0
    L = math.hypot(vx, vy) or 1.0
    ux, uy = vx/L, vy/L
    px, py = -uy, ux
    tip = (x0, y0)
    base = (x0 - ux*size, y0 - uy*size)
    left  = (base[0] + px*size*0.5, base[1] + py*size*0.5)
    right = (base[0] - px*size*0.5, base[1] - py*size*0.5)
    tri = ui.Path()
    tri.move_to(*tip); tri.line_to(*left); tri.line_to(*right); tri.close()
    ui.set_color(SPIRAL_COLOR); tri.fill()

# ===== View =====
class FibPoster(ui.View):
    def __init__(self):
        super().__init__(bg_color=(0.98, 0.98, 1.0))
        self.flex = 'WH'
        t,_,b,_ = _ios_safe_insets()
        if (t,b) == (0.0,0.0):
            ft,_,fb,_ = _fallback_insets(self.width,self.height)
            t, b = max(t,ft), max(b,fb)
        self._safe_top, self._safe_bottom = t, b

    def layout(self):
        t,_,b,_ = _ios_safe_insets()
        if (t,b) == (0.0,0.0):
            ft,_,fb,_ = _fallback_insets(self.width,self.height)
            t, b = max(t,ft), max(b,fb)
        self._safe_top, self._safe_bottom = t, b
        self.set_needs_display()

    def draw(self):
        t, b = self._safe_top, self._safe_bottom
        m = Map(self.bounds, safe_top=t, safe_bottom=b)

        # Card
        ui.set_color((1.0, 1.0, 1.0))
        ui.Path.rect(m.ox, m.oy, W*m.k, H*m.k).fill()

        # Grid
        if SHOW_GRID:
            ui.set_color((0.2, 0.4, 0.7, GRID_ALPHA))
            for gx in range(W+1):
                x = m.x_to_px(gx)
                p = ui.Path(); p.move_to(x, m.oy); p.line_to(x, m.oy + H*m.k); p.stroke()
            for gy in range(H+1):
                y = m.y_to_py(gy)
                p = ui.Path(); p.move_to(m.ox, y); p.line_to(m.ox + W*m.k, y); p.stroke()

        # Squares + labels
        for name, s, x, y in SQUARES:
            rx, ry, rw, rh = m.rect_ll(x, y, s)
            ui.set_color(TINTS.get(1 if name in ('1a','1b') else s, (0.85,0.85,0.85,0.65)))
            ui.Path.rect(rx, ry, rw, rh).fill()
            ui.set_color((0,0,0,0.08)); ui.Path.rect(rx, ry, rw, rh).stroke()
            if SHOW_TINY_1x1_LABELS or s != 1:
                ui.set_color(LABEL_COLOR)
                txt = str(1 if name in ('1a','1b') else s)
                tw, th = ui.measure_string(txt, font=FONT_LABEL)
                ui.draw_string(txt, (rx + rw/2 - tw/2, ry + rh/2 - th/2, tw, th),
                               font=FONT_LABEL, color=LABEL_COLOR, alignment=ui.ALIGN_CENTER)

        # Frame + divider at x=21
        ui.set_color(BORDER_COLOR + (0.3,))
        frame_path = ui.Path.rect(m.ox, m.oy, W*m.k, H*m.k)
        frame_path.line_width = 1.5
        frame_path.stroke()
        xdiv = m.x_to_px(21)
        d = ui.Path(); d.move_to(xdiv, m.oy); d.line_to(xdiv, m.oy + H*m.k)
        d.line_width = 1.0; d.stroke()

        # Title & footer
        title = 'Fibonacci Sequence'
        tw, th = ui.measure_string(title, font=FONT_TITLE)
        ui.draw_string(title, (MARGIN, max(10, 10 + t), tw, th), font=FONT_TITLE, color=TITLE_COLOR)
        seq = '0, 1, 1, 2, 3, 5, 8, 13, 21, 34...'
        sw, sh = ui.measure_string(seq, font=FONT_SERIES)
        ui.draw_string(seq, (MARGIN, self.height - sh - 8 - max(0, b),
                             self.width - 2*MARGIN, sh), font=FONT_SERIES, color=LABEL_COLOR)

        # Spiral — now +90° CCW arcs (flipped orientation)
        spiral, start_dir = build_spiral(m)
        stroke = max(2.0, SPIRAL_WIDTH_PT * (m.k / 20.0))
        spiral.line_width = stroke
        ui.set_color(SPIRAL_COLOR); spiral.stroke()

        if SHOW_START_ARROW and start_dir:
            draw_arrowhead(*start_dir, size=10 + 0.12*m.k)

if __name__ == '__main__':
    FibPoster().present('fullscreen', hide_title_bar=True)