# Pythonista 3 — Fibonacci Poster (flipped arc orientation: +90° CCW)
# Exact 34×21 tiling, distinct colors, notch-safe layout
# Origin: (24, 6) with 270° (down) initial tangent
# --------------------------------------------------------------
#  + Close (×) button in the safe top-right corner
#  + Export (PNG) button — saves & shares a PNG of the BOARD ONLY
#  * Safe-area fix (call .safeAreaInsets())
#  * Export fix: zero-origin mapper (no CTM needed)
# --------------------------------------------------------------

import ui, math, os, datetime, console, time
from objc_util import ObjCClass, on_main_thread

# ===== Appearance =====
MARGIN = 18
GRID_ALPHA = 0.35
FONT_TITLE   = ('<System-Bold>', 28)
FONT_LABEL   = ('<System>', 20)
FONT_SERIES  = ('<System-Bold>', 20)
SPIRAL_WIDTH_PT = 4.0

SHOW_GRID = True
SHOW_TINY_1x1_LABELS = True

PALETTES = [
    {
        'name': 'Sunrise Fields',
        'background': (0.98, 0.98, 1.0),
        'spiral': (1.00, 0.45, 0.10),
        'label': (1.00, 0.45, 0.10),
        'title': (0.05, 0.20, 0.45),
        'border': (0.14, 0.18, 0.45),
        'tints': {
            1:  (0.98, 0.90, 0.60, 0.75),
            2:  (0.95, 0.70, 0.50, 0.75),
            3:  (0.70, 0.85, 0.98, 0.75),
            5:  (0.80, 0.95, 0.80, 0.75),
            8:  (0.95, 0.85, 0.95, 0.75),
            13: (0.90, 0.95, 0.99, 0.75),
            21: (0.99, 0.98, 0.80, 0.70),
        }
    },
    {
        'name': 'Ocean Shell',
        'background': (0.95, 0.98, 1.0),
        'spiral': (0.00, 0.46, 0.54),
        'label': (0.00, 0.46, 0.54),
        'title': (0.02, 0.24, 0.34),
        'border': (0.08, 0.18, 0.36),
        'tints': {
            1:  (0.88, 0.96, 0.99, 0.78),
            2:  (0.76, 0.90, 0.95, 0.78),
            3:  (0.70, 0.84, 0.92, 0.78),
            5:  (0.82, 0.93, 0.95, 0.78),
            8:  (0.94, 0.98, 0.99, 0.78),
            13: (0.80, 0.92, 0.92, 0.78),
            21: (0.90, 0.97, 0.97, 0.78),
        }
    },
    {
        'name': 'Forest Canopy',
        'background': (0.97, 0.99, 0.96),
        'spiral': (0.25, 0.55, 0.18),
        'label': (0.25, 0.45, 0.15),
        'title': (0.10, 0.30, 0.12),
        'border': (0.20, 0.42, 0.24),
        'tints': {
            1:  (0.90, 0.98, 0.87, 0.75),
            2:  (0.84, 0.95, 0.82, 0.75),
            3:  (0.80, 0.93, 0.76, 0.75),
            5:  (0.86, 0.96, 0.85, 0.75),
            8:  (0.92, 0.98, 0.90, 0.75),
            13: (0.88, 0.96, 0.86, 0.75),
            21: (0.94, 0.98, 0.92, 0.75),
        }
    },
]

# ===== Exact tiling on a 34×21 grid (y-up) =====
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
W, H = 34, 21  # board width/height in grid units

# ===== Safe-area =====
@on_main_thread
def _ios_safe_insets():
    """Return (top, left, bottom, right) safe-area in points."""
    try:
        UIApplication = ObjCClass('UIApplication')
        app = UIApplication.sharedApplication()
        win = app.keyWindow() or (app.windows() and app.windows()[0])
        if win:
            ins = win.safeAreaInsets()
            return float(ins.top), float(ins.left), float(ins.bottom), float(ins.right)
    except Exception:
        pass
    return 0.0, 0.0, 0.0, 0.0

