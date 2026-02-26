"""HTTP client for FastAPI backend — used by Streamlit pages.

Optimized with:
- Connection pooling (keep-alive)
- Streamlit caching on all read-only GET calls (TTL=60s)
- Lower timeout for snappy UX
"""

import os
import hashlib
import json

import httpx
import streamlit as st

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
_API_KEY = os.getenv("API_KEY", "")
_headers = {"X-API-Key": _API_KEY} if _API_KEY else {}
_client = httpx.Client(
    base_url=BASE_URL,
    timeout=10.0,
    headers=_headers,
    limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
)

# ── Low-level helpers ────────────────────────────────────────────────


class APIError(RuntimeError):
    """Wraps httpx errors with user-friendly messages."""


def _handle_error(e: Exception) -> None:
    """Convert httpx exceptions to readable APIError."""
    if isinstance(e, httpx.ConnectError):
        raise APIError("API server unreachable — is the backend running?") from e
    if isinstance(e, httpx.TimeoutException):
        raise APIError("API request timed out — server may be overloaded") from e
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = e.response.text[:200]
        raise APIError(f"API error {status}: {detail}") from e
    raise APIError(str(e)) from e


def _get(path: str, params: dict | None = None) -> dict | list:
    try:
        r = _client.get(path, params=params)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        _handle_error(e)


def _post(path: str, data: dict | None = None) -> dict | list:
    try:
        r = _client.post(path, json=data or {})
        r.raise_for_status()
        return r.json()
    except Exception as e:
        _handle_error(e)


def _put(path: str, data: dict | None = None) -> dict | list:
    try:
        r = _client.put(path, json=data or {})
        r.raise_for_status()
        return r.json()
    except Exception as e:
        _handle_error(e)


def _delete(path: str) -> dict | list:
    try:
        r = _client.delete(path)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        _handle_error(e)


# ── Cached GET wrapper ───────────────────────────────────────────────
# All list/read operations cached for 60s. Mutations (POST/PUT/DELETE)
# call _clear_cache() to invalidate immediately.

@st.cache_data(ttl=60, show_spinner=False)
def _cached_get(path: str, _params_key: str = "", **kwargs) -> dict | list:
    """Cached GET — _params_key is a hashable repr of params for cache key."""
    params = kwargs.get("params")
    return _get(path, params=params)


