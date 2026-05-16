#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生活规划本 - Life Planner Desktop App"""

import tkinter as tk
from tkinter import messagebox, ttk
import tkinter.font as tkfont
import json, os, math, uuid
from datetime import datetime, date, timedelta
import calendar as cal_mod
import time as time_mod

# ================================================================
# DATA FILE
# ================================================================
_onedrive = os.environ.get("OneDriveConsumer") or os.environ.get("OneDrive")
DATA_FILE = os.path.join(_onedrive, "lifeplanner_data.json") if _onedrive else \
            os.path.join(os.path.expanduser("~"), "Documents", "lifeplanner_data.json")

# ================================================================
# THEME COLORS
# ================================================================
BG      = "#FFF8EE"
CARD    = "#FFFFFF"
TOOLBAR = "#FFF0DC"
ACCENT  = "#FFD166"
ACCENT2 = "#FFC23A"
PINK    = "#FFDCE8"
PINK2   = "#FFB3C6"
PINK3   = "#FF6A9F"
GREEN   = "#C8F5DC"
GREEN2  = "#96E6B3"
BLUE    = "#DCF0FF"
BLUE2   = "#74B9FF"
LAV     = "#EDE0FF"
TEXT    = "#5A4040"
TEXTG   = "#9A8878"
TEXTL   = "#C0B0A8"
URGENT  = "#FF6B6B"
IMPRT   = "#FFA07A"
NORMAL  = "#74B9FF"
BORDER  = "#F0E0D0"

PRIO_ORDER  = {"u": 0, "i": 1, "n": 2}
PRIO_COLOR  = {"u": URGENT, "i": IMPRT, "n": NORMAL}
PRIO_BG     = {"u": "#FFF0F0", "i": "#FFF5EE", "n": "#F0F5FF"}
PRIO_LABEL  = {"u": "🔴 紧急", "i": "🟠 重要", "n": "🔵 不重要"}
PRIO_BADGE  = {"u": "#FFE0E0", "i": "#FFE8D8", "n": "#E0EEFF"}

WEEKDAY_CN = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

# ================================================================
# DATA MANAGEMENT
# ================================================================
def _load():
    if not os.path.exists(DATA_FILE):
        return {"tasks": {}, "countdowns": [], "weight": [], "summaries": {}, "thoughts": [], "finance": [], "focus": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            for k in ("tasks", "summaries"):
                if k not in d: d[k] = {}
            for k in ("countdowns", "weight", "thoughts", "finance", "focus"):
                if k not in d: d[k] = []
            return d
    except:
        return {"tasks": {}, "countdowns": [], "weight": [], "summaries": {}, "thoughts": [], "finance": [], "focus": []}

def _save(d):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def dk(d):
    if isinstance(d, str): return d
    return d.strftime("%Y-%m-%d")

def today_key(): return dk(date.today())

# ─── TASKS ───────────────────────────────────────────────────────
def task_add(date_key, name, desc, pri):
    d = _load()
    if date_key not in d["tasks"]: d["tasks"][date_key] = []
    d["tasks"][date_key].append({"id": uuid.uuid4().hex[:8], "name": name,
                                   "desc": desc, "pri": pri, "done": False})
    _save(d)

def task_toggle(date_key, tid):
    d = _load()
    for t in d["tasks"].get(date_key, []):
        if t["id"] == tid: t["done"] = not t["done"]
    _save(d)

def task_del(date_key, tid):
    d = _load()
    d["tasks"][date_key] = [t for t in d["tasks"].get(date_key, []) if t["id"] != tid]
    _save(d)

def tasks_for(date_key):
    return list(_load()["tasks"].get(date_key, []))

def task_edit(date_key, tid, name, desc, pri):
    d = _load()
    for t in d["tasks"].get(date_key, []):
        if t["id"] == tid:
            t["name"] = name; t["desc"] = desc; t["pri"] = pri
    _save(d)

def cd_edit(cid, name, date_str, rep):
    d = _load()
    for c in d["countdowns"]:
        if c["id"] == cid:
            c["name"] = name; c["date"] = date_str; c["rep"] = rep
    _save(d)

def tasks_in_range(sk, ek):
    res = []
    for k, ts in _load()["tasks"].items():
        if sk <= k <= ek: res.extend(ts)
    return res

# ─── COUNTDOWNS ──────────────────────────────────────────────────
def cd_add(name, date_str, rep):
    d = _load()
    d["countdowns"].append({"id": uuid.uuid4().hex[:8], "name": name, "date": date_str, "rep": rep})
    _save(d)

def cd_del(cid):
    d = _load(); d["countdowns"] = [c for c in d["countdowns"] if c["id"] != cid]; _save(d)

def cd_cleanup():
    d = _load(); today = date.today()
    before = len(d["countdowns"])
    d["countdowns"] = [
        c for c in d["countdowns"]
        if c.get("rep", "none") != "none" or date.fromisoformat(c["date"]) >= today
    ]
    if len(d["countdowns"]) != before: _save(d)

def cd_next_date(c):
    today = date.today()
    orig = date.fromisoformat(c["date"])
    if c["rep"] == "none": return orig
    if c["rep"] == "daily":  return today
    if c["rep"] == "yearly":
        try: nd = date(today.year, orig.month, orig.day)
        except ValueError: nd = date(today.year, orig.month, 28)
        if nd < today: nd = nd.replace(year=nd.year + 1)
        return nd
    if c["rep"] == "monthly":
        try: nd = date(today.year, today.month, orig.day)
        except ValueError: nd = (date(today.year, today.month + 1, 1) - timedelta(1))
        if nd < today:
            m = today.month % 12 + 1; y = today.year + (1 if today.month == 12 else 0)
            try: nd = date(y, m, orig.day)
            except ValueError: nd = date(y, m + 1, 1) - timedelta(1)
        return nd
    return orig

def cd_days(c):
    return (cd_next_date(c) - date.today()).days

def cd_dates_in_month(year, month):
    s = set()
    for c in _load()["countdowns"]:
        if c["rep"] == "daily":
            for i in range(1, 32): s.add(i)
        elif c["rep"] == "yearly":
            o = date.fromisoformat(c["date"])
            if o.month == month: s.add(o.day)
        elif c["rep"] == "monthly":
            o = date.fromisoformat(c["date"])
            mx = cal_mod.monthrange(year, month)[1]
            if o.day <= mx: s.add(o.day)
        else:
            o = date.fromisoformat(c["date"])
            if o.year == year and o.month == month: s.add(o.day)
    return s

# ─── THOUGHTS (胡思乱想) ─────────────────────────────────────────
def period_label(type_, period):
    if type_ == "year":  return f"{period}年"
    if type_ == "month":
        p = period.split("-")
        return f"{p[0]}年{int(p[1])}月"
    if type_ == "week":
        p = period.split("-W")
        return f"{p[0]}年第{int(p[1])}周"
    return period

def thought_add(type_, period, content):
    d = _load()
    d["thoughts"].append({"id": uuid.uuid4().hex[:8], "type": type_,
                           "period": period, "content": content,
                           "created": datetime.now().strftime("%Y-%m-%d %H:%M")})
    _save(d)

def thought_edit(tid, type_, period, content):
    d = _load()
    for t in d["thoughts"]:
        if t["id"] == tid:
            t["type"] = type_; t["period"] = period; t["content"] = content
    _save(d)

def thought_del(tid):
    d = _load()
    d["thoughts"] = [t for t in d["thoughts"] if t["id"] != tid]
    _save(d)

def thoughts_by_type(type_):
    return [t for t in _load()["thoughts"] if t["type"] == type_]

# ─── FINANCE (记账) ─────────────────────────────────────────
FINANCE_INCOME_CATS  = ["工资", "其他"]
FINANCE_EXPENSE_CATS = ["饮食", "娱乐", "人情", "生活", "服饰", "其他"]

def finance_add(ftype, category, amount, date_str, note):
    d = _load()
    d["finance"].append({"id": uuid.uuid4().hex[:8], "ftype": ftype,
                          "category": category, "amount": float(amount),
                          "date": date_str, "note": note})
    _save(d)

def finance_del(fid):
    d = _load(); d["finance"] = [f for f in d["finance"] if f["id"] != fid]; _save(d)

def finance_edit(fid, ftype, category, amount, date_str, note):
    d = _load()
    for f in d["finance"]:
        if f["id"] == fid:
            f["ftype"] = ftype; f["category"] = category
            f["amount"] = float(amount); f["date"] = date_str; f["note"] = note
    _save(d)

def finance_all():
    return list(_load()["finance"])

def finance_in_range(start_key, end_key):
    return [f for f in _load()["finance"] if start_key <= f["date"] <= end_key]

def finance_for_month(year, month):
    prefix = f"{year}-{month:02d}"
    return [f for f in _load()["finance"] if f["date"].startswith(prefix)]

# ─── WEIGHT ──────────────────────────────────────────────────────
def weight_add(w, ws):
    d = _load(); key = today_key()
    idx = next((i for i, e in enumerate(d["weight"]) if e["date"] == key), -1)
    if idx >= 0:
        if w is not None:  d["weight"][idx]["w"]  = w
        if ws is not None: d["weight"][idx]["ws"] = ws
    else:
        d["weight"].append({"date": key, "w": w, "ws": ws})
    d["weight"].sort(key=lambda e: e["date"]); _save(d)

def weight_del(date_key):
    d = _load()
    d["weight"] = [e for e in d["weight"] if e["date"] != date_key]
    _save(d)

def weight_update(date_key, w, ws):
    d = _load()
    idx = next((i for i, e in enumerate(d["weight"]) if e["date"] == date_key), -1)
    if idx >= 0:
        if w is not None: d["weight"][idx]["w"] = w
        if ws is not None: d["weight"][idx]["ws"] = ws
    _save(d)

def weight_latest():
    d = _load(); return d["weight"][-1] if d["weight"] else None

def weight_for_week(monday):
    d = _load(); res = []
    for i in range(7):
        key = dk(monday + timedelta(i))
        e = next((x for x in d["weight"] if x["date"] == key), None)
        res.append({"w": e["w"] if e and "w" in e else None,
                    "ws": e["ws"] if e and "ws" in e else None})
    return res

def weight_for_month(year, month):
    d = _load(); res = []
    for day in range(1, cal_mod.monthrange(year, month)[1] + 1):
        key = f"{year}-{month:02d}-{day:02d}"
        e = next((x for x in d["weight"] if x["date"] == key), None)
        res.append({"label": str(day), "w": e["w"] if e and "w" in e else None,
                    "ws": e["ws"] if e and "ws" in e else None})
    return res

def weight_for_year(year):
    d = _load(); res = []
    mnames = ["1月","2月","3月","4月","5月","6月","7月","8月","9月","10月","11月","12月"]
    for m in range(1, 13):
        es = [e for e in d["weight"] if e["date"].startswith(f"{year}-{m:02d}")]
        ws = [e["w"] for e in es if e.get("w") is not None]
        wss = [e["ws"] for e in es if e.get("ws") is not None]
        res.append({"label": mnames[m-1],
                    "w": sum(ws)/len(ws) if ws else None,
                    "ws": sum(wss)/len(wss) if wss else None})
    return res

# ─── FOCUS SESSIONS (专注计时) ────────────────────────────────────
def _ensure_focus(d):
    if "focus" not in d: d["focus"] = []

def focus_add(name, duration, date_str, note=""):
    d = _load(); _ensure_focus(d)
    d["focus"].append({"id": uuid.uuid4().hex[:8], "name": name,
                       "duration": duration, "date": date_str, "note": note})
    _save(d)

def focus_edit(fid, name, duration, note):
    d = _load(); _ensure_focus(d)
    for f in d["focus"]:
        if f["id"] == fid:
            f["name"] = name; f["duration"] = duration; f["note"] = note
    _save(d)

def focus_del(fid):
    d = _load(); _ensure_focus(d)
    d["focus"] = [f for f in d["focus"] if f["id"] != fid]
    _save(d)

def focus_all():
    d = _load(); _ensure_focus(d)
    return list(d["focus"])

def focus_names():
    d = _load(); _ensure_focus(d)
    return list(set(f["name"] for f in d["focus"] if f.get("name")))

def focus_in_range(start_key, end_key):
    d = _load(); _ensure_focus(d)
    return [f for f in d["focus"] if start_key <= f["date"] <= end_key]

def focus_for_today():
    return focus_in_range(today_key(), today_key())

def focus_for_week(monday):
    return focus_in_range(dk(monday), dk(monday + timedelta(6)))

def focus_aggregated(sessions):
    agg = {}
    for s in sessions:
        name = s["name"]
        agg[name] = agg.get(name, 0) + s["duration"]
    return agg

# ─── SUMMARIES ───────────────────────────────────────────────────
def reflection_save(key, text):
    d = _load()
    if key not in d["summaries"]: d["summaries"][key] = {}
    d["summaries"][key]["ref"] = text; _save(d)

def reflection_get(key):
    return _load()["summaries"].get(key, {}).get("ref", "")

# ================================================================
# HELPERS
# ================================================================
def monday_of(d):
    return d - timedelta(days=d.weekday())

def fmt_cn(date_str):
    d = date.fromisoformat(date_str)
    return f"{d.year}年{d.month}月{d.day}日"

def hover_bind(widget, color_in, color_out):
    widget.bind("<Enter>", lambda e: widget.configure(bg=color_in))
    widget.bind("<Leave>", lambda e: widget.configure(bg=color_out))

def clickable_label(parent, text, bg, fg, font, cmd, pad_x=10, pad_y=5):
    lbl = tk.Label(parent, text=text, bg=bg, fg=fg, font=font,
                   padx=pad_x, pady=pad_y, cursor="hand2")
    lbl.bind("<Button-1>", lambda e: cmd())
    return lbl

# ================================================================
# ROUNDED RECTANGLE HELPERS
# ================================================================
def draw_rr(c, x1, y1, x2, y2, r, fill, tags=''):
    r = max(2, min(r, (x2 - x1) // 2 - 1, (y2 - y1) // 2 - 1))
    c.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90,
                 fill=fill, outline='', style='pieslice', tags=tags)
    c.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90,
                 fill=fill, outline='', style='pieslice', tags=tags)
    c.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90,
                 fill=fill, outline='', style='pieslice', tags=tags)
    c.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90,
                 fill=fill, outline='', style='pieslice', tags=tags)
    c.create_rectangle(x1+r, y1, x2-r, y2, fill=fill, outline='', tags=tags)
    c.create_rectangle(x1, y1+r, x2, y2-r, fill=fill, outline='', tags=tags)


