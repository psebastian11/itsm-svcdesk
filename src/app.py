# ai-generated: 90% - FastAPI implementation generated for Lab 1 conformance
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Header, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="svcdesk")

DB_PATH = os.environ.get("SVCDESK_DB_PATH", "tickets.db")
WARSAW_TZ = ZoneInfo("Europe/Warsaw")
UTC_TZ = ZoneInfo("UTC")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                reporter_name TEXT NOT NULL,
                reporter_email TEXT,
                reporter_vip INTEGER NOT NULL,
                impact INTEGER NOT NULL,
                urgency INTEGER NOT NULL,
                priority TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                acknowledged_at TEXT,
                resolved_at TEXT,
                closed_at TEXT,
                related_to TEXT,
                ack_due_at TEXT NOT NULL,
                resolve_due_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


init_db()


def parse_rfc3339(ts_str: str) -> datetime:
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    return datetime.fromisoformat(ts_str)


def format_rfc3339(dt: datetime) -> str:
    dt_utc = dt.astimezone(UTC_TZ)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_request_now(x_test_clock: Optional[str]) -> datetime:
    test_clock_enabled = os.environ.get("SVCDESK_TEST_CLOCK", "").lower() in ("1", "true")
    if test_clock_enabled and x_test_clock:
        try:
            dt = parse_rfc3339(x_test_clock)
            if dt.tzinfo is None:
                raise HTTPException(status_code=422, detail="Clock must include timezone offset")
            return dt
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid X-Test-Clock header")
    return datetime.now(UTC_TZ)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": "validation", "message": str(exc)}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "error", "message": exc.detail}},
    )


# --- SLA Calculation Engine ---

def compute_priority(impact: int, urgency: int, vip: bool) -> str:
    matrix = {
        (1, 1): "P1", (1, 2): "P2", (1, 3): "P3",
        (2, 1): "P2", (2, 2): "P3", (2, 3): "P4",
        (3, 1): "P3", (3, 2): "P4", (3, 3): "P4",
    }
    p = matrix.get((impact, urgency), "P4")
    # C3: vip elevation
    if vip and p in ("P3", "P4"):
        p = "P2"
    return p


def is_in_business_window(dt: datetime) -> bool:
    local_dt = dt.astimezone(WARSAW_TZ)
    if local_dt.weekday() >= 5:
        return False
    opening = local_dt.replace(hour=8, minute=0, second=0, microsecond=0)
    closing = local_dt.replace(hour=16, minute=0, second=0, microsecond=0)
    return opening <= local_dt < closing


def add_business_seconds(start_dt: datetime, seconds_needed: int) -> datetime:
    curr = start_dt.astimezone(WARSAW_TZ)
    rem = seconds_needed

    while rem > 0:
        if curr.weekday() >= 5:
            days_ahead = 7 - curr.weekday()
            curr = (curr + timedelta(days=days_ahead)).replace(hour=8, minute=0, second=0, microsecond=0)
            continue

        opening = curr.replace(hour=8, minute=0, second=0, microsecond=0)
        closing = curr.replace(hour=16, minute=0, second=0, microsecond=0)

        if curr < opening:
            curr = opening
        elif curr >= closing:
            curr = (curr + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
            continue

        window_remaining = int((closing - curr).total_seconds())
        if rem <= window_remaining:
            return curr + timedelta(seconds=rem)
        else:
            rem -= window_remaining
            curr = (curr + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)

    return curr


def compute_sla_due(created_at: datetime, priority: str) -> tuple[datetime, datetime]:
    # C1 = wallclock: P1 is wallclock; P2..P4 are business hours
    if priority == "P1":
        ack_due = created_at + timedelta(minutes=15)
        resolve_due = created_at + timedelta(hours=4)
        return ack_due, resolve_due

    targets = {
        "P2": (1 * 3600, 8 * 3600),
        "P3": (4 * 3600, 24 * 3600),
        "P4": (8 * 3600, 72 * 3600),
    }
    ack_sec, resolve_sec = targets[priority]
    ack_due = add_business_seconds(created_at, ack_sec)
    resolve_due = add_business_seconds(created_at, resolve_sec)
    return ack_due, resolve_due


def row_to_ticket_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"] or "",
        "reporter": {
            "name": row["reporter_name"],
            "email": row["reporter_email"],
            "vip": bool(row["reporter_vip"]),
        },
        "impact": row["impact"],
        "urgency": row["urgency"],
        "priority": row["priority"],
        "state": row["state"],
        "created_at": row["created_at"],
        "acknowledged_at": row["acknowledged_at"],
        "resolved_at": row["resolved_at"],
        "closed_at": row["closed_at"],
        "related_to": row["related_to"],
        "sla": {
            "ack_due_at": row["ack_due_at"],
            "resolve_due_at": row["resolve_due_at"],
        },
    }


# --- Models ---