def _fallback_insets(w, h):
    return (44.0, 0.0, 34.0, 0.0) if h > w else (20.0, 0.0, 20.0, 0.0)

# ===== Grid→screen mapper =====
class Map:
    """Maps grid coords (x right, y up) to iOS view coords (y down)."""
    def __init__(self, frame, safe_top=0.0, safe_bottom=0.0):
        vw, vh = frame.width, frame.height
        top_pad = MARGIN + safe_top + 12
        bottom_pad = MARGIN + safe_bottom + 6
        avail_w = vw - 2 * MARGIN
        avail_h = vh - top_pad - bottom_pad
        self.k = min(avail_w / W, avail_h / H)  # uniform scale
        self.ox = MARGIN + (avail_w - W * self.k) * 0.5
        self.oy = top_pad + (avail_h - H * self.k) * 0.5
        try:
            UIScreen = ObjCClass('UIScreen')
            self.scale = float(UIScreen.mainScreen().scale())
        except Exception:
            self.scale = 2.0

    def rect_ll(self, x, y, s):
        """Return rect in points for square at (x,y) size s (lower-left origin in grid)."""
        return (self.ox + x * self.k,
                self.oy + (H - (y + s)) * self.k,
                s * self.k, s * self.k)

    def pt(self, gx, gy):
        """Map a grid point (gx, gy) to view coords (px, py)."""
        return self.ox + gx * self.k, self.oy + (H - gy) * self.k

    def x_to_px(self, gx): return self.ox + gx * self.k
    def y_to_py(self, gy): return self.oy + (H - gy) * self.k

    def crisp(self, v, line_width_pt=1.0):
        """Snap a coordinate to pixel centers for sharp strokes."""
        px = v * self.scale
        px = round(px) + (0.5 if (line_width_pt * self.scale) % 2 else 0.0)
        return px / self.scale

# ===== Golden spiral geometry (y-up) =====
C1, C2, C3, C5, C8, C13, C21 = (25,6), (24,6), (24,5), (26,5), (26,8), (21,8), (21,0)
SPIRAL_ARCS = [
    (C1, (24,6), +90),
    (C1, (25,5), +90),
    (C2, (26,6), +90),
    (C3, (24,8), +90),
    (C5, (21,5), +90),
    (C8, (26,0), +90),
    (C13, (34,8), +90),
    (C21, (21,21), +90),
]

def arc_poly(mapper, center, start, sweep_deg, px_per_seg=6.0):
    """Sample a circular arc as a polyline with approx segment length in device pixels."""
    cx, cy = center
    sx, sy = start
    r = math.hypot(sx - cx, sy - cy)
    if r == 0 or sweep_deg == 0:
        return []
    a0 = math.atan2(sy - cy, sx - cx)
    a1 = a0 + math.radians(sweep_deg)
    segs = max(24, int(abs(r * mapper.k * math.radians(sweep_deg)) / (px_per_seg / mapper.scale)))
    pts = []
    for i in range(segs + 1):
        t = a0 + (a1 - a0) * (i / segs)
        gx = cx + r * math.cos(t)
        gy = cy + r * math.sin(t)
        pts.append(mapper.pt(gx, gy))
    return pts

def build_spiral(mapper):
    """Create a single ui.Path made of chained quarter-arc polylines (round caps/joins)."""
    path = ui.Path()
    path.line_cap_style = getattr(ui, 'LINE_CAP_ROUND', 1)
    path.line_join_style = getattr(ui, 'LINE_JOIN_ROUND', 1)
    first = True
    for center, start, sweep in SPIRAL_ARCS:
        seg = arc_poly(mapper, center, start, sweep)
        if not seg:
            continue
        if first:
            path.move_to(*seg[0])
            first = False
        for x, y in seg[1:]:
            path.line_to(x, y)
    return path

def build_spiral_points(mapper):
    pts = []
    for center, start, sweep in SPIRAL_ARCS:
        seg = arc_poly(mapper, center, start, sweep)
        if not seg:
            continue
        if not pts:
            pts.extend(seg)
        else:
            pts.extend(seg[1:])
    return pts