class RCard(tk.Canvas):
    def __init__(self, parent, r=16, bg=CARD, **kw):
        pbg = BG
        try: pbg = parent.cget('bg')
        except: pass
        super().__init__(parent, bg=pbg, highlightthickness=0, bd=0, **kw)
        self._r = r; self._bg = bg
        self.inner = tk.Frame(self, bg=bg)
        self._wid = self.create_window(0, 0, anchor='nw', window=self.inner)
        self.bind('<Configure>', self._draw)

    def _draw(self, _=None):
        self.delete('rc')
        w, h = self.winfo_width(), self.winfo_height()
        if w < 8 or h < 8: return
        r = min(self._r, w // 2 - 1, h // 2 - 1)
        draw_rr(self, 0, 0, w-1, h-1, r, BORDER, 'rc')
        draw_rr(self, 1, 1, w-2, h-2, max(r-1, 2), self._bg, 'rc')
        self.tag_lower('rc')
        self.itemconfigure(self._wid, width=w-4, height=h-4)
        self.coords(self._wid, 2, 2)


# ================================================================
# SCROLLABLE FRAME
# ================================================================
class ScrollFrame(tk.Frame):
    def __init__(self, parent, bg=CARD, **kw):
        super().__init__(parent, bg=bg, **kw)
        c = tk.Canvas(self, bg=bg, highlightthickness=0)
        c.pack(side='left', fill='both', expand=True)
        sb = tk.Scrollbar(self, orient='vertical', command=c.yview)
        self._sb = sb
        self.inner = tk.Frame(c, bg=bg)
        self._wid = c.create_window((0, 0), window=self.inner, anchor='nw')
        c.configure(yscrollcommand=sb.set)
        self._c = c
        self.inner.bind('<Configure>', self._upd)
        c.bind('<Configure>', self._upd)
        c.bind('<MouseWheel>', self._on_mousewheel)
        self.inner.bind('<MouseWheel>', self._on_mousewheel)

    def _on_mousewheel(self, event):
        self._c.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _upd(self, _=None):
        cw = self._c.winfo_width()
        if cw > 1:
            self._c.itemconfigure(self._wid, width=cw)
        self._c.configure(scrollregion=self._c.bbox('all'))
        if self.inner.winfo_reqheight() > self._c.winfo_height():
            self._sb.pack(side='right', fill='y')
        else:
            self._sb.pack_forget()


# ================================================================
# MAIN APPLICATION
# ================================================================
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.sel_date  = date.today()
        self.cur_year  = date.today().year
        self.cur_month = date.today().month
        self._resize_id = None
        self._cal_resize_id = None
        self._wt_resize_id = None

        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except: pass

        # Detect cute font
        available = tkfont.families()
        for candidate in ("幼圆", "华文圆体", "Microsoft YaHei UI", "Microsoft YaHei"):
            if candidate in available:
                self.FONT = candidate
                break
        else:
            self.FONT = "Microsoft YaHei UI"

        self.root.title("🌸 生活规划本  Life Planner")
        self.root.geometry("1300x820")
        self.root.minsize(950, 620)
        self.root.configure(bg=BG)

        # Try to set window icon
        try:
            from PIL import Image, ImageTk
            icon_path = r"C:\Users\18910\OneDrive\文档\xwechat_files\wxid_qyxc5gfkyifq22_7972\temp\RWTemp\2026-05\eefff5639825558d9769355e8a4d28e8.jpg"
            img = Image.open(icon_path).resize((64, 64), Image.LANCZOS)
            self._icon = ImageTk.PhotoImage(img)
            self.root.iconphoto(True, self._icon)
        except: pass

        self._build()
        self.root.after(100, self._render_all)
        self.root.bind("<Configure>", self._on_resize)

    def run(self): self.root.mainloop()

    # ──────────────────────────────────────────────────────────────
    # FONT HELPERS
    # ──────────────────────────────────────────────────────────────
    def FS(self, size=9):   return (self.FONT, size)
    def FM(self, size=11):  return (self.FONT, size)
    def FL(self, size=13):  return (self.FONT, size)
    def FB(self, size=14):  return (self.FONT, size, "bold")
    def FT(self, size=18):  return (self.FONT, size, "bold")

    # ──────────────────────────────────────────────────────────────
    # BUILD UI
    # ──────────────────────────────────────────────────────────────
    def _build(self):
        self._build_toolbar()
        tk.Frame(self.root, bg=BORDER, height=2).pack(fill="x")

        # Main container uses grid for responsive layout
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=10, pady=8)
        main.columnconfigure(0, weight=1)   # left: 1/3
        main.columnconfigure(1, weight=2)   # right: 2/3
        main.rowconfigure(0, weight=1)

        # Left panel
        self.left = tk.Frame(main, bg=BG)
        self.left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.left.columnconfigure(0, weight=1)
        self.left.rowconfigure(0, weight=1)   # Calendar top 1/3
        self.left.rowconfigure(1, weight=2)   # Countdown bottom 2/3

        # Right panel
        self.right = tk.Frame(main, bg=BG)
        self.right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.right.columnconfigure(0, weight=1)
        self.right.rowconfigure(0, weight=2)   # Todo top
        self.right.rowconfigure(1, weight=0)   # Finance summary (fixed)
        self.right.rowconfigure(2, weight=1)   # Weight bottom

        self._build_left()
        self._build_right()

    def _build_toolbar(self):
        tb = tk.Frame(self.root, bg=TOOLBAR, pady=14)
        tb.pack(fill="x")
        tk.Label(tb, text="🌸 生活规划本", bg=TOOLBAR, fg=TEXT,
                 font=(self.FONT, 19, "bold")).pack(side="left", padx=(14, 12))
        specs = [
            ("💰 记账",       "#D4EDDA", "#B1DFBB",   self._open_finance),
            ("💭 胡思乱想",  LAV,     "#D8C8F8",       self._open_thoughts),
            ("📤 导出记录",  GREEN,   GREEN2,           self._open_export_dialog),
            ("📝添加日程",   ACCENT,  ACCENT2,         self._open_add_task),
            ("⏰ 添加倒数日", PINK,    PINK2,           self._open_add_cd),
            ("📊总结",       BLUE,    "#B0D8FF",       lambda: self._open_summary("week")),
        ]
        for txt, bg, bgh, cmd in specs:
            lbl = clickable_label(tb, txt, bg, TEXT, (self.FONT, 12, "bold"), cmd, 13, 8)
            lbl.pack(side="left", padx=4)
            hover_bind(lbl, bgh, bg)
        # Focus timer button (top-right)
        focus_btn = clickable_label(tb, "🎯 专注计时", "#E8F4FD", TEXT,
                                    (self.FONT, 12, "bold"), self._open_focus_timer, 13, 8)
        focus_btn.pack(side="right", padx=(4, 14))
        hover_bind(focus_btn, "#C8E6F5", "#E8F4FD")

    def _build_left(self):
        # ── Calendar RCard ──────────────────────────────────────
        cal_card = RCard(self.left, r=16, bg=CARD)
        cal_card.grid(row=0, column=0, sticky="nsew", pady=(0, 6))

        # Calendar header (fixed height inside inner)
        cal_card.inner.columnconfigure(0, weight=1)
        cal_card.inner.rowconfigure(0, weight=0)  # header fixed
        cal_card.inner.rowconfigure(1, weight=1)  # canvas expands

        ch = tk.Frame(cal_card.inner, bg=CARD)
        ch.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))

        prev_btn = self._circle_btn(ch, "‹", PINK, PINK2, self._prev_month)
        prev_btn.pack(side="left")
        self._cal_my_lbl = clickable_label(ch, "", CARD, TEXT, (self.FONT, 15, "bold"),
                                            self._open_cal_picker, 8, 2)
        self._cal_my_lbl.pack(side="left", expand=True)
        hover_bind(self._cal_my_lbl, "#FFF5DC", CARD)
        td_btn = clickable_label(ch, "今天", ACCENT, TEXT, (self.FONT, 11, "bold"),
                                  self._go_today, 7, 2)
        td_btn.pack(side="left", padx=4)
        next_btn = self._circle_btn(ch, "›", PINK, PINK2, self._next_month)
        next_btn.pack(side="right")

        # Calendar canvas (responsive)
        self._cal_cvs = tk.Canvas(cal_card.inner, bg=CARD, highlightthickness=0)
        self._cal_cvs.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self._cal_cvs.bind("<Button-1>", self._cal_click)
        self._cal_cvs.bind("<Configure>", self._on_cal_configure)
        self._cal_cells = {}

        # ── Countdown RCard ──────────────────────────────────────
        cd_card = RCard(self.left, r=16, bg=CARD)
        cd_card.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        cd_card.inner.columnconfigure(0, weight=1)
        cd_card.inner.rowconfigure(1, weight=1)

        tk.Label(cd_card.inner, text="⏰ 倒数日", bg=CARD, fg=TEXT,
                 font=(self.FONT, 14, "bold")).grid(row=0, column=0, sticky="w",
                                                     padx=12, pady=(10, 5))

        cd_scroll = ScrollFrame(cd_card.inner, bg=CARD)
        cd_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._cd_frame = cd_scroll.inner

    def _build_right(self):
        # ── Combined Todo+Date RCard (top) ───────────────────────
        todo_card = RCard(self.right, r=16, bg=CARD)
        todo_card.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
        todo_card.inner.columnconfigure(0, weight=1)
        todo_card.inner.rowconfigure(3, weight=1)  # scroll row expands

        # Date display (centered at top of todo card)
        date_outer = tk.Frame(todo_card.inner, bg=CARD)
        date_outer.grid(row=0, column=0, sticky="ew")
        date_outer.columnconfigure(0, weight=1)
        date_inner = tk.Frame(date_outer, bg=CARD)
        date_inner.grid(row=0, column=0)

        self._date_big_lbl = tk.Label(date_inner, text="", bg=CARD, fg=TEXT,
                                       font=(self.FONT, 22, "bold"), anchor="center")
        self._date_big_lbl.pack(pady=(14, 3))
        self._date_sub_lbl = tk.Label(date_inner, text="", bg=CARD, fg=TEXTG,
                                       font=(self.FONT, 12), anchor="center")
        self._date_sub_lbl.pack(pady=(0, 8))

        # Separator
        tk.Frame(todo_card.inner, bg=BORDER, height=1).grid(
            row=1, column=0, sticky="ew", padx=12)

        # Todo header
        th = tk.Frame(todo_card.inner, bg=CARD)
        th.grid(row=2, column=0, sticky="ew", padx=12, pady=(8, 4))
        self._todo_hdr = tk.StringVar(value="📋 今日待办")
        tk.Label(th, textvariable=self._todo_hdr, bg=CARD, fg=TEXT,
                 font=(self.FONT, 15, "bold")).pack(side="left")

        # Scrollable todo list
        self._todo_scroll = ScrollFrame(todo_card.inner, bg=CARD)
        self._todo_scroll.grid(row=3, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._todo_frame = self._todo_scroll.inner

        # ── Finance Summary (one-line strip) ─────────────────────
        fin_bar = tk.Frame(self.right, bg="#D4EDDA", pady=4)
        fin_bar.grid(row=1, column=0, sticky="ew", pady=(3, 3))
        for i in range(4): fin_bar.columnconfigure(i, weight=1)
        self._fin_lbls = []
        for i in range(4):
            lb = tk.Label(fin_bar, text="", bg="#D4EDDA", fg=TEXT,
                          font=(self.FONT, 11))
            lb.grid(row=0, column=i, sticky="ew")
            self._fin_lbls.append(lb)

        # ── Weight RCard (bottom, full width) ────────────────────
        weight_card = RCard(self.right, r=16, bg=CARD)
        weight_card.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        weight_card.inner.columnconfigure(0, weight=1)
        weight_card.inner.rowconfigure(2, weight=1)  # charts row expands

        # Header row: title + inputs + button all in one line
        wh = tk.Frame(weight_card.inner, bg=CARD)
        wh.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        tk.Label(wh, text="⚖️ 体重管理", bg=CARD, fg=TEXT,
                 font=(self.FONT, 14, "bold")).pack(side="left")
        self._w_entry  = self._num_input(wh, "体重", "kg")
        self._w_entry.pack(side="left", padx=(18, 6))
        self._ws_entry = self._num_input(wh, "腰围", "cm")
        self._ws_entry.pack(side="left", padx=(0, 6))
        add_btn = clickable_label(wh, "+ 记录", GREEN, TEXT,
                                   (self.FONT, 11, "bold"), self._do_add_weight, 8, 4)
        add_btn.pack(side="left")
        hover_bind(add_btn, GREEN2, GREEN)

        # Latest weight (shown/hidden via grid/grid_remove in _render_weight)
        self._wt_latest = tk.Frame(weight_card.inner, bg=GREEN, padx=10, pady=4)
        self._wt_latest_lbl = tk.Label(self._wt_latest, text="", bg=GREEN, fg=TEXT,
                                        font=(self.FONT, 11))
        self._wt_latest_lbl.pack(anchor="w")

        # Charts side by side
        cf = tk.Frame(weight_card.inner, bg=CARD)
        cf.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        cf.columnconfigure(0, weight=1)
        cf.columnconfigure(1, weight=1)
        cf.rowconfigure(1, weight=1)

        self._wt_clbl = tk.Label(cf, text="本周体重 (kg)", bg=CARD, fg=TEXTG, font=(self.FONT, 11))
        self._wt_clbl.grid(row=0, column=0, sticky="w", pady=(4, 2), padx=(0, 4))
        self._wt_cvs = tk.Canvas(cf, bg="#FFF8EE", highlightthickness=0)
        self._wt_cvs.grid(row=1, column=0, sticky="nsew", padx=(0, 4))
        self._wt_cvs.bind("<Configure>", self._on_wt_configure)

        self._ws_clbl = tk.Label(cf, text="本周腰围 (cm)", bg=CARD, fg=TEXTG, font=(self.FONT, 11))
        self._ws_clbl.grid(row=0, column=1, sticky="w", pady=(4, 2), padx=(4, 0))
        self._ws_cvs = tk.Canvas(cf, bg="#FFF8EE", highlightthickness=0)
        self._ws_cvs.grid(row=1, column=1, sticky="nsew", padx=(4, 0))
        self._ws_cvs.bind("<Configure>", self._on_ws_configure)

        self._weight_cf = cf

    # ──────────────────────────────────────────────────────────────
    # UI HELPERS
    # ──────────────────────────────────────────────────────────────
    def _circle_btn(self, parent, txt, bg, bgh, cmd):
        lbl = clickable_label(parent, txt, bg, TEXT, (self.FONT, 15, "bold"), cmd, 6, 3)
        hover_bind(lbl, bgh, bg)
        return lbl

    def _num_input(self, parent, label, unit):
        f = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        inner = tk.Frame(f, bg=CARD, padx=5, pady=3); inner.pack()
        tk.Label(inner, text=label, bg=CARD, fg=TEXTG, font=(self.FONT, 10)).pack(side="left")
        e = tk.Entry(inner, width=5, bg=CARD, fg=TEXT, font=(self.FONT, 12, "bold"),
                     relief="flat", bd=0)
        e.pack(side="left", padx=2)
        tk.Label(inner, text=unit, bg=CARD, fg=TEXTL, font=(self.FONT, 10)).pack(side="left")
        f._entry = e
        return f

    def _center(self, win, w, h):
        self.root.update_idletasks()
        rx = self.root.winfo_x() + (self.root.winfo_width() - w) // 2
        ry = self.root.winfo_y() + (self.root.winfo_height() - h) // 2
        win.geometry(f"{w}x{h}+{max(0,rx)}+{max(0,ry)}")

    # ──────────────────────────────────────────────────────────────
    # RENDER
    # ──────────────────────────────────────────────────────────────
    def _render_all(self):
        self._render_cal()
        self._render_todo()
        self._render_cds()
        self._render_date_display()
        self._render_finance_summary()
        self.root.after(200, self._render_weight)

    def _on_resize(self, event):
        if event.widget is self.root:
            if self._resize_id:
                self.root.after_cancel(self._resize_id)
            self._resize_id = self.root.after(200, self._render_weight)

    def _on_cal_configure(self, event=None):
        if self._cal_resize_id:
            self.root.after_cancel(self._cal_resize_id)
        self._cal_resize_id = self.root.after(200, self._render_cal)

    def _on_wt_configure(self, event=None):
        if self._wt_resize_id:
            self.root.after_cancel(self._wt_resize_id)
        self._wt_resize_id = self.root.after(200, self._render_weight)

    def _on_ws_configure(self, event=None):
        # reuse same debounce id as weight
        if self._wt_resize_id:
            self.root.after_cancel(self._wt_resize_id)
        self._wt_resize_id = self.root.after(200, self._render_weight)

    # ─── DATE DISPLAY ───────────────────────────────────────────
    def _render_date_display(self):
        d = self.sel_date
        wd_str = WEEKDAY_CN[d.weekday()]
        date_str = f"{d.year}年{d.month}月{d.day}日  ·  {wd_str}"
        tasks = tasks_for(dk(d))
        total = len(tasks)
        done  = sum(1 for t in tasks if t.get("done"))
        sub_str = f"今日待办: {total} 件   ·   已完成: {done} 件"
        self._date_big_lbl.configure(text=date_str)
        self._date_sub_lbl.configure(text=sub_str)

    # ─── FINANCE SUMMARY (主界面) ───────────────────────────────
    def _render_finance_summary(self):
        today = date.today()
        recs = finance_for_month(today.year, today.month)
        inc = sum(r["amount"] for r in recs if r["ftype"] == "income")
        exp = sum(r["amount"] for r in recs if r["ftype"] == "expense")
        bal = inc - exp
        sign = "+" if bal >= 0 else ""
        texts = [f"💰 {today.month}月", f"收入 ¥{inc:.2f}",
                 f"支出 ¥{exp:.2f}", f"结余 {sign}¥{bal:.2f}"]
        for lb, t in zip(self._fin_lbls, texts):
            lb.configure(text=t)
        self._fin_lbls[3].configure(font=(self.FONT, 12, "bold"))

    # ─── CALENDAR ───────────────────────────────────────────────
    def _render_cal(self):
        self._cal_my_lbl.configure(text=f"{self.cur_year}年 {self.cur_month}月")
        c = self._cal_cvs
        c.update_idletasks()
        W = c.winfo_width()
        H = c.winfo_height()
        if W < 10 or H < 10:
            self.root.after(150, self._render_cal)
            return
        c.delete("all")

        CW = W // 7
        # Weekday row height
        WH = 28
        # Compute rows needed
        first = date(self.cur_year, self.cur_month, 1)
        dow0  = first.weekday()
        days_m = cal_mod.monthrange(self.cur_year, self.cur_month)[1]
        rows = math.ceil((dow0 + days_m) / 7)
        # Available height for cells
        cell_h = max(32, (H - WH) // rows)
        Y0 = WH

        # Weekday headers
        for i, wd in enumerate(["一", "二", "三", "四", "五", "六", "日"]):
            c.create_text(i * CW + CW // 2, WH // 2,
                          text=wd, fill=TEXTG, font=(self.FONT, 14, "bold"))

        cd_set = cd_dates_in_month(self.cur_year, self.cur_month)
        data   = _load()
        today  = date.today()
        prev_m = self.cur_month - 1 or 12
        prev_y = self.cur_year if self.cur_month > 1 else self.cur_year - 1
        days_p = cal_mod.monthrange(prev_y, prev_m)[1]
        self._cal_cells = {}

        def draw_cell(idx, day, other, this_date=None):
            col, row = idx % 7, idx // 7
            x1 = col * CW
            y1 = Y0 + row * cell_h
            x2 = x1 + CW
            y2 = y1 + cell_h
            cx = x1 + CW // 2
            cy_num = y1 + cell_h // 2 - 4

            # Selection background
            if this_date and this_date == self.sel_date:
                pad = 3
                draw_rr(c, x1+pad, y1+pad, x2-pad, y2-pad, 10, ACCENT, 'cell_bg')
            elif not other and this_date == today:
                pad = 3
                draw_rr(c, x1+pad, y1+pad, x2-pad, y2-pad, 10, "#FFF0D0", 'cell_bg')

            # Countdown circle (behind number)
            if not other and this_date and this_date.day in cd_set:
                c.create_oval(cx-14, cy_num-14, cx+14, cy_num+14,
                              fill="#FFE4EE", outline=PINK2, width=1.5)

            # Day number
            if other:
                nc = TEXTL
            elif this_date == today:
                nc = "#E04060"
            else:
                nc = TEXT
            fw = "bold" if (not other and this_date == today) else "normal"
            c.create_text(cx, cy_num, text=str(day), fill=nc, font=(self.FONT, 14, fw))

            # Task dots
            if not other and this_date:
                tasks = data["tasks"].get(dk(this_date), [])
                has = {p: any(t["pri"] == p for t in tasks) for p in ("u", "i", "n")}
                dots = [(URGENT, "u"), (IMPRT, "i"), (NORMAL, "n")]
                active = [col2 for col2, p in dots if has[p]]
                if active:
                    tw = len(active) * 8 - 2
                    dx = cx - tw // 2
                    dy = y2 - 8
                    for dc_color in active:
                        c.create_oval(dx, dy-3, dx+6, dy+3, fill=dc_color, outline="")
                        dx += 8

            if not other and this_date:
                self._cal_cells[dk(this_date)] = (x1, y1, x2, y2)

        # Previous month padding
        for i in range(dow0):
            draw_cell(i, days_p - dow0 + 1 + i, True)

        # Current month
        for d in range(1, days_m + 1):
            draw_cell(dow0 + d - 1, d, False, date(self.cur_year, self.cur_month, d))

        # Next month padding
        total = rows * 7
        for i in range(dow0 + days_m, total):
            draw_cell(i, i - (dow0 + days_m) + 1, True)

    def _cal_click(self, event):
        for date_key, (x1, y1, x2, y2) in self._cal_cells.items():
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.sel_date = date.fromisoformat(date_key)
                self._render_cal()
                self._render_todo()
                self._render_date_display()
                return

    def _prev_month(self):
        if self.cur_month == 1: self.cur_month = 12; self.cur_year -= 1
        else: self.cur_month -= 1
        self._render_cal()

    def _next_month(self):
        if self.cur_month == 12: self.cur_month = 1; self.cur_year += 1
        else: self.cur_month += 1
        self._render_cal()

    def _go_today(self):
        self.sel_date = date.today()
        self.cur_year  = self.sel_date.year
        self.cur_month = self.sel_date.month
        self._render_cal()
        self._render_todo()
        self._render_date_display()

    # ─── TODO ───────────────────────────────────────────────────
    def _render_todo(self):
        d = self.sel_date
        self._todo_hdr.set(f"📋 {d.year}年{d.month}月{d.day}日 待办")
        for w in self._todo_frame.winfo_children(): w.destroy()
        tasks = tasks_for(dk(d))
        if not tasks:
            tk.Label(self._todo_frame, text="🌸 今天没有待办，好好放松~",
                     bg=CARD, fg=TEXTG, font=(self.FONT, 13)).pack(pady=10)
            return
        for t in tasks:
            self._todo_item(self._todo_frame, t, dk(d))

    def _todo_item(self, parent, task, date_key):
        pri  = task["pri"]
        ibg  = PRIO_BG[pri]
        bc   = PRIO_COLOR[pri]
        row  = tk.Frame(parent, bg=ibg); row.pack(fill="x", pady=3, padx=4)
        # drag handle (pack before color strip so it's leftmost)
        dh = tk.Label(row, text="⠿", bg=ibg, fg=TEXTG,
                      font=(self.FONT, 14), padx=4, cursor="hand2")
        dh.pack(side="left", fill="y")
        self._setup_drag(dh, row,
            get_fn=lambda dk=date_key: tasks_for(dk),
            save_fn=lambda items, dk=date_key: self._save_task_order(dk, items),
            render_fn=lambda: (self._render_todo(), self._render_cal()))
        # color strip
        tk.Frame(row, bg=bc, width=4).pack(side="left", fill="y")
        inner = tk.Frame(row, bg=ibg, padx=7); inner.pack(side="left", fill="both", expand=True)
        # checkbox (single-click)
        chk_txt = "✓" if task.get("done") else "○"
        chk = tk.Label(inner, text=chk_txt, bg=ibg,
                       fg=bc if task.get("done") else TEXTG,
                       font=(self.FONT, 14, "bold"), cursor="hand2")
        chk.pack(side="left", padx=(0, 5))
        chk.bind("<Button-1>", lambda e, k=date_key, tid=task["id"]: (
            task_toggle(k, tid), self._render_todo(),
            self._render_cal(), self._render_date_display()
        ))
        # content
        cont = tk.Frame(inner, bg=ibg); cont.pack(side="left", fill="both", expand=True, pady=5)
        name_font = (self.FONT, 13) if task.get("done") else (self.FONT, 13, "bold")
        name_lbl = tk.Label(cont, text=task["name"], bg=ibg,
                             fg=TEXTG if task.get("done") else TEXT,
                             font=name_font, anchor="w")
        name_lbl.pack(anchor="w")
        # badge
        badge_bg = PRIO_BADGE[pri]
        tk.Label(inner, text=PRIO_LABEL[pri], bg=badge_bg, fg=bc,
                 font=(self.FONT, 10, "bold"), padx=5, pady=1).pack(side="left", padx=4)
        if task.get("desc"):
            desc_lbl = tk.Label(cont, text=task["desc"], bg=ibg, fg=TEXTG,
                     font=(self.FONT, 11), anchor="w", justify="left")
            desc_lbl.pack(fill="x", anchor="w")
            desc_lbl.bind("<Configure>", lambda e, l=desc_lbl: l.config(wraplength=max(1, e.width - 4)))
        # double-click on row/content → edit popup
        def on_dbl(e, k=date_key, t=task):
            self._open_task_edit(k, t)
        for w in (row, cont, name_lbl):
            w.bind("<Double-Button-1>", on_dbl)

    # ─── COUNTDOWNS ────────────────────────────────────────────
    def _render_cds(self):
        cd_cleanup()
        for w in self._cd_frame.winfo_children(): w.destroy()
        cds = sorted(_load()["countdowns"], key=lambda c: cd_days(c))
        if not cds:
            tk.Label(self._cd_frame, text="暂无倒数日，点击顶部按钮添加~",
                     bg=CARD, fg=TEXTG, font=(self.FONT, 12)).pack(pady=8)
            return
        for c in cds:
            days = cd_days(c)
            if days == 0:   dt = "🎉 今天！"
            elif days > 0:  dt = f"还有 {days} 天"
            else:           dt = f"已过 {-days} 天"
            rep_map = {"none": "", "yearly": " · 每年", "monthly": " · 每月", "daily": " · 每日"}
            row = tk.Frame(self._cd_frame, bg=PINK, pady=8)
            row.pack(fill="x", pady=3, padx=4)
            # drag handle (leftmost)
            dh = tk.Label(row, text="⠿", bg=PINK, fg=TEXTG,
                          font=(self.FONT, 15), padx=6, cursor="hand2")
            dh.pack(side="left", fill="y")
            self._setup_drag(dh, row,
                get_fn=lambda: _load()["countdowns"],
                save_fn=self._save_cd_order,
                render_fn=self._render_cds)
            # days label (pack before lf so expand doesn't bury it)
            rf = tk.Frame(row, bg=PINK); rf.pack(side="right", padx=(0, 8))
            dc = PINK3 if days > 0 else TEXTG
            tk.Label(rf, text=dt, bg=PINK, fg=dc,
                     font=(self.FONT, 15, "bold")).pack()
            # name + date
            lf = tk.Frame(row, bg=PINK, padx=6)
            lf.pack(side="left", fill="both", expand=True)
            name_lbl = tk.Label(lf, text=c["name"], bg=PINK, fg=TEXT,
                                 font=(self.FONT, 16, "bold"))
            name_lbl.pack(anchor="w")
            sub_lbl = tk.Label(lf,
                                text=fmt_cn(c["date"]) + rep_map.get(c.get("rep","none"),""),
                                bg=PINK, fg=TEXTG, font=(self.FONT, 13))
            sub_lbl.pack(anchor="w")
            # double-click → edit/delete popup
            def on_dbl(e, ci=c): self._open_cd_edit(ci)
            for w in (row, lf, rf, name_lbl, sub_lbl):
                w.bind("<Double-Button-1>", on_dbl)

    # ─── WEIGHT ────────────────────────────────────────────────
    def _render_weight(self):
        mon = monday_of(date.today()); sun = mon + timedelta(6)
        self._wt_clbl.configure(text=f"本周体重 (kg)  {mon.month}/{mon.day}—{sun.month}/{sun.day}")
        self._ws_clbl.configure(text=f"本周腰围 (cm)  {mon.month}/{mon.day}—{sun.month}/{sun.day}")
        wd = weight_for_week(mon)
        lbls = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        self._draw_chart(self._wt_cvs, lbls, [d["w"]  for d in wd], "#FF9F7F")
        self._draw_chart(self._ws_cvs, lbls, [d["ws"] for d in wd], "#74B9FF")
        self._wt_week_mon = mon
        self._wt_cvs.bind("<Button-1>", lambda e: self._on_chart_click(e))
        self._ws_cvs.bind("<Button-1>", lambda e: self._on_chart_click(e))
        lt = weight_latest()
        if lt:
            wstr  = f"{lt['w']:.1f} kg"  if lt.get("w")  is not None else "--"
            wsstr = f"{lt['ws']:.1f} cm" if lt.get("ws") is not None else "--"
            self._wt_latest_lbl.configure(
                text=f"最新体重: {wstr}  腰围: {wsstr}  ({fmt_cn(lt['date'])})")
            self._wt_latest.configure(cursor="")
            self._wt_latest_lbl.configure(cursor="")
            self._wt_latest.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        else:
            self._wt_latest.grid_remove()

    def _do_add_weight(self):
        wv  = self._w_entry._entry.get().strip()
        wsv = self._ws_entry._entry.get().strip()
        if not wv and not wsv:
            messagebox.showwarning("提示", "请输入体重或腰围！"); return
        try:
            w  = float(wv)  if wv  else None
            ws = float(wsv) if wsv else None
        except ValueError:
            messagebox.showwarning("提示", "请输入有效数字！"); return
        weight_add(w, ws)
        self._w_entry._entry.delete(0, "end")
        self._ws_entry._entry.delete(0, "end")
        self._render_weight()

    # ──────────────────────────────────────────────────────────────
    # DRAG-TO-REORDER
    # ──────────────────────────────────────────────────────────────
    def _setup_drag(self, handle, row, get_fn, save_fn, render_fn):
        state = {"y0": 0, "active": False}
        def on_press(e):
            state["y0"] = e.y_root; state["active"] = True
            handle.configure(fg=ACCENT2)
        def on_release(e):
            if not state["active"]: return
            state["active"] = False
            handle.configure(fg=TEXTG)
            dy = e.y_root - state["y0"]
            if abs(dy) < 8: return
            h = max(row.winfo_height(), 48)
            steps = round(dy / h)
            if steps == 0: return
            items = get_fn()
            siblings = [w for w in row.master.winfo_children()
                        if isinstance(w, tk.Frame)]
            if row not in siblings: return
            idx = siblings.index(row)
            new_idx = max(0, min(len(items) - 1, idx + steps))
            if new_idx == idx: return
            item = items.pop(idx); items.insert(new_idx, item)
            save_fn(items); render_fn()
        handle.bind("<ButtonPress-1>", on_press)
        handle.bind("<B1-Motion>", lambda e: None)
        handle.bind("<ButtonRelease-1>", on_release)

    def _save_task_order(self, date_key, items):
        d = _load(); d["tasks"][date_key] = items; _save(d)

    def _save_cd_order(self, items):
        d = _load(); d["countdowns"] = items; _save(d)

    # ──────────────────────────────────────────────────────────────
    # EDIT DIALOGS
    # ──────────────────────────────────────────────────────────────
    def _open_task_edit(self, date_key, task):
        win = tk.Toplevel(self.root); win.title("编辑日程")
        win.configure(bg=CARD); win.resizable(False, False); win.grab_set()
        self._center(win, 420, 480)
        tk.Label(win, text="✏️ 编辑日程", bg=CARD, fg=TEXT,
                 font=(self.FONT, 20, "bold")).pack(pady=(22, 14))
        f = tk.Frame(win, bg=CARD, padx=26); f.pack(fill="x")

        def row_entry(label, value=""):
            tk.Label(f, text=label, bg=CARD, fg=TEXTG,
                     font=(self.FONT, 12, "bold")).pack(anchor="w")
            e = tk.Entry(f, font=(self.FONT, 13), relief="flat", bg="#FFF8EE", fg=TEXT,
                         bd=1, highlightthickness=1, highlightbackground=BORDER)
            e.pack(fill="x", pady=(3, 10), ipady=5)
            if value: e.insert(0, value)
            return e

        name_e = row_entry("事件名称", task["name"])
        tk.Label(f, text="简介（可选）", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 12, "bold")).pack(anchor="w")
        desc_t = tk.Text(f, font=(self.FONT, 13), relief="flat", bg="#FFF8EE", fg=TEXT,
                         bd=1, height=3, highlightthickness=1, highlightbackground=BORDER)
        desc_t.pack(fill="x", pady=(3, 10))
        if task.get("desc"): desc_t.insert("1.0", task["desc"])

        tk.Label(f, text="优先级", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 12, "bold")).pack(anchor="w")
        pf = tk.Frame(f, bg=CARD); pf.pack(fill="x", pady=(3, 14))
        pri_var = tk.StringVar(value=task["pri"]); pbtns = {}
        def upd_pri():
            for pid, b in pbtns.items():
                b.configure(bg=PRIO_COLOR[pid] if pri_var.get()==pid else PRIO_BADGE[pid],
                            fg="white" if pri_var.get()==pid else PRIO_COLOR[pid])
        for pid, plbl in [("u","🔴 紧急"),("i","🟠 重要"),("n","🔵 不重要")]:
            b = tk.Label(pf, text=plbl, bg=PRIO_BADGE[pid], fg=PRIO_COLOR[pid],
                         font=(self.FONT, 12, "bold"), padx=8, pady=7, cursor="hand2")
            b.pack(side="left", expand=True, fill="x", padx=2)
            b.bind("<Button-1>", lambda e, p=pid: (pri_var.set(p), upd_pri()))
            pbtns[pid] = b
        upd_pri()

        bf = tk.Frame(f, bg=CARD); bf.pack(fill="x", pady=(0, 4))
        def do_save():
            nm = name_e.get().strip()
            if not nm: messagebox.showwarning("提示", "请输入事件名称！", parent=win); return
            dc = desc_t.get("1.0", "end-1c").strip()
            task_edit(date_key, task["id"], nm, dc, pri_var.get())
            win.destroy()
            self._render_todo(); self._render_cal(); self._render_date_display()
        def do_del():
            if messagebox.askyesno("确认", f"删除「{task['name']}」？", parent=win):
                task_del(date_key, task["id"]); win.destroy()
                self._render_todo(); self._render_cal(); self._render_date_display()
        save_btn = clickable_label(bf, "💾 保存", GREEN, TEXT, (self.FONT, 12, "bold"), do_save, 0, 10)
        save_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        hover_bind(save_btn, GREEN2, GREEN)
        del_btn = clickable_label(bf, "🗑 删除", "#FFEEEE", URGENT, (self.FONT, 12, "bold"), do_del, 0, 10)
        del_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))
        hover_bind(del_btn, "#FFD0D0", "#FFEEEE")
        win.bind("<Escape>", lambda e: win.destroy())

    def _open_cd_edit(self, c):
        win = tk.Toplevel(self.root); win.title("编辑倒数日")
        win.configure(bg=CARD); win.resizable(False, False); win.grab_set()
        self._center(win, 420, 400)
        tk.Label(win, text="✏️ 编辑倒数日", bg=CARD, fg=TEXT,
                 font=(self.FONT, 20, "bold")).pack(pady=(22, 14))
        f = tk.Frame(win, bg=CARD, padx=26); f.pack(fill="x")

        def row_entry(label, value=""):
            tk.Label(f, text=label, bg=CARD, fg=TEXTG,
                     font=(self.FONT, 12, "bold")).pack(anchor="w")
            e = tk.Entry(f, font=(self.FONT, 13), relief="flat", bg="#FFF8EE", fg=TEXT,
                         bd=1, highlightthickness=1, highlightbackground=BORDER)
            e.pack(fill="x", pady=(3, 10), ipady=5)
            if value: e.insert(0, value)
            return e

        name_e = row_entry("名称", c["name"])
        date_e = row_entry("日期 (YYYY-MM-DD)", c["date"])

        tk.Label(f, text="是否重复", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 12, "bold")).pack(anchor="w")
        rf2 = tk.Frame(f, bg=CARD); rf2.pack(fill="x", pady=(3, 14))
        rep_var = tk.StringVar(value=c.get("rep", "none")); rbtns = {}
        def upd_rep():
            for rid, b in rbtns.items():
                b.configure(bg=PINK if rep_var.get()==rid else "#FFF8EE",
                            fg=TEXT if rep_var.get()==rid else TEXTG)
        for rid, rlbl in [("none","不重复"),("yearly","每年"),("monthly","每月"),("daily","每日")]:
            b = tk.Label(rf2, text=rlbl, bg="#FFF8EE", fg=TEXTG,
                         font=(self.FONT, 12, "bold"), padx=6, pady=7, cursor="hand2")
            b.pack(side="left", expand=True, fill="x", padx=2)
            b.bind("<Button-1>", lambda e, r=rid: (rep_var.set(r), upd_rep()))
            rbtns[rid] = b
        upd_rep()

        bf = tk.Frame(f, bg=CARD); bf.pack(fill="x", pady=(0, 4))
        def do_save():
            nm = name_e.get().strip(); ds = date_e.get().strip()
            if not nm: messagebox.showwarning("提示", "请输入名称！", parent=win); return
            try: date.fromisoformat(ds)
            except: messagebox.showwarning("提示", "日期格式错误，请用 YYYY-MM-DD", parent=win); return
            cd_edit(c["id"], nm, ds, rep_var.get())
            win.destroy(); self._render_cds(); self._render_cal()
        def do_del():
            if messagebox.askyesno("确认", f"删除「{c['name']}」？", parent=win):
                cd_del(c["id"]); win.destroy()
                self._render_cds(); self._render_cal()
        save_btn = clickable_label(bf, "💾 保存", GREEN, TEXT, (self.FONT, 12, "bold"), do_save, 0, 10)
        save_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        hover_bind(save_btn, GREEN2, GREEN)
        del_btn = clickable_label(bf, "🗑 删除", "#FFEEEE", URGENT, (self.FONT, 12, "bold"), do_del, 0, 10)
        del_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))
        hover_bind(del_btn, "#FFD0D0", "#FFEEEE")
        win.bind("<Escape>", lambda e: win.destroy())

    def _on_chart_click(self, event):
        mon = getattr(self, "_wt_week_mon", None)
        if mon is None: return
        W = event.widget.winfo_width()
        pL, pR = 38, 10; cW = W - pL - pR
        best_idx, best_dist = 0, float("inf")
        for i in range(7):
            x = pL + (i / 6) * cW
            d = abs(event.x - x)
            if d < best_dist: best_dist = d; best_idx = i
        if best_dist > 40: return
        entry_date = dk(mon + timedelta(best_idx))
        entry = next((e for e in _load()["weight"] if e["date"] == entry_date), None)
        if entry: self._open_weight_edit(entry)

    def _open_weight_edit(self, entry):
        pop = tk.Toplevel(self.root)
        pop.title("编辑体重记录")
        pop.configure(bg=CARD)
        pop.resizable(False, False)
        self._center(pop, 300, 190)
        pop.grab_set()

        tk.Label(pop, text=f"📅 {fmt_cn(entry['date'])}", bg=CARD, fg=TEXT,
                 font=(self.FONT, 14, "bold")).pack(pady=(16, 10))

        ef = tk.Frame(pop, bg=CARD); ef.pack(pady=(0, 12))
        w_ent  = self._num_input(ef, "体重", "kg"); w_ent.pack(side="left", padx=(0, 8))
        ws_ent = self._num_input(ef, "腰围", "cm"); ws_ent.pack(side="left")
        if entry.get("w")  is not None: w_ent._entry.insert(0, str(entry["w"]))
        if entry.get("ws") is not None: ws_ent._entry.insert(0, str(entry["ws"]))

        def do_save():
            wv = w_ent._entry.get().strip(); wsv = ws_ent._entry.get().strip()
            try:
                w  = float(wv)  if wv  else None
                ws = float(wsv) if wsv else None
            except ValueError:
                messagebox.showwarning("提示", "请输入有效数字！"); return
            weight_update(entry["date"], w, ws)
            self._render_weight(); pop.destroy()

        def do_del():
            if messagebox.askyesno("确认", f"删除 {fmt_cn(entry['date'])} 的体重记录？"):
                weight_del(entry["date"])
                self._render_weight(); pop.destroy()

        bf = tk.Frame(pop, bg=CARD); bf.pack(pady=(0, 14))
        save_btn = clickable_label(bf, "💾 保存", GREEN, TEXT, (self.FONT, 12, "bold"), do_save, 14, 6)
        save_btn.pack(side="left", padx=(0, 10))
        hover_bind(save_btn, GREEN2, GREEN)
        del_btn  = clickable_label(bf, "🗑 删除", "#FFEEEE", URGENT, (self.FONT, 12, "bold"), do_del, 14, 6)
        del_btn.pack(side="left")
        hover_bind(del_btn, "#FFD0D0", "#FFEEEE")

    def _open_cal_picker(self):
        pop = tk.Toplevel(self.root)
        pop.title(""); pop.configure(bg=CARD)
        pop.resizable(False, False)
        self._center(pop, 260, 150)
        pop.grab_set()

        tk.Label(pop, text="跳转到年月", bg=CARD, fg=TEXT,
                 font=(self.FONT, 14, "bold")).grid(row=0, column=0, columnspan=4,
                                                      padx=16, pady=(14, 10))

        tk.Label(pop, text="年份", bg=CARD, fg=TEXTG, font=(self.FONT, 11)).grid(
            row=1, column=0, padx=(16, 4))
        y_var = tk.StringVar(value=str(self.cur_year))
        y_entry = tk.Entry(pop, textvariable=y_var, width=6, font=(self.FONT, 13),
                           relief="flat", bg="#FFF8EE", bd=1)
        y_entry.grid(row=1, column=1, padx=(0, 10))

        tk.Label(pop, text="月份", bg=CARD, fg=TEXTG, font=(self.FONT, 11)).grid(
            row=1, column=2, padx=(0, 4))
        months = [f"{i}" for i in range(1, 13)]
        m_var = tk.StringVar(value=str(self.cur_month))
        m_cb = ttk.Combobox(pop, textvariable=m_var, values=months, width=4,
                             font=(self.FONT, 12), state="readonly")
        m_cb.grid(row=1, column=3, padx=(0, 16))

        def go():
            try: y = int(y_var.get())
            except ValueError:
                messagebox.showwarning("提示", "请输入有效年份！"); return
            try: m = int(m_var.get())
            except ValueError: return
            if 1 <= m <= 12 and 1900 <= y <= 2100:
                self.cur_year = y; self.cur_month = m
                self._render_cal(); pop.destroy()

        btn = clickable_label(pop, "跳转 ›", ACCENT, TEXT, (self.FONT, 12, "bold"), go, 18, 6)
        btn.grid(row=2, column=0, columnspan=4, pady=(12, 14))
        hover_bind(btn, ACCENT2, ACCENT)
        y_entry.bind("<Return>", lambda e: go())

    def _draw_chart(self, canvas, labels, values, color):
        canvas.delete("all"); canvas.update_idletasks()
        W = canvas.winfo_width(); H = canvas.winfo_height()
        if W <= 1: W = 260
        pL, pR, pT, pB = 38, 10, 12, 20
        cW = W - pL - pR; cH = H - pT - pB
        canvas.create_rectangle(0, 0, W, H, fill="#FFF8EE", outline="")
        nv = [v for v in values if v is not None]
        if not nv:
            canvas.create_text(W // 2, H // 2, text="暂无数据", fill=TEXTG,
                               font=(self.FONT, 11)); return {}
        mn, mx = min(nv), max(nv); rng = mx - mn or 1; pad = rng * 0.35
        ymin, ymax = mn - pad, mx + pad

        def tx(i): return pL + (i / max(len(labels) - 1, 1)) * cW
        def ty(v): return pT + cH - ((v - ymin) / (ymax - ymin)) * cH

        for i in range(5):
            y = pT + (i / 4) * cH
            canvas.create_line(pL, y, pL + cW, y, fill=BORDER, width=1)
        for i, lb in enumerate(labels):
            canvas.create_text(tx(i), H - 5, text=lb, fill=TEXTG, font=(self.FONT, 9))
        for i in range(3):
            v = ymin + (i / 2) * (ymax - ymin)
            canvas.create_text(pL - 4, pT + cH - (i / 2) * cH,
                               text=f"{v:.1f}", fill=TEXTG, font=(self.FONT, 9), anchor="e")

        segs = []; cur = []
        for i, v in enumerate(values):
            if v is not None: cur.append((tx(i), ty(v)))
            else:
                if cur: segs.append(cur); cur = []
        if cur: segs.append(cur)
        for seg in segs:
            if len(seg) > 1:
                pts = [coord for pt in seg for coord in pt]
                canvas.create_line(pts, fill=color, width=2.5, smooth=False,
                                   capstyle="round", joinstyle="round")
        for i, v in enumerate(values):
            if v is None: continue
            x, y = tx(i), ty(v)
            canvas.create_oval(x-4, y-4, x+4, y+4, fill=color, outline="")
            canvas.create_oval(x-2, y-2, x+2, y+2, fill="white", outline="")
            canvas.create_text(x, y - 9, text=f"{v:.1f}", fill=color, font=(self.FONT, 9))
        return {i: (tx(i), ty(v) if v is not None else None)
                for i, v in enumerate(values)}

    # ──────────────────────────────────────────────────────────────
    # DIALOGS
    # ──────────────────────────────────────────────────────────────
    def _open_add_task(self):
        win = tk.Toplevel(self.root); win.title("添加日程")
        win.configure(bg=CARD); win.resizable(False, False); win.grab_set()
        self._center(win, 420, 540)
        tk.Label(win, text="✏️ 添加日程", bg=CARD, fg=TEXT,
                 font=(self.FONT, 20, "bold")).pack(pady=(22, 14))
        f = tk.Frame(win, bg=CARD, padx=26); f.pack(fill="x")

        def row_entry(label, value=""):
            tk.Label(f, text=label, bg=CARD, fg=TEXTG,
                     font=(self.FONT, 12, "bold")).pack(anchor="w")
            e = tk.Entry(f, font=(self.FONT, 13), relief="flat", bg="#FFF8EE", fg=TEXT,
                         bd=1, highlightthickness=1, highlightbackground=BORDER)
            e.pack(fill="x", pady=(3, 10), ipady=5)
            if value: e.insert(0, value)
            return e

        date_e = row_entry("日期 (YYYY-MM-DD)", dk(self.sel_date))
        name_e = row_entry("事件名称")

        tk.Label(f, text="简介（可选）", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 12, "bold")).pack(anchor="w")
        desc_t = tk.Text(f, font=(self.FONT, 13), relief="flat", bg="#FFF8EE", fg=TEXT,
                         bd=1, height=3, highlightthickness=1, highlightbackground=BORDER)
        desc_t.pack(fill="x", pady=(3, 10))

        tk.Label(f, text="优先级", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 12, "bold")).pack(anchor="w")
        pf = tk.Frame(f, bg=CARD); pf.pack(fill="x", pady=(3, 14))
        pri_var = tk.StringVar(value="n"); pbtns = {}

        def upd_pri():
            for pid, b in pbtns.items():
                if pri_var.get() == pid:
                    b.configure(bg=PRIO_COLOR[pid], fg="white")
                else:
                    b.configure(bg=PRIO_BADGE[pid], fg=PRIO_COLOR[pid])

        for pid, plbl in [("u", "🔴 紧急"), ("i", "🟠 重要"), ("n", "🔵 不重要")]:
            b = tk.Label(pf, text=plbl, bg=PRIO_BADGE[pid], fg=PRIO_COLOR[pid],
                         font=(self.FONT, 12, "bold"), padx=8, pady=7, cursor="hand2")
            b.pack(side="left", expand=True, fill="x", padx=2)
            b.bind("<Button-1>", lambda e, p=pid: (pri_var.set(p), upd_pri()))
            pbtns[pid] = b
        upd_pri()

        def submit():
            ds = date_e.get().strip(); nm = name_e.get().strip()
            dc = desc_t.get("1.0", "end-1c").strip()
            if not ds: messagebox.showwarning("提示", "请输入日期！", parent=win); return
            if not nm: messagebox.showwarning("提示", "请输入事件名称！", parent=win); return
            try: date.fromisoformat(ds)
            except: messagebox.showwarning("提示", "日期格式错误，请用 YYYY-MM-DD", parent=win); return
            task_add(ds, nm, dc, pri_var.get())
            win.destroy()
            self.sel_date   = date.fromisoformat(ds)
            self.cur_year   = self.sel_date.year
            self.cur_month  = self.sel_date.month
            self._render_cal(); self._render_todo(); self._render_date_display()

        sb = clickable_label(f, "添加日程  🌸", ACCENT, TEXT,
                             (self.FONT, 14, "bold"), submit, 0, 12)
        sb.pack(fill="x"); hover_bind(sb, ACCENT2, ACCENT)
        win.bind("<Return>", lambda e: submit())
        win.bind("<Escape>", lambda e: win.destroy())

    def _open_add_cd(self):
        win = tk.Toplevel(self.root); win.title("添加倒数日")
        win.configure(bg=CARD); win.resizable(False, False); win.grab_set()
        self._center(win, 420, 380)
        tk.Label(win, text="⏰ 添加倒数日", bg=CARD, fg=TEXT,
                 font=(self.FONT, 20, "bold")).pack(pady=(22, 14))
        f = tk.Frame(win, bg=CARD, padx=26); f.pack(fill="x")

        def row_entry(label, value=""):
            tk.Label(f, text=label, bg=CARD, fg=TEXTG,
                     font=(self.FONT, 12, "bold")).pack(anchor="w")
            e = tk.Entry(f, font=(self.FONT, 13), relief="flat", bg="#FFF8EE", fg=TEXT,
                         bd=1, highlightthickness=1, highlightbackground=BORDER)
            e.pack(fill="x", pady=(3, 10), ipady=5)
            if value: e.insert(0, value)
            return e

        name_e = row_entry("名称")
        date_e = row_entry("日期 (YYYY-MM-DD)", dk(self.sel_date))

        tk.Label(f, text="是否重复", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 12, "bold")).pack(anchor="w")
        rf = tk.Frame(f, bg=CARD); rf.pack(fill="x", pady=(3, 14))
        rep_var = tk.StringVar(value="none"); rbtns = {}

        def upd_rep():
            for rid, b in rbtns.items():
                b.configure(
                    bg=PINK if rep_var.get() == rid else "#FFF8EE",
                    fg=TEXT if rep_var.get() == rid else TEXTG
                )

        for rid, rlbl in [("none", "不重复"), ("yearly", "每年"), ("monthly", "每月"), ("daily", "每日")]:
            b = tk.Label(rf, text=rlbl, bg="#FFF8EE", fg=TEXTG,
                         font=(self.FONT, 12, "bold"), padx=6, pady=7, cursor="hand2")
            b.pack(side="left", expand=True, fill="x", padx=2)
            b.bind("<Button-1>", lambda e, r=rid: (rep_var.set(r), upd_rep()))
            rbtns[rid] = b
        upd_rep()

        def submit():
            nm = name_e.get().strip(); ds = date_e.get().strip()
            if not nm: messagebox.showwarning("提示", "请输入名称！", parent=win); return
            if not ds: messagebox.showwarning("提示", "请输入日期！", parent=win); return
            try: date.fromisoformat(ds)
            except: messagebox.showwarning("提示", "日期格式错误，请用 YYYY-MM-DD", parent=win); return
            cd_add(nm, ds, rep_var.get()); win.destroy()
            self._render_cds(); self._render_cal()

        sb = clickable_label(f, "添加倒数日  ⏰", PINK2, TEXT,
                             (self.FONT, 14, "bold"), submit, 0, 12)
        sb.pack(fill="x"); hover_bind(sb, PINK3, PINK2)
        win.bind("<Return>", lambda e: submit())
        win.bind("<Escape>", lambda e: win.destroy())

    def _open_summary(self, init_type):
        win = tk.Toplevel(self.root); win.title("总结")
        win.configure(bg=CARD); win.resizable(True, True); win.grab_set()
        self._center(win, 700, 860)
        tk.Label(win, text="✨ 总 结", bg=CARD, fg=TEXT,
                 font=(self.FONT, 20, "bold")).pack(pady=(22, 14))

        state = {"t": init_type, "off": 0}

        # Tabs
        tf = tk.Frame(win, bg=CARD); tf.pack(pady=(0, 12)); tabs = {}

        def sw(t): state["t"] = t; state["off"] = 0; upd_tabs(); refresh()
        for tid, tlbl in [("week", "📅周总结"), ("month", "📊月总结"), ("year", "🗓️年总结")]:
            b = tk.Label(tf, text=tlbl,
                         bg=ACCENT if tid == init_type else "#FFF8EE", fg=TEXT,
                         font=(self.FONT, 12, "bold"), padx=14, pady=5, cursor="hand2")
            b.pack(side="left", padx=3)
            b.bind("<Button-1>", lambda e, t=tid: sw(t))
            tabs[tid] = b

        def upd_tabs():
            for tid, b in tabs.items():
                b.configure(bg=ACCENT if state["t"] == tid else "#FFF8EE")

        # Nav
        nf = tk.Frame(win, bg=CARD); nf.pack(pady=(0, 12))
        period_v = tk.StringVar()
        pb = self._circle_btn(nf, "‹", BORDER, "#E0D0C0",
                              lambda: (state.__setitem__("off", state["off"] - 1), refresh()))
        pb.pack(side="left")
        tk.Label(nf, textvariable=period_v, bg=CARD, fg=TEXT,
                 font=(self.FONT, 15, "bold"), width=24).pack(side="left", padx=8)
        nb = self._circle_btn(nf, "›", BORDER, "#E0D0C0",
                              lambda: (state.__setitem__("off", state["off"] + 1), refresh()))
        nb.pack(side="left")

        # Charts
        chf = tk.Frame(win, bg=CARD); chf.pack(fill="x", padx=20, pady=(0, 12))
        wt_cf = tk.Frame(chf, bg="#FFF8EE"); wt_cf.pack(side="left", fill="both", expand=True, padx=(0, 4))
        tk.Label(wt_cf, text="体重趋势 (kg)", bg="#FFF8EE", fg=TEXTG,
                 font=(self.FONT, 11)).pack(anchor="w", padx=6, pady=3)
        s_wt = tk.Canvas(wt_cf, bg="#FFF8EE", highlightthickness=0, height=120)
        s_wt.pack(fill="x", padx=4)
        ws_cf = tk.Frame(chf, bg="#FFF8EE"); ws_cf.pack(side="left", fill="both", expand=True, padx=(4, 0))
        tk.Label(ws_cf, text="腰围趋势 (cm)", bg="#FFF8EE", fg=TEXTG,
                 font=(self.FONT, 11)).pack(anchor="w", padx=6, pady=3)
        s_ws = tk.Canvas(ws_cf, bg="#FFF8EE", highlightthickness=0, height=120)
        s_ws.pack(fill="x", padx=4)

        # Stats
        sf2 = tk.Frame(win, bg=CARD); sf2.pack(fill="x", padx=20, pady=(0, 14))
        sv_u = tk.StringVar(value="0")
        sv_i = tk.StringVar(value="0")
        sv_n = tk.StringVar(value="0")
        for sv, slbl, sbg, sc in [
            (sv_u, "🔴 完成紧急",   "#FFF0F0", URGENT),
            (sv_i, "🟠 完成重要",   "#FFF5EE", IMPRT),
            (sv_n, "🔵 完成不重要", "#F0F5FF", NORMAL),
        ]:
            sf3 = tk.Frame(sf2, bg=sbg, padx=10, pady=10)
            sf3.pack(side="left", fill="both", expand=True, padx=3)
            tk.Label(sf3, textvariable=sv, bg=sbg, fg=sc,
                     font=(self.FONT, 24, "bold")).pack()
            tk.Label(sf3, text=slbl, bg=sbg, fg=TEXTG, font=(self.FONT, 11)).pack()

        # Focus pie chart
        focus_chf = tk.Frame(win, bg=CARD)
        focus_chf.pack(fill="x", padx=20, pady=(0, 12))
        tk.Label(focus_chf, text="🎯 专注时间分布", bg=CARD, fg=TEXT,
                 font=(self.FONT, 12, "bold")).pack(anchor="w", pady=(0, 4))
        s_focus_pie = tk.Canvas(focus_chf, bg=CARD, highlightthickness=0, height=140)
        s_focus_pie.pack(fill="x")
        s_focus_top3 = tk.Label(focus_chf, text="", bg=CARD, fg=TEXT,
                                 font=(self.FONT, 10), anchor="w")
        s_focus_top3.pack(fill="x", pady=(4, 0))

        # Reflection
        tk.Label(win, text="💭 反思与展望", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 13, "bold")).pack(anchor="w", padx=20, pady=(4, 0))
        ref_t = tk.Text(win, height=5, font=(self.FONT, 13), relief="flat",
                        bg="white", fg=TEXT, bd=1, padx=10, pady=8, wrap="word",
                        highlightthickness=1, highlightbackground=BORDER)
        ref_t.pack(fill="x", padx=20, pady=(6, 8))
        sav = clickable_label(win, "保存反思  💾", GREEN, TEXT,
                              (self.FONT, 13, "bold"), lambda: None, 0, 9)
        sav.pack(fill="x", padx=20, pady=(0, 18))
        hover_bind(sav, GREEN2, GREEN)

        def get_key():
            today = date.today(); t, off = state["t"], state["off"]
            if t == "week": return "w_" + dk(monday_of(today) + timedelta(weeks=off))
            if t == "month":
                y = today.year + ((today.month - 1 + off) // 12)
                m = (today.month - 1 + off) % 12 + 1
                return f"m_{y}_{m}"
            return f"y_{today.year + off}"

        def do_save():
            reflection_save(get_key(), ref_t.get("1.0", "end-1c"))
            sav.configure(text="已保存 ✓")
            win.after(2000, lambda: sav.configure(text="保存反思  💾"))

        sav.bind("<Button-1>", lambda e: do_save())

        def refresh():
            today = date.today(); t, off = state["t"], state["off"]
            if t == "week":
                mon = monday_of(today) + timedelta(weeks=off); sun = mon + timedelta(6)
                period_v.set(f"{mon.month}月{mon.day}日 — {sun.month}月{sun.day}日")
                sk, ek = dk(mon), dk(sun)
                wd   = weight_for_week(mon)
                lbls = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                wts  = [d["w"]  for d in wd]
                wss  = [d["ws"] for d in wd]
            elif t == "month":
                y = today.year + ((today.month - 1 + off) // 12)
                m = (today.month - 1 + off) % 12 + 1
                period_v.set(f"{y}年{m}月")
                sk = f"{y}-{m:02d}-01"; ek = dk(date(y, m, cal_mod.monthrange(y, m)[1]))
                md   = weight_for_month(y, m)
                lbls = [d["label"] for d in md]
                wts  = [d["w"]  for d in md]
                wss  = [d["ws"] for d in md]
            else:
                yr = today.year + off; period_v.set(f"{yr}年")
                sk = f"{yr}-01-01"; ek = f"{yr}-12-31"
                yd   = weight_for_year(yr)
                lbls = [d["label"] for d in yd]
                wts  = [d["w"]  for d in yd]
                wss  = [d["ws"] for d in yd]
            win.after(60, lambda: (
                self._draw_chart(s_wt, lbls, wts, "#FF9F7F"),
                self._draw_chart(s_ws, lbls, wss, "#74B9FF")
            ))
            tasks = tasks_in_range(sk, ek); done = [t2 for t2 in tasks if t2.get("done")]
            sv_u.set(str(sum(1 for t2 in done if t2["pri"] == "u")))
            sv_i.set(str(sum(1 for t2 in done if t2["pri"] == "i")))
            sv_n.set(str(sum(1 for t2 in done if t2["pri"] == "n")))
            # Focus pie chart
            f_sessions = focus_in_range(sk, ek)
            f_agg = focus_aggregated(f_sessions)
            def _draw_focus():
                pw = s_focus_pie.winfo_width()
                if pw < 10: pw = 400
                self._draw_pie_chart(s_focus_pie, f_agg, pw, 130)
                if f_agg:
                    top3 = sorted(f_agg.items(), key=lambda x: -x[1])[:3]
                    parts = []
                    for nm, dur in top3:
                        hrs = int(dur // 3600); mins = int((dur % 3600) // 60)
                        ts = f"{hrs}h{mins:02d}m" if hrs else f"{mins}m"
                        parts.append(f"{nm}(共{ts})")
                    s_focus_top3.configure(text="耗时最长: " + "  ".join(parts))
                else:
                    s_focus_top3.configure(text="")
            win.after(100, _draw_focus)
            ref_t.delete("1.0", "end"); ref_t.insert("1.0", reflection_get(get_key()))
            upd_tabs()

        win.bind("<Escape>", lambda e: win.destroy())
        refresh()


    # ──────────────────────────────────────────────────────────────
    # 胡思乱想 DIALOG
    # ──────────────────────────────────────────────────────────────
    def _open_thoughts(self):
        win = tk.Toplevel(self.root); win.title("💭 胡思乱想")
        win.configure(bg=BG); win.resizable(True, True); win.grab_set()
        self._center(win, 920, 720)

        main = tk.Frame(win, bg=BG)
        main.pack(fill="both", expand=True, padx=10, pady=10)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)

        # ── Left panel ──
        left_card = RCard(main, r=16, bg=CARD)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left_card.inner.columnconfigure(0, weight=1)
        left_card.inner.rowconfigure(1, weight=1)

        tab_row = tk.Frame(left_card.inner, bg=CARD)
        tab_row.grid(row=0, column=0, sticky="ew", padx=8, pady=(10, 6))

        list_scroll = ScrollFrame(left_card.inner, bg=CARD)
        list_scroll.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 8))
        list_frame = list_scroll.inner

        tab_var = tk.StringVar(value="year")
        tab_btns = {}

        def refresh_list():
            for w in list_frame.winfo_children(): w.destroy()
            items = sorted(thoughts_by_type(tab_var.get()),
                           key=lambda x: x["period"], reverse=True)
            if not items:
                tk.Label(list_frame, text="暂无记录~", bg=CARD, fg=TEXTL,
                         font=(self.FONT, 12)).pack(pady=30)
                return
            for item in items:
                card = tk.Frame(list_frame, bg=PINK, pady=8, padx=10)
                card.pack(fill="x", pady=3, padx=4)
                top = tk.Frame(card, bg=PINK); top.pack(fill="x")
                tk.Label(top, text=item["created"], bg=PINK, fg=TEXTG,
                         font=(self.FONT, 9)).pack(side="left")
                tk.Label(top, text=period_label(item["type"], item["period"]),
                         bg=PINK, fg=PINK3, font=(self.FONT, 11, "bold")).pack(side="right")
                c_lbl = tk.Label(card, text=item["content"], bg=PINK, fg=TEXT,
                                 font=(self.FONT, 11), anchor="nw", justify="left",
                                 wraplength=230)
                c_lbl.pack(fill="x", pady=(4, 0))
                c_lbl.bind("<Configure>", lambda e, l=c_lbl: l.config(wraplength=max(1, e.width - 8)))
                def on_dbl(e, it=item):
                    self._open_thought_edit(it, refresh_list)
                for w in (card, top, c_lbl):
                    w.bind("<Double-Button-1>", on_dbl)

        def switch_tab(t):
            tab_var.set(t)
            for tid, b in tab_btns.items():
                b.configure(bg=PINK2 if t == tid else PINK,
                            fg=TEXT if t == tid else TEXTG)
            refresh_list()

        for tid, tlbl in [("year", "年计划"), ("month", "月计划"), ("week", "周计划")]:
            b = clickable_label(tab_row, tlbl, PINK, TEXTG,
                                (self.FONT, 11, "bold"),
                                lambda t=tid: switch_tab(t), 6, 5)
            b.pack(side="left", fill="x", expand=True, padx=1)
            hover_bind(b, PINK2, PINK)
            tab_btns[tid] = b
        switch_tab("year")

        # ── Right panel ──
        right_card = RCard(main, r=16, bg=CARD)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right_card.inner.columnconfigure(0, weight=1)

        tk.Label(right_card.inner, text="💭 胡思乱想", bg=CARD, fg=TEXT,
                 font=(self.FONT, 16, "bold")).pack(pady=(16, 10), padx=20, anchor="w")

        rf = tk.Frame(right_card.inner, bg=CARD, padx=20); rf.pack(fill="x")

        tk.Label(rf, text="类型", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 12, "bold")).pack(anchor="w")
        type_f = tk.Frame(rf, bg=CARD); type_f.pack(fill="x", pady=(4, 8))
        type_var = tk.StringVar(value="year"); type_btns = {}

        period_frame = tk.Frame(rf, bg=CARD); period_frame.pack(fill="x", pady=(0, 8))
        year_var  = tk.StringVar(value=str(date.today().year))
        month_var = tk.StringVar(value=str(date.today().month))
        week_var  = tk.StringVar(value=str(date.today().isocalendar()[1]))

        def upd_period_ui():
            for w in period_frame.winfo_children(): w.destroy()
            t = type_var.get()
            inner = tk.Frame(period_frame, bg=CARD); inner.pack(anchor="w")
            entry_kw = dict(font=(self.FONT, 12), relief="flat", bg="#FFF8EE", bd=1,
                            highlightthickness=1, highlightbackground=BORDER)
            tk.Label(inner, text="年份", bg=CARD, fg=TEXTG,
                     font=(self.FONT, 11)).grid(row=0, column=0, padx=(0, 4))
            tk.Entry(inner, textvariable=year_var, width=6,
                     **entry_kw).grid(row=0, column=1, padx=(0, 12))
            if t == "month":
                tk.Label(inner, text="月份", bg=CARD, fg=TEXTG,
                         font=(self.FONT, 11)).grid(row=0, column=2, padx=(0, 4))
                tk.Entry(inner, textvariable=month_var, width=4,
                         **entry_kw).grid(row=0, column=3)
            elif t == "week":
                tk.Label(inner, text="第", bg=CARD, fg=TEXTG,
                         font=(self.FONT, 11)).grid(row=0, column=2, padx=(0, 2))
                tk.Entry(inner, textvariable=week_var, width=4,
                         **entry_kw).grid(row=0, column=3)
                tk.Label(inner, text="周", bg=CARD, fg=TEXTG,
                         font=(self.FONT, 11)).grid(row=0, column=4, padx=(2, 0))

        def upd_type():
            for tid, b in type_btns.items():
                b.configure(bg=ACCENT if type_var.get() == tid else "#FFF8EE", fg=TEXT)
            upd_period_ui()

        for tid, tlbl in [("year", "年计划"), ("month", "月计划"), ("week", "周计划")]:
            b = tk.Label(type_f, text=tlbl, bg="#FFF8EE", fg=TEXT,
                         font=(self.FONT, 12, "bold"), padx=8, pady=6, cursor="hand2")
            b.pack(side="left", fill="x", expand=True, padx=2)
            b.bind("<Button-1>", lambda e, t=tid: (type_var.set(t), upd_type()))
            type_btns[tid] = b
        upd_type()

        tk.Label(rf, text="内容", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 12, "bold")).pack(anchor="w")
        content_t = tk.Text(rf, font=(self.FONT, 13), relief="flat", bg="#FFF8EE",
                            fg=TEXT, bd=1, height=11, highlightthickness=1,
                            highlightbackground=BORDER, wrap="word", padx=8, pady=6)
        content_t.pack(fill="x", pady=(4, 12))

        def get_period_str():
            t = type_var.get(); y = int(year_var.get().strip())
            if t == "year":  return str(y)
            m = int(month_var.get().strip())
            if t == "month": return f"{y}-{m:02d}"
            w = int(week_var.get().strip())
            return f"{y}-W{w:02d}"

        def do_add():
            content = content_t.get("1.0", "end-1c").strip()
            if not content:
                messagebox.showwarning("提示", "请输入内容！", parent=win); return
            try:
                period = get_period_str()
            except (ValueError, AttributeError):
                messagebox.showwarning("提示", "请输入有效的年份/月份/周数！", parent=win); return
            thought_add(type_var.get(), period, content)
            content_t.delete("1.0", "end")
            switch_tab(type_var.get())

        add_btn = clickable_label(rf, "添加  💭", ACCENT, TEXT,
                                  (self.FONT, 14, "bold"), do_add, 0, 12)
        add_btn.pack(fill="x"); hover_bind(add_btn, ACCENT2, ACCENT)
        win.bind("<Escape>", lambda e: win.destroy())

    def _open_thought_edit(self, item, refresh_fn):
        pop = tk.Toplevel(self.root); pop.title("编辑")
        pop.configure(bg=CARD); pop.resizable(False, False); pop.grab_set()
        self._center(pop, 440, 420)

        tk.Label(pop, text="✏️ 编辑计划", bg=CARD, fg=TEXT,
                 font=(self.FONT, 16, "bold")).pack(pady=(18, 4))
        tk.Label(pop, text=period_label(item["type"], item["period"]),
                 bg=ACCENT, fg=TEXT, font=(self.FONT, 12, "bold"),
                 padx=10, pady=4).pack(pady=(0, 10))

        f = tk.Frame(pop, bg=CARD, padx=24); f.pack(fill="x")
        tk.Label(f, text="内容", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 12, "bold")).pack(anchor="w")
        content_t = tk.Text(f, font=(self.FONT, 13), relief="flat", bg="#FFF8EE",
                            fg=TEXT, bd=1, height=9, highlightthickness=1,
                            highlightbackground=BORDER, wrap="word", padx=8, pady=6)
        content_t.pack(fill="x", pady=(4, 12))
        content_t.insert("1.0", item["content"])

        bf = tk.Frame(f, bg=CARD); bf.pack(fill="x", pady=(0, 8))

        def do_save():
            content = content_t.get("1.0", "end-1c").strip()
            if not content:
                messagebox.showwarning("提示", "内容不能为空！", parent=pop); return
            thought_edit(item["id"], item["type"], item["period"], content)
            pop.destroy(); refresh_fn()

        def do_del():
            if messagebox.askyesno("确认",
                    f"删除这条{period_label(item['type'], item['period'])}的记录？", parent=pop):
                thought_del(item["id"]); pop.destroy(); refresh_fn()

        save_btn = clickable_label(bf, "💾 保存", GREEN, TEXT, (self.FONT, 12, "bold"), do_save, 0, 10)
        save_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        hover_bind(save_btn, GREEN2, GREEN)
        del_btn = clickable_label(bf, "🗑 删除", "#FFEEEE", URGENT, (self.FONT, 12, "bold"), do_del, 0, 10)
        del_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))
        hover_bind(del_btn, "#FFD0D0", "#FFEEEE")
        pop.bind("<Escape>", lambda e: pop.destroy())

    # ──────────────────────────────────────────────────────────────
    # FINANCE (记账) DIALOG
    # ──────────────────────────────────────────────────────────────
    def _open_finance(self):
        win = tk.Toplevel(self.root)
        win.title("💰 记账本")
        win.configure(bg=BG)
        win.option_add('*TCombobox*Listbox.font', (self.FONT, 14))
        win.resizable(True, True)
        win.grab_set()
        self._center(win, 1000, 700)

        today = date.today()
        state = {"tab": "month", "off": 0}

        main = tk.Frame(win, bg=BG)
        main.pack(fill="both", expand=True, padx=10, pady=10)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        # ── Left Panel (History) ──
        left_card = RCard(main, r=16, bg=CARD)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left_card.inner.columnconfigure(0, weight=1)
        left_card.inner.rowconfigure(2, weight=1)

        tab_row = tk.Frame(left_card.inner, bg=CARD)
        tab_row.grid(row=0, column=0, sticky="ew", padx=8, pady=(10, 4))
        tab_btns = {}

        nav_row = tk.Frame(left_card.inner, bg=CARD)
        nav_row.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))
        period_var = tk.StringVar()

        list_scroll = ScrollFrame(left_card.inner, bg=CARD)
        list_scroll.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0, 4))
        list_frame = list_scroll.inner

        sum_frame = tk.Frame(left_card.inner, bg="#FFF8EE", padx=10, pady=8)
        sum_frame.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 8))
        sum_inc_v = tk.StringVar(value="收入: ¥0.00")
        sum_exp_v = tk.StringVar(value="支出: ¥0.00")
        sum_bal_v = tk.StringVar(value="结余: ¥0.00")
        tk.Label(sum_frame, textvariable=sum_inc_v, bg="#FFF8EE", fg="#2E7D32",
                 font=(self.FONT, 11, "bold")).pack(anchor="w")
        tk.Label(sum_frame, textvariable=sum_exp_v, bg="#FFF8EE", fg="#D32F2F",
                 font=(self.FONT, 11, "bold")).pack(anchor="w")
        tk.Label(sum_frame, textvariable=sum_bal_v, bg="#FFF8EE", fg=TEXT,
                 font=(self.FONT, 13, "bold")).pack(anchor="w")

        # ── Right Panel (Input) ──
        right_card = RCard(main, r=16, bg=CARD)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right_card.inner.columnconfigure(0, weight=1)

        export_f = tk.Frame(right_card.inner, bg=CARD)
        export_f.pack(side="bottom", fill="x", padx=12, pady=(0, 10))
        exp_btn = clickable_label(export_f, "📤 导出记录", GREEN, TEXT,
                                  (self.FONT, 11, "bold"),
                                  lambda: self._open_finance_export(win), 10, 6)
        exp_btn.pack(side="right")
        hover_bind(exp_btn, GREEN2, GREEN)

        ms_frame = tk.Frame(right_card.inner, bg=GREEN, padx=12, pady=8)
        ms_frame.pack(fill="x", padx=12, pady=(12, 8))
        ms_var = tk.StringVar()
        tk.Label(ms_frame, textvariable=ms_var, bg=GREEN, fg=TEXT,
                 font=(self.FONT, 12, "bold"), justify="left", anchor="w").pack(fill="x")

        tk.Label(right_card.inner, text="💰 添加记录", bg=CARD, fg=TEXT,
                 font=(self.FONT, 14, "bold")).pack(anchor="w", padx=20, pady=(4, 6))

        rf = tk.Frame(right_card.inner, bg=CARD, padx=20)
        rf.pack(fill="x")

        tk.Label(rf, text="收支类型", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 13, "bold")).pack(anchor="w")
        ft_frame = tk.Frame(rf, bg=CARD)
        ft_frame.pack(fill="x", pady=(2, 6))
        ft_var = tk.StringVar(value="expense")
        ft_btns = {}
        cat_var = tk.StringVar()

        def upd_ft():
            for ft, b in ft_btns.items():
                sel = ft_var.get() == ft
                b.configure(bg=(GREEN if ft == "income" else PINK2) if sel else "#FFF8EE",
                            fg=TEXT if sel else TEXTG)
            cats = FINANCE_INCOME_CATS if ft_var.get() == "income" else FINANCE_EXPENSE_CATS
            cat_cb["values"] = cats
            if cat_var.get() not in cats:
                cat_var.set(cats[0])

        for ft, flbl in [("income", "存入"), ("expense", "支出")]:
            b = tk.Label(ft_frame, text=flbl, bg="#FFF8EE", fg=TEXTG,
                         font=(self.FONT, 14, "bold"), padx=12, pady=5, cursor="hand2")
            b.pack(side="left", fill="x", expand=True, padx=2)
            b.bind("<Button-1>", lambda e, t=ft: (ft_var.set(t), upd_ft()))
            ft_btns[ft] = b

        tk.Label(rf, text="日期", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 13, "bold")).pack(anchor="w")
        d_frame = tk.Frame(rf, bg=CARD)
        d_frame.pack(fill="x", pady=(2, 6))
        entry_kw = dict(font=(self.FONT, 13), relief="flat", bg="#FFF8EE", fg=TEXT,
                        bd=1, highlightthickness=1, highlightbackground=BORDER)
        yr_var = tk.StringVar(value=str(today.year))
        mo_var = tk.StringVar(value=str(today.month))
        dy_var = tk.StringVar(value=str(today.day))
        tk.Entry(d_frame, textvariable=yr_var, width=5, **entry_kw).pack(side="left")
        tk.Label(d_frame, text="年", bg=CARD, fg=TEXTG, font=(self.FONT, 12)).pack(side="left", padx=(1, 4))
        ttk.Combobox(d_frame, textvariable=mo_var, values=[str(m) for m in range(1, 13)],
                     state="readonly", width=3, font=(self.FONT, 14)).pack(side="left")
        tk.Label(d_frame, text="月", bg=CARD, fg=TEXTG, font=(self.FONT, 12)).pack(side="left", padx=(1, 4))
        ttk.Combobox(d_frame, textvariable=dy_var, values=[str(d2) for d2 in range(1, 32)],
                     state="readonly", width=3, font=(self.FONT, 14)).pack(side="left")
        tk.Label(d_frame, text="日", bg=CARD, fg=TEXTG, font=(self.FONT, 12)).pack(side="left", padx=(1, 0))

        tk.Label(rf, text="金额", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 13, "bold")).pack(anchor="w")
        a_frame = tk.Frame(rf, bg=CARD)
        a_frame.pack(fill="x", pady=(2, 6))
        amt_e = tk.Entry(a_frame, font=(self.FONT, 14, "bold"), relief="flat",
                         bg="#FFF8EE", fg=TEXT, bd=1, width=10,
                         highlightthickness=1, highlightbackground=BORDER)
        amt_e.pack(side="left", ipady=3)
        tk.Label(a_frame, text="元", bg=CARD, fg=TEXTG, font=(self.FONT, 13)).pack(side="left", padx=4)

        tk.Label(rf, text="分类", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 13, "bold")).pack(anchor="w")
        cat_cb = ttk.Combobox(rf, textvariable=cat_var, state="readonly",
                              width=10, font=(self.FONT, 14))
        cat_cb.pack(anchor="w", pady=(2, 6))

        tk.Label(rf, text="备注", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 13, "bold")).pack(anchor="w")
        note_e = tk.Entry(rf, font=(self.FONT, 13), relief="flat",
                          bg="#FFF8EE", fg=TEXT, bd=1,
                          highlightthickness=1, highlightbackground=BORDER)
        note_e.pack(fill="x", pady=(2, 8), ipady=3)

        upd_ft()

        def upd_ms():
            try:
                y = int(yr_var.get()); m = int(mo_var.get())
            except (ValueError, TypeError):
                y, m = today.year, today.month
            recs = finance_for_month(y, m)
            inc = sum(r["amount"] for r in recs if r["ftype"] == "income")
            exp = sum(r["amount"] for r in recs if r["ftype"] == "expense")
            bal = inc - exp
            sign = "+" if bal >= 0 else ""
            ms_var.set(f"📊 {y}年{m}月  |  收入: ¥{inc:.2f}  支出: ¥{exp:.2f}  结余: {sign}¥{bal:.2f}")

        def get_range():
            t, off = state["tab"], state["off"]
            if t == "year":
                y = today.year + off
                return f"{y}-01-01", f"{y}-12-31", f"{y}年"
            elif t == "month":
                y = today.year + ((today.month - 1 + off) // 12)
                m = (today.month - 1 + off) % 12 + 1
                last = cal_mod.monthrange(y, m)[1]
                return f"{y}-{m:02d}-01", f"{y}-{m:02d}-{last:02d}", f"{y}年{m}月"
            else:
                mon = monday_of(today) + timedelta(weeks=off)
                sun = mon + timedelta(6)
                return dk(mon), dk(sun), f"{mon.month}月{mon.day}日—{sun.month}月{sun.day}日"

        def refresh():
            sk, ek, label = get_range()
            period_var.set(label)
            for tid, b in tab_btns.items():
                b.configure(bg=ACCENT if state["tab"] == tid else "#FFF8EE",
                            fg=TEXT if state["tab"] == tid else TEXTG)
            records = sorted(finance_in_range(sk, ek), key=lambda r: r["date"])
            for w in list_frame.winfo_children(): w.destroy()
            if not records:
                tk.Label(list_frame, text="暂无记录~", bg=CARD, fg=TEXTL,
                         font=(self.FONT, 12)).pack(pady=30)
            else:
                for r in records:
                    is_inc = r["ftype"] == "income"
                    rbg = "#F0FFF0" if is_inc else "#FFF5F5"
                    row = tk.Frame(list_frame, bg=rbg, pady=4, padx=8)
                    row.pack(fill="x", pady=2, padx=4)
                    top = tk.Frame(row, bg=rbg); top.pack(fill="x")
                    sign = "+" if is_inc else "-"
                    clr = "#2E7D32" if is_inc else "#D32F2F"
                    tk.Label(top, text=f"{sign}¥{r['amount']:.2f}",
                             bg=rbg, fg=clr,
                             font=(self.FONT, 12, "bold")).pack(side="left")
                    cbg = GREEN if is_inc else PINK
                    tk.Label(top, text=r["category"], bg=cbg, fg=TEXT,
                             font=(self.FONT, 9), padx=4, pady=1).pack(side="left", padx=6)
                    tk.Label(top, text=r["date"], bg=rbg, fg=TEXTG,
                             font=(self.FONT, 9)).pack(side="right")
                    if r.get("note"):
                        tk.Label(row, text=f"📝 {r['note']}", bg=rbg, fg=TEXTG,
                                 font=(self.FONT, 9), anchor="w").pack(fill="x", pady=(2, 0))
                    def on_dbl(e, item=r):
                        self._open_finance_edit(item, refresh)
                    for w in row.winfo_children(): w.bind("<Double-Button-1>", on_dbl)
                    row.bind("<Double-Button-1>", on_dbl)

            def bind_scroll(w):
                w.bind("<MouseWheel>", lambda e: list_scroll._c.yview_scroll(
                    int(-1 * (e.delta / 120)), "units"))
                for ch in w.winfo_children(): bind_scroll(ch)
            bind_scroll(list_frame)

            inc = sum(r["amount"] for r in records if r["ftype"] == "income")
            exp = sum(r["amount"] for r in records if r["ftype"] == "expense")
            bal = inc - exp
            sign = "+" if bal >= 0 else ""
            sum_inc_v.set(f"收入: ¥{inc:.2f}")
            sum_exp_v.set(f"支出: ¥{exp:.2f}")
            sum_bal_v.set(f"结余: {sign}¥{bal:.2f}")
            upd_ms()
            self._render_finance_summary()

        def switch_tab(t):
            state["tab"] = t; state["off"] = 0; refresh()

        for tid, tlbl in [("year", "年"), ("month", "月"), ("week", "周")]:
            b = clickable_label(tab_row, tlbl, "#FFF8EE", TEXTG,
                                (self.FONT, 12, "bold"),
                                lambda t=tid: switch_tab(t), 12, 5)
            b.pack(side="left", fill="x", expand=True, padx=2)
            hover_bind(b, ACCENT, "#FFF8EE")
            tab_btns[tid] = b

        prev_b = self._circle_btn(nav_row, "‹", BORDER, "#E0D0C0",
            lambda: (state.__setitem__("off", state["off"] - 1), refresh()))
        prev_b.pack(side="left")
        tk.Label(nav_row, textvariable=period_var, bg=CARD, fg=TEXT,
                 font=(self.FONT, 13, "bold"), width=18).pack(side="left", expand=True)
        next_b = self._circle_btn(nav_row, "›", BORDER, "#E0D0C0",
            lambda: (state.__setitem__("off", state["off"] + 1), refresh()))
        next_b.pack(side="right")

        def do_add():
            try:
                y = int(yr_var.get()); m = int(mo_var.get()); d2 = int(dy_var.get())
                ds = f"{y}-{m:02d}-{d2:02d}"
                date.fromisoformat(ds)
            except (ValueError, TypeError):
                messagebox.showwarning("提示", "请输入有效日期！", parent=win); return
            amt = amt_e.get().strip()
            if not amt:
                messagebox.showwarning("提示", "请输入金额！", parent=win); return
            try: amt_f = float(amt)
            except ValueError:
                messagebox.showwarning("提示", "请输入有效金额！", parent=win); return
            cat = cat_var.get()
            if not cat:
                messagebox.showwarning("提示", "请选择分类！", parent=win); return
            finance_add(ft_var.get(), cat, amt_f, ds, note_e.get().strip())
            amt_e.delete(0, "end"); note_e.delete(0, "end")
            refresh()

        add_btn = clickable_label(rf, "添加记录  💰", ACCENT, TEXT,
                                  (self.FONT, 13, "bold"), do_add, 0, 10)
        add_btn.pack(fill="x", pady=(2, 0))
        hover_bind(add_btn, ACCENT2, ACCENT)

        yr_var.trace("w", lambda *_: upd_ms())
        mo_var.trace("w", lambda *_: upd_ms())
        refresh()
        win.bind("<Escape>", lambda e: win.destroy())

    def _open_finance_edit(self, item, refresh_fn):
        pop = tk.Toplevel(self.root)
        pop.title("编辑记录")
        pop.configure(bg=CARD); pop.resizable(False, False); pop.grab_set()
        pop.option_add('*TCombobox*Listbox.font', (self.FONT, 12))
        self._center(pop, 380, 460)

        tk.Label(pop, text="✏️ 编辑记录", bg=CARD, fg=TEXT,
                 font=(self.FONT, 16, "bold")).pack(pady=(16, 8))
        f = tk.Frame(pop, bg=CARD, padx=20); f.pack(fill="x")

        tk.Label(f, text="类型", bg=CARD, fg=TEXTG, font=(self.FONT, 11, "bold")).pack(anchor="w")
        ft_f = tk.Frame(f, bg=CARD); ft_f.pack(fill="x", pady=(2, 6))
        ft_v = tk.StringVar(value=item["ftype"])
        ft_b = {}
        cat_v = tk.StringVar(value=item["category"])

        def upd_e():
            for ft, b in ft_b.items():
                sel = ft_v.get() == ft
                b.configure(bg=(GREEN if ft == "income" else PINK2) if sel else "#FFF8EE",
                            fg=TEXT if sel else TEXTG)
            cats = FINANCE_INCOME_CATS if ft_v.get() == "income" else FINANCE_EXPENSE_CATS
            cc["values"] = cats
            if cat_v.get() not in cats: cat_v.set(cats[0])

        for ft, flbl in [("income", "存入"), ("expense", "支出")]:
            b = tk.Label(ft_f, text=flbl, bg="#FFF8EE", fg=TEXTG,
                         font=(self.FONT, 11, "bold"), padx=8, pady=4, cursor="hand2")
            b.pack(side="left", fill="x", expand=True, padx=2)
            b.bind("<Button-1>", lambda e, t=ft: (ft_v.set(t), upd_e()))
            ft_b[ft] = b

        tk.Label(f, text="日期 (YYYY-MM-DD)", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 11, "bold")).pack(anchor="w")
        de = tk.Entry(f, font=(self.FONT, 12), relief="flat", bg="#FFF8EE", fg=TEXT,
                      bd=1, highlightthickness=1, highlightbackground=BORDER)
        de.pack(fill="x", pady=(2, 6), ipady=3)
        de.insert(0, item["date"])

        tk.Label(f, text="金额", bg=CARD, fg=TEXTG, font=(self.FONT, 11, "bold")).pack(anchor="w")
        ae = tk.Entry(f, font=(self.FONT, 12), relief="flat", bg="#FFF8EE", fg=TEXT,
                      bd=1, highlightthickness=1, highlightbackground=BORDER)
        ae.pack(fill="x", pady=(2, 6), ipady=3)
        ae.insert(0, str(item["amount"]))

        tk.Label(f, text="分类", bg=CARD, fg=TEXTG, font=(self.FONT, 11, "bold")).pack(anchor="w")
        cc = ttk.Combobox(f, textvariable=cat_v, state="readonly", width=10, font=(self.FONT, 12))
        cc.pack(anchor="w", pady=(2, 6))

        tk.Label(f, text="备注", bg=CARD, fg=TEXTG, font=(self.FONT, 11, "bold")).pack(anchor="w")
        ne = tk.Entry(f, font=(self.FONT, 11), relief="flat", bg="#FFF8EE", fg=TEXT,
                      bd=1, highlightthickness=1, highlightbackground=BORDER)
        ne.pack(fill="x", pady=(2, 8), ipady=3)
        if item.get("note"): ne.insert(0, item["note"])
        upd_e()

        bf = tk.Frame(f, bg=CARD); bf.pack(fill="x", pady=(0, 8))
        def do_save():
            ds = de.get().strip()
            try: date.fromisoformat(ds)
            except: messagebox.showwarning("提示", "日期格式错误！", parent=pop); return
            try: av = float(ae.get().strip())
            except: messagebox.showwarning("提示", "请输入有效金额！", parent=pop); return
            finance_edit(item["id"], ft_v.get(), cat_v.get(), av, ds, ne.get().strip())
            pop.destroy(); refresh_fn()
        def do_del():
            if messagebox.askyesno("确认", "删除这条记录？", parent=pop):
                finance_del(item["id"]); pop.destroy(); refresh_fn()
        save_b = clickable_label(bf, "💾 保存", GREEN, TEXT, (self.FONT, 11, "bold"), do_save, 0, 8)
        save_b.pack(side="left", fill="x", expand=True, padx=(0, 4))
        hover_bind(save_b, GREEN2, GREEN)
        del_b = clickable_label(bf, "🗑 删除", "#FFEEEE", URGENT, (self.FONT, 11, "bold"), do_del, 0, 8)
        del_b.pack(side="left", fill="x", expand=True, padx=(4, 0))
        hover_bind(del_b, "#FFD0D0", "#FFEEEE")
        pop.bind("<Escape>", lambda e: pop.destroy())

    # ──────────────────────────────────────────────────────────────
    # FINANCE EXPORT
    # ──────────────────────────────────────────────────────────────
    def _open_finance_export(self, parent):
        win = tk.Toplevel(parent)
        win.title("导出记账记录"); win.configure(bg=CARD)
        win.resizable(False, False); win.grab_set()
        self._center(win, 300, 340)

        tk.Label(win, text="📤 导出记账记录", bg=CARD, fg=TEXT,
                 font=(self.FONT, 15, "bold")).pack(pady=(18, 12))
        frm = tk.Frame(win, bg=CARD); frm.pack(fill="x", padx=20)

        def make_btn(label, cmd):
            b = tk.Button(frm, text=label, command=cmd,
                          bg=TOOLBAR, fg=TEXT, font=(self.FONT, 12),
                          relief="flat", cursor="hand2", pady=8, anchor="w", padx=14)
            b.pack(fill="x", pady=3)
            b.bind("<Enter>", lambda e: b.configure(bg=ACCENT))
            b.bind("<Leave>", lambda e: b.configure(bg=TOOLBAR))

        def do_all():
            if messagebox.askyesno("确认", "是否导出全部记账记录？", parent=win):
                win.destroy(); self._export_finance_pdf()

        make_btn("📋 全部导出", do_all)
        make_btn("📅 年导出", lambda: self._finance_export_year(win))
        make_btn("🗓 月导出", lambda: self._finance_export_month(win))
        make_btn("📆 随机日期导出", lambda: self._finance_export_custom(win))

        tk.Button(win, text="取消", command=win.destroy,
                  bg=CARD, fg=TEXTG, font=(self.FONT, 10),
                  relief="flat", cursor="hand2").pack(pady=(8, 14))
        win.bind("<Escape>", lambda e: win.destroy())

    def _finance_export_year(self, export_win):
        records = finance_all()
        years = sorted(set(int(r["date"][:4]) for r in records if len(r["date"]) >= 4))
        if not years:
            messagebox.showinfo("提示", "暂无记账记录！", parent=export_win); return
        win = tk.Toplevel(export_win)
        win.title("年导出"); win.configure(bg=CARD)
        win.resizable(False, False); win.grab_set()
        win.option_add('*TCombobox*Listbox.font', (self.FONT, 13))
        self._center(win, 280, 200)
        tk.Label(win, text="选择年份", bg=CARD, fg=TEXT,
                 font=(self.FONT, 14, "bold")).pack(pady=(18, 8))
        var = tk.StringVar(value=str(years[-1]))
        ttk.Combobox(win, textvariable=var, values=[str(y) for y in reversed(years)],
                     state="readonly", width=10, font=(self.FONT, 13)).pack(pady=4)
        def do_export():
            y = int(var.get())
            if messagebox.askyesno("确认", f"是否导出 {y} 年的记账记录？", parent=win):
                win.destroy(); export_win.destroy()
                self._export_finance_pdf(start_dt=date(y, 1, 1), end_dt=date(y, 12, 31))
        tk.Button(win, text="导出", command=do_export, bg=GREEN, fg=TEXT,
                  font=(self.FONT, 12, "bold"), relief="flat", cursor="hand2",
                  pady=6, padx=20).pack(pady=(10, 4))
        tk.Button(win, text="返回", command=win.destroy, bg=CARD, fg=TEXTG,
                  font=(self.FONT, 10), relief="flat", cursor="hand2").pack(pady=(0, 12))
        win.bind("<Escape>", lambda e: win.destroy())

    def _finance_export_month(self, export_win):
        records = finance_all()
        years = sorted(set(int(r["date"][:4]) for r in records if len(r["date"]) >= 4))
        if not years:
            messagebox.showinfo("提示", "暂无记账记录！", parent=export_win); return
        win = tk.Toplevel(export_win)
        win.title("月导出"); win.configure(bg=CARD)
        win.resizable(False, False); win.grab_set()
        win.option_add('*TCombobox*Listbox.font', (self.FONT, 13))
        self._center(win, 300, 220)
        tk.Label(win, text="选择月份", bg=CARD, fg=TEXT,
                 font=(self.FONT, 14, "bold")).pack(pady=(18, 8))
        row = tk.Frame(win, bg=CARD); row.pack()
        yr_v = tk.StringVar(value=str(years[-1]))
        mo_v = tk.StringVar(value="1")
        ttk.Combobox(row, textvariable=yr_v, values=[str(y) for y in reversed(years)],
                     state="readonly", width=7, font=(self.FONT, 13)).pack(side="left", padx=3)
        tk.Label(row, text="年", bg=CARD, fg=TEXT, font=(self.FONT, 12)).pack(side="left")
        ttk.Combobox(row, textvariable=mo_v, values=[str(m) for m in range(1, 13)],
                     state="readonly", width=4, font=(self.FONT, 13)).pack(side="left", padx=3)
        tk.Label(row, text="月", bg=CARD, fg=TEXT, font=(self.FONT, 12)).pack(side="left")
        def do_export():
            y = int(yr_v.get()); m = int(mo_v.get())
            last = cal_mod.monthrange(y, m)[1]
            if messagebox.askyesno("确认", f"是否导出 {y}年{m}月 的记账记录？", parent=win):
                win.destroy(); export_win.destroy()
                self._export_finance_pdf(start_dt=date(y, m, 1), end_dt=date(y, m, last))
        tk.Button(win, text="导出", command=do_export, bg=GREEN, fg=TEXT,
                  font=(self.FONT, 12, "bold"), relief="flat", cursor="hand2",
                  pady=6, padx=20).pack(pady=(10, 4))
        tk.Button(win, text="返回", command=win.destroy, bg=CARD, fg=TEXTG,
                  font=(self.FONT, 10), relief="flat", cursor="hand2").pack(pady=(0, 12))
        win.bind("<Escape>", lambda e: win.destroy())

    def _finance_export_custom(self, export_win):
        win = tk.Toplevel(export_win)
        win.title("随机日期导出"); win.configure(bg=CARD)
        win.resizable(False, False); win.grab_set()
        self._center(win, 340, 260)
        tk.Label(win, text="选择日期范围", bg=CARD, fg=TEXT,
                 font=(self.FONT, 14, "bold")).pack(pady=(18, 8))
        f = tk.Frame(win, bg=CARD, padx=20); f.pack(fill="x")
        today = date.today()
        tk.Label(f, text="开始日期 (YYYY-MM-DD)", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 11)).pack(anchor="w")
        se = tk.Entry(f, font=(self.FONT, 12), relief="flat", bg="#FFF8EE", fg=TEXT,
                      bd=1, highlightthickness=1, highlightbackground=BORDER)
        se.pack(fill="x", pady=(2, 6), ipady=3)
        se.insert(0, f"{today.year}-01-01")
        tk.Label(f, text="结束日期 (YYYY-MM-DD)", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 11)).pack(anchor="w")
        ee = tk.Entry(f, font=(self.FONT, 12), relief="flat", bg="#FFF8EE", fg=TEXT,
                      bd=1, highlightthickness=1, highlightbackground=BORDER)
        ee.pack(fill="x", pady=(2, 8), ipady=3)
        ee.insert(0, dk(today))
        def do_export():
            try:
                sd = date.fromisoformat(se.get().strip())
                ed = date.fromisoformat(ee.get().strip())
            except ValueError:
                messagebox.showwarning("提示", "日期格式错误！", parent=win); return
            if sd > ed:
                messagebox.showwarning("提示", "开始日期不能大于结束日期！", parent=win); return
            if messagebox.askyesno("确认",
                    f"是否导出 {sd.year}年{sd.month}月{sd.day}日 至 "
                    f"{ed.year}年{ed.month}月{ed.day}日 的记账记录？", parent=win):
                win.destroy(); export_win.destroy()
                self._export_finance_pdf(start_dt=sd, end_dt=ed)
        tk.Button(win, text="导出", command=do_export, bg=GREEN, fg=TEXT,
                  font=(self.FONT, 12, "bold"), relief="flat", cursor="hand2",
                  pady=6, padx=20).pack(pady=(4, 4))
        tk.Button(win, text="返回", command=win.destroy, bg=CARD, fg=TEXTG,
                  font=(self.FONT, 10), relief="flat", cursor="hand2").pack(pady=(0, 12))
        win.bind("<Escape>", lambda e: win.destroy())

    # ──────────────────────────────────────────────────────────────
    # FINANCE PDF EXPORT
    # ──────────────────────────────────────────────────────────────
    def _export_finance_pdf(self, start_dt=None, end_dt=None):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors as rc
            from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                             PageBreak, Table, TableStyle)
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError:
            messagebox.showwarning("提示",
                "请先安装 reportlab：\npip install reportlab\n然后重新运行程序。")
            return

        font_candidates = [
            ("C:/Windows/Fonts/msyh.ttc", True),
            ("C:/Windows/Fonts/simsun.ttc", True),
            ("C:/Windows/Fonts/simhei.ttf", False),
        ]
        registered = False
        reg_fp = None; reg_ttc = False
        for fp, is_ttc in font_candidates:
            if not os.path.exists(fp): continue
            try:
                if is_ttc:
                    pdfmetrics.registerFont(TTFont("CNFont", fp, subfontIndex=0))
                else:
                    pdfmetrics.registerFont(TTFont("CNFont", fp))
                registered = True; reg_fp = fp; reg_ttc = is_ttc; break
            except: continue
        if not registered:
            messagebox.showwarning("提示", "找不到合适的中文字体，无法生成PDF。"); return

        bold_candidates = [
            ("C:/Windows/Fonts/msyhbd.ttc", True),
            ("C:/Windows/Fonts/simhei.ttf", False),
            (reg_fp, reg_ttc),
        ]
        for fp_b, is_ttc_b in bold_candidates:
            if not fp_b or not os.path.exists(fp_b): continue
            try:
                if is_ttc_b:
                    pdfmetrics.registerFont(TTFont("CNFontBold", fp_b, subfontIndex=0))
                else:
                    pdfmetrics.registerFont(TTFont("CNFontBold", fp_b))
                break
            except: continue

        out_dir = r"D:\lifeplanner\recording"
        os.makedirs(out_dir, exist_ok=True)
        fname = f"记账本_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        fpath = os.path.join(out_dir, fname)

        PW, PH = A4
        doc = SimpleDocTemplate(fpath, pagesize=A4,
                                leftMargin=2.5*cm, rightMargin=2.5*cm,
                                topMargin=2.2*cm, bottomMargin=2.2*cm)
        body_w = PW - 5*cm

        c_text   = rc.HexColor("#5A4040")
        c_textg  = rc.HexColor("#9A8878")
        c_border = rc.HexColor("#F0E0D0")
        c_inc    = rc.HexColor("#2E7D32")
        c_exp    = rc.HexColor("#D32F2F")

        def S(nm, sz, align=0, color=None, before=0, after=5, font="CNFont"):
            return ParagraphStyle(nm, fontName=font, fontSize=sz,
                                  textColor=color or c_text, alignment=align,
                                  spaceBefore=before, spaceAfter=after,
                                  leading=sz * 1.65)

        s_title   = S("FT",  28, align=1, before=50, after=10, font="CNFontBold")
        s_sub     = S("FSub",13, align=1, after=6, color=c_textg)
        s_year    = S("FYr", 20, before=12, after=6, font="CNFontBold")
        s_month   = S("FMo", 16, before=8,  after=4, font="CNFontBold")
        s_summary = S("FSum",14, before=4,  after=3, font="CNFontBold")
        s_cattot  = S("FCt", 11, before=2,  after=2)
        s_ai      = S("FAI", 10, color=c_inc)
        s_ae      = S("FAE", 10, color=c_exp)
        s_item    = S("FIt", 10, after=2)
        s_note    = S("FNo",  9, after=3, color=c_textg)
        s_dcol    = S("FDc", 10, color=c_textg)

        records = finance_all()
        if start_dt:
            records = [r for r in records if r["date"] >= dk(start_dt)]
        if end_dt:
            records = [r for r in records if r["date"] <= dk(end_dt)]
        if not records:
            messagebox.showinfo("提示", "所选范围内暂无记账记录！"); return
        records.sort(key=lambda r: r["date"])

        from collections import defaultdict
        by_ym = defaultdict(list)
        for r in records:
            by_ym[(int(r["date"][:4]), int(r["date"][5:7]))].append(r)

        story = []
        story.append(Spacer(1, 3*cm))
        story.append(Paragraph("记账本", s_title))
        story.append(Paragraph("Finance Record", s_sub))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(
            f"生成时间：{datetime.now().strftime('%Y年%m月%d日')}",
            S("FDt", 11, align=1, color=c_textg)))
        story.append(PageBreak())

        years = sorted(set(k[0] for k in by_ym))
        for year in years:
            story.append(Paragraph(f"{year}年", s_year))
            story.append(Spacer(1, 0.2*cm))
            months = sorted(k[1] for k in by_ym if k[0] == year)
            for month in months:
                mr = by_ym[(year, month)]
                story.append(Paragraph(f"{month}月", s_month))
                inc = sum(r["amount"] for r in mr if r["ftype"] == "income")
                exp = sum(r["amount"] for r in mr if r["ftype"] == "expense")
                bal = inc - exp
                sign = "+" if bal >= 0 else ""
                story.append(Paragraph(f"收入: ¥{inc:.2f}", s_summary))
                story.append(Paragraph(f"支出: ¥{exp:.2f}", s_summary))
                story.append(Paragraph(f"结余: {sign}¥{bal:.2f}", s_summary))
                cat_totals = {}
                for r in mr:
                    cat = r["category"]
                    if cat == "其他":
                        cat = "收入其他" if r["ftype"] == "income" else "支出其他"
                    cat_totals[cat] = cat_totals.get(cat, 0) + r["amount"]
                for c, v in cat_totals.items():
                    story.append(Paragraph(f"{c}: ¥{v:.2f}", s_cattot))
                t = Table([[""]], colWidths=[body_w], rowHeights=[2])
                t.setStyle(TableStyle([
                    ("LINEBELOW", (0,0), (-1,0), 1.5, c_border),
                    ("TOPPADDING", (0,0), (-1,-1), 0),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 0),
                ]))
                story.append(t)
                story.append(Spacer(1, 0.1*cm))
                for r in sorted(mr, key=lambda x: x["date"]):
                    is_i = r["ftype"] == "income"
                    sg = "+" if is_i else "-"
                    row_data = [[
                        Paragraph(f"{sg}¥{r['amount']:.2f}", s_ai if is_i else s_ae),
                        Paragraph(r["category"], s_item),
                        Paragraph(r["date"], s_dcol),
                    ]]
                    t2 = Table(row_data, colWidths=[body_w*0.3, body_w*0.35, body_w*0.35])
                    t2.setStyle(TableStyle([
                        ("TOPPADDING", (0,0), (-1,-1), 3),
                        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
                        ("LEFTPADDING", (0,0), (-1,-1), 4),
                    ]))
                    story.append(t2)
                    if r.get("note"):
                        story.append(Paragraph(f"备注: {r['note']}", s_note))
                    div = Table([[""]], colWidths=[body_w], rowHeights=[1])
                    div.setStyle(TableStyle([
                        ("LINEBELOW", (0,0), (-1,0), 0.5, c_border),
                        ("TOPPADDING", (0,0), (-1,-1), 0),
                        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
                    ]))
                    story.append(div)
                story.append(Spacer(1, 0.3*cm))

        while story and isinstance(story[-1], (PageBreak, Spacer)):
            story.pop()

        def footer(canvas, _doc):
            canvas.saveState()
            canvas.setFont("CNFont", 9)
            canvas.setFillColor(c_textg)
            canvas.drawRightString(PW - 2.5*cm, 1.3*cm,
                                   f"第 {canvas.getPageNumber()} 页")
            canvas.setStrokeColor(c_border)
            canvas.line(2.5*cm, 1.6*cm, PW - 2.5*cm, 1.6*cm)
            canvas.restoreState()

        try:
            doc.build(story, onFirstPage=footer, onLaterPages=footer)
            messagebox.showinfo("导出成功", f"记账本 PDF 已保存至：\n{fpath}")
        except Exception as e:
            messagebox.showerror("导出失败", f"生成 PDF 时出错：\n{e}")

    # ──────────────────────────────────────────────────────────────
    # EXPORT DIALOG
    # ──────────────────────────────────────────────────────────────
    def _open_export_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("导出记录")
        win.configure(bg=CARD)
        win.resizable(False, False)
        win.grab_set()
        self._center(win, 300, 360)
        win.bind("<Escape>", lambda e: win.destroy())

        tk.Label(win, text="📤 导出记录", bg=CARD, fg=TEXT,
                 font=(self.FONT, 17, "bold")).pack(pady=(22, 14))

        frm = tk.Frame(win, bg=CARD)
        frm.pack(fill="x", padx=24)

        def make_btn(label, cmd):
            b = tk.Button(frm, text=label, command=cmd,
                          bg=TOOLBAR, fg=TEXT, font=(self.FONT, 12),
                          relief="flat", cursor="hand2",
                          pady=8, anchor="w", padx=14)
            b.pack(fill="x", pady=3)
            b.bind("<Enter>", lambda e: b.configure(bg=ACCENT))
            b.bind("<Leave>", lambda e: b.configure(bg=TOOLBAR))

        make_btn("📋  全部导出", lambda: (win.destroy(), self._export_pdf()))
        make_btn("📅  年导出",   lambda: self._export_year_dialog(win))
        make_btn("🗓  月导出",    lambda: self._export_month_dialog(win))
        make_btn("📆  周导出",   lambda: self._export_week_dialog(win))
        make_btn("✏  自由导出",   lambda: self._export_custom_dialog(win))

        tk.Button(win, text="取消", command=win.destroy,
                  bg=CARD, fg=TEXTG, font=(self.FONT, 10),
                  relief="flat", cursor="hand2").pack(pady=(10, 18))

    def _get_data_years(self):
        d = _load()
        thoughts   = d.get("thoughts", [])
        summaries  = d.get("summaries", {})
        tasks_data = d.get("tasks", {})
        yrs = set()
        for k in tasks_data:
            try: yrs.add(int(k[:4]))
            except: pass
        for k in summaries:
            try:
                if k.startswith("y_"):   yrs.add(int(k[2:]))
                elif k.startswith("m_"): yrs.add(int(k.split("_")[1]))
                elif k.startswith("w_"): yrs.add(int(k[2:6]))
            except: pass
        for t in thoughts:
            try: yrs.add(int(t["period"][:4]))
            except: pass
        return sorted(yrs)

    def _export_year_dialog(self, parent):
        years = self._get_data_years()
        if not years:
            messagebox.showinfo("提示", "暂无数据！", parent=parent); return

        win = tk.Toplevel(parent)
        win.title("年导出")
        win.configure(bg=CARD)
        win.resizable(False, False)
        win.grab_set()
        self._center(win, 280, 200)
        win.bind("<Escape>", lambda e: win.destroy())

        tk.Label(win, text="选择导出年份", bg=CARD, fg=TEXT,
                 font=(self.FONT, 14, "bold")).pack(pady=(20, 10))

        var = tk.StringVar(value=str(years[-1]))
        ttk.Combobox(win, textvariable=var,
                     values=[str(y) for y in reversed(years)],
                     state="readonly", width=12,
                     font=(self.FONT, 12)).pack(pady=6)

        def do_export():
            year = int(var.get())
            if messagebox.askyesno("确认", f"导出 {year} 年的全部记录？",
                                   parent=win):
                win.destroy(); parent.destroy()
                self._export_pdf(start_dt=date(year, 1, 1),
                                 end_dt=date(year, 12, 31))

        tk.Button(win, text="导出", command=do_export,
                  bg=GREEN, fg=TEXT, font=(self.FONT, 12, "bold"),
                  relief="flat", cursor="hand2",
                  pady=6, padx=20).pack(pady=(8, 4))
        tk.Button(win, text="返回", command=win.destroy,
                  bg=CARD, fg=TEXTG, font=(self.FONT, 10),
                  relief="flat", cursor="hand2").pack(pady=(0, 14))

    def _export_month_dialog(self, parent):
        years = self._get_data_years()
        if not years:
            messagebox.showinfo("提示", "暂无数据！", parent=parent); return

        win = tk.Toplevel(parent)
        win.title("月导出")
        win.configure(bg=CARD)
        win.resizable(False, False)
        win.grab_set()
        self._center(win, 300, 210)
        win.bind("<Escape>", lambda e: win.destroy())

        tk.Label(win, text="选择导出月份", bg=CARD, fg=TEXT,
                 font=(self.FONT, 14, "bold")).pack(pady=(20, 10))

        row = tk.Frame(win, bg=CARD)
        row.pack()
        yr_var = tk.StringVar(value=str(years[-1]))
        mo_var = tk.StringVar(value="1")
        ttk.Combobox(row, textvariable=yr_var,
                     values=[str(y) for y in reversed(years)],
                     state="readonly", width=8,
                     font=(self.FONT, 12)).pack(side="left", padx=3)
        tk.Label(row, text="年", bg=CARD, fg=TEXT,
                 font=(self.FONT, 12)).pack(side="left")
        ttk.Combobox(row, textvariable=mo_var,
                     values=[str(m) for m in range(1, 13)],
                     state="readonly", width=5,
                     font=(self.FONT, 12)).pack(side="left", padx=3)
        tk.Label(row, text="月", bg=CARD, fg=TEXT,
                 font=(self.FONT, 12)).pack(side="left")

        def do_export():
            year = int(yr_var.get()); month = int(mo_var.get())
            last = cal_mod.monthrange(year, month)[1]
            if messagebox.askyesno("确认",
                    f"导出 {year} 年 {month} 月的记录？", parent=win):
                win.destroy(); parent.destroy()
                self._export_pdf(start_dt=date(year, month, 1),
                                 end_dt=date(year, month, last))

        tk.Button(win, text="导出", command=do_export,
                  bg=GREEN, fg=TEXT, font=(self.FONT, 12, "bold"),
                  relief="flat", cursor="hand2",
                  pady=6, padx=20).pack(pady=(12, 4))
        tk.Button(win, text="返回", command=win.destroy,
                  bg=CARD, fg=TEXTG, font=(self.FONT, 10),
                  relief="flat", cursor="hand2").pack(pady=(0, 14))

    def _export_week_dialog(self, parent):
        years = self._get_data_years()
        if not years:
            messagebox.showinfo("提示", "暂无数据！", parent=parent); return

        win = tk.Toplevel(parent)
        win.title("周导出")
        win.configure(bg=CARD)
        win.resizable(False, False)
        win.grab_set()
        self._center(win, 310, 210)
        win.bind("<Escape>", lambda e: win.destroy())

        tk.Label(win, text="选择导出周", bg=CARD, fg=TEXT,
                 font=(self.FONT, 14, "bold")).pack(pady=(20, 10))

        row = tk.Frame(win, bg=CARD)
        row.pack()
        yr_var = tk.StringVar(value=str(years[-1]))
        wk_var = tk.StringVar(value="1")
        ttk.Combobox(row, textvariable=yr_var,
                     values=[str(y) for y in reversed(years)],
                     state="readonly", width=8,
                     font=(self.FONT, 12)).pack(side="left", padx=3)
        tk.Label(row, text="年  第", bg=CARD, fg=TEXT,
                 font=(self.FONT, 12)).pack(side="left")
        ttk.Combobox(row, textvariable=wk_var,
                     values=[str(w) for w in range(1, 54)],
                     state="readonly", width=5,
                     font=(self.FONT, 12)).pack(side="left", padx=3)
        tk.Label(row, text="周", bg=CARD, fg=TEXT,
                 font=(self.FONT, 12)).pack(side="left")

        def do_export():
            year = int(yr_var.get()); week = int(wk_var.get())
            try:
                start = datetime.strptime(
                    f"{year}-W{week:02d}-1", "%G-W%V-%u").date()
                end = start + timedelta(6)
            except ValueError:
                messagebox.showwarning(
                    "提示", f"{year} 年没有第 {week} 周！", parent=win)
                return
            if messagebox.askyesno("确认",
                    f"导出 {year} 年第 {week} 周\n"
                    f"({start.month}月{start.day}日—"
                    f"{end.month}月{end.day}日)的记录？",
                    parent=win):
                win.destroy(); parent.destroy()
                self._export_pdf(start_dt=start, end_dt=end)

        tk.Button(win, text="导出", command=do_export,
                  bg=GREEN, fg=TEXT, font=(self.FONT, 12, "bold"),
                  relief="flat", cursor="hand2",
                  pady=6, padx=20).pack(pady=(12, 4))
        tk.Button(win, text="返回", command=win.destroy,
                  bg=CARD, fg=TEXTG, font=(self.FONT, 10),
                  relief="flat", cursor="hand2").pack(pady=(0, 14))

    def _export_custom_dialog(self, parent):
        years = self._get_data_years()
        if not years:
            messagebox.showinfo("提示", "暂无数据！", parent=parent); return

        win = tk.Toplevel(parent)
        win.title("自由导出")
        win.configure(bg=CARD)
        win.resizable(False, False)
        win.grab_set()
        self._center(win, 370, 295)
        win.bind("<Escape>", lambda e: win.destroy())

        tk.Label(win, text="✏ 自由导出", bg=CARD, fg=TEXT,
                 font=(self.FONT, 14, "bold")).pack(pady=(18, 6))

        yr_vals = [str(y) for y in reversed(years)]
        mo_vals = [str(m) for m in range(1, 13)]
        wk_vals = [str(w) for w in range(1, 54)]

        range_var = tk.StringVar(value="year")
        rfrm = tk.Frame(win, bg=CARD)
        rfrm.pack(pady=4)
        for val, lbl in [("year", "按年"), ("month", "按月"), ("week", "按周")]:
            tk.Radiobutton(rfrm, text=lbl, variable=range_var, value=val,
                           bg=CARD, fg=TEXT, font=(self.FONT, 11),
                           activebackground=CARD,
                           selectcolor=ACCENT).pack(side="left", padx=12)

        content = tk.Frame(win, bg=CARD)
        content.pack(pady=6, fill="x", padx=24)

        # ── 年范围 ──
        frm_y   = tk.Frame(content, bg=CARD)
        from_yr = tk.StringVar(value=yr_vals[-1])
        to_yr   = tk.StringVar(value=yr_vals[0])
        for lbl, var in [("从", from_yr), ("到", to_yr)]:
            r = tk.Frame(frm_y, bg=CARD); r.pack(pady=3)
            tk.Label(r, text=lbl, bg=CARD, fg=TEXT,
                     font=(self.FONT, 11), width=3).pack(side="left")
            ttk.Combobox(r, textvariable=var, values=yr_vals,
                         state="readonly", width=8,
                         font=(self.FONT, 11)).pack(side="left", padx=3)
            tk.Label(r, text="年", bg=CARD, fg=TEXT,
                     font=(self.FONT, 11)).pack(side="left")

        # ── 月范围 ──
        frm_m     = tk.Frame(content, bg=CARD)
        from_m_yr = tk.StringVar(value=yr_vals[-1])
        from_m    = tk.StringVar(value="1")
        to_m_yr   = tk.StringVar(value=yr_vals[0])
        to_m      = tk.StringVar(value="12")
        for lbl, yv, mv in [("从", from_m_yr, from_m), ("到", to_m_yr, to_m)]:
            r = tk.Frame(frm_m, bg=CARD); r.pack(pady=3)
            tk.Label(r, text=lbl, bg=CARD, fg=TEXT,
                     font=(self.FONT, 11), width=3).pack(side="left")
            ttk.Combobox(r, textvariable=yv, values=yr_vals,
                         state="readonly", width=7,
                         font=(self.FONT, 11)).pack(side="left", padx=2)
            tk.Label(r, text="年", bg=CARD, fg=TEXT,
                     font=(self.FONT, 11)).pack(side="left")
            ttk.Combobox(r, textvariable=mv, values=mo_vals,
                         state="readonly", width=4,
                         font=(self.FONT, 11)).pack(side="left", padx=2)
            tk.Label(r, text="月", bg=CARD, fg=TEXT,
                     font=(self.FONT, 11)).pack(side="left")

        # ── 周范围 ──
        frm_w     = tk.Frame(content, bg=CARD)
        from_w_yr = tk.StringVar(value=yr_vals[-1])
        from_w    = tk.StringVar(value="1")
        to_w_yr   = tk.StringVar(value=yr_vals[0])
        to_w      = tk.StringVar(value="52")
        for lbl, yv, wv in [("从", from_w_yr, from_w), ("到", to_w_yr, to_w)]:
            r = tk.Frame(frm_w, bg=CARD); r.pack(pady=3)
            tk.Label(r, text=lbl, bg=CARD, fg=TEXT,
                     font=(self.FONT, 11), width=3).pack(side="left")
            ttk.Combobox(r, textvariable=yv, values=yr_vals,
                         state="readonly", width=7,
                         font=(self.FONT, 11)).pack(side="left", padx=2)
            tk.Label(r, text="年 第", bg=CARD, fg=TEXT,
                     font=(self.FONT, 11)).pack(side="left")
            ttk.Combobox(r, textvariable=wv, values=wk_vals,
                         state="readonly", width=4,
                         font=(self.FONT, 11)).pack(side="left", padx=2)
            tk.Label(r, text="周", bg=CARD, fg=TEXT,
                     font=(self.FONT, 11)).pack(side="left")

        def show_mode(*_):
            frm_y.pack_forget(); frm_m.pack_forget(); frm_w.pack_forget()
            {"year": frm_y, "month": frm_m, "week": frm_w}[range_var.get()].pack()
        range_var.trace("w", show_mode)
        show_mode()

        def do_export():
            mode = range_var.get()
            try:
                if mode == "year":
                    y1, y2 = int(from_yr.get()), int(to_yr.get())
                    if y1 > y2:
                        messagebox.showwarning("提示", "起始年不能大于结束年！",
                                               parent=win); return
                    s_dt = date(y1, 1, 1); e_dt = date(y2, 12, 31)
                    desc = f"{y1} — {y2} 年"
                elif mode == "month":
                    y1, m1 = int(from_m_yr.get()), int(from_m.get())
                    y2, m2 = int(to_m_yr.get()),   int(to_m.get())
                    s_dt = date(y1, m1, 1)
                    e_dt = date(y2, m2, cal_mod.monthrange(y2, m2)[1])
                    if s_dt > e_dt:
                        messagebox.showwarning("提示", "起始月不能大于结束月！",
                                               parent=win); return
                    desc = f"{y1}年{m1}月 — {y2}年{m2}月"
                else:
                    y1, w1 = int(from_w_yr.get()), int(from_w.get())
                    y2, w2 = int(to_w_yr.get()),   int(to_w.get())
                    s_dt = datetime.strptime(
                        f"{y1}-W{w1:02d}-1", "%G-W%V-%u").date()
                    e_mon = datetime.strptime(
                        f"{y2}-W{w2:02d}-1", "%G-W%V-%u").date()
                    e_dt = e_mon + timedelta(6)
                    if s_dt > e_dt:
                        messagebox.showwarning("提示", "起始周不能大于结束周！",
                                               parent=win); return
                    desc = f"{y1}年第{w1}周 — {y2}年第{w2}周"
            except ValueError as ex:
                messagebox.showwarning("提示", f"日期无效：{ex}", parent=win)
                return
            if messagebox.askyesno("确认", f"导出 {desc} 的记录？", parent=win):
                win.destroy(); parent.destroy()
                self._export_pdf(start_dt=s_dt, end_dt=e_dt)

        bfrm = tk.Frame(win, bg=CARD)
        bfrm.pack(pady=(6, 16))
        tk.Button(bfrm, text="导出", command=do_export,
                  bg=GREEN, fg=TEXT, font=(self.FONT, 12, "bold"),
                  relief="flat", cursor="hand2",
                  pady=6, padx=20).pack(side="left", padx=8)
        tk.Button(bfrm, text="返回", command=win.destroy,
                  bg=CARD, fg=TEXTG, font=(self.FONT, 10),
                  relief="flat", cursor="hand2",
                  pady=6).pack(side="left", padx=8)

    # ──────────────────────────────────────────────────────────────
    # PDF EXPORT
    # ──────────────────────────────────────────────────────────────
    def _export_pdf(self, start_dt=None, end_dt=None):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors as rc
            from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                             PageBreak, Table, TableStyle)
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.graphics.shapes import Drawing, String
            from reportlab.graphics.charts.piecharts import Pie
        except ImportError:
            messagebox.showwarning("提示",
                "请先安装 reportlab：\npip install reportlab\n然后重新运行程序。")
            return

        # Register Chinese font (try multiple candidates)
        font_candidates = [
            ("C:/Windows/Fonts/msyh.ttc",    True),
            ("C:/Windows/Fonts/simsun.ttc",  True),
            ("C:/Windows/Fonts/simhei.ttf",  False),
        ]
        registered = False
        reg_fp = None; reg_ttc = False
        for fp, is_ttc in font_candidates:
            if not os.path.exists(fp): continue
            try:
                if is_ttc:
                    pdfmetrics.registerFont(TTFont("CNFont", fp, subfontIndex=0))
                else:
                    pdfmetrics.registerFont(TTFont("CNFont", fp))
                registered = True; reg_fp = fp; reg_ttc = is_ttc; break
            except Exception:
                continue
        if not registered:
            messagebox.showwarning("提示", "找不到合适的中文字体，无法生成PDF。"); return

        bold_candidates = [
            ("C:/Windows/Fonts/msyhbd.ttc", True),
            ("C:/Windows/Fonts/simhei.ttf", False),
            (reg_fp, reg_ttc),
        ]
        for fp_b, is_ttc_b in bold_candidates:
            if not fp_b or not os.path.exists(fp_b): continue
            try:
                if is_ttc_b:
                    pdfmetrics.registerFont(TTFont("CNFontBold", fp_b, subfontIndex=0))
                else:
                    pdfmetrics.registerFont(TTFont("CNFontBold", fp_b))
                break
            except Exception:
                continue

        out_dir = r"D:\lifeplanner\recording"
        os.makedirs(out_dir, exist_ok=True)
        fname = f"生活规划本_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        fpath = os.path.join(out_dir, fname)

        PW, PH = A4
        doc = SimpleDocTemplate(fpath, pagesize=A4,
                                leftMargin=2.5*cm, rightMargin=2.5*cm,
                                topMargin=2.2*cm, bottomMargin=2.2*cm)
        body_w = PW - 5*cm

        # Color palette matching app
        c_text   = rc.HexColor("#5A4040")
        c_textg  = rc.HexColor("#9A8878")
        c_accent = rc.HexColor("#FFD166")
        c_pink   = rc.HexColor("#FFDCE8")
        c_green  = rc.HexColor("#C8F5DC")
        c_blue   = rc.HexColor("#DCF0FF")
        c_lav    = rc.HexColor("#EDE0FF")
        c_toolbar= rc.HexColor("#FFF0DC")
        c_border = rc.HexColor("#F0E0D0")

        def S(nm, sz, align=0, color=None, before=0, after=5, font="CNFont"):
            return ParagraphStyle(nm, fontName=font, fontSize=sz,
                                  textColor=color or c_text, alignment=align,
                                  spaceBefore=before, spaceAfter=after,
                                  leading=sz * 1.65)

        s_title = S("T",  28, align=1, before=50, after=10, color=c_text, font="CNFontBold")
        s_sub   = S("Su", 13, align=1, after=6,  color=c_textg)
        s_h1    = S("H1", 17, before=4, after=4, color=c_text, font="CNFontBold")
        s_h2    = S("H2", 13, before=2, after=2, color=c_text, font="CNFontBold")
        s_h3    = S("H3", 11, before=6, after=3, color=c_text, font="CNFontBold")
        s_body  = S("B",  10, after=4, color=c_text)
        s_meta  = S("M",   9, after=6, color=c_textg)

        def hdr(text, bg, style, width):
            t = Table([[Paragraph(text, style)]], colWidths=[width])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), bg),
                ("LEFTPADDING",   (0,0), (-1,-1), 10),
                ("RIGHTPADDING",  (0,0), (-1,-1), 10),
                ("TOPPADDING",    (0,0), (-1,-1), 7),
                ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ]))
            return t

        # ── Load data ──
        d = _load()
        thoughts  = d.get("thoughts", [])
        summaries = d.get("summaries", {})
        tasks_data = d.get("tasks", {})
        weight_data = d.get("weight", [])
        focus_data = d.get("focus", [])

        def focus_in(sk, ek):
            return [f for f in focus_data if sk <= f["date"] <= ek]

        def focus_agg(sessions):
            agg = {}
            for s in sessions:
                agg[s["name"]] = agg.get(s["name"], 0) + s["duration"]
            return agg

        def focus_top3_text(agg):
            if not agg: return ""
            top3 = sorted(agg.items(), key=lambda x: -x[1])[:3]
            parts = []
            for nm, dur in top3:
                hrs = int(dur // 3600); mins = int((dur % 3600) // 60)
                ts = f"{hrs}小时{mins}分钟" if hrs else f"{mins}分钟"
                parts.append(f"{nm} (共{ts})")
            return "耗时最长: " + "、".join(parts)

        _mac_rc = [rc.HexColor(c) for c in self._MACARON]

        def make_focus_pie(agg, draw_w=380, draw_h=160):
            items = sorted(agg.items(), key=lambda x: -x[1])
            total = sum(v for _, v in items)
            if total == 0:
                return None
            d = Drawing(draw_w, draw_h)
            pie = Pie()
            pie.x = draw_w // 2 - 70
            pie.y = 15
            pie.width = 120
            pie.height = 120
            pie.data = [v for _, v in items]
            pie.labels = None
            pie.slices.strokeWidth = 0.5
            pie.slices.strokeColor = rc.white
            for idx in range(len(items)):
                pie.slices[idx].fillColor = _mac_rc[idx % len(_mac_rc)]
            d.add(pie)
            lx = pie.x + pie.width + 18
            ly = draw_h - 18
            for idx, (nm, dur) in enumerate(items):
                hrs = int(dur // 3600); mins = int((dur % 3600) // 60)
                ts = f"{hrs}h{mins:02d}m" if hrs else f"{mins}m"
                pct = f"{dur/total*100:.0f}%"
                color = _mac_rc[idx % len(_mac_rc)]
                d.add(String(lx, ly, "■", fontSize=10, fillColor=color))
                d.add(String(lx + 12, ly, f"{nm} ({ts}, {pct})",
                             fontSize=8, fillColor=rc.HexColor("#5A4040"),
                             fontName="CNFont"))
                ly -= 15
            return d

        def focus_section(story_list, agg):
            story_list.append(Paragraph("专注时间分布：", s_h3))
            chart = make_focus_pie(agg)
            if chart:
                story_list.append(chart)
            story_list.append(Paragraph(focus_top3_text(agg), s_body))
            story_list.append(Spacer(1, 0.1*cm))

        def get_ref(key):
            v = summaries.get(key, {})
            if isinstance(v, dict): return v.get("ref", "")
            return str(v) if v else ""

        def task_stats(done_list):
            u  = sum(1 for t2 in done_list if t2["pri"] == "u")
            i_ = sum(1 for t2 in done_list if t2["pri"] == "i")
            n  = sum(1 for t2 in done_list if t2["pri"] == "n")
            return u, i_, n

        def tasks_in(sk, ek):
            res = []
            for k, ts in tasks_data.items():
                if sk <= k <= ek: res.extend(ts)
            return res

        # Collect years with any data
        all_years = set()
        for k in tasks_data:
            try: all_years.add(int(k[:4]))
            except: pass
        for k in summaries:
            try:
                if k.startswith("y_"):   all_years.add(int(k[2:]))
                elif k.startswith("m_"): all_years.add(int(k.split("_")[1]))
                elif k.startswith("w_"): all_years.add(int(k[2:6]))
            except: pass
        for t in thoughts:
            try: all_years.add(int(t["period"][:4]))
            except: pass

        # Apply date-range filter to years
        if start_dt or end_dt:
            _s = start_dt or date.min
            _e = end_dt   or date.max
            all_years = {y for y in all_years
                         if date(y, 1, 1) <= _e and date(y, 12, 31) >= _s}

        def in_range(ds, de):
            if start_dt is None and end_dt is None: return True
            return ds <= (end_dt or date.max) and de >= (start_dt or date.min)

        if not all_years:
            messagebox.showinfo("提示", "暂无可导出的数据！"); return

        story = []

        # Title page
        story.append(Spacer(1, 3*cm))
        story.append(Paragraph("生活规划本", s_title))
        story.append(Paragraph("Life Planner", s_sub))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(
            f"生成时间：{datetime.now().strftime('%Y年%m月%d日')}",
            S("Dt", 11, align=1, color=c_textg)))
        story.append(PageBreak())

        for year in sorted(all_years, reverse=True):
            yr_story = []; has = False

            show_yr_level = (
                (start_dt is None or start_dt <= date(year, 1, 1)) and
                (end_dt   is None or end_dt   >= date(year, 12, 31))
            )

            # Year header
            yr_story.append(hdr(f"{year} 年", c_accent, s_h1, body_w))
            yr_story.append(Spacer(1, 0.25*cm))

            # 年专注时间
            yr_focus = focus_in(f"{year}-01-01", f"{year}-12-31")
            yr_focus_agg = focus_agg(yr_focus)
            if show_yr_level and yr_focus_agg:
                has = True
                focus_section(yr_story, yr_focus_agg)

            # 年计划
            yr_th = sorted([t for t in thoughts
                            if t["type"] == "year" and t["period"] == str(year)],
                           key=lambda x: x["created"])
            if show_yr_level and yr_th:
                has = True
                yr_story.append(hdr("年计划", c_lav, s_h2, body_w))
                yr_story.append(Spacer(1, 0.1*cm))
                for t in yr_th:
                    yr_story.append(Paragraph(f"[ {t['created']} ]", s_meta))
                    for line in t["content"].split("\n"):
                        if line.strip():
                            yr_story.append(Paragraph(line, s_body))
                yr_story.append(Spacer(1, 0.2*cm))

            # 年总结 (with weight trend)
            yr_ref  = get_ref(f"y_{year}")
            yr_done = [t for t in tasks_in(f"{year}-01-01", f"{year}-12-31")
                       if t.get("done")]
            yr_wt   = [e for e in weight_data if e["date"].startswith(str(year))]

            if show_yr_level and (yr_done or yr_ref or yr_wt):
                has = True
                yr_story.append(hdr("年总结", c_green, s_h2, body_w))
                yr_story.append(Spacer(1, 0.1*cm))
                if yr_done:
                    u, i_, n = task_stats(yr_done)
                    yr_story.append(Paragraph(
                        f"完成事件：紧急 {u} 件 / 重要 {i_} 件 / 不重要 {n} 件", s_body))
                if yr_ref:
                    yr_story.append(Paragraph("反思与展望：", s_h3))
                    for line in yr_ref.split("\n"):
                        if line.strip():
                            yr_story.append(Paragraph(line, s_body))
                if yr_wt:
                    yr_story.append(Paragraph("体重波动：", s_h3))
                    # Monthly averages
                    monthly_wt_avg = []
                    monthly_ws_avg = []
                    for m in range(1, 13):
                        prefix = f"{year}-{m:02d}"
                        mes  = [e for e in yr_wt if e["date"].startswith(prefix)]
                        wv   = [e["w"]  for e in mes if e.get("w")  is not None]
                        wsv  = [e["ws"] for e in mes if e.get("ws") is not None]
                        monthly_wt_avg.append(sum(wv)/len(wv)   if wv  else None)
                        monthly_ws_avg.append(sum(wsv)/len(wsv) if wsv else None)
                    # Text stats
                    all_wt = [e for e in yr_wt if e.get("w")  is not None]
                    all_ws = [e for e in yr_wt if e.get("ws") is not None]
                    if all_wt:
                        mn = min(e["w"] for e in all_wt)
                        mx = max(e["w"] for e in all_wt)
                        avg = sum(e["w"] for e in all_wt) / len(all_wt)
                        yr_story.append(Paragraph(
                            f"体重 — 最低 {mn:.1f} kg  最高 {mx:.1f} kg  平均 {avg:.1f} kg",
                            s_body))
                    if all_ws:
                        mn = min(e["ws"] for e in all_ws)
                        mx = max(e["ws"] for e in all_ws)
                        avg = sum(e["ws"] for e in all_ws) / len(all_ws)
                        yr_story.append(Paragraph(
                            f"腰围 — 最低 {mn:.1f} cm  最高 {mx:.1f} cm  平均 {avg:.1f} cm",
                            s_body))
                    # Line chart (monthly averages)
                    try:
                        from reportlab.graphics.shapes import Drawing
                        from reportlab.graphics.charts.lineplots import LinePlot
                        from reportlab.graphics.shapes import Rect as GRect, String as GStr
                        ch_w = float(body_w); ch_h = 130.0
                        drw  = Drawing(ch_w, ch_h)
                        lp   = LinePlot()
                        lp.x = 44; lp.y = 24
                        lp.width  = ch_w - 54
                        lp.height = ch_h - 40
                        wt_pts = [(i+1, v) for i, v in enumerate(monthly_wt_avg) if v is not None]
                        ws_pts = [(i+1, v) for i, v in enumerate(monthly_ws_avg) if v is not None]
                        s_data = []; s_colors = []; s_labels = []
                        if len(wt_pts) >= 2:
                            s_data.append(wt_pts)
                            s_colors.append(rc.HexColor("#FF9F7F"))
                            s_labels.append("体重(kg)")
                        if len(ws_pts) >= 2:
                            s_data.append(ws_pts)
                            s_colors.append(rc.HexColor("#74B9FF"))
                            s_labels.append("腰围(cm)")
                        if s_data:
                            lp.data = s_data
                            for si, clr in enumerate(s_colors):
                                lp.lines[si].strokeColor = clr
                                lp.lines[si].strokeWidth  = 2
                            lp.xValueAxis.valueMin  = 0.5
                            lp.xValueAxis.valueMax  = 12.5
                            lp.xValueAxis.valueStep = 1
                            lp.xValueAxis.labelTextFormat = '%d月'
                            lp.xValueAxis.labels.fontName  = "CNFont"
                            lp.xValueAxis.labels.fontSize  = 7
                            all_y = [v for pts in s_data for _, v in pts]
                            rng   = max(all_y) - min(all_y) or 1
                            lp.yValueAxis.valueMin = max(0, min(all_y) - rng * 0.3)
                            lp.yValueAxis.valueMax = max(all_y) + rng * 0.3
                            lp.yValueAxis.labelTextFormat = '%.1f'
                            lp.yValueAxis.labels.fontName  = "CNFont"
                            lp.yValueAxis.labels.fontSize  = 7
                            drw.add(lp)
                            for li, (clr, lbl) in enumerate(zip(s_colors, s_labels)):
                                lx = lp.x + li * 90
                                drw.add(GRect(lx, ch_h - 14, 18, 7,
                                              fillColor=clr, strokeColor=None))
                                drw.add(GStr(lx + 22, ch_h - 14, lbl,
                                             fontName="CNFont", fontSize=8,
                                             fillColor=c_textg))
                            yr_story.append(drw)
                    except Exception:
                        pass
                yr_story.append(Spacer(1, 0.3*cm))

            # Months
            for month in range(1, 13):
                mperiod = f"{year}-{month:02d}"
                mref    = get_ref(f"m_{year}_{month}")
                mth     = sorted([t for t in thoughts
                                  if t["type"] == "month" and t["period"] == mperiod],
                                 key=lambda x: x["created"])
                msk = f"{year}-{month:02d}-01"
                mek = f"{year}-{month:02d}-{cal_mod.monthrange(year, month)[1]:02d}"
                m_done = [t for t in tasks_in(msk, mek) if t.get("done")]
                m_focus = focus_in(msk, mek)
                m_focus_agg = focus_agg(m_focus)

                if not in_range(date(year, month, 1),
                                date(year, month, cal_mod.monthrange(year, month)[1])):
                    continue
                if not mth and not mref and not m_done and not m_focus_agg: continue
                has = True
                yr_story.append(hdr(f"{month} 月", c_toolbar, s_h2, body_w))
                yr_story.append(Spacer(1, 0.1*cm))

                if m_focus_agg:
                    focus_section(yr_story, m_focus_agg)

                if mth:
                    yr_story.append(Paragraph("月计划", s_h3))
                    for t in mth:
                        yr_story.append(Paragraph(f"[ {t['created']} ]", s_meta))
                        for line in t["content"].split("\n"):
                            if line.strip():
                                yr_story.append(Paragraph(line, s_body))
                    yr_story.append(Spacer(1, 0.1*cm))

                if m_done or mref:
                    yr_story.append(Paragraph("月总结", s_h3))
                    if m_done:
                        u, i_, n = task_stats(m_done)
                        yr_story.append(Paragraph(
                            f"完成事件：紧急 {u} 件 / 重要 {i_} 件 / 不重要 {n} 件", s_body))
                    if mref:
                        yr_story.append(Paragraph("反思与展望：", s_h3))
                        for line in mref.split("\n"):
                            if line.strip():
                                yr_story.append(Paragraph(line, s_body))
                yr_story.append(Spacer(1, 0.2*cm))

            # Weeks (only Mondays in this year)
            d_ = date(year, 1, 1)
            d_ -= timedelta(days=d_.weekday())  # Monday of week containing Jan 1
            if d_.year < year: d_ += timedelta(7)

            while d_.year == year:
                wend    = d_ + timedelta(6)
                if not in_range(d_, wend):
                    d_ += timedelta(7); continue
                wperiod = f"{year}-W{d_.isocalendar()[1]:02d}"
                wref    = get_ref(f"w_{dk(d_)}")
                wth     = sorted([t for t in thoughts
                                  if t["type"] == "week" and t["period"] == wperiod],
                                 key=lambda x: x["created"])
                wsk = dk(d_); wek = dk(wend)
                w_done = [t for t in tasks_in(wsk, wek) if t.get("done")]
                w_focus = focus_in(wsk, wek)
                w_focus_agg = focus_agg(w_focus)

                if wth or wref or w_done or w_focus_agg:
                    has = True
                    wnum  = d_.isocalendar()[1]
                    wlbl  = (f"第 {wnum} 周  "
                             f"({d_.month}月{d_.day}日 — {wend.month}月{wend.day}日)")
                    yr_story.append(hdr(wlbl, c_blue, s_h2, body_w))
                    yr_story.append(Spacer(1, 0.1*cm))

                    if w_focus_agg:
                        focus_section(yr_story, w_focus_agg)

                    if wth:
                        yr_story.append(Paragraph("周计划", s_h3))
                        for t in wth:
                            yr_story.append(Paragraph(f"[ {t['created']} ]", s_meta))
                            for line in t["content"].split("\n"):
                                if line.strip():
                                    yr_story.append(Paragraph(line, s_body))
                        yr_story.append(Spacer(1, 0.1*cm))

                    if w_done or wref:
                        yr_story.append(Paragraph("周总结", s_h3))
                        if w_done:
                            u, i_, n = task_stats(w_done)
                            yr_story.append(Paragraph(
                                f"完成事件：紧急 {u} 件 / 重要 {i_} 件 / 不重要 {n} 件", s_body))
                        if wref:
                            yr_story.append(Paragraph("反思与展望：", s_h3))
                            for line in wref.split("\n"):
                                if line.strip():
                                    yr_story.append(Paragraph(line, s_body))
                    yr_story.append(Spacer(1, 0.2*cm))

                d_ += timedelta(7)

            if has:
                story.extend(yr_story)
                story.append(PageBreak())

        while story and isinstance(story[-1], PageBreak):
            story.pop()

        def footer(canvas, _doc):
            canvas.saveState()
            canvas.setFont("CNFont", 9)
            canvas.setFillColor(c_textg)
            canvas.drawRightString(PW - 2.5*cm, 1.3*cm,
                                   f"第 {canvas.getPageNumber()} 页")
            canvas.setStrokeColor(c_border)
            canvas.line(2.5*cm, 1.6*cm, PW - 2.5*cm, 1.6*cm)
            canvas.restoreState()

        try:
            doc.build(story, onFirstPage=footer, onLaterPages=footer)
            messagebox.showinfo("导出成功", f"PDF 已保存至：\n{fpath}")
        except Exception as e:
            messagebox.showerror("导出失败", f"生成 PDF 时出错：\n{e}")


    # ──────────────────────────────────────────────────────────────
    # FOCUS TIMER (专注计时)
    # ──────────────────────────────────────────────────────────────
    _MACARON = ["#FFB5B5", "#FFDAA5", "#FFFAB5", "#B5EAAA", "#B5E8E3",
                "#B5D4F7", "#C9B5F7", "#F7B5E0", "#F7C5B5", "#A5E0D6",
                "#E8C5F0", "#F0D5A8", "#A8D8EA", "#F5B7B1", "#D5F5E3"]

    def _draw_pie_chart(self, canvas, agg_data, w, h):
        canvas.delete("all")
        if not agg_data:
            canvas.create_text(w // 2, h // 2, text="暂无数据", fill=TEXTG,
                               font=(self.FONT, 11))
            return
        total = sum(agg_data.values())
        if total == 0:
            canvas.create_text(w // 2, h // 2, text="暂无数据", fill=TEXTG,
                               font=(self.FONT, 11))
            return
        r = min(w // 4, h // 2 - 8, 75)
        cy = h // 2
        items = sorted(agg_data.items(), key=lambda x: -x[1])
        legend_w_est = 160
        total_w = 2 * r + 18 + legend_w_est
        cx = max(r + 6, (w - total_w) // 2 + r)
        start = 0
        legend_x = cx + r + 18
        legend_y = max(6, cy - len(items) * 9)
        for idx, (name, dur) in enumerate(items):
            color = self._MACARON[idx % len(self._MACARON)]
            if len(items) == 1:
                canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                   fill=color, outline="white", width=2)
            else:
                extent = (dur / total) * 360
                canvas.create_arc(cx - r, cy - r, cx + r, cy + r,
                                  start=start, extent=extent,
                                  fill=color, outline="white", width=2)
                start += extent
            hrs = int(dur // 3600)
            mins = int((dur % 3600) // 60)
            time_str = f"{hrs}h{mins:02d}m" if hrs else f"{mins}m"
            pct = f"{dur/total*100:.0f}%"
            canvas.create_rectangle(legend_x, legend_y, legend_x + 10, legend_y + 10,
                                     fill=color, outline="")
            canvas.create_text(legend_x + 14, legend_y + 5, anchor="w",
                               text=f"{name} ({time_str}, {pct})",
                               fill=TEXT, font=(self.FONT, 9))
            legend_y += 17

    def _open_focus_timer(self):
        win = tk.Toplevel(self.root)
        win.title("🎯 专注计时")
        win.configure(bg=BG)
        win.resizable(True, True)
        win.grab_set()
        self._center(win, 1000, 700)

        tk.Label(win, text="🎯 专注计时", bg=BG, fg=TEXT,
                 font=(self.FONT, 18, "bold")).pack(pady=(12, 8))

        main = tk.Frame(win, bg=BG)
        main.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        # ── Left Panel (History) ──
        left_card = RCard(main, r=16, bg=CARD)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left_card.inner.columnconfigure(0, weight=1)
        left_card.inner.rowconfigure(2, weight=1)

        tk.Label(left_card.inner, text="📋 历史记录", bg=CARD, fg=TEXT,
                 font=(self.FONT, 14, "bold")).grid(row=0, column=0, sticky="w",
                                                     padx=12, pady=(10, 2))

        # Search + date filter (compact single row)
        filter_f = tk.Frame(left_card.inner, bg=CARD)
        filter_f.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 4))
        search_var = tk.StringVar()
        tk.Label(filter_f, text="🔍", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 10)).pack(side="left")
        search_e = tk.Entry(filter_f, textvariable=search_var, font=(self.FONT, 10),
                            relief="flat", bg="#FFF8EE", fg=TEXT, bd=1, width=12,
                            highlightthickness=1, highlightbackground=BORDER)
        search_e.pack(side="left", fill="x", expand=True, ipady=2, padx=(2, 6))
        date_var = tk.StringVar()
        tk.Label(filter_f, text="📅", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 10)).pack(side="left")
        date_e = tk.Entry(filter_f, textvariable=date_var, font=(self.FONT, 10),
                          relief="flat", bg="#FFF8EE", fg=TEXT, bd=1, width=10,
                          highlightthickness=1, highlightbackground=BORDER)
        date_e.pack(side="left", ipady=2, padx=(2, 0))

        left_card.inner.rowconfigure(2, weight=1)
        list_scroll = ScrollFrame(left_card.inner, bg=CARD)
        list_scroll.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0, 8))
        list_frame = list_scroll.inner

        def refresh_history():
            for w in list_frame.winfo_children(): w.destroy()
            query = search_var.get().strip()
            dt_filter = date_var.get().strip()
            all_sessions = focus_all()
            has_filter = bool(query or dt_filter)
            if has_filter:
                filtered = all_sessions
                if query:
                    filtered = [s for s in filtered
                                if query.lower() in s["name"].lower()]
                if dt_filter:
                    filtered = [s for s in filtered if s["date"] == dt_filter]
            else:
                filtered = all_sessions
            filtered.sort(key=lambda x: x["date"], reverse=True)
            if not filtered:
                msg = "暂无专注记录~" if not has_filter else "未找到匹配记录"
                tk.Label(list_frame, text=msg, bg=CARD, fg=TEXTL,
                         font=(self.FONT, 12)).pack(pady=30)
                return
            for s in filtered:
                row = tk.Frame(list_frame, bg="#F0F8FF", pady=6, padx=10)
                row.pack(fill="x", pady=2, padx=4)
                top = tk.Frame(row, bg="#F0F8FF")
                top.pack(fill="x")
                name_lbl = tk.Label(top, text=s["name"], bg="#F0F8FF", fg=TEXT,
                                     font=(self.FONT, 12, "bold"))
                name_lbl.pack(side="left")
                tk.Label(top, text=s["date"], bg="#F0F8FF", fg=TEXTG,
                         font=(self.FONT, 9)).pack(side="left", padx=(6, 0))
                dur = s["duration"]
                hrs = int(dur // 3600)
                mins = int((dur % 3600) // 60)
                time_str = f"{hrs}小时{mins:02d}分" if hrs else f"{mins}分钟"
                tk.Label(top, text=time_str, bg="#F0F8FF", fg=BLUE2,
                         font=(self.FONT, 12, "bold")).pack(side="right")
                if s.get("note"):
                    tk.Label(row, text=f"📝 {s['note']}", bg="#F0F8FF", fg=TEXTG,
                             font=(self.FONT, 10), anchor="w", justify="left",
                             wraplength=350).pack(fill="x", pady=(3, 0))
                def on_dbl(e, item=s):
                    self._open_focus_record_popup(item, refresh_history, refresh_pie)
                for widget in (row, top, name_lbl):
                    widget.bind("<Double-Button-1>", on_dbl)

        search_var.trace("w", lambda *_: refresh_history())
        date_var.trace("w", lambda *_: refresh_history())

        # ── Right Panel (Timer Setup + Pie Chart) ──
        right_card = RCard(main, r=16, bg=CARD)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right_card.inner.columnconfigure(0, weight=1)
        right_card.inner.rowconfigure(4, weight=1)

        tk.Label(right_card.inner, text="⏱ 开始专注", bg=CARD, fg=TEXT,
                 font=(self.FONT, 14, "bold")).pack(pady=(12, 8), padx=20, anchor="w")

        rf = tk.Frame(right_card.inner, bg=CARD, padx=20)
        rf.pack(fill="x")

        # Event name with autocomplete
        tk.Label(rf, text="专注事件", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 12, "bold")).pack(anchor="w")
        name_frame = tk.Frame(rf, bg=CARD)
        name_frame.pack(fill="x", pady=(2, 8))
        name_var = tk.StringVar()
        name_e = tk.Entry(name_frame, textvariable=name_var, font=(self.FONT, 13),
                          relief="flat", bg="#FFF8EE", fg=TEXT, bd=1,
                          highlightthickness=1, highlightbackground=BORDER)
        name_e.pack(fill="x", ipady=4)

        # Autocomplete dropdown
        suggest_lb = tk.Listbox(name_frame, font=(self.FONT, 11), bg="#FFF8EE",
                                fg=TEXT, height=4, relief="flat", bd=1,
                                highlightthickness=1, highlightbackground=BORDER)

        def on_name_change(*_):
            val = name_var.get().strip()
            if not val:
                suggest_lb.pack_forget()
                return
            names = focus_names()
            matches = [n for n in names if val.lower() in n.lower()]
            if matches and val not in matches:
                suggest_lb.delete(0, "end")
                for m in matches[:5]:
                    suggest_lb.insert("end", m)
                suggest_lb.pack(fill="x")
            else:
                suggest_lb.pack_forget()

        def on_suggest_select(e):
            sel = suggest_lb.curselection()
            if sel:
                name_var.set(suggest_lb.get(sel[0]))
                suggest_lb.pack_forget()

        name_var.trace("w", on_name_change)
        suggest_lb.bind("<ButtonRelease-1>", on_suggest_select)

        # Timer mode
        tk.Label(rf, text="计时模式", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 12, "bold")).pack(anchor="w")
        mode_f = tk.Frame(rf, bg=CARD)
        mode_f.pack(fill="x", pady=(2, 8))
        mode_var = tk.StringVar(value="countup")
        mode_btns = {}

        def upd_mode():
            for mid, b in mode_btns.items():
                sel = mode_var.get() == mid
                b.configure(bg="#B8DFFB" if sel else "#FFF8EE",
                            fg=TEXT if sel else TEXTG)

        for mid, mlbl in [("countup", "正计时"), ("countdown", "倒计时")]:
            b = tk.Label(mode_f, text=mlbl, bg="#FFF8EE", fg=TEXTG,
                         font=(self.FONT, 12, "bold"), padx=14, pady=5, cursor="hand2")
            b.pack(side="left", fill="x", expand=True, padx=2)
            b.bind("<Button-1>", lambda e, m=mid: (mode_var.set(m), upd_mode()))
            mode_btns[mid] = b
        upd_mode()

        # Duration input (for countdown)
        tk.Label(rf, text="专注时间（倒计时用）", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 12, "bold")).pack(anchor="w")
        dur_f = tk.Frame(rf, bg=CARD)
        dur_f.pack(fill="x", pady=(2, 12))
        hr_var = tk.StringVar(value="0")
        min_var = tk.StringVar(value="25")
        tk.Entry(dur_f, textvariable=hr_var, width=4, font=(self.FONT, 13),
                 relief="flat", bg="#FFF8EE", bd=1,
                 highlightthickness=1, highlightbackground=BORDER).pack(side="left", ipady=3)
        tk.Label(dur_f, text="小时", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 11)).pack(side="left", padx=(2, 8))
        tk.Entry(dur_f, textvariable=min_var, width=4, font=(self.FONT, 13),
                 relief="flat", bg="#FFF8EE", bd=1,
                 highlightthickness=1, highlightbackground=BORDER).pack(side="left", ipady=3)
        tk.Label(dur_f, text="分钟", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 11)).pack(side="left", padx=(2, 0))

        # Start button
        def do_start():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("提示", "请输入专注事件名称！", parent=win)
                return
            mode = mode_var.get()
            countdown_secs = 0
            if mode == "countdown":
                try:
                    h = int(hr_var.get() or 0)
                    m = int(min_var.get() or 0)
                    countdown_secs = h * 3600 + m * 60
                    if countdown_secs <= 0:
                        messagebox.showwarning("提示", "请设置倒计时时间！", parent=win)
                        return
                except ValueError:
                    messagebox.showwarning("提示", "请输入有效的时间！", parent=win)
                    return
            self._start_focus_session(win, name, mode, countdown_secs,
                                      refresh_history, refresh_pie)

        start_btn = clickable_label(rf, "▶ 开始专注", "#B8DFFB", TEXT,
                                    (self.FONT, 14, "bold"), do_start, 0, 12)
        start_btn.pack(fill="x")
        hover_bind(start_btn, "#9AD0F5", "#B8DFFB")

        # Today's pie chart
        tk.Label(right_card.inner, text="📊 今日专注分布", bg=CARD, fg=TEXT,
                 font=(self.FONT, 13, "bold")).pack(pady=(12, 4), padx=20, anchor="w")
        pie_cvs = tk.Canvas(right_card.inner, bg=CARD, highlightthickness=0, height=180)
        pie_cvs.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        def refresh_pie():
            today_sessions = focus_for_today()
            agg = focus_aggregated(today_sessions)
            pie_cvs.update_idletasks()
            pw = max(pie_cvs.winfo_width(), 300)
            ph = max(pie_cvs.winfo_height(), 180)
            self._draw_pie_chart(pie_cvs, agg, pw, ph)

        pie_cvs.bind("<Configure>", lambda e: win.after(100, refresh_pie))
        win.after(300, refresh_pie)
        win.after(200, refresh_history)
        win.bind("<Escape>", lambda e: win.destroy())

    def _open_focus_record_popup(self, item, refresh_fn, refresh_pie_fn):
        pop = tk.Toplevel(self.root)
        pop.title("专注记录")
        pop.configure(bg=CARD)
        pop.resizable(False, False)
        pop.grab_set()
        self._center(pop, 400, 360)

        tk.Label(pop, text="✏️ 编辑专注记录", bg=CARD, fg=TEXT,
                 font=(self.FONT, 16, "bold")).pack(pady=(16, 10))

        f = tk.Frame(pop, bg=CARD, padx=24)
        f.pack(fill="x")

        tk.Label(f, text="事件名称", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 11, "bold")).pack(anchor="w")
        name_e = tk.Entry(f, font=(self.FONT, 12), relief="flat", bg="#FFF8EE", fg=TEXT,
                          bd=1, highlightthickness=1, highlightbackground=BORDER)
        name_e.pack(fill="x", pady=(2, 6), ipady=3)
        name_e.insert(0, item["name"])

        tk.Label(f, text="专注时间", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 11, "bold")).pack(anchor="w")
        dur_f = tk.Frame(f, bg=CARD)
        dur_f.pack(fill="x", pady=(2, 6))
        dur = item["duration"]
        hr_var = tk.StringVar(value=str(int(dur // 3600)))
        min_var = tk.StringVar(value=str(int((dur % 3600) // 60)))
        tk.Entry(dur_f, textvariable=hr_var, width=4, font=(self.FONT, 12),
                 relief="flat", bg="#FFF8EE", bd=1).pack(side="left", ipady=2)
        tk.Label(dur_f, text="小时", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 10)).pack(side="left", padx=(1, 6))
        tk.Entry(dur_f, textvariable=min_var, width=4, font=(self.FONT, 12),
                 relief="flat", bg="#FFF8EE", bd=1).pack(side="left", ipady=2)
        tk.Label(dur_f, text="分钟", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 10)).pack(side="left", padx=(1, 0))

        tk.Label(f, text="备注", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 11, "bold")).pack(anchor="w")
        note_t = tk.Text(f, font=(self.FONT, 11), relief="flat", bg="#FFF8EE",
                         fg=TEXT, bd=1, height=3, highlightthickness=1,
                         highlightbackground=BORDER, wrap="word", padx=6, pady=4)
        note_t.pack(fill="x", pady=(2, 10))
        if item.get("note"):
            note_t.insert("1.0", item["note"])

        bf = tk.Frame(f, bg=CARD)
        bf.pack(fill="x", pady=(0, 8))

        def do_save():
            nm = name_e.get().strip()
            if not nm:
                messagebox.showwarning("提示", "请输入事件名称！", parent=pop)
                return
            try:
                h = int(hr_var.get() or 0)
                m = int(min_var.get() or 0)
                new_dur = h * 3600 + m * 60
            except ValueError:
                messagebox.showwarning("提示", "请输入有效时间！", parent=pop)
                return
            note = note_t.get("1.0", "end-1c").strip()
            focus_edit(item["id"], nm, new_dur, note)
            pop.destroy()
            refresh_fn()
            refresh_pie_fn()

        def do_del():
            if messagebox.askyesno("确认", f"删除「{item['name']}」的记录？", parent=pop):
                focus_del(item["id"])
                pop.destroy()
                refresh_fn()
                refresh_pie_fn()

        save_btn = clickable_label(bf, "💾 保存", GREEN, TEXT,
                                   (self.FONT, 12, "bold"), do_save, 0, 9)
        save_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        hover_bind(save_btn, GREEN2, GREEN)
        del_btn = clickable_label(bf, "🗑 删除", "#FFEEEE", URGENT,
                                  (self.FONT, 12, "bold"), do_del, 0, 9)
        del_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))
        hover_bind(del_btn, "#FFD0D0", "#FFEEEE")
        pop.bind("<Escape>", lambda e: pop.destroy())

    def _start_focus_session(self, parent_win, name, mode, countdown_secs,
                             refresh_fn, refresh_pie_fn):
        TIMER_BG = TOOLBAR
        try:
            parent_win.grab_release()
        except Exception:
            pass
        timer_win = tk.Toplevel(self.root)
        timer_win.title("专注中...")
        timer_win.configure(bg=TIMER_BG)
        timer_win.resizable(False, False)
        timer_win.attributes("-topmost", True)
        self._center(timer_win, 400, 330)

        state = {"running": True, "start_time": time_mod.time(),
                 "notified": False}

        # Current date/time display
        clock_var = tk.StringVar()
        tk.Label(timer_win, textvariable=clock_var, bg=TIMER_BG, fg=TEXTG,
                 font=(self.FONT, 12)).pack(pady=(20, 8))

        # Event name
        tk.Label(timer_win, text=f"🎯 {name}", bg=TIMER_BG, fg=TEXT,
                 font=(self.FONT, 16, "bold")).pack(pady=(0, 12))

        # Timer display
        timer_var = tk.StringVar(value="00:00:00")
        timer_lbl = tk.Label(timer_win, textvariable=timer_var, bg=TIMER_BG, fg=TEXT,
                             font=(self.FONT, 36, "bold"))
        timer_lbl.pack(pady=(0, 6))

        # Mode label
        mode_lbl_var = tk.StringVar(value="正计时" if mode == "countup" else "倒计时")
        tk.Label(timer_win, textvariable=mode_lbl_var, bg=TIMER_BG, fg=TEXTG,
                 font=(self.FONT, 11)).pack(pady=(0, 16))

        def update_clock():
            if not state["running"]:
                return
            now = datetime.now()
            clock_var.set(now.strftime("%Y年%m月%d日  %H:%M:%S"))
            elapsed = time_mod.time() - state["start_time"]
            if mode == "countup":
                h = int(elapsed // 3600)
                m = int((elapsed % 3600) // 60)
                s = int(elapsed % 60)
                timer_var.set(f"{h:02d}:{m:02d}:{s:02d}")
            else:
                remaining = countdown_secs - elapsed
                if remaining > 0:
                    h = int(remaining // 3600)
                    m = int((remaining % 3600) // 60)
                    s = int(remaining % 60)
                    timer_var.set(f"{h:02d}:{m:02d}:{s:02d}")
                else:
                    over = elapsed - countdown_secs
                    h = int(over // 3600)
                    m = int((over % 3600) // 60)
                    s = int(over % 60)
                    timer_var.set(f"+{h:02d}:{m:02d}:{s:02d}")
                    timer_lbl.configure(fg=URGENT)
                    mode_lbl_var.set("已超时 · 继续计时中")
                    if not state["notified"]:
                        state["notified"] = True
                        messagebox.showinfo("提示", "到时间啦！",
                                            parent=timer_win)
            timer_win.after(500, update_clock)

        def do_end():
            state["running"] = False
            elapsed = time_mod.time() - state["start_time"]
            if messagebox.askyesno("确认", "是否结束本次专注？", parent=timer_win):
                timer_win.destroy()
                self._show_focus_result(name, elapsed, refresh_fn, refresh_pie_fn)
            else:
                state["running"] = True
                timer_win.after(500, update_clock)

        end_btn = clickable_label(timer_win, "⏹ 结束专注", PINK2, TEXT,
                                  (self.FONT, 14, "bold"), do_end, 0, 12)
        end_btn.pack(fill="x", padx=40)
        hover_bind(end_btn, PINK3, PINK2)

        timer_win.protocol("WM_DELETE_WINDOW", lambda: None)
        update_clock()

    def _show_focus_result(self, name, elapsed_secs, refresh_fn, refresh_pie_fn):
        pop = tk.Toplevel(self.root)
        pop.title("专注完成")
        pop.configure(bg=CARD)
        pop.resizable(False, False)
        pop.grab_set()
        self._center(pop, 420, 380)

        hrs = int(elapsed_secs // 3600)
        mins = int((elapsed_secs % 3600) // 60)
        secs = int(elapsed_secs % 60)
        time_str = ""
        if hrs: time_str += f"{hrs}小时"
        if mins: time_str += f"{mins}分钟"
        if secs and not hrs: time_str += f"{secs}秒"
        if not time_str: time_str = "0秒"

        tk.Label(pop, text="🎉 专注完成！", bg=CARD, fg=TEXT,
                 font=(self.FONT, 18, "bold")).pack(pady=(20, 8))
        tk.Label(pop, text=f"本次专注用时：{time_str}", bg=CARD, fg=BLUE2,
                 font=(self.FONT, 14, "bold")).pack(pady=(0, 12))

        f = tk.Frame(pop, bg=CARD, padx=24)
        f.pack(fill="x")

        tk.Label(f, text="备注（可选）", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 12, "bold")).pack(anchor="w")
        note_t = tk.Text(f, font=(self.FONT, 12), relief="flat", bg="#FFF8EE",
                         fg=TEXT, bd=1, height=3, highlightthickness=1,
                         highlightbackground=BORDER, wrap="word", padx=6, pady=4)
        note_t.pack(fill="x", pady=(3, 8))

        # Edit time
        tk.Label(f, text="编辑时间", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 12, "bold")).pack(anchor="w")
        edit_f = tk.Frame(f, bg=CARD)
        edit_f.pack(fill="x", pady=(2, 12))
        edit_hr = tk.StringVar(value=str(hrs))
        edit_min = tk.StringVar(value=str(mins))
        edit_sec = tk.StringVar(value=str(secs))
        tk.Entry(edit_f, textvariable=edit_hr, width=4, font=(self.FONT, 12),
                 relief="flat", bg="#FFF8EE", bd=1).pack(side="left", ipady=2)
        tk.Label(edit_f, text="时", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 10)).pack(side="left", padx=(1, 4))
        tk.Entry(edit_f, textvariable=edit_min, width=4, font=(self.FONT, 12),
                 relief="flat", bg="#FFF8EE", bd=1).pack(side="left", ipady=2)
        tk.Label(edit_f, text="分", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 10)).pack(side="left", padx=(1, 4))
        tk.Entry(edit_f, textvariable=edit_sec, width=4, font=(self.FONT, 12),
                 relief="flat", bg="#FFF8EE", bd=1).pack(side="left", ipady=2)
        tk.Label(edit_f, text="秒", bg=CARD, fg=TEXTG,
                 font=(self.FONT, 10)).pack(side="left", padx=(1, 0))

        def do_confirm():
            try:
                h = int(edit_hr.get() or 0)
                m = int(edit_min.get() or 0)
                s = int(edit_sec.get() or 0)
                final_dur = h * 3600 + m * 60 + s
            except ValueError:
                messagebox.showwarning("提示", "请输入有效时间！", parent=pop)
                return
            note = note_t.get("1.0", "end-1c").strip()
            focus_add(name, final_dur, today_key(), note)
            pop.destroy()
            refresh_fn()
            refresh_pie_fn()

        confirm_btn = clickable_label(f, "✓ 确认保存", GREEN, TEXT,
                                      (self.FONT, 13, "bold"), do_confirm, 0, 10)
        confirm_btn.pack(fill="x")
        hover_bind(confirm_btn, GREEN2, GREEN)
        pop.bind("<Escape>", lambda e: pop.destroy())



# ================================================================
# ENTRY POINT
# ================================================================
if __name__ == "__main__":
    App().run()
