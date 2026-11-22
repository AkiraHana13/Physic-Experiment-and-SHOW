"""直線運動實驗室。以 Python 3.8+（含 Tkinter）執行本檔即可。"""

import math
import time
import tkinter as tk
from dataclasses import dataclass
from tkinter import font as tkfont
from tkinter import ttk
from typing import Optional


@dataclass(frozen=True)
class Motion:
    duration: float
    v0: float
    a0: float
    switch: Optional[float] = None
    a1: float = 0.0

    def state(self, t):
        """傳回位置、速度、加速度。切換瞬間採用右側的新加速度。"""
        before = t if self.switch is None else min(t, self.switch)
        v = self.v0 + self.a0 * before
        x = (self.v0 + 0.5 * self.a0 * before) * before
        if self.switch is None or t < self.switch:
            return x, v, self.a0
        after = t - before
        return x + (v + 0.5 * self.a1 * after) * after, v + self.a1 * after, self.a1

    def landmarks(self):
        """除端點與切換點外，也保留速度過零的位置極值。"""
        cuts = sorted({0.0, self.duration, self.switch or 0.0})
        marks = set(cuts)
        for start, end in zip(cuts, cuts[1:]):
            _, v, a = self.state(start)
            if a and 0 < -v / a < end - start:
                marks.add(start - v / a)
        return sorted(marks)

    def acceleration_steps(self):
        if self.switch is None:
            return [(0, self.a0)]
        if self.switch == 0:
            return [(0, self.a1)]
        return [(0, self.a0), (self.switch, self.a1)]


@dataclass(frozen=True)
class BrakeRun:
    """車頭為位置基準。接觸行人時結束實驗，保留接觸瞬間的速度。"""
    v0: float                      # m/s
    reaction: float                # s
    deceleration: float            # m/s²，正值表示大小
    target: Optional[float] = None

    @property
    def reaction_distance(self):
        return self.v0 * self.reaction

    @property
    def braking_distance(self):
        return 0.5 * self.v0 * (self.v0 / self.deceleration)

    @property
    def stop_distance(self):
        return self.reaction_distance + self.braking_distance

    @property
    def critical_speed(self):
        """使停車距離等於行人距離的非負速率（m/s）。"""
        if self.target is None or self.target == 0:
            return self.target
        b, d = self.deceleration, self.target
        bt = b * self.reaction
        # 將正根有理化，避免 sqrt((bτ)² + 2bD) − bτ 相減損失精度。
        return 2*b*d / (math.hypot(bt, math.sqrt(2*b*d)) + bt)

    @property
    def stop_time(self):
        return self.reaction + self.v0 / self.deceleration if self.v0 else 0.0

    @property
    def outcome(self):
        if self.target is None:
            return None
        if math.isclose(self.target, self.stop_distance, rel_tol=1e-14):
            return "touch"
        return "hit" if self.target < self.stop_distance else "clear"

    @property
    def duration(self):
        if self.outcome != "hit":
            return self.stop_time
        if self.target <= self.reaction_distance:
            return self.target / self.v0
        # 以平均速度求時間，避免兩個接近的速度相減造成精度損失。
        d = self.target - self.reaction_distance
        v_hit = math.sqrt(2 * self.deceleration * (self.stop_distance - self.target))
        return self.reaction + 2 * d / (self.v0 + v_hit)

    @property
    def switch(self):
        return self.reaction if self.v0 and self.reaction <= self.duration else None

    def state(self, t):
        t = min(max(0.0, t), self.duration)
        if t >= self.stop_time:
            return self.stop_distance, 0.0, 0.0
        if t < self.reaction:
            return self.v0 * t, self.v0, 0.0
        dt = t - self.reaction
        v = max(0.0, self.v0 - self.deceleration * dt)
        x = self.reaction_distance + 0.5 * (self.v0 + v) * dt
        return x, v, -self.deceleration

    def landmarks(self):
        return sorted({0.0, self.duration, self.switch or 0.0})

    def acceleration_steps(self):
        return [(t, self.state(t)[2]) for t in self.landmarks()]


BG = "#e2eff1"
WHITE = "#ffffff"
NAVY = "#1a2332"
INK = "#18354a"
MUTED = "#435f70"
TEAL = "#2d8b8b"
DEEP_TEAL = "#155e65"
SEAFOAM = "#a8dadc"
CREAM = "#f1faee"
GRID = "#c9dcdf"
PAPER = "#eff7f7"
AXIS = "#859fa8"
ROAD = "#395568"
BLUE = "#205e96"
ORANGE = "#ac5128"
COLORS = (DEEP_TEAL, BLUE, ORANGE)


def num(value, precision=4):
    return format(value if value else 0, f".{precision}g")


def bounds(values):
    lo, hi = min(0, *values), max(0, *values)
    pad = (hi - lo) * 0.13 if hi > lo else 1.0
    return lo - pad, hi + pad


def ticks(lo, hi, count):
    raw = (hi - lo) / count
    base = 10 ** math.floor(math.log10(raw))
    step = min((1, 2, 2.5, 5, 10), key=lambda k: abs(math.log(k * base / raw))) * base
    return [i * step for i in range(math.ceil(lo / step), math.floor(hi / step) + 1)]