class ReporterModel(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: Optional[str] = None
    vip: Optional[bool] = False


class TicketCreateModel(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default="", max_length=4000)
    reporter: ReporterModel
    impact: int = Field(ge=1, le=3)
    urgency: int = Field(ge=1, le=3)
    related_to: Optional[str] = None

    class Config:
        extra = "ignore"


# --- Endpoints ---

@app.get("/health")
def health():
    return {"status": "ok", "service": "svcdesk"}


@app.post("/tickets", status_code=status.HTTP_201_CREATED)
def create_ticket(ticket_in: TicketCreateModel, x_test_clock: Optional[str] = Header(None)):
    now = get_request_now(x_test_clock)
    now_str = format_rfc3339(now)

    vip_flag = ticket_in.reporter.vip or False
    priority = compute_priority(ticket_in.impact, ticket_in.urgency, vip_flag)
    ack_due, resolve_due = compute_sla_due(now, priority)

    ticket_id = str(uuid.uuid4())
    ack_due_str = format_rfc3339(ack_due)
    resolve_due_str = format_rfc3339(resolve_due)

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO tickets (
                id, title, description, reporter_name, reporter_email, reporter_vip,
                impact, urgency, priority, state, created_at, acknowledged_at,
                resolved_at, closed_at, related_to, ack_due_at, resolve_due_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, NULL, NULL, NULL, ?, ?, ?)
            """,
            (
                ticket_id,
                ticket_in.title,
                ticket_in.description or "",
                ticket_in.reporter.name,
                ticket_in.reporter.email,
                1 if vip_flag else 0,
                ticket_in.impact,
                ticket_in.urgency,
                priority,
                now_str,
                ticket_in.related_to,
                ack_due_str,
                resolve_due_str,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        return row_to_ticket_dict(row)


@app.get("/tickets")
def list_tickets(state: Optional[str] = Query(None), priority: Optional[str] = Query(None)):
    query = "SELECT * FROM tickets WHERE 1=1"
    params = []
    if state:
        query += " AND state = ?"
        params.append(state)
    if priority:
        query += " AND priority = ?"
        params.append(priority)

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [row_to_ticket_dict(r) for r in rows]


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return row_to_ticket_dict(row)


@app.get("/tickets/{ticket_id}/sla")
def get_ticket_sla(ticket_id: str, x_test_clock: Optional[str] = Header(None)):
    now = get_request_now(x_test_clock)
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        ack_due = parse_rfc3339(row["ack_due_at"])
        resolve_due = parse_rfc3339(row["resolve_due_at"])

        if row["acknowledged_at"]:
            ack_time = parse_rfc3339(row["acknowledged_at"])
            ack_breached = ack_time > ack_due
        else:
            ack_breached = now > ack_due

        if row["state"] in ("resolved", "closed") and row["resolved_at"]:
            res_time = parse_rfc3339(row["resolved_at"])
            resolve_breached = res_time > resolve_due
        else:
            resolve_breached = now > resolve_due

        # C1: P1 wallclock never pauses
        priority = row["priority"]
        if priority == "P1":
            paused = False
        else:
            is_open = row["state"] not in ("resolved", "closed")
            paused = is_open and (not is_in_business_window(now))

        return {
            "priority": priority,
            "ack_due_at": row["ack_due_at"],
            "resolve_due_at": row["resolve_due_at"],
            "ack_breached": ack_breached,
            "resolve_breached": resolve_breached,
            "paused": paused,
        }


# --- State Transitions ---

@app.post("/tickets/{ticket_id}/ack")
def ack_ticket(ticket_id: str, x_test_clock: Optional[str] = Header(None)):
    now_str = format_rfc3339(get_request_now(x_test_clock))
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if row["state"] != "new":
            raise HTTPException(status_code=409, detail="Invalid transition to acknowledged")

        conn.execute(
            "UPDATE tickets SET state = 'acknowledged', acknowledged_at = ? WHERE id = ?",
            (now_str, ticket_id),
        )
        conn.commit()
        return row_to_ticket_dict(conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone())


@app.post("/tickets/{ticket_id}/start")
def start_ticket(ticket_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if row["state"] != "acknowledged":
            raise HTTPException(status_code=409, detail="Invalid transition to in_progress")

        conn.execute("UPDATE tickets SET state = 'in_progress' WHERE id = ?", (ticket_id,))
        conn.commit()
        return row_to_ticket_dict(conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone())


@app.post("/tickets/{ticket_id}/resolve")
def resolve_ticket(ticket_id: str, x_test_clock: Optional[str] = Header(None)):
    now_str = format_rfc3339(get_request_now(x_test_clock))
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if row["state"] != "in_progress":
            raise HTTPException(status_code=409, detail="Invalid transition to resolved")

        conn.execute(
            "UPDATE tickets SET state = 'resolved', resolved_at = ? WHERE id = ?",
            (now_str, ticket_id),
        )
        conn.commit()
        return row_to_ticket_dict(conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone())


@app.post("/tickets/{ticket_id}/close")
def close_ticket(ticket_id: str, x_test_clock: Optional[str] = Header(None)):
    now_str = format_rfc3339(get_request_now(x_test_clock))
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if row["state"] != "resolved":
            raise HTTPException(status_code=409, detail="Invalid transition to closed")

        conn.execute(
            "UPDATE tickets SET state = 'closed', closed_at = ? WHERE id = ?",
            (now_str, ticket_id),
        )
        conn.commit()
        return row_to_ticket_dict(conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone())


@app.post("/tickets/{ticket_id}/reopen")
def reopen_ticket(ticket_id: str, x_test_clock: Optional[str] = Header(None)):
    now = get_request_now(x_test_clock)
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # C2 = immutable: reopen only from resolved; closed is immutable
        if row["state"] == "closed":
            raise HTTPException(status_code=409, detail="Closed tickets are immutable")

        if row["state"] != "resolved":
            raise HTTPException(status_code=409, detail="Only resolved tickets can be reopened")

        resolved_at = parse_rfc3339(row["resolved_at"])
        if now > resolved_at + timedelta(days=7):
            raise HTTPException(status_code=409, detail="Reopen window expired (7 days)")

        conn.execute(
            "UPDATE tickets SET state = 'in_progress', resolved_at = NULL, closed_at = NULL WHERE id = ?",
            (ticket_id,),
        )
        conn.commit()
        return row_to_ticket_dict(conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone())
