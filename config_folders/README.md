# How to generate a new dashboard
To generate a new dashboard, please go to the Folder: `config_folders`. Create a new `YAML` file by the folder name you would like to have in Grafana. 
The format of the folder name will be: `Aaa_Bbb_Ccc`
```
datasource_variable: DS_POSTGRES

dashboards:

  - title: "YOUR NEW DASHBOARD TITLE"
```
The `title` parameter is the title for your dashboard. 

## How to generate a new panel
To generate a new panel, please add the following template under the dashboard head you just add to the `YAML` file:
```
	panels:
	      - title: ""
	        table: ""
	        chart_type: ""
	        condition: ""
	        groupby: ["", ""]
	        filters: {"": [""]}
	        distinct: False
```

### Parameters:
1. title: your panel's title
2. table: the table you would like to monitoring
3. chart_type: the chart type for the panel, the available chart types are the following:
- `barchart`: groupby can have multiple elements
- `histogram`: groupby should only contain 1 element
- `timeseries`: groupby should only contain 2 elements: `time`, `elem`
- `text`: only for iv_curve_plot
- `stat`: count the number
- `table`: table -> same with database
- `gauge`: show the lastest data
- `piechart`: only for module status
4. condition: extra condition you would want to have, some example conditions:
```
1. "module_info.assembled IS NOT NULL"
2. "i_at_600v < 1e-6 OR i_at_ref_a < 1e-6"
3. (now() - log_timestamp AT TIME ZONE 'America/New_York') < INTERVAL '15 MINUTE'
```
5. groupby: the columns that you would like to monitor. If you would like to have 2 columns as 1 parameter - select A if not null otherwise select B, please input the element as a list.
6. filters: the filters that would appear on the top, the format of the filters will be: {"filter table 1" : ["filter column A", "filter column B"], "filter table 2" : ["filter column C"]}
7. distinct: only avaiable for `module_qc_summary` table
  

# How to add an alert rule 
  
- To generate a new alert that link with a specific panel, please go to the corresponding dashboard yaml file (in the folder config_folders) and scroll down to alerts part. Copy the following code after the existing alert rules and make modifications:

``` yaml
- title: ""
    dashboard: ""
    panelID: ""
    parameter: ""
    threshold: []
    logicType: ""
    duration: ""
    interval: ""
    summary: ""
    labels: 
        "team": "inspectors"
```

- To generate an alert rule that applies to all the tables, please copy and paste the following code after the existing alert rules in config_folders/Other_Alerts_Config/All_Table_Alerts_Config.yaml and make modifications:
```yaml
- title: ""
    table: ""
    sql: ""
    conditions: 
      - ""
      - ""
    threshold: [0]
    logicType: "gt"
    duration: ""
    interval: ""
    summary: ""
    labels: 
        "team": "inspectors"
    dashboard: None
    panelID: None
    parameter: ""
    ignore_columns:
      - "comment"
```




## parameters

- `title`: The title of the alert, normally would be a condensed summary of the situaion. Such as "High Temperature Alert".

- `dashboard`: The dashboard that the alert is connected to. Leave it `""` if there is no linked dashboard.
- `panelID`: The panel that the alert is connected to.  The panelID (n) will be the n-th panel under dashboard. 
- `parameter`:The parameter you want to keep track of.
- `threshold`: A specific value that tells the bourdary between normal and abnormal situation. Please make sure this is a list. If there is both an upper boundary and a lower boundary, please make sure it is in the form of [lower,upper]. **Note**: For all table alerts, please leave it `[0]`.
- `logicTypes`:
  1. "gt": greater than
   2. "lt": less than
   3. "eq": equal to
   4. "ne": not equal to
   5. "within_range": fire when data in the range
   6. "outside_range": fire when data out of range
  **Note**: For all table alerts, please leave it `"gt"`
- `duration`: How long should the situation hold before sending an alert.
- `interval`: The frequency for grafana to check the data.
- `summary`: A more detailed message of the alert.
- `labels`: Labels for the alert, such as the severity of the alert.



# How to add a contact point
There is only one contact point "inspectors" by default. Users can create another group of people with different members by adding a new contact point.

To add a new contact point, go to Contact_Config.yaml (Contact_Config_example.yaml at first) in the contact_configs folder, copy, and paste the following code after the contact point "inspectors".

```
- name: <the name of this contact point>
  type: email
  addresses:
    - <your_email_address>
```


# How to add a notification policy
By default, all email notifications will be sent to the contact point "inspectors". If the user wants to send emails to different people based on labels of the alert rule, the user would need a more detailed notification policy.

Same as the contact point, go to Contact_Config.yaml file. Modify, copy, and paste the following code under "routes".
```
- receiver: <contact point name>
  group_by: 
    - grafana_folder
    - alertname
  object_matchers: 
    - ["", "", ""]
    - ["", "", ""]
  group_wait: 
  group_interval: 
  repeat_interval: 
```
### parameters:
- receiver: the name of the contact point
- group_by: how alerts are grouped together into a single notification. By default, we use "grafana folder" and "alertname".
  - common group_by:
    - alertname: the name of the alert rule
    - instance: the host/IP triggering the alert
    - severity: alert level (e.g., warning, critical)
    - grafana_folder: the folder where the alert is defined
- object_matchers: [key,operator,value]
  - key: the label that we care for this notification policy
  - operator: it can be `"=","!=","=~","!~"`
- group_wait: the time period grafana will wait after receiving the first alert message. Grafana will gather all the alert messages received in this time period and send all of them to the contact point in one notification.
- group_interval: The minimum time to wait before sending a new notification for a different group of alerts
- repeat_interval: How often Grafana repeats a notification for an alert that is still firing.