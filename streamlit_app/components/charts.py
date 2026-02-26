"""Reusable Plotly charts for the Streamlit dashboard."""

import plotly.graph_objects as go


def health_gauge(score: float, title: str = "Health Score") -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [0, 50], "color": "#ff4444"},
                {"range": [50, 75], "color": "#ffaa00"},
                {"range": [75, 100], "color": "#00cc44"},
            ],
            "threshold": {"line": {"color": "black", "width": 2}, "thickness": 0.75, "value": score},
        },
    ))
    fig.update_layout(height=250, margin=dict(t=40, b=20, l=20, r=20))
    return fig


def kpi_bar_chart(kpis: dict, title: str = "KPI Summary") -> go.Figure:
    names = []
    values = []
    for k, v in kpis.items():
        if v is not None and isinstance(v, (int, float)):
            names.append(k.replace("_", " ").title())
            values.append(v)

    colors = ["#1f77b4" if v >= 80 else "#ff7f0e" if v >= 50 else "#d62728" for v in values]
    fig = go.Figure(go.Bar(x=names, y=values, marker_color=colors))
    fig.update_layout(title=title, yaxis_title="Value", height=350, margin=dict(t=50, b=40))
    return fig


def weibull_curve(times: list[float], reliabilities: list[float], title: str = "Reliability Curve") -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=reliabilities, mode="lines", name="R(t)", line=dict(color="#1f77b4", width=2)))
    fig.update_layout(title=title, xaxis_title="Time (days)", yaxis_title="Reliability R(t)", height=350, yaxis=dict(range=[0, 1.05]))
    return fig


def node_distribution_pie(counts: dict, title: str = "Hierarchy Distribution") -> go.Figure:
    fig = go.Figure(go.Pie(labels=list(counts.keys()), values=list(counts.values()), hole=0.4))
    fig.update_layout(title=title, height=350)
    return fig


def hierarchy_sunburst(nodes: list[dict], title: str = "Hierarchy Sunburst") -> go.Figure:
    """Interactive sunburst chart showing the full plant hierarchy."""
    if not nodes:
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig

    TYPE_COLORS = {
        "PLANT": "#1B5E20", "AREA": "#0D47A1", "SYSTEM": "#E65100",
        "EQUIPMENT": "#4A148C", "SUB_ASSEMBLY": "#006064", "MAINTAINABLE_ITEM": "#BF360C",
    }

    node_ids_in_set = {n["node_id"] for n in nodes}
    ids, labels, parents, colors = [], [], [], []

    for n in nodes:
        ids.append(n["node_id"])
        labels.append(n["name"][:25])
        parent = n.get("parent_node_id", "")
        parents.append(parent if parent in node_ids_in_set else "")
        colors.append(TYPE_COLORS.get(n.get("node_type", ""), "#999"))

    fig = go.Figure(go.Sunburst(
        ids=ids, labels=labels, parents=parents,
        marker=dict(colors=colors),
        branchvalues="total",
        hovertemplate="<b>%{label}</b><extra></extra>",
        maxdepth=4,
    ))
    fig.update_layout(
        title=title, height=500,
        margin=dict(t=40, l=0, r=0, b=0),
        font=dict(family="Segoe UI, system-ui, sans-serif"),
    )
    return fig


# ── Phase 3: M1-3 Charts ────────────────────────────────────────────

def backlog_stratification_chart(stratification: dict, title: str = "Backlog Stratification") -> go.Figure:
    """Grouped bar chart showing backlog breakdown by reason, priority, criticality."""
    fig = go.Figure()
    colors = {"by_reason": "#1f77b4", "by_priority": "#ff7f0e", "by_equipment_criticality": "#2ca02c"}
    for category, data in stratification.items():
        if isinstance(data, dict) and data:
            fig.add_trace(go.Bar(
                name=category.replace("by_", "").replace("_", " ").title(),
                x=list(data.keys()),
                y=list(data.values()),
                marker_color=colors.get(category, "#666"),
            ))
    fig.update_layout(title=title, barmode="group", height=400, yaxis_title="Count")
    return fig


def schedule_utilization_chart(schedule_entries: list[dict], title: str = "Schedule Utilization") -> go.Figure:
    """Daily utilization bar chart from schedule entries."""
    dates = [e.get("date", "") for e in schedule_entries]
    utilization = [e.get("utilization_percent", 0) for e in schedule_entries]
    colors = ["#00cc44" if u < 80 else "#ffaa00" if u < 95 else "#ff4444" for u in utilization]

    fig = go.Figure(go.Bar(x=dates, y=utilization, marker_color=colors))
    fig.update_layout(title=title, yaxis_title="Utilization %", yaxis=dict(range=[0, 110]), height=350)
    fig.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="Target 80%")
    return fig


