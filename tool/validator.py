import csv

from tool.helper import *

"""
This file defines the validator for the input for the config files used to generate Grafana dashboards/panels and alert-rules.
"""

# ============================================================
# === Dashboards Validator ===================================
# ============================================================

class DashboardValidator:
    SPECIAL_CASES = ["shipping_status", "count"]

    def __init__(self, config_path: str):
        self._cfg = ConfigLoader(config_path)

    # ============================================================
    def iter_dashboards(self) -> dict:
        """Iterate over all dashboards in the config file.
        """
        return self._cfg.get("dashboards", [])

    def iter_panels(self) -> tuple:
        """Iterate over all panels in the config file.
           - Yield (dash_title, panel_title, panel_dict)
        """
        for dash in self.iter_dashboards():
            dash_title = dash.get("title", "<Untitled>")
            for panel in dash.get("panels", []):
                panel_title = panel.get("title", "<Unnamed Panel>")
                yield dash_title, panel_title, panel

    def should_skip_panel(self, panel: dict) -> bool:
        """Check the panel chart_type to determine if it should be skipped.
        """
        chart_type = str(panel.get("chart_type", "")).strip().lower()

        return chart_type in ("text", "piechart")

    def print_error(self, dash_title: str, panel_title: str, message: str):
        """Print out the error message.
        """
        print(f"[Error] Dashboard '{dash_title}', Panel '{panel_title}' — {message}")

    def validate_types(self, data: dict, expected: dict, dash_title: str, panel_title: str) -> bool:
        """Check if the keys in the data dictionary have the expected value type.
        """
        passed = True   # assume all checks pass
        for key, expected_type in expected.items():
            if key not in data:
                self.print_error(dash_title, panel_title, f"Missing key '{key}'")
                passed = False
            elif not isinstance(data[key], expected_type):
                self.print_error(dash_title, panel_title, f"Key '{key}' should be {expected_type}, got {type(data[key])}")
                passed = False
        return passed

    # ============================================================
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
        
        for dash_title, panel_title, panel in self.iter_panels():
            if self.should_skip_panel(panel):
                continue

            if not self.validate_types(panel, valid_types, dash_title, panel_title):
                passed = False

        return passed

    def _check_dashboards_exist(self) -> bool:
        """Check if dashboards are defined in the config file.
        """
        passed = True   # assume check pass
        dashboards = self.iter_dashboards()

        if not dashboards:
            print("[Error] No dashboards defined.")
            passed = False

        return passed

    def _check_each_dashboard_has_panels(self) -> bool:
        """Check if each dashboard has at least one panel.
        """
        passed = True   # assume check pass

        for dash in self.iter_dashboards():
            dash_title = dash.get("title", "<Untitled>")
            if not dash.get("panels"):
                print(f"[Warning] Dashboard '{dash_title}' has no panels.")
                passed = False

        return passed

    def _check_required_fields_not_empty(self) -> bool:
        """Check if required fields in each panel are not empty.
        - Skip 'text' chart_type panels.
        """
        passed = True   # assume check pass

        required_fields = ['title', 'table', 'chart_type', 'groupby', 'distinct']

        for dash_title, panel_title, panel in self.iter_panels():
            if self.should_skip_panel(panel):
                continue
            for field in required_fields:
                val = panel.get(field)
                if val is None or (isinstance(val, (str, list, dict)) and not val):
                    self.print_error(dash_title, panel_title, f"Field '{field}' is empty or missing.")
                    passed = False

        return passed

    def _check_duplicate_dashboard_titles(self) -> bool:
        """Check if there are duplicate dashboard titles in the config file.
        """
        passed = True   # assume check pass
        seen = set()    # initialize

        for dash in self.iter_dashboards():
            title = dash.get("title", "<Untitled>")
            if title in seen:
                print(f"[Error] Duplicate dashboard title '{title}'")
                passed = False
            seen.add(title)

        return passed

    def _check_duplicate_panel_titles(self) -> bool:
        """Check if there are duplicate panel titles within each dashboard.
        """
        passed = True   # assume check pass

        for dash in self.iter_dashboards():
            dash_title = dash.get("title", "<Untitled>")
            seen = set()    # reset
            for panel in dash.get("panels", []):
                title = panel.get("title", "<Unnamed Panel>")
                if title in seen:
                    print(f"[Warning] Duplicate panel title '{title}' in Dashboard '{dash_title}'")
                    passed = False
                seen.add(title)

        return passed

    def _check_table_and_fields_exist(self) -> bool:
        """Check if table exists and all groupby/filter fields are valid.
        """
        passed = True   # assume check pass

        for dash_title, panel_title, panel in self.iter_panels():
            if self.should_skip_panel(panel):
                continue

            # Check table
            table = panel.get("table")
            valid_columns = get_valid_columns(table)
            if not valid_columns:
                self.print_error(dash_title, panel_title, f"Table '{table}' not found.")
                passed = False
                continue

            # Check groupby
            groupby = panel.get("groupby")
            if isinstance(groupby, list):
                for col in groupby:
                    cols = col if isinstance(col, list) else [col]
                    for c in cols:
                        if c not in valid_columns and c not in self.SPECIAL_CASES:
                            self.print_error(dash_title, panel_title, f"GroupBy column '{c}' not in '{table}'")
                            passed = False

            elif isinstance(groupby, dict):
                for sub_table, cols in groupby.items():
                    cols = cols if isinstance(cols, list) else [cols]
                    valid_sub_cols = get_valid_columns(sub_table)
                    if not valid_sub_cols:
                        self.print_error(dash_title, panel_title, f"GroupBy sub-table '{sub_table}' not found.")
                        passed = False
                        continue
                    for c in cols:
                        if c not in valid_sub_cols and c not in self.SPECIAL_CASES:
                            self.print_error(dash_title, panel_title, f"GroupBy column '{c}' not in '{sub_table}'")
                            passed = False

            # Check filters
            filters = panel.get("filters", {})
            if isinstance(filters, dict):
                for filter_table, filter_cols in filters.items():
                    filter_columns = get_valid_columns(filter_table)
                    if not filter_columns:
                        self.print_error(dash_title, panel_title, f"Filter table '{filter_table}' not found.")
                        passed = False
                        continue
                    if not isinstance(filter_cols, list):
                        self.print_error(dash_title, panel_title, f"Filters for '{filter_table}' must be a list.")
                        passed = False
                        continue
                    for col in filter_cols:
                        if col not in filter_columns and col not in self.SPECIAL_CASES:
                            self.print_error(dash_title, panel_title, f"Filter column '{col}' not in '{filter_table}'")
                            passed = False

        return passed


    def run_all_checks(self):
        checks = {
            "Check if dashboards exist": self._check_dashboards_exist,
            "Check if each dashboard has at least one panel": self._check_each_dashboard_has_panels,
            "Check if panel keys have correct types": self._check_panel_keys,
            "Check if required fields are not empty": self._check_required_fields_not_empty,
            "Check if duplicate dashboard titles exist": self._check_duplicate_dashboard_titles,
            "Check if duplicate panel titles exist": self._check_duplicate_panel_titles,
            "Check if table and columns exist": self._check_table_and_fields_exist
        }

        all_passed = True
        for name, fn in checks.items():
            print(f"— {name}...", end=" ")
            passed = fn()
            print(">> Passed" if passed else ">> Failed")
            all_passed &= passed
        return all_passed


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