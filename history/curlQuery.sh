#!/bin/bash
if [ $# != 2 ];then
    printf "format:./query.sh \"endpoint\" \"counter\"\n"
    exit 1
fi

# args
endpoint=$1
counter=$2
cf="AVERAGE"

# form request body
end_ts=`date +%s`
start_ts=`expr $end_ts - 180`
req="{\"start\":$start_ts, \"end\":$end_ts, \"cf\":\"$cf\", \"endpoint_counters\": [{\"endpoint\":\"$endpoint\", \"counter\":\"$counter\"}]}"

# request 
url="http://query.owl.fastweb.com.cn/graph/history"
curl -s -X POST -d "$req" "$url" | python -m json.tool