def priority_distribution_pie(items: list[dict], title: str = "Priority Distribution") -> go.Figure:
    """Pie chart of backlog items by priority."""
    from collections import Counter
    priorities = [i.get("priority", "UNKNOWN") for i in items]
    counts = Counter(priorities)
    color_map = {"1_EMERGENCY": "#d62728", "2_URGENT": "#ff7f0e", "3_NORMAL": "#1f77b4", "4_PLANNED": "#2ca02c"}
    colors = [color_map.get(p, "#999") for p in counts.keys()]

    fig = go.Figure(go.Pie(labels=list(counts.keys()), values=list(counts.values()), hole=0.4, marker=dict(colors=colors)))
    fig.update_layout(title=title, height=350)
    return fig


# ── Phase 4B: Scheduling Charts ──────────────────────────────────

def gantt_chart(gantt_rows: list[dict], title: str = "Weekly Program Gantt") -> go.Figure:
    """Horizontal bar Gantt chart from GanttRow dicts."""
    specialty_colors = {
        "MECHANICAL": "#4472C4", "ELECTRICAL": "#FFC000",
        "INSTRUMENTATION": "#70AD47", "WELDING": "#ED7D31",
        "GENERAL": "#A5A5A5",
    }

    fig = go.Figure()
    for row in reversed(gantt_rows):
        name = row.get("name", "")
        start = row.get("start_date", "")
        end = row.get("end_date", "")
        spec = row.get("specialty", "GENERAL")
        hours = row.get("duration_hours", 0)
        color = specialty_colors.get(spec, "#BDD7EE")

        fig.add_trace(go.Bar(
            x=[hours], y=[name],
            orientation="h",
            marker_color=color,
            name=spec,
            showlegend=False,
            hovertemplate=f"{name}<br>{start} to {end}<br>{spec}: {hours}h<extra></extra>",
        ))

    fig.update_layout(
        title=title, barmode="stack",
        xaxis_title="Hours", yaxis_title="",
        height=max(300, len(gantt_rows) * 35 + 100),
        margin=dict(l=200, t=50, b=40),
    )
    return fig


# ── Phase 5 Charts ────────────────────────────────────────────────────

ZONE_COLORS = {
    "ACUTE": "#e74c3c",
    "CHRONIC": "#f39c12",
    "COMPLEX": "#3498db",
    "CONTROLLED": "#2ecc71",
}


def jackknife_chart(points: list[dict], title: str = "Jack-Knife Diagram") -> go.Figure:
    """Scatter plot colored by zone with median crosshair lines."""
    fig = go.Figure()
    if not points:
        fig.update_layout(title=title)
        return fig

    for zone, color in ZONE_COLORS.items():
        zone_pts = [p for p in points if p.get("zone") == zone]
        if not zone_pts:
            continue
        fig.add_trace(go.Scatter(
            x=[p["mtbf_days"] for p in zone_pts],
            y=[p["mttr_hours"] for p in zone_pts],
            mode="markers+text",
            name=zone,
            marker=dict(size=12, color=color),
            text=[p.get("equipment_tag", p.get("equipment_id", ""))[:10] for p in zone_pts],
            textposition="top center",
            hovertemplate="%{text}<br>MTBF: %{x:.0f}d<br>MTTR: %{y:.1f}h<extra></extra>",
        ))

    import statistics
    mtbf_vals = [p["mtbf_days"] for p in points if p.get("mtbf_days", 0) > 0]
    mttr_vals = [p["mttr_hours"] for p in points if p.get("mttr_hours", 0) > 0]
    if mtbf_vals:
        med_mtbf = statistics.median(mtbf_vals)
        fig.add_vline(x=med_mtbf, line_dash="dash", line_color="gray", annotation_text="Median MTBF")
    if mttr_vals:
        med_mttr = statistics.median(mttr_vals)
        fig.add_hline(y=med_mttr, line_dash="dash", line_color="gray", annotation_text="Median MTTR")

    fig.update_layout(
        title=title,
        xaxis_title="MTBF (days)", yaxis_title="MTTR (hours)",
        height=500, legend_title="Zone",
    )
    return fig


