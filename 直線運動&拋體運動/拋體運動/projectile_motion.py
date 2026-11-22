import math
import time
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont


INK = "#1a2332"
SLATE = "#3e606c"
PAPER = "#fcfefa"
BASE = "#e8f2f1"
RULE = "#b9d3d4"
TEAL = "#206d70"
SEAFOAM = "#a8dadc"
CREAM = "#f1faee"
UI = "Microsoft JhengHei UI"
MATH = "DejaVu Sans"


def set_theme(window):
    global UI, MATH
    available = set(tkfont.families(window))
    UI = next((f for f in ("Microsoft JhengHei UI", "PingFang TC", "Noto Sans CJK TC")
               if f in available), "TkDefaultFont")
    if MATH not in available:
        MATH = "Segoe UI" if "Segoe UI" in available else UI
    window.option_add("*Font", (UI, 10))
    style = ttk.Style(window)
    style.theme_use("clam")
    style.configure(".", font=(UI, 10), foreground=INK, background=BASE)
    style.configure("TNotebook", borderwidth=0, tabmargins=(0, 4, 0, 0))
    style.configure("TNotebook.Tab", padding=(15, 7), background=BASE, borderwidth=0)
    style.map("TNotebook.Tab", background=[("selected", INK), ("active", SEAFOAM)],
              foreground=[("selected", PAPER)])
    style.configure("TButton", padding=(9, 4), borderwidth=1, background=PAPER,
                    bordercolor=RULE, lightcolor=PAPER, darkcolor=PAPER)
    style.configure("Primary.TButton", background=INK, foreground=PAPER,
                    bordercolor=INK, lightcolor=INK, darkcolor=INK)
    style.map("Primary.TButton", background=[("active", SLATE)])
    style.configure("TEntry", padding=4, fieldbackground=PAPER)
    style.configure("TCombobox", padding=3, fieldbackground=PAPER)
    style.configure("Paper.TFrame", background=PAPER)
    style.configure("Muted.TLabel", foreground=SLATE)
    style.configure("Clock.TLabel", font=(MATH, 11, "bold"))


def reading_area(parent):
    frame = ttk.Frame(parent, style="Paper.TFrame")
    frame.pack(fill="both", expand=True)
    text = tk.Text(frame, width=1, height=1, wrap="char", relief="flat",
                   highlightthickness=0, bg=PAPER, fg=INK, padx=24, pady=14,
                   font=(UI, 12), spacing2=4, spacing3=3)
    scroll = ttk.Scrollbar(frame, command=text.yview)
    scroll.pack(side="right", fill="y")
    text.configure(yscrollcommand=scroll.set)
    text.pack(fill="both", expand=True)
    text.tag_configure("heading", font=(UI, 17, "bold"), spacing3=12)
    text.tag_configure("label", foreground=TEAL, font=(UI, 10, "bold"), spacing1=9)
    text.tag_configure("formula", font=(UI, 13, "bold"), background="#e3f1eb",
                       lmargin1=12, lmargin2=12, spacing1=3, spacing3=3)
    return text


def range_and_time(speed, g, angle):
    theta = math.radians(angle)
    flight_time = 2 * speed * math.sin(theta) / g
    distance = 0.0 if angle == 90 else speed * math.cos(theta) * flight_time
    return distance, flight_time