# ===== Main View =====
class FibPoster(ui.View):
    def __init__(self):
        super().__init__()
        self.palette_index = 0
        self.current_palette = PALETTES[self.palette_index]
        self.background_color = self.current_palette['background']
        self.flex = 'WH'
        self._safe_top = self._safe_bottom = 0.0
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._active_touch_id = None
        self._touch_prev = None
        self.anim_duration = 3.0
        self.anim_progress = 0.0
        self._animating = False
        self.update_safe_insets()
        self._start_spiral_animation()

        # Close (×) button
        self.close_btn = ui.Button(
            title='×',
            font=('<System-Bold>', 32),
            tint_color=(0.3, 0.3, 0.3),
            background_color=(1, 1, 1, 0.7),
            corner_radius=20,
            action=self._close_action)
        self.close_btn.flex = 'L'
        self.add_subview(self.close_btn)

        # Export (PNG) button
        self.export_btn = ui.Button(
            title='PNG',
            font=('<System-Bold>', 16),
            tint_color=(1, 1, 1),
            background_color=(0.12, 0.12, 0.14, 0.85),
            corner_radius=8,
            action=self._export_board_png)
        self.export_btn.flex = 'L'
        self.add_subview(self.export_btn)

        # Palette button
        self.palette_btn = ui.Button(
            title='Palette',
            font=('<System>', 14),
            tint_color=(1, 1, 1),
            background_color=(0.2, 0.2, 0.25, 0.85),
            corner_radius=8,
            action=self._cycle_palette)
        self.palette_btn.flex = 'L'
        self.add_subview(self.palette_btn)

    # ---------- Actions ----------
    def _close_action(self, sender):
        self.close()

    def _export_board_png(self, sender):
        """Export ONLY the 34×21 board as a PNG (no transforms needed)."""
        self.update_safe_insets()

        # Make a mapper for screen metrics
        m_screen = Map(self.bounds, safe_top=self._safe_top, safe_bottom=self._safe_bottom)
        board_w, board_h = W * m_screen.k, H * m_screen.k

        scale_options = [('1× (Screen)', 1.0), ('2× (Retina)', 2.0), ('4× (Print)', 4.0)]
        button_titles = [opt[0] for opt in scale_options]
        try:
            choice = console.alert('Export Resolution', 'Choose a scale for the PNG.',
                                   button_titles[0], button_titles[1], button_titles[2])
        except KeyboardInterrupt:
            return
        except Exception:
            choice = 1
        factor = scale_options[min(max(choice, 1), len(scale_options)) - 1][1]
        board_w *= factor
        board_h *= factor

        # Make a zero-origin mapper that draws the same board at (0,0)
        class ZeroMap(Map): pass
        m_zero = ZeroMap(self.bounds, safe_top=0, safe_bottom=0)
        m_zero.k = m_screen.k * factor
        m_zero.scale = m_screen.scale * factor
        m_zero.ox = 0.0
        m_zero.oy = 0.0

        with ui.ImageContext(board_w, board_h) as ctx:
            # White background
            ui.set_color((1, 1, 1, 1))
            ui.Path.rect(0, 0, board_w, board_h).fill()

            # Draw only the board using the zero-origin mapper
            self._draw_board(m_zero, spiral_progress=1.0)

            img = ctx.get_image()

        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f'FibonacciBoard_{ts}.png'
        path = os.path.join(os.getcwd(), fname)
        with open(path, 'wb') as f:
            f.write(img.to_png())

        console.quicklook(path)
        try:
            console.open_in(path)
        except Exception:
            pass
        console.hud_alert('Board PNG exported', 'success', 1.2)

    # ---------- Layout & draw ----------
    def update_safe_insets(self):
        t, _, b, _ = _ios_safe_insets()
        if t == 0 and b == 0:
            t, _, b, _ = _fallback_insets(self.width, self.height)
        self._safe_top, self._safe_bottom = t, b

    def layout(self):
        self.update_safe_insets()
        btn_size = 44
        safe = self._safe_top
        self.close_btn.width = self.close_btn.height = btn_size
        self.close_btn.x = self.width - btn_size - MARGIN
        self.close_btn.y = safe + 8
        self.export_btn.height = 30
        self.export_btn.width = 66
        self.export_btn.y = safe + 15
        self.export_btn.x = self.close_btn.x - self.export_btn.width - 8
        self.palette_btn.height = 30
        self.palette_btn.width = 86
        self.palette_btn.y = safe + 15
        self.palette_btn.x = self.export_btn.x - self.palette_btn.width - 8
        self.set_needs_display()

    def _draw_board(self, m, spiral_progress=None):
        """Draw ONLY the poster board (used on-screen and for PNG export)."""
        palette = self.current_palette
        # Board background
        card_path = ui.Path.rect(m.ox, m.oy, W * m.k, H * m.k)
        ui.set_color(palette['background'])
        card_path.fill()

        # Squares
        for name, s, x, y in SQUARES:
            rx, ry, rw, rh = m.rect_ll(x, y, s)
            tint = palette['tints'].get(1 if name in ('1a', '1b') else s, (0.85, 0.85, 0.85, 0.65))
            ui.set_color(tint)
            ui.Path.rect(rx, ry, rw, rh).fill()
            ui.set_color((0, 0, 0, 0.08))
            ui.Path.rect(rx, ry, rw, rh).stroke()
            if SHOW_TINY_1x1_LABELS or s != 1:
                txt = str(1 if name in ('1a', '1b') else s)
                tw, th = ui.measure_string(txt, font=FONT_LABEL)
                ui.draw_string(txt, (rx + rw/2 - tw/2, ry + rh/2 - th/2, tw, th),
                               font=FONT_LABEL, color=palette['label'])

        # Grid
        if SHOW_GRID:
            ui.set_color((0.3, 0.5, 0.8, GRID_ALPHA))
            line = ui.Path()
            line.line_width = 0.5
            for gx in range(W + 1):
                x = m.crisp(m.x_to_px(gx), line.line_width)
                line.move_to(x, m.oy)
                line.line_to(x, m.oy + H * m.k)
            for gy in range(H + 1):
                y = m.crisp(m.y_to_py(gy), line.line_width)
                line.move_to(m.ox, y)
                line.line_to(m.ox + W * m.k, y)
            line.stroke()

        # Frame + divider
        border_color = palette['border']
        ui.set_color(border_color + (0.3,))
        frame_path = ui.Path.rect(m.ox, m.oy, W * m.k, H * m.k)
        frame_path.line_width = 1.5
        frame_path.stroke()
        xdiv = m.crisp(m.x_to_px(21), 1.0)
        d = ui.Path()
        d.move_to(xdiv, m.oy)
        d.line_to(xdiv, m.oy + H * m.k)
        d.line_width = 1.0
        d.stroke()

        # Spiral (no arrow)
        if spiral_progress is None:
            spiral_progress = self.anim_progress
        spiral_progress = max(0.0, min(1.0, spiral_progress))
        pts = build_spiral_points(m)
        if pts:
            total = 0.0
            seg_lens = []
            for i in range(1, len(pts)):
                l = math.hypot(pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1])
                seg_lens.append(l)
                total += l
            path = ui.Path()
            path.move_to(*pts[0])
            if total == 0:
                draw_to = 0
            else:
                draw_to = total * spiral_progress
            acc = 0.0
            for i in range(1, len(pts)):
                seg = seg_lens[i-1] if i-1 < len(seg_lens) else 0.0
                if acc + seg >= draw_to and seg > 0:
                    t = (draw_to - acc) / seg
                    x = pts[i-1][0] + (pts[i][0] - pts[i-1][0]) * t
                    y = pts[i-1][1] + (pts[i][1] - pts[i-1][1]) * t
                    path.line_to(x, y)
                    break
                path.line_to(*pts[i])
                acc += seg
            else:
                pass
            stroke = max(2.0, SPIRAL_WIDTH_PT * (m.k / 20.0))
            path.line_width = stroke
            ui.set_color(palette['spiral'])
            path.stroke()

    def draw(self):
        self.update_safe_insets()
        t, b = self._safe_top, self._safe_bottom
        m = Map(self.bounds, safe_top=t, safe_bottom=b)

        base_cx = m.ox + W * m.k * 0.5
        base_cy = m.oy + H * m.k * 0.5
        m.k *= self.zoom
        m.ox = base_cx - W * m.k * 0.5 + self.pan_x
        m.oy = base_cy - H * m.k * 0.5 + self.pan_y

        # Board (exactly what PNG exports)
        self._draw_board(m)

        # Title & footer (on-screen only)
        palette = self.current_palette
        title = 'Fibonacci Sequence'
        tw, th = ui.measure_string(title, font=FONT_TITLE)
        ui.draw_string(title, (MARGIN, max(10, 10 + t), tw, th),
                       font=FONT_TITLE, color=palette['title'])

        seq = '0, 1, 1, 2, 3, 5, 8, 13, 21, 34...'
        sw, sh = ui.measure_string(seq, font=FONT_SERIES)
        ui.draw_string(seq, (MARGIN, self.height - sh - 8 - max(0, b),
                             self.width - 2*MARGIN, sh),
                       font=FONT_SERIES, color=palette['label'])

        palette_name = self.current_palette['name']
        pw, ph = ui.measure_string(palette_name, font=('<System>', 14))
        ui.draw_string(palette_name,
                       (self.width - pw - MARGIN, self.height - ph - 10 - max(0, b),
                        pw, ph), font=('<System>', 14), color=palette['label'])

    # ---------- Palette & animation helpers ----------
    def _cycle_palette(self, sender=None):
        self.palette_index = (self.palette_index + 1) % len(PALETTES)
        self.current_palette = PALETTES[self.palette_index]
        self.background_color = self.current_palette['background']
        self._start_spiral_animation()
        self.set_needs_display()

    def _start_spiral_animation(self):
        self.anim_progress = 0.0
        self._animating = True
        self.anim_start = time.time()
        ui.delay(self._step_animation, 0.0)

    def _step_animation(self):
        if not self._animating:
            return
        elapsed = time.time() - self.anim_start
        if self.anim_duration <= 0:
            self.anim_progress = 1.0
            self._animating = False
            self.set_needs_display()
            return
        progress = min(1.0, elapsed / self.anim_duration)
        self.anim_progress = progress
        self.set_needs_display()
        if progress < 1.0:
            ui.delay(self._step_animation, 1/60.0)
        else:
            self._animating = False

    # ---------- Gesture handling ----------
    def touch_began(self, touch):
        self._active_touch_id = touch.touch_id
        self._touch_prev = touch.location

    def touch_moved(self, touch):
        if self._active_touch_id != touch.touch_id or self.zoom <= 0:
            return
        x, y = touch.location
        px, py = self._touch_prev if self._touch_prev else (x, y)
        self.pan_x += x - px
        self.pan_y += y - py
        self._touch_prev = (x, y)
        self.set_needs_display()

    def touch_ended(self, touch):
        if touch.touch_id == self._active_touch_id:
            self._active_touch_id = None
            self._touch_prev = None
        if touch.tap_count >= 2:
            self._handle_double_tap(touch.location)
        elif touch.tap_count == 1 and self.anim_progress >= 1.0:
            self._start_spiral_animation()

    def _handle_double_tap(self, location):
        lx, ly = location
        if self.zoom >= 3.5:
            self.zoom = 1.0
            self.pan_x = 0.0
            self.pan_y = 0.0
        else:
            old_zoom = self.zoom
            new_zoom = min(4.0, self.zoom * 1.6)
            if old_zoom == 0:
                old_zoom = 1.0
            factor = new_zoom / old_zoom
            self.pan_x = (self.pan_x + lx) * factor - lx
            self.pan_y = (self.pan_y + ly) * factor - ly
            self.zoom = new_zoom
        self.set_needs_display()

if __name__ == '__main__':
    FibPoster().present('fullscreen', hide_title_bar=True)
