import csv
from difflib import get_close_matches

from tool.helper import *

"""
This file defines the validator and auto_match classes for the input for the config files used to generate Grafana dashboards/panels and alert-rules.
"""

# ============================================================
# === Validator ==============================================
# ============================================================
"""
The Validator class is used to validate the input config files for the Grafana dashboards/panels and alert-rules.
    - Dashboards:
        - Check if dashboards exist
        - Check if table and columns exist           
        - Check if each dashboard has at least one panel
        - Check if panel keys have correct types
        - Check if duplicate dashboard titles exist
        - Check if duplicate panel titles exist

    - Alert_rules:
        - Check if alert rule keys have correct types
        - Check if alert rule's table exists
        - Check if alert rule's dashboard exists
        - Check if alert rule's panelID is correct
        - Check if alert rule's logicType is valid
        - Check if alert rule's panel chart_type is valid
"""

# ============================================================
# ============================================================

class DashboardValidator:
    def __init__(self, config_path: str):
        self._cfg = ConfigLoader(config_path)

    # ============================================================
    def iter_dashboards(self) -> dict:
        """Iterate over all dashboards in the config file.
        """
        return self._cfg.get("dashboards", [])

    def iter_panels(self):
        """Iterate over all panels in the config file.
           - Yield (dash_title, panel_title, panel_dict)
        """
        for dash in self.iter_dashboards():
            dash_title = dash.get("title", "<Untitled>")
            for panel in dash.get("panels", []):
                panel_title = panel.get("title", "<Unnamed Panel>")
                yield dash_title, panel_title, panel
    
    def get_valid_columns(self, table_name: str) -> list:
        """Return the list of valid column names from a given table CSV.
        """
        table_path = os.path.join(DB_INFO_PATH, f"{table_name}.csv")

        try:
            with open(table_path, newline='') as f:
                reader = csv.reader(f)
                return [row[0].strip() for row in reader if row and row[0].strip()]
        except FileNotFoundError:
            print(f"[Error] Table not found: {table_path}")
            return []

    def should_skip_panel(self, panel: dict) -> bool:
        """Check the panel chart_type to determine if it should be skipped.
        """
        chart_type = str(panel.get("chart_type", "")).strip().lower()

        return chart_type in ("text", "piechart")

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
    
    def print_error(self, dash_title: str, panel_title: str, message: str):
        """Print out the error message.
        """
        print(f"[Error] Dashboard '{dash_title}', Panel '{panel_title}' — {message}")


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
            'distinct': (list, type(None))
        }

        passed = True   # assume all checks pass
        
        for dash_title, panel_title, panel in self.iter_panels():
            if self.should_skip_panel(panel):
                continue

            if not self.validate_types(panel, valid_types, dash_title, panel_title):
                passed = False

        return passed
    
    def _check_table_and_columns_exist(self) -> bool:
        """Check if table exists and all groupby/filter fields are valid.
           - Skip 'text' and 'piechart' chart_type panels.
        """
        passed = True   # assume check pass
        SPECIAL_CASES = ["shipping_status", "count", "row_count"]

        for dash_title, panel_title, panel in self.iter_panels():
            if self.should_skip_panel(panel):
                continue

            # Check table
            table = panel.get("table")
            valid_columns = self.get_valid_columns(table)
            if not valid_columns:
                self.print_error(dash_title, panel_title, f"Table '{table}' not found.")
                passed = False
                continue

            # Check groupby
            groupby = panel.get("groupby")
            if isinstance(groupby, list):
                for col in groupby:
                    cols = col if isinstance(col, list) else [col]
                    for sub_col in cols:
                        if sub_col not in valid_columns and sub_col not in SPECIAL_CASES:
                            self.print_error(dash_title, panel_title, f"GroupBy column '{sub_col}' not in '{table}'")
                            passed = False

            elif isinstance(groupby, dict):
                for sub_table, cols in groupby.items():
                    cols = cols if isinstance(cols, list) else [cols]
                    valid_sub_cols = self.get_valid_columns(sub_table)
                    if not valid_sub_cols:
                        self.print_error(dash_title, panel_title, f"GroupBy sub-table '{sub_table}' not found.")
                        passed = False
                        continue
                    for sub_col in cols:
                        if isinstance(sub_col, list):
                            for sub_sub_col in sub_col:
                                if sub_sub_col not in valid_sub_cols and sub_sub_col not in SPECIAL_CASES:
                                    self.print_error(dash_title, panel_title, f"GroupBy column '{sub_sub_col}' not in '{sub_table}'")
                                    passed = False
                        else:
                            if sub_col not in valid_sub_cols and sub_col not in SPECIAL_CASES:
                                self.print_error(dash_title, panel_title, f"GroupBy column '{sub_col}' not in '{sub_table}'")
                                passed = False

            # Check filters
            filters = panel.get("filters", {})
            if isinstance(filters, dict):
                for filter_table, filter_cols in filters.items():
                    filter_columns = self.get_valid_columns(filter_table)
                    if not filter_columns:
                        self.print_error(dash_title, panel_title, f"Filter table '{filter_table}' not found.")
                        passed = False
                        continue
                    if not isinstance(filter_cols, list):
                        self.print_error(dash_title, panel_title, f"Filters for '{filter_table}' must be a list.")
                        passed = False
                        continue
                    for col in filter_cols:
                        if col not in filter_columns and col not in SPECIAL_CASES:
                            self.print_error(dash_title, panel_title, f"Filter column '{col}' not in '{filter_table}'")
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


    # ============================================================
    def run_all_checks(self) -> bool:
        """Run all validator checks and print a summary.
        """
        checks = {
            "Check if dashboards exist": self._check_dashboards_exist,
            "Check if table and columns exist": self._check_table_and_columns_exist,            
            "Check if each dashboard has at least one panel": self._check_each_dashboard_has_panels,
            "Check if panel keys have correct types": self._check_panel_keys,
            "Check if duplicate dashboard titles exist": self._check_duplicate_dashboard_titles,
            "Check if duplicate panel titles exist": self._check_duplicate_panel_titles
        }

        # loop all checks
        for name, fn in checks.items():
            print(f"— {name}...", end=" ")
            passed = fn()
            print(">> Passed" if passed else ">> Failed")
            
            if not passed:
                return False    # exit checking

        return True