def target_lesson(x, y, g, known_speed, given):
    """每一張講解卡依序放標題、算式與物理意義。"""
    d = abs(x)
    steps = [f"先讀目標的位置\n水平距離 d = {d:g} m\n目標高度 y = {y:g} m\n\n球從地面出發。看紫色圓圈：球必須在同一時刻走完這段水平距離，也升到指定高度。"]
    if d == 0 and y == 0:
        steps.append("目標就在起點\nx(0) = 0，y(0) = 0\n\n出發的瞬間已經通過目標，因此無法用這個點決定唯一的初速或仰角。")
        if known_speed:
            return [(given, 0., 0.)], steps
        theta = math.radians(given)
        return [(0. if given == 90 else math.cos(theta), math.sin(theta), 0.)], steps

    if known_speed:
        v = given
        if d == 0:
            highest = v*v/(2*g)
            steps.append(f"往正上方拋\n仰角 = 90°\n最高高度 = 初速² ÷ (2 × g)\n= {v:g}² ÷ (2 × {g:g}) = {highest:.4g} m\n\n把最高高度和目標的 {y:g} m 比一比。")
            if y > highest and not math.isclose(y, highest, rel_tol=2e-14):
                steps.append(f"球還差多高？\n{y:g} − {highest:.4g} ≈ {y-highest:.4g} m\n\n把全部初速用在向上運動，仍然到不了紫色圈的高度。")
                return [], steps
            steps.append(f"何時通過這個高度？\n高度 = 向上初速 × 時間 − ½ × g × 時間²\n{y:g} = {v:g}t − {g/2:g}t²\n\n低於最高點時，球上升和下降各通過一次。")
        else:
            rmax = v*v/g
            ymax = (rmax-d)*(1+d/rmax)/2
            steps.append(f"先看水平方向\n水平速度 = {v:g} × cos θ\n抵達時間 t = {d:g} ÷ 水平速度\n\nθ 是朝目標拋出的仰角。水平速度愈小，走到同一個位置就要愈久。")
            steps.append(f"再看球有多高\n向上初速 = {v:g} × sin θ\n球高 = 向上初速 × t − {g/2:g} × t²\n\n第一項是球靠初速上升的高度；第二項是重力讓它少升的高度。")
            if d > rmax and not math.isclose(d,rmax,rel_tol=2e-14):
                steps.append(f"先落地，還是先到目標？\n最遠落點 = 初速² ÷ g\n= {v:g}² ÷ {g:g} = {rmax:.4g} m\n目標距離 = {d:g} m\n\n即使以 45° 拋到最遠，仍差 {d-rmax:.4g} m。綠色區域在目標前就結束了。")
                return [], steps
            steps.append(f"同一個位置，最高能到哪裡？\n最遠落點 R = 初速² ÷ g = {rmax:.4g} m\n綠色上界高度 = (R² − d²) ÷ (2R)\n在 d = {d:g} m 時約為 {ymax:.4g} m。\n\n這條界線把所有角度能到達的最高位置連起來。把它和目標高度 {y:g} m 比較。")
        s = v*v - g*y
        length = math.hypot(d, y)
        threshold = g*(y+length)
        delta = (v*v-threshold)*(s+g*length)
        tangent = math.isclose(v*v, threshold, rel_tol=2e-14)
        if tangent:
            delta = 0.0
        if delta < 0:
            steps.append(f"目標在上界外\n目標高度 − 可達高度 ≈ {y-ymax:.4g} m\n\n橘球示範在目標的水平位置升得最高的那條路徑。換其他角度也無法補足這段高度。")
            return [], steps
        denom = math.sqrt(s + math.sqrt(delta))
        times = [math.sqrt(2)*length/denom]
        if not tangent:
            times.append(math.sqrt(2)*denom/g)
        solutions = [(x/t, y/t + g*t/2, t) for t in times]
        if d:
            # 用高一的配方法連接高度與仰角，解題時不必解四次式。
            b = g*d*d/(2*v*v)
            steps.append(f"把角度換成斜率\n設 k = tan θ（向上速度 ÷ 水平速率）\n設 B = gd² ÷ (2v₀²) ≈ {b:.4g} m\n球高 = dk − B(1 + k²)\n\n這是把前面的時間代入高度式，再利用 1/cos²θ = 1 + tan²θ 得到的。")
            steps.append(f"用配方法找角度\n最高可達高度 − 目標高度\n= B × (k − d/(2B))²\n\nk = d/(2B) ± √[(最高可達高度 − y)/B]\n\n平方根為零時只有一個角度；大於零時得到兩種斜率。用計算機的反正切把斜率換回角度。")
    else:
        angle = given
        theta = math.radians(angle)
        if angle == 90:
            steps.append("看正上拋的路徑\n水平速度 = 0\nx(t) = 0\n\n不論拋得多快，球都沿著起點正上方的直線運動。")
            if d:
                steps.append(f"水平方向到不了\n球的水平位移 = 0 m\n目標的水平距離 = {d:g} m\n\n看綠色直線和紫色圈之間的水平距離。")
                return [], steps
            v = math.sqrt(2*g*y)
            steps.append(f"剛好碰到目標的最小初速\n在最高點，向上速度剛好變成 0。\nv₀ = √(2 × g × 高度)\n= √(2 × {g:g} × {y:g}) ≈ {v:.4g} m/s\n\n更大的初速也能通過此點，畫面示範最小值。")
            solutions = [(0., v, v/g)]
        else:
            straight = d*math.tan(theta)
            drop = straight-y
            steps.append(f"想像球沿直線前進\n直線高度 = 水平距離 × tan θ\n= {d:g} × tan({angle:g}°) ≈ {straight:.4g} m\n\n這是沒有重力時的路線。真實軌跡會往下彎。")
            if not d or drop <= 0 or math.isclose(straight,y,rel_tol=2e-15):
                reason = ("球只在出發時位於 x = 0，當時高度是 0 m。" if not d else
                          "從地面水平拋出，球在起點就接觸地面，空中飛行時間為零。" if angle == 0 else
                          "在相同水平位置，只要經過正的時間，球一定比起始方向線低。")
                steps.append(f"比較目標和方向線\n目標高度 = {y:g} m\n方向線高度 ≈ {straight:.4g} m\n\n{reason} 這個角度下沒有可行的有限初速。")
                return [], steps
            t = math.sqrt(2*drop/g)
            u = d/t
            w = u*math.tan(theta)
            steps.append(f"從下落量算時間\n下落量 = 直線高度 − 目標高度\n≈ {straight:.4g} − {y:g} = {drop:.4g} m\n\n下落量 = ½ × g × t²\nt = √(2 × 下落量 ÷ g) ≈ {t:.4g} s")
            steps.append(f"從時間算回初速\n水平速率 = 距離 ÷ 時間\n≈ {d:g} ÷ {t:.4g} = {u:.4g} m/s\n\n初速 = 水平速率 ÷ cos θ\n≈ {u:.4g} ÷ cos({angle:g}°) = {math.hypot(u,w):.4g} m/s")
            solutions = [(math.copysign(u,x), w, t)]
    for i, (vx, vy, t) in enumerate(solutions, 1):
        a = math.degrees(math.atan2(vy,abs(vx)))
        steps.append(f"用動畫驗算 · 路徑 {i}\n仰角 ≈ {a:.4g}°，初速 ≈ {math.hypot(vx,vy):.4g} m/s\n抵達時間 ≈ {t:.4g} s\n\n水平位置 = 水平速度 × 時間 ≈ {vx*t:.4g} m\n高度 = 向上初速 × 時間 − ½gt² ≈ {vy*t-g*t*t/2:.4g} m\n\n將時間軸拖到終點，小球應與紫色圈重合。")
    return solutions, steps


