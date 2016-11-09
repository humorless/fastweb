#!/bin/sh



# 取得 rrd files 的檔名
queryAddr="query.owl.fastweb.com.cn"
endpoint="cnc-sd-027-209-182-025"
curl --include \
     --request POST \
     --header "Content-Type: application/json" \
     --data-binary "[
    {
        \"endpoint\": \"$endpoint\",
        \"counter\": \"load.1min\"
    },
    {
        \"endpoint\": \"$endpoint\",
        \"counter\": \"cpu.idle\"
    }
]" \
"http://$queryAddr/graph/info"

