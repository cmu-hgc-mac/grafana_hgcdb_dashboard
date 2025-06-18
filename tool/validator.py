import csv

from tool.helper import *

"""
This file defines the validator for the input for the config files used to generate Grafana dashboards/panels and alert-rules.
"""

# ============================================================
# === Dashboards Validator ===================================
# ============================================================

class DashboardValidator:
    def __init__(self, config_path: str):
        self._cfg = ConfigLoader(config_path)
    
    def _check_panel_keys(self) -> bool:
        """Check if each key in each panel has the correct value type.
        - Skip 'text' and 'piechart' chart_type panels.
        """
        # Define the valid types for each key in a panel
        valid_types = {
            'title': str,
            'table': str,
            'chart_type': str,
            'condition': (str, type(None)),
            'groupby': (list, dict, type(None)),
            'filters': (dict, type(None)),
            'distinct': bool
        }

        passed = True   # assume all checks pass
        dashboards = self._cfg.get("dashboards", [])

        for dash in dashboards:
            dash_title = dash.get("title", "<Untitled>")
            for panel_idx, panel in enumerate(dash.get("panels", [])):
                panel_title = panel.get("title", f"<Panel {panel_idx + 1}>")
                chart_type = str(panel.get("chart_type", "")).strip().lower()

                # skip certain chart types
                if chart_type in ("text", "piechart"):
                    continue

                for key, expected_type in valid_types.items():
                    if key not in panel:
                        print(f"[Missing Key] Dashboard '{dash_title}', Panel '{panel_title}' — Missing required key '{key}'")
                        passed = False
                    elif not isinstance(panel[key], expected_type):
                        print(f"[Type Error] Dashboard '{dash_title}', Panel '{panel_title}' — "
                            f"Key '{key}' should be {expected_type}, but got {type(panel[key])}")
                        passed = False

        return passed

    
    def _check_dashboards_exist(self) -> bool:
        """Check if dashboards are defined in the config file.
        """
        passed = True   # assume check pass
        dashboards = self._cfg.get("dashboards", [])

        if not dashboards:
            print("[Error] No dashboards defined.")
            passed = False

        return passed
    
    def _check_each_dashboard_has_panels(self) -> bool:
        """Check if each dashboard has at least one panel.
        """
        passed = True   # assume check pass
        dashboards = self._cfg.get("dashboards", [])

        for dash in dashboards:
            title = dash.get("title", "<Untitled>")
            panels = dash.get("panels", [])
            if not panels:
                print(f"[Warning] Dashboard '{title}' has no panels.")
                passed = False

        return passed
    
    def _check_required_fields_not_empty(self) -> bool:
        """Check if required fields in each panel are not empty.
        - Skip 'text' chart_type panels.
        """
        passed = True   # assume check pass
        dashboards = self._cfg.get("dashboards", [])
        required_fields = ['title', 'table', 'chart_type', 'groupby', "distinct"]

        for dash in dashboards:
            dash_title = dash.get("title", "<Untitled>")
            for panel in dash.get("panels", []):
                panel_title = panel.get("title", "<Unnamed Panel>")
                chart_type = str(panel.get("chart_type", "")).strip().lower()

                # skip 'text' and 'piechart' panels (e.g., IV curve plot, Module Shipping Status)
                if chart_type == "text" or chart_type == "piechart":
                    continue

                for field in required_fields:
                    val = panel.get(field)
                    if val is None or (isinstance(val, (str, list, dict)) and not val):
                        print(f"[Empty Value] Dashboard '{dash_title}', Panel '{panel_title}' — Field '{field}' is empty or missing.")
                        passed = False

        return passed

    def _check_duplicate_dashboard_titles(self) -> bool:
        """Check if there are duplicate dashboard titles in the config file.
        """
        passed = True   # assume check pass
        dashboards = self._cfg.get("dashboards", [])
        seen_titles = set()  # reset

        for dash in dashboards:
            title = dash.get("title", "<Untitled>")
            if title in seen_titles:
                print(f"[Error] Duplicate dashboard title '{title}'")
                passed = False
            else:
                seen_titles.add(title)

        return passed

    def _check_duplicate_panel_titles(self) -> bool:
        """Check if there are duplicate panel titles within each dashboard.
        """
        passed = True   # assume check pass
        dashboards = self._cfg.get("dashboards", [])

        for dash in dashboards:
            dash_title = dash.get("title", "<Untitled>")
            seen_titles = set()  # reset

            for panel in dash.get("panels", []):
                panel_title = panel.get("title", "<Unnamed Panel>")
                if panel_title in seen_titles:
                    print(f"[Warning] Duplicate panel title '{panel_title}' in Dashboard '{dash_title}'")
                    passed = False
                else:
                    seen_titles.add(panel_title)

        return passed

    def run_all_checks(self) -> bool:
        """Run all validator checks and print a summary.
        """
        checks = {
            "Check if dashboards exist": self._check_dashboards_exist,
            "Check if each dashboard has at least one panel": self._check_each_dashboard_has_panels,
            "Check if panel keys have correct types": self._check_panel_keys,
            "Check if required fields are not empty": self._check_required_fields_not_empty,
            "Check if duplicate dashboard titles exist": self._check_duplicate_dashboard_titles,
            "Check for duplicate panel titles": self._check_duplicate_panel_titles,
        }

        overall_passed = True

        for description, check_fn in checks.items():
            print(f"— {description}...", end=" ")
            passed = check_fn()
            if passed:
                print(" >> Passed")
            else:
                print(" >> Failed")
                overall_passed = False

        return overall_passed


# ============================================================
# === Alert Rules Validator ==================================
# ============================================================

class AlertRuleValidator:
    def __init__(self, config_path: str):
        self._cfg = ConfigLoader(config_path)

    def _check_alert_keys(self) -> bool:
        """Check if each key in each alert rule has the correct value type.
        """
        # Define the valid types for each key in a panel
        valid_types = {
            "title": str,
            "table": str,
            "panelID": str,
            "parameter": str,
            "threshold": list,
            "logicType": str,
            "duration": str,
            "interval": str,
            "summary": (str, type(None)),
            "labels": (dict, type(None))
        }

        passed = True   # assume all checks pass
        alerts = self._cfg.get("alerts", [])

        for alert_idx, alert in enumerate(alerts):
            alert_title = alert.get("title", f"<Alert {alert_idx + 1}>")

            for key, expected_type in valid_types.items():
                if key not in alert:
                    print(f"[Missing Key] Alert '{alert_title}' — Missing required key '{key}'")
                    passed = False
                elif not isinstance(alert[key], expected_type):
                    print(f"[Type Error] Alert '{alert_title}' — "
                        f"Key '{key}' should be {expected_type}, but got {type(alert[key])}")
                    passed = False

        return passed

    def run_all_checks(self) -> bool:
        """Run all validator checks and print a summary.
        """
        checks = {
            # "Check if dashboards exist": self._check_dashboards_exist,
            # "Check if each dashboard has at least one panel": self._check_each_dashboard_has_panels,
            "Check if alert keys have correct types": self._check_alert_keys
            # "Check if required fields are not empty": self._check_required_fields_not_empty,
            # "Check if duplicate dashboard titles exist": self._check_duplicate_dashboard_titles,
            # "Check for duplicate panel titles": self._check_duplicate_panel_titles,
        }

        overall_passed = True

        for description, check_fn in checks.items():
            print(f"— {description}...", end=" ")
            passed = check_fn()
            if passed:
                print(" >> Passed")
            else:
                print(" >> Failed")
                overall_passed = False

        return overall_passed