class ProjectileLab:
    """高中物理拋體運動模擬器。使用 Python 標準函式庫 Tkinter。"""

    HORIZONTAL = "#206d70"
    VERTICAL = "#334e73"
    GRID = "#dfe3e5"
    INK = INK

    def __init__(self, parent, mode=1):
        self.root = parent.winfo_toplevel()
        self.mode = mode
        self.target = None
        self.preview = None
        self.ready = False
        self.solutions = []
        self.steps = []

        self.t = 0.0
        self.timer = None
        self.running = False
        self.rate = 1.0
        self.fields = []

        settings = ttk.Frame(parent, padding=(12, 8))
        settings.pack(fill="x")
        if mode == 3:
            self.known = ttk.Combobox(settings, state="readonly", width=19,
                                     values=("已知初速，求仰角", "已知仰角，求初速"))
            self.known.current(0)
            self.known.grid(row=0, column=0, sticky="w", padx=(0, 8))
            self.known.bind("<<ComboboxSelected>>", self.switch_known)
        definitions = [
            ("觀察時間 T（s）", "3"),
            ("重力加速度大小 g（m/s²）", "10"),
            ("初速 v₀（m/s）", "20"),
            ("仰角 θ（°）", "30"),
        ]
        if mode == 2:
            definitions = definitions[1:]
        if mode == 3:
            definitions = [("目標 x（m）", "6"), ("目標 y（m）", "2"),
                           ("重力加速度大小 g（m/s²）", "10"), ("初速 v₀（m/s）", "10")]
        for column, (name, default) in enumerate(definitions, start=int(mode == 3)):
            settings.columnconfigure(column, weight=1)
            field_label = ttk.Label(settings, text=name)
            field_label.grid(row=0, column=column, sticky="w")
            value = tk.StringVar(value=default)
            entry = ttk.Entry(settings, textvariable=value, width=10)
            entry.grid(row=1, column=column, sticky="ew", padx=(0, 10))
            entry.bind("<Return>", lambda event: self.apply())
            self.fields.append(value)
        self.last_field_label = field_label
        ttk.Button(settings, text="套用並播放" if mode == 1 else "計算並播放",
                   style="Primary.TButton", command=self.apply).grid(row=1, column=column+1)

        body = ttk.Frame(parent)
        body.pack(fill="both", expand=True)
        plot_parent = self.build_lesson(body) if mode != 1 else body
        self.canvas = tk.Canvas(plot_parent, bg=PAPER, highlightthickness=0, width=1, height=1)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=4)
        self.canvas.bind("<Configure>", lambda event: self.draw())

        controls = ttk.Frame(parent, padding=8)
        controls.pack(fill="x")
        self.play_button = ttk.Button(controls, text="播放", style="Primary.TButton", command=self.toggle)
        self.play_button.pack(side="left")
        ttk.Button(controls, text="回到起點", command=self.reset).pack(
            side="left", padx=6
        )
        self.clock = ttk.Label(controls, width=17, style="Clock.TLabel")
        self.clock.pack(side="left")

        ttk.Label(controls, text="播放倍速").pack(side="left")
        self.rate_box = ttk.Combobox(
            controls, width=6, values=("0.25", "0.5", "1", "1.5", "2", "4", "8")
        )
        self.rate_box.set("1")
        self.rate_box.pack(side="left", padx=4)
        self.rate_box.bind("<<ComboboxSelected>>", self.change_rate)
        self.rate_box.bind("<Return>", self.change_rate)
        ttk.Button(controls, text="套用倍速", command=self.change_rate).pack(side="left")

        # 時間軸使用比例 0～1，再換算成這次實驗的秒數。
        self.progress = tk.DoubleVar(value=0)
        self.slider = ttk.Scale(
            controls, from_=0, to=1, variable=self.progress,
            orient="horizontal", command=self.seek
        )
        self.slider.pack(side="left", fill="x", expand=True, padx=8)
        self.slider.bind("<ButtonPress-1>", lambda event: self.pause())

        self.message = ttk.Label(parent, padding=(12, 0, 12, 7), style="Muted.TLabel")
        self.message.pack(fill="x")
        self.apply(autoplay=False)

    def apply(self, autoplay=True):
        """讀取參數，建立新實驗。角度從水平向右量起。"""
        self.pause()
        if self.mode != 1:
            self.calculate_lesson(autoplay)
            return
        limits = [
            ("觀察時間", 0.01, 600),
            ("重力加速度大小", 0.01, 100),
            ("初速", 0, 300),
            ("仰角", 0, 90),
        ]
        values = []
        for field, (name, minimum, maximum) in zip(self.fields, limits):
            try:
                value = float(field.get())
                if not minimum <= value <= maximum:
                    raise ValueError
            except ValueError:
                self.message.config(
                    text=f"請在「{name}」輸入 {minimum:g} 到 {maximum:g} 之間的數字。"
                )
                return
            values.append(value)

        self.duration, self.g, speed, angle = values
        theta = math.radians(angle)
        self.vx0 = 0.0 if angle == 90 else speed * math.cos(theta)
        self.vy0 = speed * math.sin(theta)

        # 從地面發射，落回同一高度時，飛行時間為 2 v₀y / g。
        self.landing = 2 * self.vy0 / self.g
        self.end = min(self.duration, self.landing)
        self.ready = True
        self.reset()
        if autoplay:
            self.play()

    def build_lesson(self, body):
        self.views = ttk.Notebook(body)
        self.views.pack(fill="both", expand=True, padx=10, pady=(0, 4))
        visual = ttk.Frame(self.views)
        lesson = ttk.Frame(self.views, padding=(0, 6, 0, 0))
        self.views.add(visual, text="觀察動畫")
        self.views.add(lesson, text="閱讀公式")

        if self.mode == 2:
            aside = ttk.Frame(visual, width=235, padding=(6, 12))
            aside.pack(side="right", fill="y")
            aside.pack_propagate(False)
            ttk.Label(aside, text="仰角關係圖", font=(UI, 12, "bold")).pack(anchor="w", pady=(0, 6))
            self.curves = tk.Canvas(aside, height=162, width=1, bg=PAPER, highlightthickness=0)
            self.curves.pack(fill="x")
            self.curves.bind("<Configure>", lambda event: self.draw_angle_curves())
        else:
            paths = ttk.Frame(visual, padding=(10, 4))
            paths.pack(fill="x")
            ttk.Label(paths, text="播放路徑").pack(side="left", padx=(0, 8))
            self.choice = ttk.Combobox(paths, state="readonly", width=32)
            self.choice.pack(side="left")
            self.choice.bind("<<ComboboxSelected>>", lambda event: self.use_solution(True))

        nav = ttk.Frame(lesson, padding=(17, 3, 12, 6))
        nav.pack(fill="x")
        self.step_title = ttk.Label(nav, style="Muted.TLabel")
        self.step_title.pack(side="left")
        self.next = ttk.Button(nav, text="下一步", command=lambda: self.step(1))
        self.next.pack(side="right")
        self.back = ttk.Button(nav, text="上一步", command=lambda: self.step(-1))
        self.back.pack(side="right", padx=6)
        self.step_text = reading_area(lesson)

        def pause_for_reading(event):
            if self.views.index("current") == 1:
                self.pause()
        self.views.bind("<<NotebookTabChanged>>", pause_for_reading)
        return visual

    def step(self, delta):
        self.step_index = max(0, min(self.step_index + delta, len(self.steps)-1))
        title, _, body = self.steps[self.step_index].partition("\n")
        self.step_text.configure(state="normal")
        self.step_text.delete("1.0", "end")
        self.step_text.insert("end", title+"\n", "heading")
        for line in body.splitlines():
            formula = any(symbol in line for symbol in ("=", "≈", "÷")) and not line.endswith("。")
            # 有語意的停頓用獨立行呈現，保留數字與單位在同一組算式中。
            lines = line.replace("。", "。\n").replace("；", "；\n").rstrip("\n")
            self.step_text.insert("end", lines+"\n", "formula" if formula else ())
        self.step_text.yview_moveto(0)
        self.step_text.configure(state="disabled")
        self.step_title.config(text=f"公式推導　{self.step_index+1} / {len(self.steps)}")
        self.back.state(["disabled" if self.step_index == 0 else "!disabled"])
        self.next.state(["disabled" if self.step_index == len(self.steps)-1 else "!disabled"])

    def switch_known(self, event=None):
        speed_mode = self.known.current() == 0
        self.last_field_label.config(text="初速 v₀（m/s）" if speed_mode else "仰角 θ（°）")
        self.fields[-1].set("10" if speed_mode else "45")
        self.apply(autoplay=False)

    def calculate_lesson(self, autoplay):
        speed_mode = self.mode == 3 and self.known.current() == 0
        limits = [("g", .01, 100), ("初速", .01, 300), ("仰角", 0, 90)]
        if self.mode == 3:
            limits = [("x", -10000, 10000), ("y", 0, 10000), ("g", .01, 100),
                      ("初速", .01, 300) if speed_mode else ("仰角", 0, 90)]
        values = []
        self.ready = False
        self.preview = None
        self.solutions = []
        self.target = None
        self.progress.set(0)
        self.clock.config(text="—")
        self.canvas.delete("all")
        if self.mode == 2:
            self.curves.delete("all")
        else:
            self.choice.set("")
            self.choice.configure(values=())
        self.step_index = 0
        for var, (name, lo, hi) in zip(self.fields, limits):
            try:
                v = float(var.get())
                if not lo <= v <= hi:
                    raise ValueError
            except ValueError:
                self.steps = [f"請在 {name} 欄輸入 {lo:g} 到 {hi:g} 的數字。"]
                self.step(0)
                self.message.config(text=self.steps[0])
                return
            values.append(v)
        if self.mode == 2:
            self.g, self.speed, self.angle = values
            distance, t = range_and_time(self.speed, self.g, self.angle)
            theta = math.radians(self.angle)
            u = 0 if self.angle == 90 else self.speed*math.cos(theta)
            w = self.speed*math.sin(theta)
            self.solutions = [(u, w, t)]
            self.steps = [
                f"把拋球動作拆成兩個方向\n水平速度 = 初速 × cos θ\n= {self.speed:g} × cos({self.angle:g}°) ≈ {u:.4g} m/s\n\n向上初速 = 初速 × sin θ\n= {self.speed:g} × sin({self.angle:g}°) ≈ {w:.4g} m/s",
                f"要多久才升到最高點？\n上升時間 = 向上初速 ÷ g\n≈ {w:.4g} ÷ {self.g:g} = {t/2:.4g} s\n\n重力每秒讓向上速度減少 {self.g:g} m/s。到最高點時，鉛直速度剛好為零。",
                f"從最高點回到地面\n飛行時間 T = 2 × 上升時間\n≈ 2 × {t/2:.4g} = {t:.4g} s\n\n忽略空氣阻力時，球落回發射高度所花的下降時間等於上升時間。",
                f"飛行期間，球水平移動多遠？\n射程 R = 水平速度 × 飛行時間\n≈ {u:.4g} × {t:.4g} = {distance:.4g} m\n\n水平方向沒有加速度，因此全程都能用「速度 × 時間」。",
                f"把兩張圖放在一起看\nT = 2v₀ sin θ ÷ g\nR = v₀² sin(2θ) ÷ g\n\n角度愈大，飛行時間愈長。射程在 45° 最長：這時 sin(2θ) = 1，射程為 {self.speed**2/self.g:.4g} m。",
                f"比較兩個加起來是 90° 的角度\n{self.angle:g}°：飛行 {t:.4g} s，射程 {distance:.4g} m\n{90-self.angle:g}°：飛行 {range_and_time(self.speed,self.g,90-self.angle)[1]:.4g} s，射程 {distance:.4g} m\n\n兩個不同的互餘角有相同射程。較高的弧線在空中停留較久。"
            ]
        else:
            x, y, self.g, given = values
            self.target = (x, y)
            self.solutions, self.steps = target_lesson(x, y, self.g, speed_mode, given)
            if self.solutions:
                labels = [f"解 {i}　{math.degrees(math.atan2(w, abs(u))):.4g}°　·　{t:.4g} s"
                          for i,(u,w,t) in enumerate(self.solutions, 1)]
                self.choice.configure(values=labels)
                self.choice.current(0)
            else:
                self.prepare_preview(speed_mode, given)
        self.step(0)
        if not self.solutions:
            self.ready = True
            self.reset()
            if autoplay:
                self.play()
            return
        self.use_solution(autoplay)

    def prepare_preview(self, known_speed, given):
        x, y = self.target
        d = abs(x)
        self.preview = "speed" if known_speed else "angle"
        self.given = given
        if known_speed:
            reach = given**2/self.g
            angle = 90 if d == 0 else (45 if d >= reach else math.degrees(math.atan2(reach,d)))
            speed = given
        else:
            angle = given
            # A representative ball speed; the shaded region covers all positive speeds.
            speed = math.sqrt(2*self.g*max(d, y, 1))
        theta = math.radians(angle)
        self.vx0 = 0.0 if angle == 90 else math.copysign(speed*math.cos(theta), x)
        self.vy0 = speed*math.sin(theta)
        self.landing = 2*self.vy0/self.g
        self.end = self.duration = self.landing if self.landing else 2.0
        example = f"示範：{angle:.4g}°，{speed:.4g} m/s"
        self.choice.set(example)
        self.choice.state(["disabled"])

    def use_solution(self, autoplay):
        self.pause()
        index = self.choice.current() if self.mode == 3 else 0
        self.vx0, self.vy0, self.end = self.solutions[index]
        self.landing = 2*self.vy0/self.g
        self.duration = self.end
        self.ready = True
        if self.mode == 3:
            self.choice.configure(state="readonly")
        self.reset()
        if self.mode == 2:
            self.draw_angle_curves()
        if autoplay:
            self.play()

    def draw_angle_curves(self):
        if not self.ready or self.curves.winfo_width() < 100:
            return
        c = self.curves
        c.delete("all")
        left, right = 40, c.winfo_width()-15
        for row, (name, maximum, color) in enumerate([
            ("水平射程 R（m）", self.speed**2/self.g, self.HORIZONTAL),
            ("飛行時間 T（s）", 2*self.speed/self.g, self.VERTICAL)
        ]):
            top, bottom = 25 + 80*row, 59 + 80*row
            c.create_text(7, top-14, anchor="w", text=name, fill=color)
            c.create_text(left-3, top, anchor="e", text=f"{maximum:.3g}")
            c.create_text(left-3, bottom, anchor="e", text="0")
            c.create_line(left,top,left,bottom,right,bottom,fill=self.INK)
            for deg in (0, 45, 90):
                xx = left+(right-left)*deg/90
                c.create_text(xx,bottom+10,text=f"{deg}°")
            def point(deg):
                value = range_and_time(self.speed,self.g,deg)[row]
                return left+(right-left)*deg/90, bottom-(bottom-top)*value/maximum
            c.create_line(*[point(deg) for deg in range(91)], fill=color, width=2)
            xx, yy = point(self.angle)
            c.create_oval(xx-4,yy-4,xx+4,yy+4,fill=color,outline="white")
            value = range_and_time(self.speed, self.g, self.angle)[row]
            unit = "m" if row == 0 else "s"
            c.create_text(right,top-14,anchor="e",
                          text=f"{self.angle:g}°  →  {value:.4g} {unit}")

    def state(self, t):
        """傳回同一時刻的 x、y、vx、vy、ax、ay。"""
        if self.preview and not self.landing:
            t = 0.0
        x = self.vx0 * t
        y = max(0.0, t * (self.vy0 - 0.5 * self.g * t))
        return x, y, self.vx0, self.vy0 - self.g * t, 0.0, -self.g

    def pause(self):
        self.running = False
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer = None
        self.play_button.config(text="播放")

    def reset(self):
        self.pause()
        self.show_time(0.0)

    def play(self):
        if self.mode != 1:
            self.views.select(0)
        if not self.ready or self.end == 0:
            return
        if self.t >= self.end:
            self.show_time(0.0)
        self.running = True
        self.play_button.config(text="暫停")
        self.last_tick = time.perf_counter()
        self.tick()

    def change_rate(self, event=None):
        try:
            rate = float(self.rate_box.get().strip())
            if not math.isfinite(rate) or rate <= 0:
                raise ValueError
        except ValueError:
            self.rate_box.set(str(self.rate))
            self.root.bell()
            self.message.config(text=f"倍速須為正數，目前使用 {self.rate:g} 倍。")
            return "break"
        if self.running:
            self.advance_clock()  # 切換前的這段時間仍使用原倍率。
            if self.t >= self.end:
                self.pause()
        self.rate = rate
        return "break"  # 避免輸入倍率後按 Enter 觸發重新發射。

    def advance_clock(self):
        now = time.perf_counter()
        elapsed = now - self.last_tick
        self.last_tick = now
        self.show_time(min(self.t + elapsed * self.rate, self.end))

    def toggle(self):
        if self.running:
            self.pause()
        else:
            self.play()

    def tick(self):
        self.timer = None
        self.advance_clock()
        if self.t >= self.end:
            self.pause()
        else:
            self.timer = self.root.after(25, self.tick)

    def seek(self, fraction):
        if not self.ready:
            return
        self.pause()
        self.show_time(float(fraction) * self.end)

    def show_time(self, t):
        if not self.ready:
            return
        self.t = t
        self.progress.set(t / self.end if self.end else 0)
        self.clock.config(text=f"{t:.2f} / {self.end:.2f} s")

        if self.preview:
            if not self.landing:
                text = "無解｜地面水平拋的飛行時間是 0 s。下方時間軸控制觀察動畫，綠色脈動圓標出唯一可達點。"
                self.clock.config(text=f"觀察 {t:.2f} / {self.end:.2f} s")
            elif self.preview == "speed":
                text = "無解｜淺綠色是這個初速朝目標側可到達的範圍。橘球示範其中一條路徑，紫色圈是目標。"
            elif self.given == 90:
                text = "無解｜固定 90° 時，所有初速的路徑都在綠色鉛直線上。紫色目標在旁邊。"
            else:
                text = "無解｜固定仰角時，可達範圍在淺綠區內。綠色虛線是起始方向，離開起點後無法碰到這條線。"
        elif self.mode == 3 and t >= self.end:
            text = f"小球通過目標（{self.target[0]:g}, {self.target[1]:g}）m，抵達時間 {self.end:.3g} s。"
        elif self.end == 0:
            text = "球從地面出發，鉛直初速為零，飛行時間為 0 秒。"
        elif t >= self.landing:
            text = "球已落地。圖中顯示碰到地面前一瞬間的速度與加速度。"
        elif t >= self.duration:
            text = "已達設定的觀察時間，球仍在空中。"
        else:
            text = "向右、向上為正方向，忽略空氣阻力。可拖曳時間軸觀察任一時刻。"
        self.message.config(text=text)
        self.draw()

    def text(self, x, y, content, anchor="w", color=None, size=10):
        self.canvas.create_text(
            x, y, text=content, anchor=anchor, fill=color or self.INK,
            font=(UI, size, "bold" if size >= 11 else "normal")
        )

    def draw(self):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width < 100 or height < 100 or not self.ready:
            return

        self.canvas.delete("all")
        split = int(height * 0.58)

        # 所有畫面共用 self.t，同步暫停、播放與倒帶。
        samples = []
        for i in range(101):
            t = self.t * (i / 100)
            samples.append((t, self.state(t)))

        self.draw_trajectory(width, split, samples)
        if self.preview and not self.landing:
            self.text(18, split+28, "為什麼球停在起點？", size=13)
            self.text(18, split+64, "從地面以 0° 拋出時，向上初速是 0 m/s。")
            self.text(18, split+94, "球在 t = 0 s 就已觸地。綠圈標出在地面以上或地面上可達的位置。")
            return
        for index, (title, unit) in enumerate([
            ("位置", "m"), ("速度", "m/s"), ("加速度", "m/s²")
        ]):
            self.draw_graph(
                index, title, unit, index * width / 3, split + 8,
                width / 3, height - split - 8, samples
            )

    def draw_trajectory(self, width, height, samples):
        c = self.canvas
        self.text(15, 17, "球的運行軌跡", size=13)
        self.text(width - 15, 17, "綠色：可達範圍　紫圈：目標　橘球：示範" if self.preview
                  else "虛線：預測軌跡　實線：已走過的軌跡", "e", size=9)
        self.text(12, 42, "高度 y（m）")

        left, right = 60, width - 30
        top, bottom = 58, height - 38
        peak_time = min(self.end, self.vy0 / self.g)
        peak = self.state(peak_time)[1]
        distance = self.state(self.end)[0]

        # 空間圖的水平與鉛直方向使用相同的公尺比例，保留拋射角度。
        span = abs(distance)
        if self.preview:
            span = max(span, abs(self.target[0]))
            peak = max(peak, self.target[1])
            if self.preview == "speed":
                span = max(span, self.given**2/self.g)
                peak = max(peak, self.given**2/(2*self.g))
        scales = []
        if span:
            scales.append((right - left) / max(span, 1e-12))
        if peak > 0:
            scales.append((bottom - top) / max(peak, 1e-12))
        scale = min(scales) * 0.93 if scales else 50

        sign = -1 if (self.target[0] if self.target else distance) < 0 else 1
        origin = right if sign < 0 else left

        def point(state):
            return origin + state[0] * scale, bottom - state[1] * scale

        if self.preview:
            self.draw_region(point, sign, (right-left)/scale, (bottom-top)/scale)

        for i in range(5):
            x = left + (right - left) * i / 4
            y = bottom - (bottom - top) * i / 4
            c.create_line(x, top, x, bottom, fill=self.GRID, dash=(2, 4))
            c.create_line(left, y, right, y, fill=self.GRID, dash=(2, 4))
            self.text(x, bottom + 3, f"{(x-origin)/scale:.3g}", "n", size=9)
            self.text(left - 6, y, f"{(bottom-y)/scale:.3g}", "e", size=9)

        c.create_line(origin, top, origin, bottom, fill=self.INK)
        c.create_line(left, bottom, right, bottom, fill=self.INK)
        self.text(right, bottom + 22, "水平位置 x（m）", "e", size=9)

        if self.end > 0:
            predicted = [
                point(self.state(self.end * (i / 100))) for i in range(101)
            ]
            c.create_line(*predicted, fill="#9aafab", width=2, dash=(4, 5))
        if self.t > 0:
            c.create_line(
                *[point(state) for _, state in samples],
                fill=self.HORIZONTAL, width=3
            )

        x, y = point(self.state(self.t))
        if self.target:
            tx, ty = point(self.target)
            c.create_oval(tx-11, ty-11, tx+11, ty+11, outline="#8c4d96", width=3)
            self.text(tx, ty+13 if ty+35 < bottom else ty-18, "目標", "center",
                      color="#74347e", size=9)
        r = 8
        c.create_oval(x-r, y-r, x+r, y+r, fill="#f2a451", outline="#794324")
        c.create_line(x-r, y, x+r, y, fill="#794324")
        c.create_line(x-2, y-r, x+4, y, x-2, y+r, smooth=True, fill="#794324")
        anchor = "e" if x > width - 120 else "w"
        self.text(x - 12 if anchor == "e" else x + 12, y - 12,
                  f"t = {0 if self.preview and not self.landing else self.t:.2f} s", anchor)

    def draw_region(self, point, sign, xmax, ymax):
        c = self.canvas
        origin = point((0, 0))
        fill, edge = "#d4eee1", "#368366"
        if self.preview == "speed":
            reach = self.given**2/self.g
            boundary = []
            for i in range(101):
                f = i/100
                boundary.append(point((sign*reach*f, reach*(1-f*f)/2)))
            c.create_polygon(origin, *boundary, fill=fill, outline="", tags="region")
            c.create_line(*boundary, fill=edge, width=2, tags="region")
        elif self.given == 90:
            c.create_line(origin, point((0, ymax)), fill=edge, width=6,
                          arrow="last", tags="region")
        elif self.given == 0:
            x, y = origin
            radius = 10 + 7*abs(math.sin(math.pi*self.t/self.end))
            c.create_oval(x-radius,y-radius,x+radius,y+radius, outline=edge,
                          width=2, tags="region")
        else:
            slope = math.tan(math.radians(self.given))
            dx = min(xmax, ymax/slope)
            tip = point((sign*dx, min(ymax, dx*slope)))
            outer = point((sign*xmax, min(ymax, xmax*slope)))
            c.create_polygon(origin, tip, outer, point((sign*xmax, 0)), fill=fill,
                             outline="", tags="region")
            c.create_line(origin, tip, fill=edge, dash=(5,4), width=2, tags="region")

    def draw_graph(self, index, title, unit, x0, y0, width, height, samples):
        c = self.canvas
        left, right = x0 + 48, x0 + width - 18
        top, bottom = y0 + 54, y0 + height - 36
        component = 2 * index
        current = self.state(self.t)

        self.text(x0 + 12, y0 + 8, f"{title}－時間圖（{unit}）", size=11)
        self.text(x0 + 12, y0 + 32, f"━ 水平 {current[component]:.2f}",
                  color=self.HORIZONTAL, size=9)
        self.text(x0 + width / 2, y0 + 32, f"┄ 鉛直 {current[component+1]:.2f}",
                  color=self.VERTICAL, size=9)

        # 固定整次實驗的圖表範圍，讓播放時的曲線斜率可以直接比較。
        values = [0.0]
        for t in (0, min(self.end, self.vy0 / self.g), self.end):
            values.extend(self.state(t)[component:component + 2])
        lo, hi = min(values), max(values)
        padding = max((hi - lo) * 0.1, 1e-12) if hi > lo else 1.0
        lo, hi = lo - padding, hi + padding
        time_range = self.end or self.duration or 1.0

        def px(t):
            return left + (t / time_range) * (right - left)

        def py(value):
            return bottom - ((value - lo) / (hi - lo)) * (bottom - top)

        for i in range(5):
            t = time_range * (i / 4)
            x = px(t)
            c.create_line(x, top, x, bottom, fill=self.GRID, dash=(2, 4))
            self.text(x, bottom + 3, f"{t:.2g}", "n", size=8)

        for value in sorted({min(values), 0.0, max(values)}):
            y = py(value)
            c.create_line(left, y, right, y,
                          fill="#94aaa8" if value == 0 else self.GRID)
            self.text(left - 5, y, f"{value:.3g}", "e", size=8)

        self.text(right, bottom + 21, "時間 t（s）", "e", size=9)
        x = px(self.t)
        c.create_line(x, top, x, bottom, fill="#788c8d", dash=(3, 3))

        for offset, color in enumerate((self.HORIZONTAL, self.VERTICAL)):
            j = component + offset
            if self.t > 0:
                curve = [(px(t), py(state[j])) for t, state in samples]
                c.create_line(*curve, fill=color, width=2, dash=(5, 3) if offset else ())
            y = py(current[j])
            c.create_oval(x-3, y-3, x+3, y+3, fill=color, outline=color)

    def close(self):
        self.pause()
        self.root.destroy()


