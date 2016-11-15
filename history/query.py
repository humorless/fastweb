#!/usr/bin/env python
#!-*- coding:utf8 -*-

import requests
import time
import json
import sys
import os.path
import yaml

local = {
    "login" : "http://10.20.30.40:1234/api/v1/auth/login",
    "hostgroup" : 'http://10.20.30.40:1234/api/v1/hostgroup/hosts',
    "aggregate" : 'http://10.20.30.40:9966/graph/history',
}

real = {
    "login" : "http://owl.fastweb.com.cn/api/v1/auth/login",
    "hostgroup" : 'http://owl.fastweb.com.cn/api/v1/hostgroup/hosts',
    "aggregate" : 'http://query.owl.fastweb.com.cn/graph/history',
}

URL = real

counters = [
    "cpu.idle",
    "disk.io.util.max",
    "df.statistics.used.percent",
    "mem.memfree.percent",
    "net.if.out.bits/iface=eth_all"
]

def login(name, password):
    url = URL["login"]
    payload = {
        'name': name,
        'password': password
    }
    r = requests.post(url, payload)
    out = r.json()
    return out["data"]["sig"]

def hostgroup2hostnames(user, sig, hostgroup):
    url = URL["hostgroup"]
    payload = {
        'cName': user,
        'cSig': sig,
        'hostgroups': hostgroup
    }

    r = requests.post(url, payload)
    out = r.json()
    res = []
    for i in out["data"]["hosts"]:
        res.append(i["hostname"])
    return res

def aggregate(user, sig, startTs, endTs, endpoints):
    url = URL["aggregate"]
    endpointCounters = [{"endpoint":x, "counter":y} for x in endpoints for y in counters]
    payload = {
        "start": startTs,
        "end": endTs,
        "cf": "AVERAGE",
        "endpoint_counters": endpointCounters
    }
    r = requests.post(url, data = json.dumps(payload))
    out = json.loads(r.text)
    return out

def average(values):
    count = len(values)
    real = []
    for item in values:
        if item["value"] is None:
            count = count - 1
        else:
            real.append(item["value"])
    if count > 0:
        return sum(real)/count
    else:
        return None

def formatting(raw, platform, endpoints, ts):
    middle = [
            {
                "metric": item["counter"],
                "value": average(item["Values"]),
                "hostname": item["endpoint"]
            } for item in raw 
        ]

    #return json.dumps(middle)
    result = []
    for e in endpoints:
        out = {"hostname": e}
        for item in middle:
            if e == item["hostname"]:
                out[item["metric"]] = item["value"]
                result.append(out)
    
    #return json.dumps(result)

    final = {
        "platform": platform,
        "count": len(endpoints),
        "timestamp": ts,
        "result": result
    } 
    return json.dumps(final)

def readConf():
    if os.path.isfile("secret.yaml"):
        pass
    else:
        return {}

    with open("secret.yaml", 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "query.py returns the 5 minute average of five platform metrics."
        print "usage: ./query.py [timestampStart] [timestampEnd] [platformName]"
        print "example: ./query.py  1478700000 1478764076 c01.i01"
        sys.exit(1) 
    startTs = int(sys.argv[1])      # input
    endTs = int(sys.argv[2])      # input
    platform = sys.argv[3]     # input
    user = ""      # data
    password = ""    # data
    conf = readConf()
    if len(conf) == 2:
        user = conf["user"]
        password = conf["pass"]
    sig = login(user, password)
    endpoints = hostgroup2hostnames(user, sig, platform)
    if len(endpoints) == 0:
        #print json.dumps({"message":"Platform is null. No endpoints inside."})
        print json.dumps(False)
        sys.exit(0)
    raw = aggregate(user, sig, startTs , endTs, endpoints) # 5mins ago  - now
    print formatting(raw, platform, endpoints, startTs)