def pareto_chart(items: list[dict], title: str = "Pareto Analysis") -> go.Figure:
    """Bar chart + cumulative line with 80% threshold."""
    fig = go.Figure()
    if not items:
        fig.update_layout(title=title)
        return fig

    labels = [i.get("equipment_tag", i.get("equipment_id", ""))[:12] for i in items]
    values = [i.get("metric_value", 0) for i in items]
    cum_pcts = [i.get("cumulative_pct", 0) for i in items]
    colors = ["#e74c3c" if i.get("is_bad_actor") else "#3498db" for i in items]

    fig.add_trace(go.Bar(
        x=labels, y=values, name="Value",
        marker_color=colors,
    ))
    fig.add_trace(go.Scatter(
        x=labels, y=cum_pcts, name="Cumulative %",
        yaxis="y2", mode="lines+markers",
        line=dict(color="#2ecc71", width=2),
    ))
    fig.add_hline(y=80, line_dash="dot", line_color="red", yref="y2",
                  annotation_text="80% threshold")

    fig.update_layout(
        title=title,
        yaxis_title="Value", yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
        height=450, barmode="group",
    )
    return fig


def rbi_risk_matrix(assessments: list[dict], title: str = "RBI Risk Matrix") -> go.Figure:
    """5×5 probability × consequence heatmap."""
    import numpy as np

    matrix = [[0]*5 for _ in range(5)]
    for a in assessments:
        p = min(5, max(1, a.get("probability_score", 1))) - 1
        c = min(5, max(1, a.get("consequence_score", 1))) - 1
        matrix[p][c] += 1

    risk_colors = [
        [1, 2, 3, 4, 5],
        [2, 4, 6, 8, 10],
        [3, 6, 9, 12, 15],
        [4, 8, 12, 16, 20],
        [5, 10, 15, 20, 25],
    ]

    fig = go.Figure(data=go.Heatmap(
        z=risk_colors,
        text=[[str(matrix[r][c]) if matrix[r][c] > 0 else "" for c in range(5)] for r in range(5)],
        texttemplate="%{text}",
        colorscale=[[0, "#2ecc71"], [0.4, "#f1c40f"], [0.7, "#e67e22"], [1.0, "#e74c3c"]],
        x=["1-Negligible", "2-Minor", "3-Moderate", "4-Major", "5-Catastrophic"],
        y=["1-Rare", "2-Unlikely", "3-Possible", "4-Likely", "5-Almost Certain"],
        showscale=False,
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Consequence", yaxis_title="Probability",
        height=450,
    )
    return fig


# ── Phase 6 Charts ────────────────────────────────────────────────────


def traffic_light_grid(kpi_data: list[dict], title: str = "KPI Traffic Lights") -> go.Figure:
    """Grid of colored indicators (GREEN/AMBER/RED) for KPIs."""
    names = [k.get("name", "") for k in kpi_data]
    colors = []
    for k in kpi_data:
        light = k.get("traffic_light", k.get("status", ""))
        if light in ("GREEN", "ON_TARGET"):
            colors.append("#2ecc71")
        elif light in ("AMBER", "ABOVE_TARGET"):
            colors.append("#f1c40f")
        else:
            colors.append("#e74c3c")
    values = [k.get("value", 0) or 0 for k in kpi_data]

    fig = go.Figure(go.Bar(
        x=names, y=values,
        marker_color=colors,
        text=[f"{v:.1f}%" if v else "" for v in values],
        textposition="outside",
    ))
    fig.update_layout(title=title, yaxis_title="Value (%)", height=400, showlegend=False)
    return fig


def kpi_trend_chart(
    periods: list[str], values: list[float], targets: list[float],
    title: str = "KPI Trend",
) -> go.Figure:
    """Line chart with actual values and target reference line."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=periods, y=values, mode="lines+markers", name="Actual"))
    fig.add_trace(go.Scatter(x=periods, y=targets, mode="lines", name="Target",
                             line=dict(dash="dash", color="red")))
    fig.update_layout(title=title, yaxis_title="Value", height=350)
    return fig


def notification_summary_chart(
    notifications: list[dict], title: str = "Active Alerts",
) -> go.Figure:
    """Horizontal stacked bar chart grouped by type and severity level."""
    types: dict[str, dict[str, int]] = {}
    for n in notifications:
        ntype = n.get("notification_type", "OTHER")
        level = n.get("level", "INFO")
        if ntype not in types:
            types[ntype] = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
        types[ntype][level] = types[ntype].get(level, 0) + 1

    fig = go.Figure()
    type_names = list(types.keys())
    for level, color in [("CRITICAL", "#e74c3c"), ("WARNING", "#f1c40f"), ("INFO", "#3498db")]:
        fig.add_trace(go.Bar(
            y=type_names,
            x=[types[t].get(level, 0) for t in type_names],
            name=level, orientation="h", marker_color=color,
        ))
    fig.update_layout(title=title, barmode="stack", height=350, xaxis_title="Count")
    return fig


def correlation_scatter(
    points: list[dict], title: str = "Correlation Analysis",
    x_label: str = "X", y_label: str = "Y",
) -> go.Figure:
    """Scatter plot for correlation display."""
    xs = [p.get("x_value", 0) for p in points]
    ys = [p.get("y_value", 0) for p in points]
    labels = [p.get("label", p.get("equipment_id", "")) for p in points]

    fig = go.Figure(go.Scatter(
        x=xs, y=ys, mode="markers+text", text=labels,
        textposition="top center", marker=dict(size=10),
    ))
    fig.update_layout(title=title, xaxis_title=x_label, yaxis_title=y_label, height=400)
    return fig


def bad_actor_overlap_chart(overlap: dict, title: str = "Bad Actor Overlap") -> go.Figure:
    """Grouped bar showing bad actor counts by source and overlaps."""
    categories = ["Jack-Knife Acute", "Pareto Bad Actors", "RBI High Risk",
                   "Overlap (2+)", "Overlap (All 3)"]
    values = [
        len(overlap.get("jackknife_acute", [])),
        len(overlap.get("pareto_bad_actors", [])),
        len(overlap.get("rbi_high_risk", [])),
        len(overlap.get("overlap_any_two", [])),
        len(overlap.get("overlap_all_three", [])),
    ]
    colors = ["#3498db", "#2ecc71", "#e67e22", "#f1c40f", "#e74c3c"]
    fig = go.Figure(go.Bar(x=categories, y=values, marker_color=colors))
    fig.update_layout(title=title, yaxis_title="Equipment Count", height=400)
    return fig


# ── Phase 9 Charts ────────────────────────────────────────────────────


def rca_level_distribution(analyses: list[dict], title: str = "RCA Level Distribution") -> go.Figure:
    """Pie chart showing RCA Level 1/2/3 distribution."""
    from collections import Counter
    levels = [a.get("level", "1") for a in analyses]
    counts = Counter(levels)
    labels = [f"Level {l}" for l in counts.keys()]
    colors = ["#2ecc71", "#f1c40f", "#e74c3c"]
    fig = go.Figure(go.Pie(
        labels=labels, values=list(counts.values()), hole=0.4,
        marker=dict(colors=colors[:len(labels)]),
    ))
    fig.update_layout(title=title, height=350)
    return fig


def planning_kpi_radar(kpis: list[dict], title: str = "Planning KPIs vs Targets") -> go.Figure:
    """Radar/spider chart for 11 planning KPIs vs targets."""
    fig = go.Figure()
    if not kpis:
        fig.update_layout(title=title)
        return fig

    names = [k.get("name", "").replace("_", " ").title()[:15] for k in kpis]
    actuals = [k.get("value", 0) or 0 for k in kpis]
    targets = [k.get("target", 0) or 0 for k in kpis]

    fig.add_trace(go.Scatterpolar(r=actuals, theta=names, fill="toself", name="Actual",
                                   line=dict(color="#1f77b4")))
    fig.add_trace(go.Scatterpolar(r=targets, theta=names, fill="toself", name="Target",
                                   line=dict(color="#ff7f0e", dash="dash"), opacity=0.4))
    fig.update_layout(title=title, polar=dict(radialaxis=dict(visible=True)), height=450)
    return fig


def de_program_gauge(score: float, maturity: str = "", title: str = "DE Program Health") -> go.Figure:
    """Gauge showing DE program score with maturity label."""
    color_map = {"INITIAL": "#e74c3c", "DEVELOPING": "#f1c40f", "ESTABLISHED": "#2ecc71", "OPTIMIZING": "#1f77b4"}
    bar_color = color_map.get(maturity, "#666")
    display_title = f"{title} — {maturity}" if maturity else title

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": display_title},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": bar_color},
            "steps": [
                {"range": [0, 25], "color": "#ffcccc"},
                {"range": [25, 50], "color": "#fff3cd"},
                {"range": [50, 75], "color": "#d4edda"},
                {"range": [75, 100], "color": "#cce5ff"},
            ],
        },
    ))
    fig.update_layout(height=250, margin=dict(t=60, b=20, l=20, r=20))
    return fig