def concept_sketch(canvas, topic):
    """同一組課堂參數的向量與曲線示意。"""
    canvas.delete("all")
    w = canvas.winfo_width()
    if w < 60:
        return
    fg, accent = INK, ProjectileLab.VERTICAL
    x0, y0 = 18, 98
    def label(x, y, text, anchor="center", color=INK):
        canvas.create_text(x, y, text=text, anchor=anchor, fill=color, font=(UI, 9))
    if topic == 0:
        dx = min(w-55, 117)
        dy = dx*math.tan(math.radians(30))
        canvas.create_line(x0,y0,x0+dx,y0,fill=fg,width=2,arrow="last")
        canvas.create_line(x0+dx,y0,x0+dx,y0-dy,fill=accent,width=2,arrow="last")
        canvas.create_line(x0,y0,x0+dx,y0-dy,fill=fg,width=2,arrow="last")
        label(x0+dx/2, y0+13, "水平 17.32 m/s")
        label(x0+dx+6, y0-dy/2, "10 m/s", "w", accent)
        label(x0+dx/2-10, y0-dy/2-14, "20 m/s")
        return
    left, right = 14, w-15
    canvas.create_line(left, y0, right, y0, fill=RULE)
    if topic == 2:
        mid = (left+right)/2
        canvas.create_line(left,55,right,55,fill=RULE)
        canvas.create_line(left,19,right,91,fill=accent,width=2)
        canvas.create_oval(mid-3,52,mid+3,58,fill=accent,outline="")
        label(left+2,6,"鉛直速度 vᵧ","w")
        label(mid+4,40,"1 s · 速度為零")
        label(right,111,"時間 t","e")
        return
    angles = [30,60] if topic == 3 else [30]
    scale = min((right-left)/(20**2*math.sin(math.radians(60))/10), 76/(15 if topic==3 else 5))
    for angle in angles:
        u = 20*math.cos(math.radians(angle))
        v = 20*math.sin(math.radians(angle))
        points = []
        for i in range(61):
            t = 2*v/10*i/60
            points.append((left+u*t*scale, y0-(v*t-5*t*t)*scale))
        canvas.create_line(*points, fill=accent if angle==60 else fg, width=2)
        ax, ay = points[30]
        if topic == 3:
            label(ax,ay-10,f"{angle}°")
        else:
            canvas.create_oval(ax-4,ay-4,ax+4,ay+4,outline=accent,width=2)
            label(ax,ay-14,"1 s · 高 5 m" if topic==1 else "指定位置")
    label(left,y0+14,"起點","w")
    label(points[-1][0],y0+14,"落地","e")


