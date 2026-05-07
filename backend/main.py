#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Life Planner — FastAPI Backend"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import sqlite3, os, uuid
from datetime import datetime, date

# ── Auth ──────────────────────────────────────────────────────────
API_TOKEN = os.environ.get("API_TOKEN", "lifeplanner_secret")

def auth(x_api_token: str = Header()):
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(title="Life Planner API", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── Database ──────────────────────────────────────────────────────
DB_PATH = os.environ.get("DB_PATH", "lifeplanner.db")

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    db = conn()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        date_key TEXT NOT NULL,
        name TEXT NOT NULL,
        desc TEXT DEFAULT '',
        pri TEXT DEFAULT 'n',
        done INTEGER DEFAULT 0,
        order_idx INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS countdowns (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        date TEXT NOT NULL,
        rep TEXT DEFAULT 'none'
    );
    CREATE TABLE IF NOT EXISTS weight (
        date_key TEXT PRIMARY KEY,
        w REAL,
        ws REAL
    );
    CREATE TABLE IF NOT EXISTS summaries (
        key TEXT PRIMARY KEY,
        ref TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS thoughts (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        period TEXT NOT NULL,
        content TEXT NOT NULL,
        created TEXT NOT NULL
    );
    """)
    db.commit(); db.close()

init_db()

# ── Pydantic models ───────────────────────────────────────────────
class TaskIn(BaseModel):
    name: str; desc: str = ""; pri: str = "n"

class TaskEdit(BaseModel):
    name: str; desc: str = ""; pri: str = "n"; done: bool = False

class TaskOrder(BaseModel):
    order: List[str]

class CdIn(BaseModel):
    name: str; date: str; rep: str = "none"

class WeightIn(BaseModel):
    w: Optional[float] = None; ws: Optional[float] = None

class SummaryIn(BaseModel):
    ref: str

class ThoughtIn(BaseModel):
    type: str; period: str; content: str

class ThoughtEdit(BaseModel):
    content: str

# ── Tasks ─────────────────────────────────────────────────────────
@app.get("/tasks/{date_key}", dependencies=[Depends(auth)])
def get_tasks(date_key: str):
    db = conn()
    rows = db.execute("SELECT * FROM tasks WHERE date_key=? ORDER BY order_idx",
                      (date_key,)).fetchall()
    db.close()
    return [{"id": r["id"], "name": r["name"], "desc": r["desc"],
             "pri": r["pri"], "done": bool(r["done"])} for r in rows]

@app.post("/tasks/{date_key}", dependencies=[Depends(auth)])
def add_task(date_key: str, t: TaskIn):
    db = conn()
    mx = db.execute("SELECT COALESCE(MAX(order_idx),0) FROM tasks WHERE date_key=?",
                    (date_key,)).fetchone()[0]
    tid = uuid.uuid4().hex[:8]
    db.execute("INSERT INTO tasks (id,date_key,name,desc,pri,done,order_idx) VALUES(?,?,?,?,?,0,?)",
               (tid, date_key, t.name, t.desc, t.pri, mx + 1))
    db.commit(); db.close()
    return {"id": tid, "name": t.name, "desc": t.desc, "pri": t.pri, "done": False}

@app.put("/tasks/{date_key}/{tid}", dependencies=[Depends(auth)])
def edit_task(date_key: str, tid: str, t: TaskEdit):
    db = conn()
    db.execute("UPDATE tasks SET name=?,desc=?,pri=?,done=? WHERE id=? AND date_key=?",
               (t.name, t.desc, t.pri, int(t.done), tid, date_key))
    db.commit(); db.close(); return {"ok": True}

@app.patch("/tasks/{date_key}/{tid}/toggle", dependencies=[Depends(auth)])
def toggle_task(date_key: str, tid: str):
    db = conn()
    row = db.execute("SELECT done FROM tasks WHERE id=?", (tid,)).fetchone()
    if not row: raise HTTPException(404)
    nd = 0 if row["done"] else 1
    db.execute("UPDATE tasks SET done=? WHERE id=?", (nd, tid))
    db.commit(); db.close(); return {"done": bool(nd)}

@app.delete("/tasks/{date_key}/{tid}", dependencies=[Depends(auth)])
def del_task(date_key: str, tid: str):
    db = conn()
    db.execute("DELETE FROM tasks WHERE id=? AND date_key=?", (tid, date_key))
    db.commit(); db.close(); return {"ok": True}

@app.patch("/tasks/{date_key}/reorder", dependencies=[Depends(auth)])
def reorder_tasks(date_key: str, body: TaskOrder):
    db = conn()
    for i, tid in enumerate(body.order):
        db.execute("UPDATE tasks SET order_idx=? WHERE id=?", (i, tid))
    db.commit(); db.close(); return {"ok": True}

@app.get("/tasks-range", dependencies=[Depends(auth)])
def tasks_range(start: str, end: str):
    db = conn()
    rows = db.execute("SELECT * FROM tasks WHERE date_key>=? AND date_key<=?",
                      (start, end)).fetchall()
    db.close()
    return [{"id": r["id"], "name": r["name"], "desc": r["desc"],
             "pri": r["pri"], "done": bool(r["done"]), "date_key": r["date_key"]}
            for r in rows]

# ── Countdowns ────────────────────────────────────────────────────
@app.get("/countdowns", dependencies=[Depends(auth)])
def get_countdowns():
    db = conn()
    rows = db.execute("SELECT * FROM countdowns").fetchall()
    db.close(); return [dict(r) for r in rows]

@app.post("/countdowns", dependencies=[Depends(auth)])
def add_countdown(c: CdIn):
    db = conn(); cid = uuid.uuid4().hex[:8]
    db.execute("INSERT INTO countdowns (id,name,date,rep) VALUES(?,?,?,?)",
               (cid, c.name, c.date, c.rep))
    db.commit(); db.close()
    return {"id": cid, "name": c.name, "date": c.date, "rep": c.rep}

@app.put("/countdowns/{cid}", dependencies=[Depends(auth)])
def edit_countdown(cid: str, c: CdIn):
    db = conn()
    db.execute("UPDATE countdowns SET name=?,date=?,rep=? WHERE id=?",
               (c.name, c.date, c.rep, cid))
    db.commit(); db.close(); return {"ok": True}

@app.delete("/countdowns/{cid}", dependencies=[Depends(auth)])
def del_countdown(cid: str):
    db = conn()
    db.execute("DELETE FROM countdowns WHERE id=?", (cid,))
    db.commit(); db.close(); return {"ok": True}

# ── Weight ────────────────────────────────────────────────────────
@app.get("/weight", dependencies=[Depends(auth)])
def get_weight():
    db = conn()
    rows = db.execute("SELECT * FROM weight ORDER BY date_key").fetchall()
    db.close()
    return [{"date": r["date_key"], "w": r["w"], "ws": r["ws"]} for r in rows]

@app.post("/weight", dependencies=[Depends(auth)])
def upsert_weight(w: WeightIn):
    dk = date.today().isoformat(); db = conn()
    db.execute("INSERT INTO weight(date_key,w,ws) VALUES(?,?,?) "
               "ON CONFLICT(date_key) DO UPDATE SET "
               "w=COALESCE(excluded.w,w),ws=COALESCE(excluded.ws,ws)",
               (dk, w.w, w.ws))
    db.commit(); db.close(); return {"ok": True}

@app.put("/weight/{date_key}", dependencies=[Depends(auth)])
def update_weight(date_key: str, w: WeightIn):
    db = conn()
    db.execute("INSERT INTO weight(date_key,w,ws) VALUES(?,?,?) "
               "ON CONFLICT(date_key) DO UPDATE SET "
               "w=COALESCE(excluded.w,w),ws=COALESCE(excluded.ws,ws)",
               (date_key, w.w, w.ws))
    db.commit(); db.close(); return {"ok": True}

@app.delete("/weight/{date_key}", dependencies=[Depends(auth)])
def del_weight(date_key: str):
    db = conn()
    db.execute("DELETE FROM weight WHERE date_key=?", (date_key,))
    db.commit(); db.close(); return {"ok": True}

# ── Summaries ─────────────────────────────────────────────────────
@app.get("/summaries/{key}", dependencies=[Depends(auth)])
def get_summary(key: str):
    db = conn()
    row = db.execute("SELECT ref FROM summaries WHERE key=?", (key,)).fetchone()
    db.close(); return {"ref": row["ref"] if row else ""}

@app.put("/summaries/{key}", dependencies=[Depends(auth)])
def save_summary(key: str, s: SummaryIn):
    db = conn()
    db.execute("INSERT INTO summaries(key,ref) VALUES(?,?) "
               "ON CONFLICT(key) DO UPDATE SET ref=excluded.ref", (key, s.ref))
    db.commit(); db.close(); return {"ok": True}

# ── Thoughts ──────────────────────────────────────────────────────
@app.get("/thoughts", dependencies=[Depends(auth)])
def get_thoughts(type: Optional[str] = None):
    db = conn()
    if type:
        rows = db.execute("SELECT * FROM thoughts WHERE type=? ORDER BY period DESC",
                          (type,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM thoughts ORDER BY period DESC").fetchall()
    db.close(); return [dict(r) for r in rows]

@app.post("/thoughts", dependencies=[Depends(auth)])
def add_thought(t: ThoughtIn):
    db = conn(); tid = uuid.uuid4().hex[:8]
    created = datetime.now().strftime("%Y-%m-%d %H:%M")
    db.execute("INSERT INTO thoughts(id,type,period,content,created) VALUES(?,?,?,?,?)",
               (tid, t.type, t.period, t.content, created))
    db.commit(); db.close()
    return {"id": tid, "type": t.type, "period": t.period,
            "content": t.content, "created": created}

@app.put("/thoughts/{tid}", dependencies=[Depends(auth)])
def edit_thought(tid: str, t: ThoughtEdit):
    db = conn()
    db.execute("UPDATE thoughts SET content=? WHERE id=?", (t.content, tid))
    db.commit(); db.close(); return {"ok": True}

@app.delete("/thoughts/{tid}", dependencies=[Depends(auth)])
def del_thought(tid: str):
    db = conn()
    db.execute("DELETE FROM thoughts WHERE id=?", (tid,))
    db.commit(); db.close(); return {"ok": True}

# ── Data migration (import existing JSON) ─────────────────────────
@app.post("/migrate", dependencies=[Depends(auth)])
def migrate(data: dict):
    db = conn(); c = db.cursor()
    for dk2, tasks in data.get("tasks", {}).items():
        for i, t in enumerate(tasks):
            c.execute("INSERT OR REPLACE INTO tasks(id,date_key,name,desc,pri,done,order_idx) "
                      "VALUES(?,?,?,?,?,?,?)",
                      (t.get("id", uuid.uuid4().hex[:8]), dk2, t["name"],
                       t.get("desc",""), t.get("pri","n"), int(t.get("done",False)), i))
    for cd in data.get("countdowns", []):
        c.execute("INSERT OR REPLACE INTO countdowns(id,name,date,rep) VALUES(?,?,?,?)",
                  (cd.get("id", uuid.uuid4().hex[:8]), cd["name"],
                   cd["date"], cd.get("rep","none")))
    for w in data.get("weight", []):
        c.execute("INSERT OR REPLACE INTO weight(date_key,w,ws) VALUES(?,?,?)",
                  (w["date"], w.get("w"), w.get("ws")))
    for key, val in data.get("summaries", {}).items():
        ref = val.get("ref","") if isinstance(val, dict) else str(val)
        c.execute("INSERT OR REPLACE INTO summaries(key,ref) VALUES(?,?)", (key, ref))
    for t in data.get("thoughts", []):
        c.execute("INSERT OR REPLACE INTO thoughts(id,type,period,content,created) "
                  "VALUES(?,?,?,?,?)",
                  (t.get("id", uuid.uuid4().hex[:8]), t["type"], t["period"],
                   t["content"], t.get("created","")))
    db.commit(); db.close()
    return {"ok": True}

# ── Bulk export (used by desktop app cache + PDF) ────────────────
@app.get("/export", dependencies=[Depends(auth)])
def export_all():
    db = conn()
    task_rows = db.execute("SELECT * FROM tasks ORDER BY date_key,order_idx").fetchall()
    tasks = {}
    for r in task_rows:
        k = r["date_key"]
        if k not in tasks: tasks[k] = []
        tasks[k].append({"id": r["id"], "name": r["name"], "desc": r["desc"],
                         "pri": r["pri"], "done": bool(r["done"])})
    sum_rows  = db.execute("SELECT * FROM summaries").fetchall()
    wt_rows   = db.execute("SELECT * FROM weight ORDER BY date_key").fetchall()
    cd_rows   = db.execute("SELECT * FROM countdowns").fetchall()
    th_rows   = db.execute("SELECT * FROM thoughts ORDER BY period DESC").fetchall()
    db.close()
    return {
        "tasks":      tasks,
        "summaries":  {r["key"]: {"ref": r["ref"]} for r in sum_rows},
        "weight":     [{"date": r["date_key"], "w": r["w"], "ws": r["ws"]} for r in wt_rows],
        "countdowns": [dict(r) for r in cd_rows],
        "thoughts":   [dict(r) for r in th_rows],
    }

# ── Static web frontend ───────────────────────────────────────────
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def root():
    idx = os.path.join(static_dir, "index.html")
    if os.path.exists(idx):
        return FileResponse(idx)
    return {"status": "Life Planner API running"}
