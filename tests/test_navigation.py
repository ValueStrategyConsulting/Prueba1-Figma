"""Navigation tests — validate all 17 Streamlit pages and components.

Verifies that:
1. Each page file (1-17) exists on disk
2. Component modules (charts, tables, forms, feedback) load correctly
3. The api_client has all expected endpoint methods
4. i18n translations are complete for all 3 languages
"""

import importlib
import json
from pathlib import Path

import pytest


# All 17 page modules
PAGE_FILES = [
    "01_field_capture.py",
    "02_work_requests.py",
    "03_backlog.py",
    "04_scheduling.py",
    "05_planner.py",
    "06_executive_dashboard.py",
    "07_hierarchy.py",
    "08_criticality.py",
    "09_fmea.py",
    "10_strategy.py",
    "11_analytics.py",
    "12_sap_review.py",
    "13_overview.py",
    "14_reliability.py",
    "15_reports_data.py",
    "16_fmeca.py",
    "17_defect_elimination.py",
]


# ════════════════════════════════════════════════════════════════════════
# SECTION 1: PAGE FILES EXIST
# ════════════════════════════════════════════════════════════════════════

class TestPageFilesExist:

    @pytest.mark.parametrize("filename", PAGE_FILES)
    def test_page_file_exists(self, filename):
        page_path = Path("streamlit_app/pages") / filename
        assert page_path.exists(), f"Page file missing: {page_path}"

    def test_pages_init_exists(self):
        assert Path("streamlit_app/pages/__init__.py").exists()

    def test_total_page_count(self):
        pages_dir = Path("streamlit_app/pages")
        page_files = sorted(pages_dir.glob("[0-9]*_*.py"))
        assert len(page_files) == 17, f"Expected 17 pages, found {len(page_files)}"


# ════════════════════════════════════════════════════════════════════════
# SECTION 2: MAIN APP MODULES
# ════════════════════════════════════════════════════════════════════════

class TestMainAppModule:

    def test_app_file_exists(self):
        assert Path("streamlit_app/app.py").exists()

    def test_streamlit_app_init_exists(self):
        assert Path("streamlit_app/__init__.py").exists()

    def test_api_client_exists(self):
        assert Path("streamlit_app/api_client.py").exists()

    def test_style_module_exists(self):
        assert Path("streamlit_app/style.py").exists()


# ════════════════════════════════════════════════════════════════════════
# SECTION 3: COMPONENT MODULES
# ════════════════════════════════════════════════════════════════════════

class TestComponentModules:

    def test_charts_module(self):
        mod = importlib.import_module("streamlit_app.components.charts")
        for name in ["health_gauge", "kpi_bar_chart"]:
            assert hasattr(mod, name), f"charts missing: {name}"

    def test_tables_module(self):
        mod = importlib.import_module("streamlit_app.components.tables")
        for name in ["render_data_table", "status_badge"]:
            assert hasattr(mod, name), f"tables missing: {name}"

    def test_forms_module_constants(self):
        mod = importlib.import_module("streamlit_app.components.forms")
        assert hasattr(mod, "CRITICALITY_CATEGORIES")
        assert hasattr(mod, "MECHANISMS")
        assert hasattr(mod, "TASK_TYPES")
        assert hasattr(mod, "STRATEGY_TYPES")
        assert hasattr(mod, "FAILURE_CONSEQUENCES")
        assert len(mod.CRITICALITY_CATEGORIES) == 11
        assert len(mod.MECHANISMS) == 18

    def test_feedback_module(self):
        mod = importlib.import_module("streamlit_app.components.feedback")
        assert hasattr(mod, "feedback_widget")
        assert callable(mod.feedback_widget)

    def test_components_init_exists(self):
        assert Path("streamlit_app/components/__init__.py").exists()


# ════════════════════════════════════════════════════════════════════════
# SECTION 4: API CLIENT COMPLETENESS
# ════════════════════════════════════════════════════════════════════════

