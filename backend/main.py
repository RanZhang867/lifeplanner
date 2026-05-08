#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Life Planner — FastAPI Backend"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import psycopg2
import psycopg2.extras
import os, uuid
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
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    db = psycopg2.connect(DATABASE_URL)
    cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return db, cur

def init_db():
    db, cur = get_db()
    cur.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        date_key TEXT NOT NULL,
        name TEXT NOT NULL,
        descr TEXT DEFAULT '',
        pri TEXT DEFAULT 'n',
        done INTEGER DEFAULT 0,
        order_idx INTEGER DEFAULT 0
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS countdowns (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        date TEXT NOT NULL,
        rep TEXT DEFAULT 'none'
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS weight (
        date_key TEXT PRIMARY KEY,
        w REAL,
        ws REAL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS summaries (
        key TEXT PRIMARY KEY,
        ref TEXT DEFAULT ''
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS thoughts (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        period TEXT NOT NULL,
        content TEXT NOT NULL,
        created TEXT NOT NULL
    )""")
    db.commit()
    cur.close()
    db.close()

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
    db, cur = get_db()
    cur.execute("SELECT * FROM tasks WHERE date_key=%s ORDER BY order_idx", (date_key,))
    rows = cur.fetchall()
    cur.close(); db.close()
    return [{"id": r["id"], "name": r["name"], "desc": r["descr"],
             "pri": r["pri"], "done": bool(r["done"])} for r in rows]

@app.post("/tasks/{date_key}", dependencies=[Depends(auth)])
def add_task(date_key: str, t: TaskIn):
    db, cur = get_db()
    cur.execute("SELECT COALESCE(MAX(order_idx),0) AS mx FROM tasks WHERE date_key=%s", (date_key,))
    mx = cur.fetchone()["mx"]
    tid = uuid.uuid4().hex[:8]
    cur.execute("INSERT INTO tasks (id,date_key,name,descr,pri,done,order_idx) VALUES(%s,%s,%s,%s,%s,0,%s)",
               (tid, date_key, t.name, t.desc, t.pri, mx + 1))
    db.commit(); cur.close(); db.close()
    return {"id": tid, "name": t.name, "desc": t.desc, "pri": t.pri, "done": False}

@app.put("/tasks/{date_key}/{tid}", dependencies=[Depends(auth)])
def edit_task(date_key: str, tid: str, t: TaskEdit):
    db, cur = get_db()
    cur.execute("UPDATE tasks SET name=%s,descr=%s,pri=%s,done=%s WHERE id=%s AND date_key=%s",
               (t.name, t.desc, t.pri, int(t.done), tid, date_key))
    db.commit(); cur.close(); db.close(); return {"ok": True}

@app.patch("/tasks/{date_key}/{tid}/toggle", dependencies=[Depends(auth)])
def toggle_task(date_key: str, tid: str):
    db, cur = get_db()
    cur.execute("SELECT done FROM tasks WHERE id=%s", (tid,))
    row = cur.fetchone()
    if not row:
        cur.close(); db.close(); raise HTTPException(404)
    nd = 0 if row["done"] else 1
    cur.execute("UPDATE tasks SET done=%s WHERE id=%s", (nd, tid))
    db.commit(); cur.close(); db.close(); return {"done": bool(nd)}

@app.delete("/tasks/{date_key}/{tid}", dependencies=[Depends(auth)])
def del_task(date_key: str, tid: str):
    db, cur = get_db()
    cur.execute("DELETE FROM tasks WHERE id=%s AND date_key=%s", (tid, date_key))
    db.commit(); cur.close(); db.close(); return {"ok": True}

@app.patch("/tasks/{date_key}/reorder", dependencies=[Depends(auth)])
def reorder_tasks(date_key: str, body: TaskOrder):
    db, cur = get_db()
    for i, tid in enumerate(body.order):
        cur.execute("UPDATE tasks SET order_idx=%s WHERE id=%s", (i, tid))
    db.commit(); cur.close(); db.close(); return {"ok": True}

@app.get("/tasks-range", dependencies=[Depends(auth)])
def tasks_range(start: str, end: str):
    db, cur = get_db()
    cur.execute("SELECT * FROM tasks WHERE date_key>=%s AND date_key<=%s", (start, end))
    rows = cur.fetchall()
    cur.close(); db.close()
    return [{"id": r["id"], "name": r["name"], "desc": r["descr"],
             "pri": r["pri"], "done": bool(r["done"]), "date_key": r["date_key"]}
            for r in rows]

# ── Countdowns ────────────────────────────────────────────────────
@app.get("/countdowns", dependencies=[Depends(auth)])
def get_countdowns():
    db, cur = get_db()
    cur.execute("SELECT * FROM countdowns")
    rows = cur.fetchall()
    cur.close(); db.close(); return [dict(r) for r in rows]

@app.post("/countdowns", dependencies=[Depends(auth)])
def add_countdown(c: CdIn):
    db, cur = get_db()
    cid = uuid.uuid4().hex[:8]
    cur.execute("INSERT INTO countdowns (id,name,date,rep) VALUES(%s,%s,%s,%s)",
               (cid, c.name, c.date, c.rep))
    db.commit(); cur.close(); db.close()
    return {"id": cid, "name": c.name, "date": c.date, "rep": c.rep}

@app.put("/countdowns/{cid}", dependencies=[Depends(auth)])
def edit_countdown(cid: str, c: CdIn):
    db, cur = get_db()
    cur.execute("UPDATE countdowns SET name=%s,date=%s,rep=%s WHERE id=%s",
               (c.name, c.date, c.rep, cid))
    db.commit(); cur.close(); db.close(); return {"ok": True}

@app.delete("/countdowns/{cid}", dependencies=[Depends(auth)])
def del_countdown(cid: str):
    db, cur = get_db()
    cur.execute("DELETE FROM countdowns WHERE id=%s", (cid,))
    db.commit(); cur.close(); db.close(); return {"ok": True}

# ── Weight ────────────────────────────────────────────────────────
@app.get("/weight", dependencies=[Depends(auth)])
def get_weight():
    db, cur = get_db()
    cur.execute("SELECT * FROM weight ORDER BY date_key")
    rows = cur.fetchall()
    cur.close(); db.close()
    return [{"date": r["date_key"], "w": r["w"], "ws": r["ws"]} for r in rows]

@app.post("/weight", dependencies=[Depends(auth)])
def upsert_weight(w: WeightIn):
    dk = date.today().isoformat()
    db, cur = get_db()
    cur.execute("INSERT INTO weight(date_key,w,ws) VALUES(%s,%s,%s) "
               "ON CONFLICT(date_key) DO UPDATE SET "
               "w=COALESCE(EXCLUDED.w,weight.w),ws=COALESCE(EXCLUDED.ws,weight.ws)",
               (dk, w.w, w.ws))
    db.commit(); cur.close(); db.close(); return {"ok": True}

@app.put("/weight/{date_key}", dependencies=[Depends(auth)])
def update_weight(date_key: str, w: WeightIn):
    db, cur = get_db()
    cur.execute("INSERT INTO weight(date_key,w,ws) VALUES(%s,%s,%s) "
               "ON CONFLICT(date_key) DO UPDATE SET "
               "w=COALESCE(EXCLUDED.w,weight.w),ws=COALESCE(EXCLUDED.ws,weight.ws)",
               (date_key, w.w, w.ws))
    db.commit(); cur.close(); db.close(); return {"ok": True}

@app.delete("/weight/{date_key}", dependencies=[Depends(auth)])
def del_weight(date_key: str):
    db, cur = get_db()
    cur.execute("DELETE FROM weight WHERE date_key=%s", (date_key,))
    db.commit(); cur.close(); db.close(); return {"ok": True}

# ── Summaries ─────────────────────────────────────────────────────
@app.get("/summaries/{key}", dependencies=[Depends(auth)])
def get_summary(key: str):
    db, cur = get_db()
    cur.execute("SELECT ref FROM summaries WHERE key=%s", (key,))
    row = cur.fetchone()
    cur.close(); db.close(); return {"ref": row["ref"] if row else ""}

@app.put("/summaries/{key}", dependencies=[Depends(auth)])
def save_summary(key: str, s: SummaryIn):
    db, cur = get_db()
    cur.execute("INSERT INTO summaries(key,ref) VALUES(%s,%s) "
               "ON CONFLICT(key) DO UPDATE SET ref=EXCLUDED.ref", (key, s.ref))
    db.commit(); cur.close(); db.close(); return {"ok": True}

# ── Thoughts ──────────────────────────────────────────────────────
@app.get("/thoughts", dependencies=[Depends(auth)])
def get_thoughts(type: Optional[str] = None):
    db, cur = get_db()
    if type:
        cur.execute("SELECT * FROM thoughts WHERE type=%s ORDER BY period DESC", (type,))
    else:
        cur.execute("SELECT * FROM thoughts ORDER BY period DESC")
    rows = cur.fetchall()
    cur.close(); db.close(); return [dict(r) for r in rows]

@app.post("/thoughts", dependencies=[Depends(auth)])
def add_thought(t: ThoughtIn):
    db, cur = get_db()
    tid = uuid.uuid4().hex[:8]
    created = datetime.now().strftime("%Y-%m-%d %H:%M")
    cur.execute("INSERT INTO thoughts(id,type,period,content,created) VALUES(%s,%s,%s,%s,%s)",
               (tid, t.type, t.period, t.content, created))
    db.commit(); cur.close(); db.close()
    return {"id": tid, "type": t.type, "period": t.period,
            "content": t.content, "created": created}

@app.put("/thoughts/{tid}", dependencies=[Depends(auth)])
def edit_thought(tid: str, t: ThoughtEdit):
    db, cur = get_db()
    cur.execute("UPDATE thoughts SET content=%s WHERE id=%s", (t.content, tid))
    db.commit(); cur.close(); db.close(); return {"ok": True}

@app.delete("/thoughts/{tid}", dependencies=[Depends(auth)])
def del_thought(tid: str):
    db, cur = get_db()
    cur.execute("DELETE FROM thoughts WHERE id=%s", (tid,))
    db.commit(); cur.close(); db.close(); return {"ok": True}

# ── Data migration (import existing JSON) ─────────────────────────
@app.post("/migrate", dependencies=[Depends(auth)])
def migrate(data: dict):
    db, cur = get_db()
    for dk2, tasks in data.get("tasks", {}).items():
        for i, t in enumerate(tasks):
            cur.execute("INSERT INTO tasks(id,date_key,name,descr,pri,done,order_idx) "
                      "VALUES(%s,%s,%s,%s,%s,%s,%s) "
                      "ON CONFLICT(id) DO UPDATE SET "
                      "date_key=EXCLUDED.date_key,name=EXCLUDED.name,descr=EXCLUDED.descr,"
                      "pri=EXCLUDED.pri,done=EXCLUDED.done,order_idx=EXCLUDED.order_idx",
                      (t.get("id", uuid.uuid4().hex[:8]), dk2, t["name"],
                       t.get("desc",""), t.get("pri","n"), int(t.get("done",False)), i))
    for cd in data.get("countdowns", []):
        cur.execute("INSERT INTO countdowns(id,name,date,rep) VALUES(%s,%s,%s,%s) "
                  "ON CONFLICT(id) DO UPDATE SET "
                  "name=EXCLUDED.name,date=EXCLUDED.date,rep=EXCLUDED.rep",
                  (cd.get("id", uuid.uuid4().hex[:8]), cd["name"],
                   cd["date"], cd.get("rep","none")))
    for w in data.get("weight", []):
        cur.execute("INSERT INTO weight(date_key,w,ws) VALUES(%s,%s,%s) "
                  "ON CONFLICT(date_key) DO UPDATE SET "
                  "w=COALESCE(EXCLUDED.w,weight.w),ws=COALESCE(EXCLUDED.ws,weight.ws)",
                  (w["date"], w.get("w"), w.get("ws")))
    for key, val in data.get("summaries", {}).items():
        ref = val.get("ref","") if isinstance(val, dict) else str(val)
        cur.execute("INSERT INTO summaries(key,ref) VALUES(%s,%s) "
                  "ON CONFLICT(key) DO UPDATE SET ref=EXCLUDED.ref", (key, ref))
    for t in data.get("thoughts", []):
        cur.execute("INSERT INTO thoughts(id,type,period,content,created) "
                  "VALUES(%s,%s,%s,%s,%s) "
                  "ON CONFLICT(id) DO UPDATE SET "
                  "type=EXCLUDED.type,period=EXCLUDED.period,"
                  "content=EXCLUDED.content,created=EXCLUDED.created",
                  (t.get("id", uuid.uuid4().hex[:8]), t["type"], t["period"],
                   t["content"], t.get("created","")))
    db.commit(); cur.close(); db.close()
    return {"ok": True}

# ── Bulk export (used by desktop app cache + PDF) ────────────────
@app.get("/export", dependencies=[Depends(auth)])
def export_all():
    db, cur = get_db()
    cur.execute("SELECT * FROM tasks ORDER BY date_key,order_idx")
    task_rows = cur.fetchall()
    tasks = {}
    for r in task_rows:
        k = r["date_key"]
        if k not in tasks: tasks[k] = []
        tasks[k].append({"id": r["id"], "name": r["name"], "desc": r["descr"],
                         "pri": r["pri"], "done": bool(r["done"])})
    cur.execute("SELECT * FROM summaries")
    sum_rows = cur.fetchall()
    cur.execute("SELECT * FROM weight ORDER BY date_key")
    wt_rows = cur.fetchall()
    cur.execute("SELECT * FROM countdowns")
    cd_rows = cur.fetchall()
    cur.execute("SELECT * FROM thoughts ORDER BY period DESC")
    th_rows = cur.fetchall()
    cur.close(); db.close()
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
