import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tool.helper import *

"""
This script is used to delete an alert rule from Grafana based on user requested UID.
    - Print `exit` to exit without deleting.
"""

# Fetch all existing alert rules' uids
result = client.get_all_alert_rules()
print(f" >> Existing alert rules uids: {result} \n")

# Ask user to input the UID of the alert rule to be deleted
while True:
    target_alert_rule_uid = input(" >> Enter the UID of the alert rule to be deleted or 'all' for deleting all alert rules: ")

    if target_alert_rule_uid in result:
        client.delete_alert_rule(target_alert_rule_uid)
        break
    elif target_alert_rule_uid.lower() == "all":
        client.delete_all_alert_rules()
        break
    elif target_alert_rule_uid.lower() == "exit":
        print("   >> Exiting without deleting.")
        break
    else:
        print(f" >> Alert rule with UID '{target_alert_rule_uid}' does not exist. Please try again.\n")