class TestAPIClientCompleteness:

    @pytest.fixture(autouse=True)
    def _load_client(self):
        self.mod = importlib.import_module("streamlit_app.api_client")

    def test_hierarchy_methods(self):
        for m in ["list_plants", "list_nodes", "get_node", "get_subtree",
                   "get_node_stats", "build_from_vendor"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_criticality_methods(self):
        for m in ["assess_criticality", "get_criticality", "approve_criticality"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_fmea_methods(self):
        for m in ["create_failure_mode", "list_failure_modes",
                   "validate_fm_combination", "get_fm_combinations", "rcm_decide"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_tasks_methods(self):
        for m in ["list_tasks", "validate_task_name"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_work_packages_methods(self):
        for m in ["list_work_packages", "approve_work_package"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_sap_methods(self):
        for m in ["list_sap_uploads", "approve_sap_upload", "get_sap_mock"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_analytics_methods(self):
        for m in ["calculate_health_score", "calculate_kpis",
                   "fit_weibull", "predict_failure"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_admin_methods(self):
        for m in ["seed_database", "get_stats", "get_audit_log", "get_agent_status"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_capture_methods(self):
        for m in ["submit_capture", "list_captures", "get_capture"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_work_requests_methods(self):
        for m in ["list_work_requests", "get_work_request",
                   "validate_work_request", "classify_work_request"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_planner_methods(self):
        for m in ["generate_recommendation", "get_recommendation",
                   "apply_planner_action"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_backlog_methods(self):
        for m in ["list_backlog", "add_to_backlog", "optimize_backlog",
                   "get_optimization", "approve_schedule", "get_schedule"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_scheduling_methods(self):
        for m in ["create_program", "list_programs", "get_program",
                   "finalize_program", "get_gantt"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_reliability_methods(self):
        for m in ["analyze_spare_parts", "create_moc", "list_mocs",
                   "advance_moc", "analyze_jackknife", "analyze_pareto", "assess_rbi"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_reporting_methods(self):
        for m in ["generate_weekly_report", "generate_monthly_report",
                   "generate_quarterly_report", "list_reports", "get_report",
                   "generate_notifications", "list_notifications",
                   "validate_import", "export_data", "run_cross_module_analysis"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_dashboard_methods(self):
        for m in ["get_executive_dashboard", "get_kpi_summary", "get_dashboard_alerts"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_rca_methods(self):
        for m in ["create_rca", "list_rcas", "get_rca", "get_rca_summary",
                   "run_5w2h", "advance_rca",
                   "calculate_planning_kpis", "list_planning_kpi_snapshots",
                   "calculate_de_kpis_full", "list_de_kpi_snapshots"]:
            assert hasattr(self.mod, m), f"Missing: {m}"

    def test_feedback_methods(self):
        for m in ["submit_feedback", "list_feedback"]:
            assert hasattr(self.mod, m), f"Missing: {m}"


# ════════════════════════════════════════════════════════════════════════
# SECTION 5: I18N COMPLETENESS
# ════════════════════════════════════════════════════════════════════════

class TestI18NCompleteness:

    def _load_translations(self):
        i18n_dir = Path("streamlit_app/i18n")
        translations = {}
        for lang in ["en", "fr", "ar"]:
            with open(i18n_dir / f"{lang}.json", "r", encoding="utf-8") as f:
                translations[lang] = json.load(f)
        return translations

    def test_all_languages_have_meta(self):
        translations = self._load_translations()
        for lang in ["en", "fr", "ar"]:
            assert "_meta" in translations[lang], f"{lang}.json missing _meta"
            assert translations[lang]["_meta"]["language"] == lang

    def test_arabic_has_rtl_direction(self):
        translations = self._load_translations()
        assert translations["ar"]["_meta"]["direction"] == "rtl"

    def test_all_languages_have_common_section(self):
        translations = self._load_translations()
        for lang in ["en", "fr", "ar"]:
            assert "common" in translations[lang], f"{lang}.json missing 'common'"
            assert "app_title" in translations[lang]["common"]

    def test_key_coverage_major_sections(self):
        translations = self._load_translations()
        major_sections = ["common", "hierarchy", "criticality"]
        for lang in ["en", "fr"]:
            sections = set(translations[lang].keys()) - {"_meta"}
            for section in major_sections:
                assert section in sections, f"{lang} missing section: {section}"