def _cached(path: str, params: dict | None = None):
    """Convenience: call _cached_get with a stable cache key from params."""
    key = hashlib.md5(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest() if params else ""
    return _cached_get(path, _params_key=key, params=params)


def _clear_cache():
    """Invalidate all cached GET results after a mutation."""
    _cached_get.clear()


# ── Hierarchy ──────────────────────────────────────────────────────────

def list_plants():
    return _cached("/hierarchy/plants")

def list_nodes(plant_id=None, node_type=None, parent_node_id=None):
    params = {}
    if plant_id: params["plant_id"] = plant_id
    if node_type: params["node_type"] = node_type
    if parent_node_id: params["parent_node_id"] = parent_node_id
    return _cached("/hierarchy/nodes", params=params or None)

def get_node(node_id):
    return _cached(f"/hierarchy/nodes/{node_id}")

def get_subtree(node_id):
    return _cached(f"/hierarchy/nodes/{node_id}/tree")

def get_node_stats(plant_id=None):
    return _cached("/hierarchy/stats", params={"plant_id": plant_id} if plant_id else None)

def build_from_vendor(data):
    result = _post("/hierarchy/build-from-vendor", data)
    _clear_cache()
    return result

# ── Criticality ────────────────────────────────────────────────────────

def assess_criticality(data):
    result = _post("/criticality/assess", data)
    _clear_cache()
    return result

def get_criticality(node_id):
    return _cached(f"/criticality/{node_id}")

def approve_criticality(assessment_id):
    result = _put(f"/criticality/{assessment_id}/approve")
    _clear_cache()
    return result

# ── FMEA ───────────────────────────────────────────────────────────────

def list_functions(node_id=None):
    return _cached("/fmea/functions", params={"node_id": node_id} if node_id else None)

def create_function(data):
    result = _post("/fmea/functions", data)
    _clear_cache()
    return result

def list_functional_failures(function_id=None):
    return _cached("/fmea/functional-failures", params={"function_id": function_id} if function_id else None)

def create_functional_failure(data):
    result = _post("/fmea/functional-failures", data)
    _clear_cache()
    return result

def create_failure_mode(data):
    result = _post("/fmea/failure-modes", data)
    _clear_cache()
    return result

def get_failure_mode(fm_id):
    return _cached(f"/fmea/failure-modes/{fm_id}")

def list_failure_modes(functional_failure_id=None):
    return _cached("/fmea/failure-modes", params={"functional_failure_id": functional_failure_id} if functional_failure_id else None)

def validate_fm_combination(mechanism, cause):
    return _post("/fmea/validate-combination", {"mechanism": mechanism, "cause": cause})

def get_fm_combinations(mechanism=None):
    return _cached("/fmea/fm-combinations", params={"mechanism": mechanism} if mechanism else None)

def rcm_decide(data):
    return _post("/fmea/rcm-decide", data)

# ── Tasks ──────────────────────────────────────────────────────────────

def create_task(data):
    result = _post("/tasks/", data)
    _clear_cache()
    return result

def get_task(task_id):
    return _cached(f"/tasks/{task_id}")

def list_tasks(failure_mode_id=None, status=None):
    params = {}
    if failure_mode_id: params["failure_mode_id"] = failure_mode_id
    if status: params["status"] = status
    return _cached("/tasks/", params=params or None)

def link_task_to_fm(task_id, fm_id):
    result = _post(f"/tasks/link-fm/{task_id}/{fm_id}")
    _clear_cache()
    return result

def validate_task_name(name, task_type=""):
    return _post("/tasks/validate-name", {"name": name, "task_type": task_type})

def validate_wp_name(name):
    return _post("/tasks/validate-wp-name", {"name": name})

# ── Work Packages ──────────────────────────────────────────────────────

def create_work_package(data):
    result = _post("/work-packages/", data)
    _clear_cache()
    return result

def get_work_package(wp_id):
    return _cached(f"/work-packages/{wp_id}")

def list_work_packages(node_id=None, status=None):
    params = {}
    if node_id: params["node_id"] = node_id
    if status: params["status"] = status
    return _cached("/work-packages/", params=params or None)

def approve_work_package(wp_id):
    result = _put(f"/work-packages/{wp_id}/approve")
    _clear_cache()
    return result

def group_tasks(items):
    return _post("/work-packages/group", {"items": items})

def generate_work_instruction(wp_id, data):
    return _post(f"/work-packages/{wp_id}/work-instruction", data)

# ── SAP ────────────────────────────────────────────────────────────────

def list_sap_uploads(plant_code=None):
    return _cached("/sap/uploads", params={"plant_code": plant_code} if plant_code else None)

def approve_sap_upload(package_id):
    result = _put(f"/sap/uploads/{package_id}/approve")
    _clear_cache()
    return result

def get_sap_mock(transaction):
    return _cached(f"/sap/mock/{transaction}")

# ── Analytics ──────────────────────────────────────────────────────────

def calculate_health_score(data):
    return _post("/analytics/health-score", data)

def calculate_kpis(data):
    return _post("/analytics/kpis", data)

def fit_weibull(failure_intervals):
    return _post("/analytics/weibull-fit", {"failure_intervals": failure_intervals})

def predict_failure(data):
    return _post("/analytics/weibull-predict", data)

# ── Admin ──────────────────────────────────────────────────────────────

def seed_database():
    result = _post("/admin/seed-database")
    _clear_cache()
    return result

def get_stats():
    return _cached("/admin/stats")

def get_audit_log(entity_type=None, limit=50):
    params = {"limit": limit}
    if entity_type: params["entity_type"] = entity_type
    return _cached("/admin/audit-log", params=params)

def get_agent_status():
    return _cached("/admin/agent-status")


# ── Capture (M1) ─────────────────────────────────────────────────────

def submit_capture(data):
    result = _post("/capture/", data)
    _clear_cache()
    return result

def list_captures():
    return _cached("/capture/")

def get_capture(capture_id):
    return _cached(f"/capture/{capture_id}")

# ── Work Requests (M1-M2) ────────────────────────────────────────────

def list_work_requests(status=None):
    return _cached("/work-requests/", params={"status": status} if status else None)

def get_work_request(request_id):
    return _cached(f"/work-requests/{request_id}")

def validate_work_request(request_id, action, modifications=None):
    result = _put(f"/work-requests/{request_id}/validate", {"action": action, "modifications": modifications})
    _clear_cache()
    return result

def classify_work_request(request_id):
    result = _post(f"/work-requests/{request_id}/classify")
    _clear_cache()
    return result

# ── Planner (M2) ─────────────────────────────────────────────────────

def generate_recommendation(work_request_id):
    return _post(f"/planner/{work_request_id}/recommend")

def get_recommendation(recommendation_id):
    return _cached(f"/planner/recommendations/{recommendation_id}")

def apply_planner_action(recommendation_id, action, modifications=None):
    result = _put(f"/planner/recommendations/{recommendation_id}/action", {"action": action, "modifications": modifications})
    _clear_cache()
    return result

# ── Backlog (M3) ─────────────────────────────────────────────────────

def list_backlog(status=None, priority=None, equipment_tag=None):
    params = {}
    if status: params["status"] = status
    if priority: params["priority"] = priority
    if equipment_tag: params["equipment_tag"] = equipment_tag
    return _cached("/backlog/", params=params or None)

def add_to_backlog(work_request_id):
    result = _post(f"/backlog/add/{work_request_id}")
    _clear_cache()
    return result

def optimize_backlog(plant_id, period_days=30):
    result = _post("/backlog/optimize", {"plant_id": plant_id, "period_days": period_days})
    _clear_cache()
    return result

def get_optimization(optimization_id):
    return _cached(f"/backlog/optimizations/{optimization_id}")

def approve_schedule(optimization_id):
    result = _put(f"/backlog/optimizations/{optimization_id}/approve")
    _clear_cache()
    return result

def get_schedule():
    return _cached("/backlog/schedule")

# ── Scheduling (Phase 4B) ──────────────────────────────────────────

def create_program(plant_id, week_number, year):
    result = _post("/scheduling/programs", {"plant_id": plant_id, "week_number": week_number, "year": year})
    _clear_cache()
    return result

def list_programs(plant_id=None, status=None):
    params = {}
    if plant_id: params["plant_id"] = plant_id
    if status: params["status"] = status
    return _cached("/scheduling/programs", params=params or None)

def get_program(program_id):
    return _cached(f"/scheduling/programs/{program_id}")

def finalize_program(program_id):
    result = _put(f"/scheduling/programs/{program_id}/finalize")
    _clear_cache()
    return result

def get_gantt(program_id):
    return _cached(f"/scheduling/programs/{program_id}/gantt")


# ── Reliability (Phase 5) ─────────────────────────────────────────

def analyze_spare_parts(plant_id, parts):
    return _post("/reliability/spare-parts/analyze", {"plant_id": plant_id, "parts": parts})

def create_shutdown(plant_id, name, planned_start, planned_end, work_orders):
    result = _post("/reliability/shutdowns", {"plant_id": plant_id, "name": name, "planned_start": planned_start, "planned_end": planned_end, "work_orders": work_orders})
    _clear_cache()
    return result

def get_shutdown(shutdown_id):
    return _cached(f"/reliability/shutdowns/{shutdown_id}")

def create_moc(plant_id, title, description, category, requester_id, affected_equipment=None, risk_level="LOW"):
    result = _post("/reliability/moc", {"plant_id": plant_id, "title": title, "description": description, "category": category, "requester_id": requester_id, "affected_equipment": affected_equipment or [], "risk_level": risk_level})
    _clear_cache()
    return result

def list_mocs(plant_id=None, status=None):
    params = {}
    if plant_id: params["plant_id"] = plant_id
    if status: params["status"] = status
    return _cached("/reliability/moc", params=params or None)

def advance_moc(moc_id, action, **kwargs):
    result = _put(f"/reliability/moc/{moc_id}/advance", data={"action": action, **kwargs})
    _clear_cache()
    return result

def calculate_ocr(data):
    return _post("/reliability/ocr/analyze", data)

def analyze_jackknife(plant_id, equipment_data):
    return _post("/reliability/jackknife/analyze", {"plant_id": plant_id, "equipment_data": equipment_data})

def analyze_pareto(plant_id, metric_type, records):
    return _post("/reliability/pareto/analyze", {"plant_id": plant_id, "metric_type": metric_type, "records": records})

def assess_rbi(plant_id, equipment_list):
    return _post("/reliability/rbi/assess", {"plant_id": plant_id, "equipment_list": equipment_list})


# ── Reporting (Phase 6) ─────────────────────────────────────────

def generate_weekly_report(plant_id, week, year, data=None):
    return _post("/reporting/reports/weekly", {"plant_id": plant_id, "week": week, "year": year, **(data or {})})

def generate_monthly_report(plant_id, month, year, data=None):
    return _post("/reporting/reports/monthly", {"plant_id": plant_id, "month": month, "year": year, **(data or {})})

def generate_quarterly_report(plant_id, quarter, year, data=None):
    return _post("/reporting/reports/quarterly", {"plant_id": plant_id, "quarter": quarter, "year": year, **(data or {})})

def list_reports(plant_id=None, report_type=None):
    params = {}
    if plant_id: params["plant_id"] = plant_id
    if report_type: params["report_type"] = report_type
    return _cached("/reporting/reports", params=params or None)

def get_report(report_id):
    return _cached(f"/reporting/reports/{report_id}")

def calculate_de_kpis_standalone(data):
    return _post("/reporting/de-kpis/calculate", data)

def generate_notifications(plant_id, data=None):
    return _post("/reporting/notifications/generate", {"plant_id": plant_id, **(data or {})})

def list_notifications(plant_id=None, level=None):
    params = {}
    if plant_id: params["plant_id"] = plant_id
    if level: params["level"] = level
    return _cached("/reporting/notifications", params=params or None)

def acknowledge_notification(notification_id):
    result = _put(f"/reporting/notifications/{notification_id}/ack")
    _clear_cache()
    return result

def validate_import(source, rows):
    return _post("/reporting/import/validate", {"source": source, "rows": rows})

def export_data(export_type, data):
    return _post("/reporting/export", {"export_type": export_type, **data})

def run_cross_module_analysis(plant_id, data=None):
    return _post("/reporting/cross-module/analyze", {"plant_id": plant_id, **(data or {})})

# ── Dashboard (Phase 6) ─────────────────────────────────────────

def get_executive_dashboard(plant_id):
    return _cached(f"/dashboard/executive/{plant_id}")

def get_kpi_summary(plant_id):
    return _cached(f"/dashboard/kpi-summary/{plant_id}")

def get_dashboard_alerts(plant_id):
    return _cached(f"/dashboard/alerts/{plant_id}")

# ── FMECA (Phase 7) ──────────────────────────────────────────────

def create_fmeca_worksheet(data):
    result = _post("/fmea/fmeca/worksheets", data)
    _clear_cache()
    return result

def get_fmeca_worksheet(worksheet_id):
    return _cached(f"/fmea/fmeca/worksheets/{worksheet_id}")

def calculate_rpn(severity, occurrence, detection):
    return _post("/fmea/fmeca/rpn", {"severity": severity, "occurrence": occurrence, "detection": detection})

def run_fmeca_decisions(worksheet_id):
    result = _put(f"/fmea/fmeca/worksheets/{worksheet_id}/run-decisions")
    _clear_cache()
    return result

def get_fmeca_summary(worksheet_id):
    return _cached(f"/fmea/fmeca/worksheets/{worksheet_id}/summary")


# ── RCA & Defect Elimination (Phase 8) ────────────────────────────

def create_rca(data):
    result = _post("/rca/analyses", data)
    _clear_cache()
    return result

def list_rcas(plant_id=None, status=None):
    params = {}
    if plant_id: params["plant_id"] = plant_id
    if status: params["status"] = status
    return _cached("/rca/analyses", params=params or None)

def get_rca(analysis_id):
    return _cached(f"/rca/analyses/{analysis_id}")

def get_rca_summary(plant_id=None):
    return _cached("/rca/analyses/summary", params={"plant_id": plant_id} if plant_id else None)

def run_5w2h(analysis_id, data):
    return _post(f"/rca/analyses/{analysis_id}/5w2h", data)

def advance_rca(analysis_id, status):
    result = _put(f"/rca/analyses/{analysis_id}/advance", {"status": status})
    _clear_cache()
    return result

def calculate_planning_kpis(data):
    return _post("/rca/planning-kpis/calculate", data)

def list_planning_kpi_snapshots(plant_id=None):
    return _cached("/rca/planning-kpis", params={"plant_id": plant_id} if plant_id else None)

def calculate_de_kpis_full(data):
    return _post("/rca/de-kpis/calculate", data)

def list_de_kpi_snapshots(plant_id=None):
    return _cached("/rca/de-kpis", params={"plant_id": plant_id} if plant_id else None)


# ── Equipment Autocomplete ────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def list_equipment_tags():
    """Get equipment nodes for autocomplete in Field Capture."""
    nodes = _get("/hierarchy/nodes", params={"node_type": "EQUIPMENT"})
    return [
        {"tag": n.get("tag") or n.get("code", ""), "name": n.get("name", ""), "node_id": n.get("node_id", "")}
        for n in nodes
        if n.get("tag") or n.get("code")
    ]

# ── Feedback (Phase 9) ─────────────────────────────────────────────

def submit_feedback(data):
    return _post("/admin/feedback", data)

def list_feedback(page=None, limit=50):
    params = {"limit": limit}
    if page:
        params["page"] = page
    return _cached("/admin/feedback", params=params)
