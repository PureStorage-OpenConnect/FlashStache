// Dynamic Generation of FlashArray Dashboards from Templates

'use strict';

// Accessible variables in this scope.
var window, document, ARGS, $, jQuery, moment, kbn;
var ARGS;
var dashboard = {
  "__inputs": [
    {
      "name": ARGS.hostname,
      "type": "constant",
      "label": "array_name",
      "value": ARGS.hostname,
      "description": ""
    }
  ],
  "__requires": [
    {
      "type": "grafana",
      "id": "grafana",
      "name": "Grafana",
      "version": "4.4.3"
    },
    {
      "type": "panel",
      "id": "graph",
      "name": "Graph",
      "version": ""
    },
    {
      "type": "datasource",
      "id": "mysql",
      "name": "MySQL",
      "version": "1.0.0"
    },
    {
      "type": "panel",
      "id": "table",
      "name": "Table",
      "version": ""
    }
  ],
  "annotations": {
    "list": [
      {
        "datasource": "default",
        "enable": true,
        "hide": false,
        "iconColor": "rgba(255, 96, 96, 1)",
        "limit": 100,
        "name": "FlashArray Alerts",
        "rawQuery": "SELECT\n    UNIX_TIMESTAMP(opened) as time_sec,\n    event as title,\n    component_name as text,\n    current_severity as tags\n  FROM flasharray_arrayalert\n  WHERE $__timeFilter(opened)\n  AND hostname LIKE $array_name\n  ORDER BY opened ASC\n  LIMIT 25\n  ",
        "showIn": 0,
        "type": "alert"
      }
    ]
  },
  "description": "Default Landing Page",
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "hideControls": true,
  "id": null,
  "links": [],
  "refresh": false,
  "title": ARGS.hostname + " Dashboard",
  "style": "light",
  "templating": {
    "list": [
      {
        "current": {
          "value": ARGS.hostname,
          "text": ARGS.hostname
        },
    "hide": 0,
    "label": "array_name",
    "name": "array_name",
    "options": [
      {
        "value": ARGS.hostname,
        "text": ARGS.hostname
      }
    ],
    "query": ARGS.hostname,
    "type": "constant"
      }
    ]
  },
  "rows": [],
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "timezone": "browser",
};
// To add more templates, add the string name here.
console.log('Loaded base dashboard object.')
var row_options = [
    'alerts',
    'flasharray_ioprofile',
    'flasharray_performance',
    'flasharray_space',
    'host_read_bandwidth',
    'host_write_bandwidth',
    'volume_read_bandwidth',
    'volume_write_bandwidth'
];
console.log('Loaded the base dashboard and variables.')
console.log(ARGS)

