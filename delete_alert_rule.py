from tool.helper import *

result = client.get_all_alert_rules()
print(f" >> Existing alert rules uids: {result} \n")

target_alert_rule_uid = input(" >> Enter the UID of the alert rule to be deleted: ")

client.delete_alert_rule(target_alert_rule_uid)