class Lab:
    def __init__(self, root):
        self.root = root
        root.configure(bg=BG)
        families = set(tkfont.families(root))
        self.family = next((f for f in ("Microsoft JhengHei", "PingFang TC",
                                        "Noto Sans CJK TC") if f in families),
                           tkfont.nametofont("TkDefaultFont").actual("family"))
        self.t = 0.0
        self.running = False
        self.rate = 1.0
        self.callback = None
        self.updating_slider = False
        self.draw_pending = False
        self.dual = tk.BooleanVar(value=False)
        self.params = {}

        style = ttk.Style(root)
        style.configure("TEntry", padding=3)
        style.configure("Lab.TCheckbutton", background=WHITE,
                        font=(self.family, 11, "bold"), foreground=INK)
        top = tk.Frame(root, bg=NAVY, padx=20, pady=6)
        top.pack(fill="x")
        self.label(top, self.page_title, 19, NAVY, CREAM, True).pack(side="left")

        body = tk.Frame(root, bg=BG, padx=12, pady=9)
        body.pack(expand=True, fill="both")
        sidebar = tk.Frame(body, bg=WHITE, padx=14, pady=12)
        sidebar.pack(side="left", fill="y", padx=(0, 8))
        self.label(sidebar, "實驗設定", 14, bold=True).pack(anchor="w", pady=(0, 4))
        self.make_fields(sidebar)
        self.toggle_fields()
        self.action(sidebar, "套用並播放", self.apply, primary=True).pack(fill="x", pady=(12, 3))
        self.error = self.label(sidebar, "", 10, fg="#ae3535")
        self.error.configure(wraplength=185, justify="left")
        self.error.pack(anchor="w")

        panel = tk.Frame(body, bg=WHITE)
        panel.pack(side="left", expand=True, fill="both")
        panel = self.make_motion_panel(panel)
        self.canvas = tk.Canvas(panel, bg=WHITE, highlightthickness=0)
        self.canvas.pack(expand=True, fill="both")
        self.canvas.bind("<Configure>", self.queue_draw)
        controls = tk.Frame(panel, bg=PAPER, padx=8, pady=5)
        controls.pack(fill="x")
        timeline = tk.Frame(controls, bg=PAPER)
        timeline.pack(fill="x", pady=(0, 3))
        self.play_button = self.action(controls, "播放", self.play_pause, primary=True)
        self.play_button.pack(side="left")
        self.action(controls, "回到起點", lambda: self.seek(0)).pack(side="left", padx=(5, 0))
        self.action(controls, "下一整秒", self.next_second).pack(side="left", padx=5)
        self.label(controls, "播放倍速", 10, PAPER).pack(side="left")
        self.rate_box = ttk.Combobox(controls, width=5,
                                     values=("0.25", "0.5", "0.75", "1", "1.5", "2", "4", "8"))
        self.rate_box.set("1")
        self.rate_box.pack(side="left")
        self.rate_box.bind("<<ComboboxSelected>>", self.change_rate)
        self.rate_box.bind("<Return>", self.change_rate)
        self.rate_box.bind("<KP_Enter>", self.change_rate)
        self.rate_box.bind("<FocusOut>", self.change_rate)
        self.slider_time = tk.DoubleVar(value=0)
        self.slider = tk.Scale(timeline, from_=0, to=8, resolution=-1, digits=12, orient="horizontal",
                               showvalue=0, bg=PAPER, troughcolor=SEAFOAM, activebackground=TEAL,
                               highlightthickness=0, bd=0, variable=self.slider_time)
        self.slider_time.trace_add("write", self.slider_changed)
        self.slider.pack(side="left", expand=True, fill="x", padx=5)
        self.clock = self.label(timeline, "", 10, PAPER, INK, True)
        self.clock.pack(side="right")
        self.load_motion(self.initial_motion)

    page_title = "直線運動實驗室"
    initial_motion = Motion(8, 0, 2)
    graph_top = 154
    switch_label = "切換"

    def make_motion_panel(self, panel):
        return panel

    def make_fields(self, sidebar):
        for key, name, val in (("T", "總時間  T（s）", "8"), ("a", "加速度  a（m/s²）", "2"),
                               ("v", "初始速度  v₀（m/s）", "0")):
            self.field(sidebar, key, name, val)
        ttk.Separator(sidebar).pack(fill="x", pady=9)
        ttk.Checkbutton(sidebar, text="中途切換加速度", variable=self.dual,
                        style="Lab.TCheckbutton", command=self.toggle_fields).pack(anchor="w")
        self.field(sidebar, "S", "切換時刻（s）", "4")
        self.field(sidebar, "b", "新加速度（m/s²）", "-4")

    def label(self, parent, text, size, bg=WHITE, fg=INK, bold=False):
        return tk.Label(parent, text=text, bg=bg, fg=fg,
                        font=(self.family, size, "bold" if bold else "normal"))

    def action(self, parent, title, command, primary=False):
        return tk.Button(parent, text=title, command=command, bd=0, padx=10, pady=5,
                         cursor="hand2", bg=DEEP_TEAL if primary else BG,
                         fg=WHITE if primary else INK, activebackground=INK,
                         activeforeground=WHITE,
                         font=(self.family, 10, "bold"))

    def field(self, parent, key, title, initial):
        self.label(parent, title, 10, fg=MUTED).pack(anchor="w", pady=(4, 0))
        entry = ttk.Entry(parent, width=18, font=(self.family, 12))
        entry.insert(0, initial)
        entry.pack(fill="x")
        self.params[key] = entry

    def toggle_fields(self):
        for key in ("S", "b"):
            self.params[key].configure(state="normal" if self.dual.get() else "disabled")

    def read(self, key, title):
        try:
            value = float(self.params[key].get())
        except ValueError:
            raise ValueError(f"請在「{title}」輸入數字。") from None
        if not math.isfinite(value):
            raise ValueError(f"「{title}」必須為有限數值。")
        return value

    def apply(self):
        try:
            motion = self.read_motion()
        except ValueError as error:
            self.error.configure(text=str(error))
            return
        self.error.configure(text="")
        self.stop()
        self.load_motion(motion)
        self.play_pause()

    def read_motion(self):
        duration = self.read("T", "總時間")
        if not 0.001 <= duration <= 600:
            raise ValueError("總時間可設為 0.001 至 600 秒。")
        v, a = self.read("v", "初始速度"), self.read("a", "加速度")
        switch = self.read("S", "切換時刻") if self.dual.get() else None
        if switch is not None and not 0 <= switch <= duration:
            raise ValueError("切換時刻須介於 0 秒與總時間之間。")
        b = self.read("b", "新加速度") if self.dual.get() else 0
        if any(n and not 1e-100 <= abs(n) <= 1e100 for n in (v, a, b)):
            raise ValueError("速度或加速度超出可繪圖範圍。")
        return Motion(duration, v, a, switch, b)

    def load_motion(self, motion):
        self.motion = motion
        self.t = 0.0
        marks = motion.landmarks()
        states = [motion.state(t) for t in marks]
        self.ranges = [bounds(list(values)) for values in zip(*states)]
        self.samples = sorted(set(marks) | {motion.duration * i / 300 for i in range(301)})
        self.history = [(t, *motion.state(t)) for t in self.samples]
        self.dots = [motion.state(i)[0] for i in range(math.floor(motion.duration) + 1)]
        self.updating_slider = True
        self.slider.configure(to=motion.duration)
        self.updating_slider = False
        self.refresh()

    def stop(self):
        self.running = False
        if self.callback is not None:
            self.root.after_cancel(self.callback)
            self.callback = None
        self.play_button.configure(text="播放")

    def play_pause(self):
        if self.running:
            self.advance_clock()
            self.stop()
            self.refresh()
            return
        if self.t >= self.motion.duration:
            self.t = 0
        self.last_wall_time = time.perf_counter()
        self.running = True
        self.play_button.configure(text="暫停")
        self.tick()

    def advance_clock(self):
        now = time.perf_counter()
        elapsed = now - self.last_wall_time
        self.last_wall_time = now
        self.t = min(self.motion.duration, self.t + elapsed * self.rate)

    def change_rate(self, event):
        message = "播放倍速須為大於零的有限數值。"
        try:
            rate = float(self.rate_box.get())
            if not math.isfinite(rate) or rate <= 0:
                raise ValueError
        except ValueError:
            self.error.configure(text=message)
            self.rate_box.set(str(self.rate))
            return "break"
        if self.error.cget("text") == message:
            self.error.configure(text="")
        if self.running:
            # 先依原倍率結算已經過的時間，新倍率從此刻開始生效。
            self.advance_clock()
            if self.t >= self.motion.duration:
                self.stop()
            self.refresh()
        self.rate = rate
        return "break"

    def tick(self):
        self.callback = None
        self.advance_clock()
        if self.t >= self.motion.duration:
            self.stop()
        self.refresh()
        if self.running:
            self.callback = self.root.after(33, self.tick)

    def next_second(self):
        self.seek(min(self.motion.duration, math.floor(self.t) + 1))

    def seek(self, t):
        self.stop()
        self.t = t
        self.refresh()

    def slider_changed(self, *_):
        if not self.updating_slider:
            self.seek(max(0.0, min(self.motion.duration, self.slider_time.get())))

    def refresh(self):
        # 只有手動拖曳才暫停，程式更新滑桿時沿用同一個播放時鐘。
        self.updating_slider = True
        self.slider.set(self.t)
        self.updating_slider = False
        self.clock.configure(text=f"{self.t:.3f} / {num(self.motion.duration)} s")
        self.draw()

    def queue_draw(self, _):
        if not self.draw_pending:
            self.draw_pending = True
            self.root.after_idle(self.draw)

    def write(self, x, y, text, size=10, color=MUTED, anchor="w", bold=False):
        self.canvas.create_text(x, y, text=text, anchor=anchor, fill=color,
                                font=(self.family, size, "bold" if bold else "normal"))

    def draw(self):
        self.draw_pending = False
        c = self.canvas
        w, h = c.winfo_width(), c.winfo_height()
        if w < 100 or h < 100:
            return
        c.delete("all")
        state = self.motion.state(self.t)
        self.draw_track(w, state)
        left, right = 90, w - 26
        top, bottom = self.graph_top, h - 32
        band = (bottom - top) / 3
        span = self.motion.duration or 1.0
        time_x = lambda t: left + (right - left) * (t / span)
        time_ticks = ticks(0, span, min(8, max(3, (right-left)//85)))
        for i, (title, unit) in enumerate((("位置", "m"), ("速度", "m/s"), ("加速度", "m/s²"))):
            row = top + i * band
            self.write(17, row, f"{title}  ({unit})", 11, INK, bold=True)
            self.write(right, row, f"{num(state[i], 5)} {unit}", 11, COLORS[i], "e", True)
            self.draw_graph(i, row + 17, row + band - 15, left, right, time_x, time_ticks, state)
        for t in time_ticks:
            self.write(time_x(t), bottom - 3, num(t), 9, anchor="n")
        self.write((left + right) / 2, h - 11, "時間  t（s）", 10, INK, "center")

    def draw_track(self, w, state):
        c = self.canvas
        self.write(18, 17, "車輛位置", 13, INK, bold=True)
        self.write(w - 15, 17, "每個圓點記錄一個整秒的位置", 10, anchor="e")
        lo, hi = self.ranges[0]
        def px(x):
            return 46 + (w - 92) * ((x - lo) / (hi - lo))
        c.create_rectangle(10, 33, w-10, 130, fill=PAPER, outline="")
        c.create_rectangle(14, 78, w-14, 95, fill=ROAD, outline="")
        c.create_line(14, 87, w-14, 87, fill=CREAM, dash=(12, 10))
        for val in ticks(lo, hi, max(3, (w-90)//90)):
            point = px(val)
            c.create_line(point, 106, point, 111, fill=MUTED)
            self.write(point, 119, num(val), 9, anchor="center")
        self.write(w-15, 120, "m", 9, anchor="e")
        c.create_line(22, 104, w-22, 104, fill=AXIS)
        for i in range(math.floor(self.t) + 1):
            point = px(self.dots[i])
            c.create_oval(point-3, 101, point+3, 107, fill=INK, outline=WHITE)
        cx = px(state[0])
        c.create_line(cx, 77, cx, 104, fill=INK, dash=(2, 3))
        direction = -1 if state[1] < 0 else 1
        self.draw_car(cx, direction)

    def draw_car(self, cx, direction=1):
        c = self.canvas
        def shape(points, color):
            coords = [(cx + direction*x, y) for x, y in points]
            c.create_polygon(*coords, fill=color, outline=INK)
        shape([(-22, 69), (-21, 60), (-12, 59), (-7, 50), (6, 50),
               (14, 59), (22, 62), (24, 69), (21, 73), (-22, 73)], TEAL)
        shape([(-9, 59), (-5, 52), (4, 52), (10, 59)], SEAFOAM)
        for dx in (-13, 14):
            wx = cx + direction*dx
            c.create_oval(wx-5, 68, wx+5, 78, fill=INK, outline="")
            c.create_oval(wx-2, 71, wx+2, 75, fill=WHITE, outline="")

    def draw_graph(self, index, top, bottom, left, right, time_x, time_ticks, state):
        c = self.canvas
        lo, hi = self.ranges[index]
        def py(value):
            return bottom - (bottom - top) * ((value - lo) / (hi - lo))
        for t in time_ticks:
            x = time_x(t)
            c.create_line(x, top, x, bottom, fill=GRID)
        for value in ticks(lo, hi, 3 if bottom-top > 66 else 2):
            y = py(value)
            c.create_line(left, y, right, y, fill=GRID if value else AXIS)
            self.write(left - 7, y, num(value), 9, anchor="e")
        c.create_line(left, top, left, bottom, right, bottom, fill=AXIS)
        switch = self.motion.switch
        if switch is not None:
            sx = time_x(switch)
            c.create_line(sx, top, sx, bottom, fill=ORANGE, dash=(3, 4))
            if index == 0:
                self.write(sx, top, f"{self.switch_label} {num(switch)} s", 9, ORANGE,
                           "ne" if sx > (left+right)/2 else "nw")
        xnow = time_x(self.t)
        c.create_line(xnow, top, xnow, bottom, fill=MUTED, dash=(2, 3))
        color = COLORS[index]
        if index == 2:
            steps = self.motion.acceleration_steps()
            for j, (start, value) in enumerate(steps):
                if start > self.t:
                    break
                end = min(self.t, steps[j+1][0]) if j+1 < len(steps) else self.t
                x, y = time_x(start), py(value)
                c.create_line(x, y, time_x(end), y, fill=color, width=3)
                if j and steps[j-1][1] != value:
                    old = py(steps[j-1][1])
                    c.create_oval(x-3, old-3, x+3, old+3, fill=WHITE, outline=color, width=2)
                    c.create_oval(x-3, y-3, x+3, y+3, fill=color, outline=color)
        else:
            points = [(time_x(row[0]), py(row[index + 1])) for row in self.history if row[0] < self.t]
            points.append((xnow, py(state[index])))
            if len(points) >= 2:
                c.create_line(*points, fill=color, width=3)
        y = py(state[index])
        c.create_oval(xnow-4, y-4, xnow+4, y+4, fill=color, outline=WHITE)


class BrakeLab(Lab):
    page_title = "煞車距離實驗室"
    initial_motion = BrakeRun(20, 1, 5)
    graph_top = 187
    switch_label = "踩煞車"

    def make_motion_panel(self, panel):
        self.views = ttk.Notebook(panel, style="Section.TNotebook")
        self.views.pack(fill="both", expand=True)
        animation = tk.Frame(self.views, bg=WHITE)
        lesson = tk.Frame(self.views, bg=WHITE, padx=16, pady=10)
        self.views.add(animation, text="運動畫面")
        self.views.add(lesson, text="初速推導")
        self.views.bind("<<NotebookTabChanged>>", self.view_changed)
        self.label(lesson, "初速多少才能在行人前停下？", 16, bold=True).pack(anchor="w")
        self.inputs_label = self.label(lesson, "", 10, fg=MUTED)
        self.inputs_label.pack(fill="x", pady=(3, 10))
        card = tk.Frame(lesson, bg=PAPER, padx=14, pady=10)
        card.pack(fill="both", expand=True)
        self.step_title = self.label(card, "", 15, PAPER, DEEP_TEAL, True)
        self.step_title.pack(anchor="w")
        self.step_body = tk.Text(card, height=1, width=1, wrap="char", bg=PAPER, fg=INK,
                                 font=(self.family, 12), relief="flat", highlightthickness=0,
                                 spacing1=2, spacing3=4)
        scroll = ttk.Scrollbar(card, command=self.step_body.yview)
        scroll.pack(side="right", fill="y", pady=(9, 0))
        self.step_body.configure(yscrollcommand=scroll.set)
        self.step_body.tag_configure("math", font=(self.family, 13, "bold"), foreground=DEEP_TEAL, spacing1=4)
        self.step_body.pack(fill="both", expand=True, pady=(8, 0))
        nav = tk.Frame(lesson, bg=WHITE)
        nav.pack(fill="x", pady=(8, 0))
        self.action(nav, "代入目前參數", self.use_lesson_inputs).pack(side="left")
        self.next_step = self.action(nav, "下一步", lambda: self.show_step(self.step+1), True)
        self.next_step.pack(side="right")
        self.prev_step = self.action(nav, "上一步", lambda: self.show_step(self.step-1))
        self.prev_step.pack(side="right", padx=5)
        return animation

    def load_motion(self, motion):
        super().load_motion(motion)
        self.lesson_steps = self.derive(motion)
        if motion.target is None:
            self.inputs_label.configure(text="需要行人的初始距離才能計算臨界初速。")
        else:
            self.inputs_label.configure(text=f"本次代入　D = {num(motion.target)} m　｜　"
                                             f"τ = {num(motion.reaction)} s　｜　"
                                             f"b = {num(motion.deceleration)} m/s²")
        self.show_step(0)

    def view_changed(self, _):
        if self.views.index("current") == 1:
            if self.running:
                self.play_pause()
            self.use_lesson_inputs()

    def use_lesson_inputs(self):
        try:
            motion = self.read_motion()
        except ValueError as error:
            self.error.configure(text=str(error))
            self.inputs_label.configure(text="請修正左側參數，再按「代入目前參數」。")
            self.lesson_steps = [("無法代入", str(error))]
            self.show_step(0)
            return
        self.error.configure(text="")
        self.stop()
        self.load_motion(motion)

    def apply(self):
        super().apply()
        if not self.error.cget("text"):
            self.views.select(0)

    def show_step(self, index):
        self.step = min(max(0, index), len(self.lesson_steps)-1)
        title, body = self.lesson_steps[self.step]
        prefix = f"{self.step+1} / {len(self.lesson_steps)}　" if len(self.lesson_steps)>1 else ""
        self.step_title.configure(text=prefix+title)
        self.step_body.configure(state="normal")
        self.step_body.delete("1.0", "end")
        for line in body.splitlines():
            is_formula = line.startswith(("反應距離 =", "反應距離 +", "0² =", "煞車距離 s", "vτ",
                                          "v ×", "v²", "(v +", "v★ =", "= √", "≈", "0 ≤"))
            self.step_body.insert("end", line+"\n", "math" if is_formula else ())
        self.step_body.configure(state="disabled")
        self.step_body.yview_moveto(0)
        self.prev_step.configure(state="normal" if self.step else "disabled")
        self.next_step.configure(state="normal" if self.step+1<len(self.lesson_steps) else "disabled")

    @staticmethod
    def derive(run):
        if run.target is None:
            return [("設定行人距離", "勾選左側「設定靜止行人」。\n輸入車頭到行人的距離，再按「代入目前參數」。")]
        if run.target == 0:
            return [("起點已接觸", "D = 0 m，車頭在起點就已接觸行人。\n\n"
                                  "即使初速是 0，兩者的間距也是 0。沒有能保留正間距的非負初速。")]
        d, tau, b = num(run.target), num(run.reaction), num(run.deceleration)
        limit = run.critical_speed
        kmh = limit * 3.6
        trial = max(0, math.ceil(kmh)-1)
        trial_run = BrakeRun(trial/3.6, run.reaction, run.deceleration, run.target)
        if trial_run.outcome != "clear":
            # 即使量級大到整數差 1 超過浮點解析度，例子仍要保留正間距。
            trial = max(0, min(trial-1, math.floor(kmh*0.99)))
            trial_run = BrakeRun(trial/3.6, run.reaction, run.deceleration, run.target)
        current = {"clear": "能在行人前停下", "touch": "停下時剛好接觸行人",
                   "hit": "會在停下前撞上行人"}[run.outcome]
        return [
            ("反應期間走多遠？", f"令 v 為待求的初速（m/s），τ 為駕駛反應時間。\n"
                             f"反應期間維持等速。\n\n反應距離 = vτ = v × {tau}　（m）"),
            ("踩下煞車後還要走多遠？", f"令 b = |a| = {b} m/s²，代表減速度大小。\n"
                                     f"設煞車距離為 s，停車時速度為 0。\n\n"
                                     f"0² = v² − 2bs\n煞車距離 s = v²/(2b) = v²/(2 × {b})　（m）"),
            ("寫出停在行人前的條件", f"反應距離 + 煞車距離 < 行人距離 D\n\n"
                                   f"vτ + v²/(2b) < D\n"
                                   f"v × {tau} + v²/(2 × {b}) < {d}\n\n"
                                   "等號代表車頭停下時剛好接觸行人。"),
            ("解出臨界初速", f"從剛好接觸的情況開始，兩邊乘以 2b，再配方。\n"
                           f"v² + 2bτv = 2bD\n(v + bτ)² = (bτ)² + 2bD\n\n"
                           f"取非負初速的解。\nv★ = √((bτ)² + 2bD) − bτ\n"
                           f"= √(({b} × {tau})² + 2 × {b} × {d}) − {b} × {tau}\n"
                           f"≈ {num(limit, 8)} m/s\n換算成時速約為 {num(kmh, 8)} km/h。"),
            ("選擇初速並驗算", f"初速越大，停車距離越長。要保留正間距，初速須符合\n0 ≤ v < v★\n"
                             f"臨界值 v★ 約為 {num(kmh, 8)} km/h。\n\n"
                             f"可測試 {trial} km/h。\n代回停車距離得到 {num(trial_run.stop_distance, 7)} m，"
                             f"車頭與行人仍相距 {num(run.target-trial_run.stop_distance, 7)} m。\n\n"
                             f"目前設定 {num(run.v0*3.6, 7)} km/h。\n完整停車需要 {num(run.stop_distance, 7)} m，{current}。")
        ]

    def make_fields(self, sidebar):
        self.field(sidebar, "speed", "行駛速度（km/h）", "72")
        self.field(sidebar, "reaction", "駕駛反應時間（s）", "1")
        self.field(sidebar, "brake", "煞車加速度（m/s²）", "-5")
        ttk.Separator(sidebar).pack(fill="x", pady=9)
        ttk.Checkbutton(sidebar, text="設定靜止行人", variable=self.dual,
                        style="Lab.TCheckbutton", command=self.toggle_fields).pack(anchor="w")
        self.field(sidebar, "target", "車頭到行人的初始距離（m）", "50")

    def toggle_fields(self):
        self.params["target"].configure(state="normal" if self.dual.get() else "disabled")

    def read_motion(self):
        speed = self.read("speed", "行駛速度")
        reaction = self.read("reaction", "駕駛反應時間")
        brake = abs(self.read("brake", "煞車加速度"))
        target = self.read("target", "行人距離") if self.dual.get() else None
        if speed < 0 or reaction < 0 or (target is not None and target < 0):
            raise ValueError("速度、反應時間與行人距離皆須大於或等於零。")
        if not brake:
            raise ValueError("請輸入非零煞車加速度，例如 −5。")
        if any(n and not 1e-50 <= n <= 1e50 for n in (speed, reaction, brake, target)):
            raise ValueError("輸入值超出可繪圖範圍。")
        motion = BrakeRun(speed / 3.6, reaction, brake, target)
        if motion.duration > 600:
            raise ValueError("本次播放超過 600 秒，請調整參數。")
        return motion

    def draw_track(self, w, state):
        c, run = self.canvas, self.motion
        x, v, _ = state
        finished = self.t >= run.duration
        phase = "已停車" if self.t >= run.stop_time else (
            "反應中・等速" if self.t < run.reaction else "煞車中・減速")
        self.write(16, 17, phase, 13, INK, bold=True)
        color = MUTED
        if run.target is None:
            caption = "車頭為位置基準｜圓點為每秒位置"
        elif not finished:
            caption = f"距行人尚有 {num(max(0, run.target-x))} m"
        elif run.outcome == "hit":
            caption = f"已撞上行人｜接觸速度 {num(v*3.6)} km/h"
            color = "#a73032"
        elif run.outcome == "touch":
            caption = "剛好接觸行人｜速度 0 km/h"
            color = ORANGE
        else:
            caption = f"未撞上｜停車後相距 {num(run.target-x)} m"
            color = INK
        self.write(w-16, 17, caption, 11, color, "e", True)

        extent = max(run.stop_distance, run.target or 0) or 1.0
        def px(distance):
            return 65 + (w-106) * (distance / extent)
        c.create_rectangle(10, 34, w-10, 130, fill=PAPER, outline="")
        c.create_rectangle(14, 78, w-14, 93, fill=ROAD, outline="")
        c.create_line(14, 86, w-14, 86, fill=CREAM, dash=(12, 10))
        for value in ticks(0, extent, max(3, (w-100)//95)):
            xx = px(value)
            c.create_line(xx, 110, xx, 114, fill=MUTED)
            self.write(xx, 121, num(value), 9, anchor="center")
        self.write(w-15, 121, "m", 9, anchor="e")
        for start, end, light, dark in (
            (0, run.reaction_distance, "#c7d7e4", BLUE),
            (run.reaction_distance, run.stop_distance, "#efd1be", ORANGE),
        ):
            c.create_line(px(start), 102, px(end), 102, fill=light, width=7)
            if x > start:
                c.create_line(px(start), 102, px(min(x, end)), 102, fill=dark, width=7)
        for i in range(math.floor(self.t)+1):
            xx = px(self.dots[i])
            c.create_oval(xx-2, 100, xx+2, 104, fill=INK, outline=WHITE)
        cx = px(x)
        self.draw_car(cx-24)
        c.create_line(cx, 71, cx, 108, fill=INK, dash=(2, 2))
        if run.target is not None:
            xx = px(run.target)
            c.create_line(xx, 79, xx, 109, fill=INK, dash=(2, 2))
            c.create_oval(xx-4, 42, xx+4, 50, fill=INK, outline="")
            c.create_line(xx, 51, xx, 65, fill=INK, width=3)
            c.create_line(xx-6, 61, xx, 54, xx+6, 61, fill=INK, width=2)
            c.create_line(xx-5, 77, xx, 65, xx+5, 77, fill=INK, width=3)

        self.write(18, 145, f"反應距離  {num(run.reaction_distance)} m", 11, BLUE, bold=True)
        self.write(w/2, 145, f"煞車距離  {num(run.braking_distance)} m", 11, ORANGE, "center", True)
        self.write(w-16, 145, f"完整停車距離  {num(run.stop_distance)} m", 11, INK, "e", True)
        self.write(18, 165, "淡色表示完整停車所需距離，深色表示已行駛距離。", 10)


def draw_concept_figure(canvas, topic, family):
    """依閱讀欄寬度按比例重畫例題；數值和比例尺都取自同一組資料。"""
    canvas.delete("all")
    width = canvas.winfo_width()
    if width <= 2:
        return
    left, right = 40, width - 48

    def label(x, y, value, color=INK, anchor="center"):
        canvas.create_text(x, y, text=value, fill=color, anchor=anchor, font=(family, 10))

    def dot(x, y):
        canvas.create_oval(x-4, y-4, x+4, y+4, fill=INK, outline=WHITE)

    if topic == "位置、速度與方向":
        end = left + (right-left)/3
        canvas.create_line(left, 28, right, 28, fill=TEAL, width=3, arrow="last")
        canvas.create_line(right, 45, end, 45, fill=INK, width=3, arrow="last")
        label((left+right)/2, 15, "向右 6 m")
        label((end+right)/2, 61, "向左 4 m")
        for x, name in [(left, "起點 0 m"), (end, "終點 2 m"), (right, "折返 6 m")]:
            label(x, 79, name)
    elif topic == "等加速度運動":
        canvas.create_line(left, 46, right, 46, fill=TEAL, width=2)
        for t in range(4):
            x = left + (right-left)*t*t/9
            label(x, 22, f"{t} s")
            dot(x, 46)
            label(x, 70, f"{t*t} m")
    elif topic == "運動圖表判讀":
        left += 55
        right -= 50
        canvas.create_polygon(left, 68, right, 68, right, 18, fill=SEAFOAM)
        canvas.create_line(left, 13, left, 68, right+17, 68, fill=INK, width=1)
        canvas.create_line(left, 68, right, 18, fill=BLUE, width=3)
        label(left-6, 18, "6 m/s", anchor="e")
        canvas.create_line(left, 18, right, 18, fill=TEAL, dash=(3, 5))
        label(left, 82, "0 s")
        label(right, 82, "3 s")
        label(left+(right-left)*.74, 55, "面積  9 m", BLUE)
    else:
        join = left + (right-left)/3
        canvas.create_line(left, 46, join, 46, fill=BLUE, width=9)
        canvas.create_line(join, 46, right, 46, fill=ORANGE, width=9)
        label((left+join)/2, 22, "反應距離  20 m", BLUE)
        label((join+right)/2, 22, "煞車距離  40 m", ORANGE)
        for x, name in [(left, "看見行人"), (join, "踩下煞車"), (right, "停車")]:
            label(x, 70, name)


def add_concepts_page(tabs, family):
    page = tk.Frame(tabs, bg=BG)
    tabs.insert(0, page, text="基礎概念與公式")
    menu = tk.Frame(page, bg=PAPER, padx=16, pady=7)
    menu.pack(fill="x")
    panel = tk.Frame(page, bg=WHITE)
    panel.pack(expand=True, fill="both", padx=12, pady=(2, 10))
    reader = tk.Text(panel, wrap="char", padx=22, pady=14, bg=WHITE, fg=INK,
                     font=(family, 12), bd=0, highlightthickness=0, width=1)
    bar = ttk.Scrollbar(panel, orient="vertical", command=reader.yview)
    bar.pack(side="right", fill="y")
    reader.configure(yscrollcommand=bar.set)
    reader.pack(fill="both", expand=True)
    reader.tag_configure("title", font=(family, 22, "bold"), spacing3=5)
    reader.tag_configure("lead", font=(family, 13), foreground=MUTED, spacing3=10)
    reader.tag_configure("heading", font=(family, 14, "bold"), spacing1=12, spacing3=4)
    reader.tag_configure("formula", font=(family, 13, "bold"), foreground=DEEP_TEAL,
                         background=PAPER, lmargin1=10, lmargin2=10, spacing1=3, spacing3=3)
    reader.tag_configure("body", spacing1=2, spacing2=3, spacing3=2)
    topics = {
        "位置、速度與方向": [
            ("lead", "從原點開到 6 m，再退回 2 m。這趟車程該記成幾公尺？"),
            ("heading", "位移看起點和終點，路程看整條路"),
            ("body", "約定向右為正。位置 x 表示車在哪裡，單位是公尺（m）。"),
            ("formula", "位移 Δx = 終點位置 − 起點位置 = 2 − 0 = +2 m"),
            ("body", "路程要把去程與回程的長度相加。這趟共走了 6 + 4 = 10 m。"),
            ("heading", "速度看位置怎麼變，加速度看速度怎麼變"),
            ("formula", "平均速度 = Δx / Δt\n平均加速度 = Δv / Δt"),
            ("body", "Δ 代表改變量，Δt 是經過的時間。速度的正負號表示方向，大小就是速率。\n加速度為 +2 m/s²，表示速度每秒增加 2 m/s。"),
            ("body", "例如，速度從 −4 變成 −2 m/s：車仍往左，速率卻從 4 降到 2 m/s。"),
            ("heading", "在動畫上觀察"),
            ("body", "圓點每隔 1 秒出現一次。若車持續朝同一方向走，點距越大，該秒的平均速率越大。"),
        ],
        "等加速度運動": [
            ("lead", "車從靜止出發，加速度固定為 2 m/s²。觀察每秒的位置點。"),
            ("heading", "經過 t 秒，車有多快？"),
            ("formula", "v = v₀ + at"),
            ("body", "v₀ 是起始速度，at 是這段時間增加的速度。\n第 3 秒：v = 0 + 2 × 3 = 6 m/s。"),
            ("heading", "同一時刻，車在哪裡？"),
            ("formula", "x = x₀ + v₀t + ½at²"),
            ("body", "x₀ 是起始位置。從 0 m 出發，第 3 秒的位置是 ½ × 2 × 3² = 9 m。\n看圖上的點距：第 1 秒走 1 m，第 2 秒走 3 m，第 3 秒走 5 m。"),
            ("heading", "已知位移，也能求速度"),
            ("formula", "v² = v₀² + 2a(x − x₀)"),
            ("body", "這條式子不需要時間，可用來求末速大小或煞車距離。\n以上三式適用於加速度固定的一段運動。a = 0 時，速度固定。"),
            ("body", "若途中改變加速度，下一段從切換時刻重新計時，並沿用當時的位置與速度。"),
        ],
        "運動圖表判讀": [
            ("lead", "三張圖都以時間為橫軸。下圖是車子在 3 秒內從靜止加速到 6 m/s 的速度圖。"),
            ("heading", "速度－時間圖　v–t"),
            ("formula", "斜率 = 加速度\n圖線與時間軸之間的帶號面積 = 位移"),
            ("body", "斜率是 (6 − 0) / 3 = 2 m/s²。圖線下方的三角形面積是 ½ × 3 × 6 = 9 m。\n時間軸上方的面積取正，下方取負。"),
            ("heading", "位置－時間圖　x–t"),
            ("formula", "兩點連線的斜率 = Δx / Δt = 平均速度"),
            ("body", "圖線上升代表車向右，下降代表向左。某一瞬間的切線越陡，當時的速率越大。\n切線水平時，當時的速度為零。"),
            ("heading", "加速度－時間圖　a–t"),
            ("formula", "圖線與時間軸之間的帶號面積 = 速度變化量 Δv"),
            ("body", "這個例子的加速度維持 +2 m/s²，因此圖線水平。\n3 秒內的長方形面積是 2 × 3 = 6 m/s，表示速度增加了 6 m/s。"),
        ],
        "反應距離與煞車距離": [
            ("lead", "以 72 km/h 行駛，反應時間 1 秒，煞車加速度 −5 m/s²。車頭會在哪裡停下？"),
            ("heading", "反應期間，車仍以原速前進"),
            ("formula", "反應距離 = 初速 × 反應時間"),
            ("body", "先換單位：72 ÷ 3.6 = 20 m/s。\n從看見行人到踩下煞車，車前進了 20 × 1 = 20 m。"),
            ("heading", "踩下煞車後，速度逐漸降到零"),
            ("formula", "煞車距離 = v₀² / (2b)"),
            ("body", "b 是煞車加速度的大小，這裡取 5 m/s²。\n在這段等減速運動中，車前進了 20² / (2 × 5) = 40 m。"),
            ("heading", "能否停在行人前？"),
            ("formula", "完整停車距離 = 反應距離 + 煞車距離 = 60 m"),
            ("body", "行人在 70 m：停車後仍相距 10 m。\n行人在 60 m：停下時，車頭剛好接觸行人。\n行人在 50 m：車頭接觸行人時，車仍在動。"),
            ("body", "維持反應時間和減速度，把初速加倍。反應距離會變成 2 倍，煞車距離會變成 4 倍。"),
        ],
    }
    buttons = {}
    figure = tk.Canvas(reader, bg=PAPER, height=94, highlightthickness=0, bd=0)
    selected = next(iter(topics))
    figure.bind("<Configure>", lambda _: draw_concept_figure(figure, selected, family))
    figure.bind("<MouseWheel>", lambda event: reader.event_generate("<MouseWheel>", delta=event.delta))

    def size_reader(event):
        # 寬視窗限制行長；小視窗把空間留給內文。
        margin = max(22, (event.width-820)//2)
        if reader.cget("padx") != margin:
            reader.configure(padx=margin)
        figure.configure(width=max(100, event.width-2*margin-6))

    def show(topic):
        nonlocal selected
        selected = topic
        reader.configure(state="normal")
        # Text 刪除嵌入視窗時也會銷毀該 widget，先解除嵌入再重用。
        if reader.window_names():
            reader.window_configure(str(figure), window="")
        reader.delete("1.0", "end")
        reader.insert("end", topic+"\n", "title")
        for tag, paragraph in topics[topic]:
            reader.insert("end", paragraph+"\n", tag)
            if tag == "lead":
                reader.window_create("end", window=figure, pady=4)
                reader.insert("end", "\n")
        draw_concept_figure(figure, topic, family)
        reader.configure(state="disabled")
        reader.yview_moveto(0)
        for name, button in buttons.items():
            button.configure(bg=DEEP_TEAL if name == topic else PAPER,
                             fg=WHITE if name == topic else INK,
                             activebackground=SEAFOAM, activeforeground=NAVY)

    reader.bind("<Configure>", size_reader)
    for topic in topics:
        button = tk.Button(menu, text=topic, bd=0, padx=12, pady=6, cursor="hand2",
                           font=(family, 11, "bold"), command=lambda name=topic: show(name))
        button.pack(side="left", padx=(0, 4))
        buttons[topic] = button
    show(selected)
    return page


def build_app(window):
    window.title("直線運動實驗室")
    window.geometry("1120x780")
    window.minsize(860, 630)
    style = ttk.Style(window)
    style.theme_use("clam")
    ui_family = tkfont.nametofont("TkDefaultFont").actual("family")
    for candidate in ("Microsoft JhengHei", "PingFang TC", "Noto Sans CJK TC"):
        if candidate in tkfont.families(window):
            ui_family = candidate
            break
    style.configure("TNotebook", background=NAVY, borderwidth=0, tabmargins=(10, 4, 0, 0))
    style.configure("TNotebook.Tab", font=(ui_family, 11, "bold"), padding=(16, 7),
                    background=NAVY, foreground=CREAM, borderwidth=0)
    style.map("TNotebook.Tab", background=[("selected", SEAFOAM), ("active", DEEP_TEAL)],
              foreground=[("selected", NAVY), ("active", WHITE)])
    style.configure("Section.TNotebook", background=PAPER, tabmargins=0)
    style.configure("Section.TNotebook.Tab", padding=(12, 4), font=(ui_family, 10, "bold"))
    style.map("Section.TNotebook.Tab", background=[("selected", DEEP_TEAL), ("!selected", BG)],
              foreground=[("selected", WHITE), ("!selected", MUTED)])
    style.configure("TEntry", fieldbackground=WHITE, bordercolor=GRID)
    style.configure("TScrollbar", background=GRID, troughcolor=PAPER, arrowsize=12)
    tabs = ttk.Notebook(window)
    tabs.pack(expand=True, fill="both")
    pages = []
    for title, page_type in (("直線運動", Lab), ("煞車距離", BrakeLab)):
        frame = tk.Frame(tabs)
        tabs.add(frame, text=title, padding=0)
        pages.append(page_type(frame))
    intro = add_concepts_page(tabs, pages[0].family)
    experiments = {str(page.root): page for page in pages}
    def switch_page(_):
        active = tabs.select()
        for frame, page in experiments.items():
            if frame != active:
                page.stop()
    def apply_current(_):
        experiment = experiments.get(tabs.select())
        if experiment is not None:
            experiment.apply()
    tabs.bind("<<NotebookTabChanged>>", switch_page)
    window.bind("<Return>", apply_current)
    tabs.select(intro)
    return tabs, pages


if __name__ == "__main__":
    window = tk.Tk()
    build_app(window)
    window.mainloop()
