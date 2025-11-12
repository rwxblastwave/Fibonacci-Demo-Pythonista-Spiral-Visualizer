# Pythonista 3 — Fibonacci Poster (each square uniquely colored, notch-safe)
import ui
from objc_util import ObjCClass, on_main_thread

# ------------------- Config -------------------
DRAW_SPIRAL = False
MARGIN = 18
GRID_ALPHA = 0.20
BORDER_COLOR = (0.14, 0.18, 0.45)
LABEL_COLOR  = (1.00, 0.45, 0.10)
TITLE_COLOR  = (0.05, 0.20, 0.45)
FONT_TITLE  = ('<System-Bold>', 28)
FONT_LABEL  = ('<System>', 20)
FONT_SERIES = ('<System-Bold>', 20)

# Distinct colors per Fibonacci square
TINTS = {
    1:  (0.95, 0.85, 0.40, 0.65),   # golden yellow
    2:  (0.90, 0.60, 0.40, 0.65),   # coral
    3:  (0.55, 0.75, 0.95, 0.65),   # light blue
    5:  (0.65, 0.85, 0.70, 0.65),   # green
    8:  (0.90, 0.75, 0.90, 0.65),   # lavender
    13: (0.80, 0.90, 0.98, 0.65),   # pale blue
    21: (0.99, 0.94, 0.70, 0.60),   # cream
}

# Exact Fibonacci tiling (34×21 rectangle)
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

# ------------------- Safe area helpers -------------------
@on_main_thread
def _ios_safe_insets():
    try:
        UIApplication = ObjCClass('UIApplication')
        app = UIApplication.sharedApplication()
        window = app.keyWindow() or app.windows().lastObject()
        if window:
            ins = window.safeAreaInsets()
            return float(ins.top), float(ins.left), float(ins.bottom), float(ins.right)
    except Exception:
        pass
    return 0.0, 0.0, 0.0, 0.0

def _fallback_insets(view_w, view_h):
    if view_h > view_w:  # portrait
        return 44.0, 0.0, 34.0, 0.0
    return 20.0, 0.0, 0.0, 0.0

# ------------------- Mapping -------------------
class Map:
    def __init__(self, frame, safe_top=0, safe_bottom=0):
        vw, vh = frame[2], frame[3]
        top_pad    = 18 + safe_top + 12
        bottom_pad = 18 + safe_bottom + 6
        sx = (vw - 2*MARGIN) / float(W)
        sy = (vh - (MARGIN + bottom_pad) - (MARGIN + top_pad)) / float(H)
        self.k = min(sx, sy)
        self.ox = MARGIN + (vw - 2*MARGIN - W*self.k) * 0.5
        self.oy = MARGIN + top_pad + (vh - (2*MARGIN + top_pad + bottom_pad) - H*self.k) * 0.5
    def rect_ll(self, x, y, s):
        px = self.ox + x * self.k
        py_top = self.oy + (H - (y + s)) * self.k
        return (px, py_top, s * self.k, s * self.k)
    def x_to_px(self, gx): return self.ox + gx * self.k
    def y_to_py(self, gy): return self.oy + (H - gy) * self.k

# ------------------- View -------------------
class FibPoster(ui.View):
    def __init__(self):
        super().__init__(bg_color='white')
        self.flex = 'WH'
        self._safe_top, self._safe_left, self._safe_bottom, self._safe_right = _ios_safe_insets()

    def layout(self):
        t, l, b, r = _ios_safe_insets()
        if (t, l, b, r) == (0.0, 0.0, 0.0, 0.0):
            ft, fl, fb, fr = _fallback_insets(self.width, self.height)
            t = max(t, ft); b = max(b, fb)
        self._safe_top, self._safe_bottom = t, b
        self.set_needs_display()

    def draw(self):
        t, b = self._safe_top, self._safe_bottom
        r = ui.Rect(*self.bounds)
        m = Map(r, safe_top=t, safe_bottom=b)

        # background
        ui.set_color((0.98, 0.99, 1.0))
        ui.Path.rect(m.ox, m.oy, W*m.k, H*m.k).fill()

        # grid
        ui.set_color((0.2, 0.4, 0.7, GRID_ALPHA))
        for gx in range(W+1):
            x = m.x_to_px(gx)
            p = ui.Path(); p.move_to(x, m.oy); p.line_to(x, m.oy + H*m.k); p.stroke()
        for gy in range(H+1):
            y = m.y_to_py(gy)
            p = ui.Path(); p.move_to(m.ox, y); p.line_to(m.ox + W*m.k, y); p.stroke()

        # squares, each with its own tint
        for name, s, x, y in SQUARES:
            rx, ry, rw, rh = m.rect_ll(x, y, s)
            tint = TINTS.get(s, (0.85, 0.85, 0.85, 0.65))
            ui.set_color(tint); ui.Path.rect(rx, ry, rw, rh).fill()
            ui.set_color((0, 0, 0, 0.12)); ui.Path.rect(rx, ry, rw, rh).stroke()
            ui.set_color(LABEL_COLOR)
            txt = str(1 if name in ('1a','1b') else s)
            tw, th = ui.measure_string(txt, font=FONT_LABEL)
            ui.draw_string(txt, (rx + rw/2 - tw/2, ry + rh/2 - th/2, tw, th),
                           font=FONT_LABEL, color=LABEL_COLOR, alignment=ui.ALIGN_CENTER)

        # frame & divider
        ui.set_color(BORDER_COLOR)
        pf = ui.Path.rect(m.ox, m.oy, W*m.k, H*m.k); pf.line_width = 2.0; pf.stroke()
        xdiv = m.x_to_px(21)
        pd = ui.Path(); pd.move_to(xdiv, m.oy); pd.line_to(xdiv, m.oy + H*m.k); pd.line_width = 2.0; pd.stroke()

        # title
        title = 'Fibonacci Sequence'
        tw, th = ui.measure_string(title, font=FONT_TITLE)
        ui.draw_string(title, (MARGIN, max(10, 10 + t), tw, th),
                       font=FONT_TITLE, color=TITLE_COLOR)

        # sequence footer
        seq = '0, 1, 1, 2, 3, 5, 8, 13, 21, 34...'
        sw, sh = ui.measure_string(seq, font=FONT_SERIES)
        ui.draw_string(seq, (MARGIN, self.height - sh - 8 - max(0, b),
                             self.width - 2*MARGIN, sh),
                       font=FONT_SERIES, color=LABEL_COLOR)

        if DRAW_SPIRAL:
            ui.set_color(LABEL_COLOR)
            pass  # Spiral logic attaches here later

if __name__ == '__main__':
    v = FibPoster()
    v.present('fullscreen', hide_title_bar=True)