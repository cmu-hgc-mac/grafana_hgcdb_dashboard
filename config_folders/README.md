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
  

# Instructions for a new alert rule
Author: Xinyue (Joyce) Zhuang. 
  
To generate a new alert, please go to the corresponding dashboard yaml file (in the folder config_folders) and scroll down to alerts part. Copy the following code after the existing alert rules and make modification:

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
        "severity": "critical"
        "sensor": "humidity"
        "location": "east"
```


## Explanations of each parameter

### title
The title of the alert, normally would be a condensed summary of the situaion. Such as "temperature high".

### dashboard
The dashboard that the alert is connected to.

### panelID
The panel that the alert is connected to.  
The panelID (n) will be the n-th panel under dashboard. 

### parameter
The parameter you want to keep track of.

### threshold
A specific value that tells the bourdary between normal and abnormal situation. Please make sure this is a list. If there is both an upper boundary and a lower boundary, please make sure it is in the form of [lower,upper].

### logicTypes
1. "gt": grater than
2. "lt": less than
3. "eq": equal to
4. "ne": not equal to
5. "within_range": in the range
6. "outside_range": out of range

### duration
How long should the situation hold before sending an alert.

### interval
The frequency for grafana to check the data.

### summary
A more detailed message of the alert.

### labels
Labels for the alert, such as the severity of the alert.