# ============================================================
# ============================================================

class AlertRuleValidator:
    def __init__(self, config_path: str):
        self._cfg = ConfigLoader(config_path)
    
    # ============================================================
    def iter_dashboards(self) -> dict:
        """Iterate over all dashboards in the config file.
        """
        return self._cfg.get("dashboards", [])

    def iter_panels(self):
        """Iterate over all panels in the config file.
           - Yield (dash_title, panel_title, panel_dict)
        """
        for dash in self.iter_dashboards():
            dash_title = dash.get("title", "<Untitled>")
            for panel in dash.get("panels", []):
                panel_title = panel.get("title", "<Unnamed Panel>")
                yield dash_title, panel_title, panel
    
    def iter_alerts(self) -> dict:
        """Iterate over all alerts in the config file.  
        """
        return self._cfg.get("alert", [])
    
    def get_valid_columns(self, table_name: str) -> list:
        """Return the list of valid column names from a given table CSV.
        """
        table_path = os.path.join(DB_INFO_PATH, f"{table_name}.csv")

        try:
            with open(table_path, newline='') as f:
                reader = csv.reader(f)
                return [row[0].strip() for row in reader if row and row[0].strip()]
        except FileNotFoundError:
            print(f"[Error] Table not found: {table_path}")
            return []
        
    def convert_panelID_to_title(self, panelID: int, dash_title: str) -> str:
        """Convert the panelID to panel title.
        """
        for dash in self.iter_dashboards():
            if dash.get("title", "") == dash_title:
                panels = dash.get("panels", [])
                return panels[panelID-1].get("title", "")

        return ""
    
    def print_error(self, alert_title: str, dash_title: str, panel_title: str, message: str):
        """Print out the error message.
        """
        print(f"[Error] Alert Rule '{alert_title}' for Dashboard '{dash_title}', Panel '{panel_title}' — {message}")
        

    # ============================================================
    def _check_alert_keys(self, alert: dict) -> bool:
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
        alert_title = alert.get("title", "<Untitled>")
    
        for key, expected_type in valid_types.items():
            if key not in alert:
                print(f"[Missing Key] Alert '{alert_title}' — Missing required key '{key}'")
                passed = False
            elif not isinstance(alert[key], expected_type):
                print(f"[Type Error] Alert '{alert_title}' — "
                    f"Key '{key}' should be {expected_type}, but got {type(alert[key])}")
                passed = False

        return passed
    
    def _check_table_exist(self, alert: dict) -> bool:
        """Check if the table exists.
        """
        passed = True   # assume all checks passed

        table = alert.get("table", "<Unknown>")
        valid_columns = self.get_valid_columns(table)

        # get name
        alert_title = alert.get("title", "<Untitled>")
        dash_title = alert.get("dashboard", "<Untitled>")
        panel_title = self.convert_panelID_to_title(int(alert.get("panelID", None)), dash_title)

        if not valid_columns:
            self.print_error(alert_title, dash_title, panel_title, f"Table '{table}' not found.")
            passed = False
        
        return passed
    
    def _check_dashboard_exist(self, alert: dict) -> bool:
        """Check if the dashboard exists.
        """
        passed = True   # assume all checks passed
        alert_title = alert.get("title", "<Untitled>")

        dash_title = alert.get("dashboard", "")
        dash_list = []

        for dash in self.iter_dashboards():
            dash_list.append(dash.get("title", "<Untitled>"))
        
        if dash_title not in dash_list:
            self.print_error(alert_title, dash_title, "<Unknown>", f"Dashboard '{dash_title}' not found.")
            passed = False
        
        return passed
    
    def _check_panelID(self, alert: dict) -> bool:
        """Check if the panelID is valid.
        """
        passed = True   # assert all checks passed

        alert_title = alert.get("title", "<Untitled>")
        dash_title = alert.get("dashboard", "<Untitled>")
        panelID_raw = alert.get("panelID")

        # Check if the panelID is an integer in str type
        try:
            panelID = int(panelID_raw)
        except (ValueError, TypeError):
            self.print_error(alert_title, dash_title, "<Unknown>", f"Invalid panelID '{panelID_raw}' — must be an integer.")
            passed = False
            return passed

        # Check dashboard existence
        target_dashboard = None
        for dash in self.iter_dashboards():
            if dash.get("title", "<Untitled>") == dash_title:
                target_dashboard = dash
                break

        if target_dashboard is None:
            self.print_error(alert_title, dash_title, "<Unknown>", f"Dashboard '{dash_title}' not found.")
            passed = False

        # Check panelID within range
        panels = target_dashboard.get("panels", [])
        if not (1 <= panelID <= len(panels)):
            self.print_error(alert_title, dash_title, "<Unknown>", f"panelID '{panelID}' is out of range. This dashboard has {len(panels)} panel(s).")
            passed = False

        return passed

    def _check_alert_logicType(self, alert: dict) -> bool:
        """Check if the logicType is valid.
        """
        valid_logicTypes = ["gt", "lt", "eq", "nq", "within_range", "outside_range"]

        passed = True   # assume all checks passed

        alert_title = alert.get("title", "<Untitled>")
        dash_title = alert.get("dashboard", "<Untitled>")
        panel_title = self.convert_panelID_to_title(int(alert.get("panelID", None)), dash_title)
        logicType = alert.get("logicType", "")

        if logicType not in valid_logicTypes:
            self.print_error(alert_title, dash_title, panel_title, f"Invalid logicType '{logicType}' — must be one of {valid_logicTypes}.")
            passed = False

        return passed
    
    def _check_alert_panelType(self, alert: dict) -> bool:
        """Check if the panel type is valid.
        """
        passed = True   # assume all checks passed

        alert_title = alert.get("title", "<Untitled>")
        dash_title = alert.get("dashboard", "<Untitled>")
        target_panel_title = self.convert_panelID_to_title(int(alert.get("panelID", None)), dash_title)

        for dash_title, panel_title, panel in self.iter_panels():
            if dash_title == dash_title and panel_title == target_panel_title:
                chart_type = panel.get("chart_type", "")
                if chart_type != "timeseries":
                    self.print_error(alert_title, dash_title, panel_title, f"Invalid panel type '{chart_type}' — must be 'timeseries'.")
                    passed = False
                    break

        return passed


    # ============================================================
    def check_single_alert(self, idx: int, alert: dict) -> bool:
        """Check every single alert rule.
        """
        alert_title = alert.get("title", "<Untitled>")
        print(f" >> Validating Alert Rule {idx+1}: '{alert_title}'...", end=" \n")

        checks = {
            "Check if alert rule keys have correct types": lambda: self._check_alert_keys(alert),
            "Check if alert rule's table exists": lambda: self._check_table_exist(alert),
            "Check if alert rule's dashboard exists": lambda: self._check_dashboard_exist(alert),
            "Check if alert rule's panelID is correct": lambda: self._check_panelID(alert),
            "Check if alert rule's logicType is valid": lambda: self._check_alert_logicType(alert),
            "Check if alert rule's panel chart_type is valid": lambda: self._check_alert_panelType(alert)
        }

        # loop all checks
        for name, fn in checks.items():
            print(f"— {name}...", end=" ")
            passed = fn()
            print(">> Passed" if passed else ">> Failed")
            
            if not passed:
                return False    # exit checking

        return True