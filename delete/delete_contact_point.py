from tool.helper import *

result = client.list_contact_points_uid()
print(f" >> Existing contact points uids: {result} \n")

target_contact_point_uid = input(" >> Enter the UID of the contact point to be deleted: ")

client.delete_contact_point(target_contact_point_uid)