def build_basics(parent):
    topics = [
        ("初速與方向", "斜拋的球，同時往哪兩個方向運動？", [
            ("先看運動", "球向右移動的同時，也會先上升、再下降。\n兩個方向共用同一個時間 t。"),
            ("初速分量", "uₓ = v₀ cos θ　　　uᵧ = v₀ sin θ"),
            ("讀懂符號", "v₀ 是出手速率，θ 是出手方向與水平線的夾角。\nuₓ 代表水平初速，uᵧ 代表鉛直初速，兩者單位都是 m/s。"),
            ("代入範例", "向右上方以 30° 拋出時，水平初速約為 17.32 m/s，鉛直初速為 10 m/s。\n把仰角改成 90°，水平初速變為零，球就會直上直下。"),
        ]),
        ("位置、速度與加速度", "經過 t 秒，球在哪裡？速度指向哪裡？", [
            ("先定方向", "以出手點為原點，向右、向上為正。\n球離手後只受重力。g 表示重力加速度的大小，地表附近約為 9.8 m/s²。"),
            ("加速度 · m/s²", "aₓ = 0　　　aᵧ = −g"),
            ("速度 · m/s", "vₓ = uₓ　　　vᵧ = uᵧ − gt"),
            ("位置 · m", "x = uₓt　　　y = uᵧt − ½gt²"),
            ("在最高點", "上升時間 = uᵧ / g　　　最大高度 = uᵧ² / (2g)\n在範例的第 1 秒，球升到 5 m，鉛直速度恰為零。\n水平速度仍約為 17.32 m/s，重力加速度仍向下。"),
        ]),
        ("讀懂三張時間圖", "如何從圖上認出最高點？", [
            ("辨認橫軸", "軌跡圖的橫軸是水平位置 x。\n三張運動圖的橫軸都是時間 t，可用同一時刻對照讀值。"),
            ("位置－時間圖", "位置曲線的斜率代表速度。\n水平位置等量增加；高度曲線在最高點的切線是水平的。"),
            ("速度－時間圖", "速度曲線的斜率代表加速度。\n鉛直速度從正值穿過零、變為負值時，球由上升轉為下降。"),
            ("加速度－時間圖", "aₓ = 0，aᵧ = −g，兩條線全程維持水平。\n球經過最高點時，加速度也維持原值。"),
            ("暫停觀察", "在第 1.00 秒暫停：球位於最高處，高度曲線達到峰值，鉛直速度線穿過零。"),
        ]),
        ("仰角、飛行時間與射程", "拋得愈高，就一定飛得愈遠嗎？", [
            ("比較條件", "球落回出手高度。比較不同仰角時，固定初速與 g。"),
            ("飛行時間 · s", "T = 2uᵧ / g = 2v₀ sin θ / g"),
            ("看時間", "T 是出手到落地的總時間。\n仰角從 0° 增加到 90°，向上初速愈大，球留在空中的時間愈長。"),
            ("水平射程 · m", "R = uₓT = v₀² sin(2θ) / g"),
            ("看距離", "射程先增加，在 45° 達到最大，再逐漸減少。\n30° 和 60° 的射程同為 34.64 m，但飛行時間分別約為 2.00 s 與 3.46 s。"),
        ]),
        ("通過指定位置", "球到達指定水平位置時，有多高？", [
            ("先讀座標", "目標 (X, Y) 的 X 是水平位置，Y 是高度。\n在同一時刻同時滿足 x = X 和 y = Y，軌跡才會通過目標。"),
            ("先找時間", "t = X / uₓ　（uₓ ≠ 0）"),
            ("再檢查高度", "y = uᵧt − ½gt²"),
            ("檢查結果", "先確認 t 介於出手和落地之間，再把球高與 Y 比較。\n若水平初速等於零，球始終位於起點的正上方或起點。"),
            ("代入範例", "出手後 1 秒，水平位置約為 17.32 m，高度為 5 m。\n軌跡會通過約 (17.32, 5) m 的位置。"),
            ("可達範圍", "固定初速或仰角後，綠色標出可到達的範圍。\n若紫色圈在範圍外，在這項固定條件下就無法通過。"),
        ]),
    ]
    panel = ttk.Frame(parent, padding=(12, 10))
    panel.pack(fill="both", expand=True)
    rail = tk.Frame(panel, width=226, bg=INK, padx=10, pady=12)
    rail.pack(side="left", fill="y", padx=(0, 10))
    rail.pack_propagate(False)
    tk.Label(rail, text="學習主題", bg=INK, fg=SEAFOAM,
             font=(UI, 10, "bold")).pack(anchor="w", padx=6, pady=(0, 8))
    buttons = []
    current = 0
    article = reading_area(panel)

    def display(index):
        nonlocal current
        current = index
        for i, button in enumerate(buttons):
            button.configure(bg=SEAFOAM if i==index else INK,
                             fg=INK if i==index else CREAM)
        _, title, sections = topics[index]
        article.configure(state="normal")
        article.delete("1.0", "end")
        article.insert("end", title+"\n", "heading")
        for heading, paragraph in sections:
            article.insert("end", heading+"\n", "label")
            for line in paragraph.splitlines():
                is_formula = "=" in line and not line.endswith("。")
                article.insert("end", line+"\n", "formula" if is_formula else ())
        article.yview_moveto(0)
        article.configure(state="disabled")
        concept_sketch(sketch, index)

    for i, (name, _, _) in enumerate(topics):
        button = tk.Button(rail, text=name, command=lambda index=i: display(index),
                           anchor="w", relief="flat", bd=0, padx=9, pady=6,
                           font=(UI, 11), cursor="hand2", activebackground=RULE)
        button.pack(fill="x", pady=1)
        buttons.append(button)
    ttk.Separator(rail).pack(fill="x", pady=(17, 9))
    tk.Label(rail, text="範例條件", fg=SEAFOAM, bg=INK, font=(UI,10,"bold")).pack(anchor="w")
    tk.Label(rail, text="初速 20 m/s　仰角 30°\ng = 10 m/s²，忽略空氣阻力",
             justify="left", fg=CREAM, bg=INK, font=(UI,10)).pack(anchor="w",pady=4)
    sketch = tk.Canvas(rail, width=1, height=125, bg=PAPER, highlightthickness=0)
    sketch.pack(fill="x", pady=4)
    sketch.bind("<Configure>", lambda event: concept_sketch(sketch, current))
    display(0)