// Also add new templates here.
var alerts = {
      "collapse": true,
      "height": "100px",
      "panels": [
        {
          "description": "Custom Alerts",
          "id": 1,
          "limit": 10,
          "links": [],
          "onlyAlertsOnDashboard": true,
          "show": "current",
          "sortOrder": 1,
          "span": 12,
          "stateFilter": [
            "alerting",
            "execution_error",
            "no_data"
          ],
          "title": "Active Alerts",
          "transparent": true,
          "type": "alertlist"
        }
      ],
      "repeat": null,
      "repeatIteration": null,
      "repeatRowId": null,
      "showTitle": true,
      "title": "Alerts",
      "titleSize": "h6"
};
var flasharray_ioprofile = {
      "collapse": true,
      "height": 250,
      "panels": [
        {
          "aliasColors": {
            "Read IO Size": "#0A50A1",
            "Read IOPs": "#BADFF4",
            "Write IO Size": "#BF1B00",
            "Write IOPs": "#E0F9D7"
          },
          "bars": false,
          "dashLength": 10,
          "dashes": false,
          "datasource": "default",
          "description": "Overview of IO Count and Sizes",
          "fill": 5,
          "id": 4,
          "legend": {
            "alignAsTable": true,
            "avg": false,
            "current": true,
            "hideEmpty": true,
            "hideZero": false,
            "max": false,
            "min": false,
            "rightSide": true,
            "show": true,
            "total": false,
            "values": true
          },
          "lines": true,
          "linewidth": 1,
          "links": [],
          "nullPointMode": "null as zero",
          "percentage": false,
          "pointradius": 5,
          "points": false,
          "renderer": "flot",
          "seriesOverrides": [
            {
              "alias": "Write IO Size",
              "dashes": true,
              "fill": 0,
              "stack": false,
              "yaxis": 2
            },
            {
              "alias": "Read IO Size",
              "dashes": true,
              "fill": 0,
              "stack": false,
              "yaxis": 2
            }
          ],
          "spaceLength": 10,
          "span": 12,
          "stack": true,
          "steppedLine": false,
          "targets": [
            {
              "alias": "",
              "format": "time_series",
              "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  reads_per_sec as value,\n  \"Read IOPs\" as metric\nFROM flasharray_arrayperformance\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC\n",
              "refId": "A"
            },
            {
              "alias": "",
              "format": "time_series",
              "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  writes_per_sec as value,\n  \"Write IOPs\" as metric\nFROM flasharray_arrayperformance\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC\n",
              "refId": "B"
            },
            {
              "alias": "",
              "format": "time_series",
              "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  (input_per_sec / writes_per_sec)/1024. as value,\n  \"Write IO Size\" as metric\nFROM flasharray_arrayperformance\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC\n",
              "refId": "C"
            },
            {
              "alias": "",
              "format": "time_series",
              "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  (output_per_sec / reads_per_sec)/1024. as value,\n  \"Read IO Size\" as metric\nFROM flasharray_arrayperformance\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC",
              "refId": "D"
            }
          ],
          "thresholds": [],
          "timeFrom": null,
          "timeShift": null,
          "title": "FlashArray IO Profile",
          "tooltip": {
            "shared": true,
            "sort": 2,
            "value_type": "individual"
          },
          "transparent": true,
          "type": "graph",
          "xaxis": {
            "buckets": null,
            "mode": "time",
            "name": null,
            "show": true,
            "values": []
          },
          "yaxes": [
            {
              "decimals": 0,
              "format": "iops",
              "label": "Throughput (IOPs)",
              "logBase": 1,
              "max": null,
              "min": "0",
              "show": true
            },
            {
              "decimals": 0,
              "format": "deckbytes",
              "label": "IO Size (kB per op)",
              "logBase": 1,
              "max": "1024",
              "min": "0",
              "show": true
            }
          ]
        }
      ],
      "repeat": null,
      "repeatIteration": null,
      "repeatRowId": null,
      "showTitle": true,
      "title": "FlashArray IO Profile",
      "titleSize": "h6"
};
var flasharray_space = {
    "collapse": true,
    "height": 250,
    "panels": [
      {
        "aliasColors": {
          "Array Capacity": "#E0752D",
          "Deduplicated Space": "#705DA0",
          "Snapshot Space": "#0A437C",
          "System Space": "#9AC48A"
        },
        "bars": false,
        "dashLength": 10,
        "dashes": false,
        "datasource": "default",
        "decimals": 2,
        "description": "Overall view of the Pure FlashArray's Space Utilization.",
        "fill": 1,
        "id": 2,
        "legend": {
          "alignAsTable": true,
          "avg": false,
          "current": true,
          "hideEmpty": true,
          "hideZero": false,
          "max": false,
          "min": false,
          "rightSide": true,
          "show": true,
          "total": false,
          "values": true
        },
        "lines": true,
        "linewidth": 1,
        "links": [],
        "nullPointMode": "null as zero",
        "percentage": false,
        "pointradius": 5,
        "points": false,
        "renderer": "flot",
        "seriesOverrides": [
          {
            "alias": "Reduction Ratio",
            "dashes": true,
            "fill": 0,
            "yaxis": 2
          },
          {
            "alias": "Array Capacity",
            "dashes": true,
            "fill": 0,
            "stack": false
          }
        ],
        "spaceLength": 10,
        "span": 12,
        "stack": true,
        "steppedLine": false,
        "targets": [
          {
            "alias": "",
            "format": "time_series",
            "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  capacity as value,\n  \"Array Capacity\" as metric\nFROM flasharray_arrayspace\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC\n",
            "refId": "A"
          },
          {
            "alias": "",
            "format": "time_series",
            "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  shared_space as value,\n  \"Deduplicated Space\" as metric\nFROM flasharray_arrayspace\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC\n",
            "refId": "B"
          },
          {
            "alias": "",
            "format": "time_series",
            "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  snapshots as value,\n  \"Snapshot Space\" as metric\nFROM flasharray_arrayspace\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC\n",
            "refId": "C"
          },
          {
            "alias": "",
            "format": "time_series",
            "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  system as value,\n  \"System Space\" as metric\nFROM flasharray_arrayspace\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC\n",
            "refId": "D"
          },
          {
            "alias": "",
            "format": "time_series",
            "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  volumes as value,\n  \"Volume Space\" as metric\nFROM flasharray_arrayspace\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC\n",
            "refId": "E"
          },
          {
            "alias": "",
            "format": "time_series",
            "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  data_reduction as value,\n  \"Reduction Ratio\" as metric\nFROM flasharray_arrayspace\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC",
            "refId": "F"
          }
        ],
        "thresholds": [],
        "timeFrom": null,
        "timeShift": null,
        "title": "FlashArray Space",
        "tooltip": {
          "shared": true,
          "sort": 2,
          "value_type": "individual"
        },
        "transparent": true,
        "type": "graph",
        "xaxis": {
          "buckets": null,
          "mode": "time",
          "name": null,
          "show": true,
          "values": []
        },
        "yaxes": [
          {
            "decimals": 0,
            "format": "decbytes",
            "label": "Used Space",
            "logBase": 1,
            "max": null,
            "min": "0",
            "show": true
          },
          {
            "decimals": 2,
            "format": "none",
            "label": "Space Reduction",
            "logBase": 1,
            "max": "25",
            "min": "0",
            "show": true
          }
        ]
      }
    ],
    "repeat": null,
    "repeatIteration": null,
    "repeatRowId": null,
    "showTitle": true,
    "title": "FlashArray Space",
    "titleSize": "h6"
};
var host_read_bandwidth = {
      "collapse": true,
      "height": 250,
      "panels": [
        {
          "aliasColors": {},
          "bars": false,
          "dashLength": 10,
          "dashes": false,
          "datasource": "default",
          "decimals": 0,
          "description": "An overview of the hosts with the most read bandwidth across the array.",
          "fill": 5,
          "id": 5,
          "legend": {
            "alignAsTable": true,
            "avg": false,
            "current": true,
            "hideEmpty": true,
            "hideZero": true,
            "max": false,
            "min": false,
            "rightSide": true,
            "show": true,
            "sort": "current",
            "sortDesc": true,
            "total": false,
            "values": true
          },
          "lines": true,
          "linewidth": 1,
          "links": [],
          "nullPointMode": "null as zero",
          "percentage": false,
          "pointradius": 5,
          "points": false,
          "renderer": "flot",
          "seriesOverrides": [],
          "spaceLength": 10,
          "span": 12,
          "stack": true,
          "steppedLine": false,
          "targets": [
            {
              "alias": "",
              "format": "time_series",
              "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  output_per_sec as value,\n  name as metric\nFROM flasharray_hostperformance\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nAND input_per_sec is not null\nAND input_per_sec > 0\nORDER BY time ASC\n",
              "refId": "A"
            }
          ],
          "thresholds": [],
          "timeFrom": null,
          "timeShift": null,
          "title": "Hosts (Read Bandwidth)",
          "tooltip": {
            "shared": true,
            "sort": 2,
            "value_type": "individual"
          },
          "transparent": true,
          "type": "graph",
          "xaxis": {
            "buckets": null,
            "mode": "time",
            "name": null,
            "show": true,
            "values": []
          },
          "yaxes": [
            {
              "decimals": 0,
              "format": "Bps",
              "label": "Write Throughput",
              "logBase": 1,
              "max": null,
              "min": "0",
              "show": true
            },
            {
              "format": "short",
              "label": null,
              "logBase": 1,
              "max": null,
              "min": null,
              "show": false
            }
          ]
        }
      ],
      "repeat": null,
      "repeatIteration": null,
      "repeatRowId": null,
      "showTitle": true,
      "title": "Hosts Read Bandwidth",
      "titleSize": "h6"
};
var host_write_bandwidth = {
      "collapse": true,
      "height": 250,
      "panels": [
        {
          "aliasColors": {},
          "bars": false,
          "dashLength": 10,
          "dashes": false,
          "datasource": "default",
          "decimals": 0,
          "description": "An overview of the hosts with the most write bandwidth across the array.",
          "fill": 5,
          "id": 6,
          "legend": {
            "alignAsTable": true,
            "avg": false,
            "current": true,
            "hideEmpty": true,
            "hideZero": true,
            "max": false,
            "min": false,
            "rightSide": true,
            "show": true,
            "sort": "current",
            "sortDesc": true,
            "total": false,
            "values": true
          },
          "lines": true,
          "linewidth": 1,
          "links": [],
          "nullPointMode": "null as zero",
          "percentage": false,
          "pointradius": 5,
          "points": false,
          "renderer": "flot",
          "seriesOverrides": [],
          "spaceLength": 10,
          "span": 12,
          "stack": true,
          "steppedLine": false,
          "targets": [
            {
              "alias": "",
              "format": "time_series",
              "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  input_per_sec as value,\n  name as metric\nFROM flasharray_hostperformance\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nAND input_per_sec is not null\nAND input_per_sec > 0\nORDER BY time ASC\n",
              "refId": "A"
            }
          ],
          "thresholds": [],
          "timeFrom": null,
          "timeShift": null,
          "title": "Hosts (Write Bandwidth)",
          "tooltip": {
            "shared": true,
            "sort": 2,
            "value_type": "individual"
          },
          "transparent": true,
          "type": "graph",
          "xaxis": {
            "buckets": null,
            "mode": "time",
            "name": null,
            "show": true,
            "values": []
          },
          "yaxes": [
            {
              "decimals": 0,
              "format": "Bps",
              "label": "Write Throughput",
              "logBase": 1,
              "max": null,
              "min": "0",
              "show": true
            },
            {
              "format": "short",
              "label": null,
              "logBase": 1,
              "max": null,
              "min": null,
              "show": false
            }
          ]
        }
      ],
      "repeat": null,
      "repeatIteration": null,
      "repeatRowId": null,
      "showTitle": true,
      "title": "Hosts Write Bandwidth",
      "titleSize": "h6"
};
var volume_read_bandwidth = {
      "collapse": true,
      "height": 226,
      "panels": [
        {
          "aliasColors": {},
          "bars": false,
          "dashLength": 10,
          "dashes": false,
          "datasource": "default",
          "decimals": 0,
          "description": "An Overview of Volume-Level Read Bandwidth.",
          "fill": 5,
          "id": 7,
          "legend": {
            "alignAsTable": true,
            "avg": false,
            "current": true,
            "hideEmpty": true,
            "hideZero": true,
            "max": false,
            "min": false,
            "rightSide": true,
            "show": true,
            "sort": "current",
            "sortDesc": true,
            "total": false,
            "values": true
          },
          "lines": true,
          "linewidth": 1,
          "links": [],
          "nullPointMode": "null as zero",
          "percentage": false,
          "pointradius": 5,
          "points": false,
          "renderer": "flot",
          "seriesOverrides": [],
          "spaceLength": 10,
          "span": 12,
          "stack": true,
          "steppedLine": false,
          "targets": [
            {
              "alias": "",
              "format": "time_series",
              "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  output_per_sec as value,\n  name as metric\nFROM flasharray_volumeperformance\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nAND output_per_sec is not null\nAND output_per_sec > 0\nORDER BY time ASC\n",
              "refId": "A"
            }
          ],
          "thresholds": [],
          "timeFrom": null,
          "timeShift": null,
          "title": "Volume Read Bandwidth",
          "tooltip": {
            "shared": true,
            "sort": 2,
            "value_type": "individual"
          },
          "transparent": true,
          "type": "graph",
          "xaxis": {
            "buckets": null,
            "mode": "time",
            "name": null,
            "show": true,
            "values": []
          },
          "yaxes": [
            {
              "decimals": 0,
              "format": "Bps",
              "label": "Throughput (Read)",
              "logBase": 1,
              "max": null,
              "min": "0",
              "show": true
            },
            {
              "format": "short",
              "label": null,
              "logBase": 1,
              "max": null,
              "min": null,
              "show": false
            }
          ]
        }
      ],
      "repeat": null,
      "repeatIteration": null,
      "repeatRowId": null,
      "showTitle": true,
      "title": "Volumes Read Bandwidth",
      "titleSize": "h6"
};
var volume_write_bandwidth = {
      "collapse": true,
      "height": 226,
      "panels": [
        {
          "aliasColors": {},
          "bars": false,
          "dashLength": 10,
          "dashes": false,
          "datasource": "default",
          "decimals": 0,
          "description": "An Overview of Volume-Level Write Bandwidth.",
          "fill": 5,
          "id": 7,
          "legend": {
            "alignAsTable": true,
            "avg": false,
            "current": true,
            "hideEmpty": true,
            "hideZero": true,
            "max": false,
            "min": false,
            "rightSide": true,
            "show": true,
            "sort": "current",
            "sortDesc": true,
            "total": false,
            "values": true
          },
          "lines": true,
          "linewidth": 1,
          "links": [],
          "nullPointMode": "null as zero",
          "percentage": false,
          "pointradius": 5,
          "points": false,
          "renderer": "flot",
          "seriesOverrides": [],
          "spaceLength": 10,
          "span": 12,
          "stack": true,
          "steppedLine": false,
          "targets": [
            {
              "alias": "",
              "format": "time_series",
              "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  input_per_sec as value,\n  name as metric\nFROM flasharray_volumeperformance\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nAND input_per_sec is not null\nAND input_per_sec > 0\nORDER BY time ASC\n",
              "refId": "A"
            }
          ],
          "thresholds": [],
          "timeFrom": null,
          "timeShift": null,
          "title": "Volume Write Bandwidth",
          "tooltip": {
            "shared": true,
            "sort": 2,
            "value_type": "individual"
          },
          "transparent": true,
          "type": "graph",
          "xaxis": {
            "buckets": null,
            "mode": "time",
            "name": null,
            "show": true,
            "values": []
          },
          "yaxes": [
            {
              "decimals": 0,
              "format": "Bps",
              "label": "Throughput (Write)",
              "logBase": 1,
              "max": null,
              "min": "0",
              "show": true
            },
            {
              "format": "short",
              "label": null,
              "logBase": 1,
              "max": null,
              "min": null,
              "show": false
            }
          ]
        }
      ],
      "repeat": null,
      "repeatIteration": null,
      "repeatRowId": null,
      "showTitle": true,
      "title": "Volumes Write Bandwidth",
      "titleSize": "h6"
};
var flasharray_performance = {
      "collapse": true,
      "height": 250,
      "panels": [
        {
          "aliasColors": {
            "Read Bandwidth": "#E0F9D7",
            "Read Latency": "#3F6833",
            "SAN Write Latency": "#EF843C",
            "Write Bandwidth": "#BADFF4",
            "Write Latency": "#0A50A1"
          },
          "bars": false,
          "dashLength": 10,
          "dashes": false,
          "datasource": "default",
          "decimals": 0,
          "description": "An Overall view of performance on the Pure FlashArray.",
          "fill": 5,
          "id": 3,
          "legend": {
            "alignAsTable": true,
            "avg": false,
            "current": true,
            "hideEmpty": true,
            "hideZero": true,
            "max": false,
            "min": false,
            "rightSide": true,
            "show": true,
            "total": false,
            "values": true
          },
          "lines": true,
          "linewidth": 1,
          "links": [],
          "nullPointMode": "null as zero",
          "percentage": false,
          "pointradius": 5,
          "points": false,
          "renderer": "flot",
          "seriesOverrides": [
            {
              "alias": "Read Latency",
              "dashes": true,
              "fill": 0,
              "stack": false,
              "yaxis": 2
            },
            {
              "alias": "Write Latency",
              "dashes": true,
              "fill": 0,
              "stack": false,
              "yaxis": 2
            },
            {
              "alias": "SAN Read Latency",
              "dashes": true,
              "fill": 0,
              "stack": false,
              "yaxis": 2
            },
            {
              "alias": "SAN Write Latency",
              "dashes": true,
              "fill": 0,
              "stack": false,
              "yaxis": 2
            }
          ],
          "spaceLength": 10,
          "span": 12,
          "stack": true,
          "steppedLine": false,
          "targets": [
            {
              "alias": "",
              "format": "time_series",
              "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  input_per_sec as value,\n  \"Write Bandwidth\" as metric\nFROM flasharray_arrayperformance\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC\n",
              "refId": "A"
            },
            {
              "alias": "",
              "format": "time_series",
              "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  output_per_sec as value,\n  \"Read Bandwidth\" as metric\nFROM flasharray_arrayperformance\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC\n",
              "refId": "B"
            },
            {
              "alias": "",
              "format": "time_series",
              "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  usec_per_read_op as value,\n  \"Read Latency\" as metric\nFROM flasharray_arrayperformance\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC",
              "refId": "C"
            },
            {
              "alias": "",
              "format": "time_series",
              "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  usec_per_write_op as value,\n  \"Write Latency\" as metric\nFROM flasharray_arrayperformance\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC",
              "refId": "D"
            },
            {
              "alias": "",
              "format": "time_series",
              "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  san_usec_per_read_op as value,\n  \"SAN Read Latency\" as metric\nFROM flasharray_arrayperformance\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC",
              "refId": "E"
            },
            {
              "alias": "",
              "format": "time_series",
              "rawSql": "SELECT\n  FLOOR(UNIX_TIMESTAMP(time)) as time_sec,\n  san_usec_per_write_op as value,\n  \"SAN Write Latency\" as metric\nFROM flasharray_arrayperformance\nWHERE $__timeFilter(time)\nAND hostname LIKE $array_name\nORDER BY time ASC",
              "refId": "F"
            }
          ],
          "thresholds": [],
          "timeFrom": null,
          "timeShift": null,
          "title": "FlashArray Performance",
          "tooltip": {
            "shared": true,
            "sort": 2,
            "value_type": "individual"
          },
          "transparent": true,
          "type": "graph",
          "xaxis": {
            "buckets": null,
            "mode": "time",
            "name": null,
            "show": true,
            "values": []
          },
          "yaxes": [
            {
              "decimals": 0,
              "format": "Bps",
              "label": "Bandwidth",
              "logBase": 1,
              "max": null,
              "min": "0",
              "show": true
            },
            {
              "decimals": 0,
              "format": "µs",
              "label": "Latency",
              "logBase": 1,
              "max": null,
              "min": "0",
              "show": true
            }
          ]
        }
      ],
      "repeat": null,
      "repeatIteration": null,
      "repeatRowId": null,
      "showTitle": true,
      "title": "FlashArray Performance",
      "titleSize": "h6"
};


// Dashboard Template Management
var add_row = function(data) {
    console.log(data)
    console.log('Adding data to rows.')
    dashboard.rows.push(data)
    console.log('Added this data to the row: ' + data)
};
row_options.forEach(function (entry) {
    // Call variable by string name
    // If it is specified in URL ARGS, then add the row.
    if (!_.isUndefined(ARGS[entry])) {
        console.log('Adding ' + entry)
        add_row(eval(entry))
    }
});

// For console debugging purposes.
console.log(JSON.stringify(dashboard, null, 4));

// Return the Dashboard Object back to Grafana.
return dashboard;