def build_app(window):
    window.title("高中物理實驗室｜拋體運動")
    set_theme(window)
    window.geometry(f"{min(1220, window.winfo_screenwidth()-30)}x{min(800,window.winfo_screenheight()-80)}")
    window.minsize(960, 610)
    mast = tk.Frame(window, bg=INK, padx=20, pady=6)
    mast.pack(fill="x")
    tk.Label(mast, text="拋體運動實驗室", bg=INK, fg=CREAM,
             font=(UI, 16, "bold")).pack(side="left")
    tk.Label(mast, text="高中物理  /  運動學", bg=INK, fg=SEAFOAM,
             font=(UI, 10)).pack(side="right")
    book = ttk.Notebook(window)
    book.pack(fill="both", expand=True)
    basics = ttk.Frame(book)
    book.add(basics, text="基礎公式與概念")
    build_basics(basics)
    pages = []
    for mode, title in enumerate(("拋體運動", "飛行距離、時間與仰角", "命中目標"), 1):
        frame = ttk.Frame(book)
        book.add(frame, text=title)
        pages.append(ProjectileLab(frame, mode))

    def tab_changed(event):
        active = book.index("current")
        for i, page in enumerate(pages, start=1):
            if i != active:
                page.pause()

    book.bind("<<NotebookTabChanged>>", tab_changed)
    return book, pages


if __name__ == "__main__":
    window = tk.Tk()
    build_app(window)
    window.mainloop()
