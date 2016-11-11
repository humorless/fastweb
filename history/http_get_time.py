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
    "http.get.time",
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

def collect(values):
    res = [
            {
                "timestamp": item["timestamp"],
                "http.get.time": item["value"]
            } for item in values
        ]
    return res

def formatting(raw, platform, endpoints, ts):
    middle = [
            {
                "metric": item["counter"],
                "value": collect(item["Values"]),
                "hostname": item["endpoint"]
            } for item in raw 
        ]

    #return json.dumps(middle)
    result = []
    for e in endpoints:
        out = {"hostname": e}
        for item in middle:
            if e == item["hostname"]:
                out["data"] = item["value"]
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
    if len(sys.argv) != 2:
        print "http_get_time.py returns the 5 minute data of the platform metric http.get.time."
        print "usage: ./http_get_time.py  [platformName]"
        print "example: ./http_get_time.py  c01.i07"
        sys.exit(1) 
    ts = int(time.time()) # input
    platform = sys.argv[1]     # input
    user = ""      # data
    password = ""    # data
    conf = readConf()
    if len(conf) == 2:
        user = conf["user"]
        password = conf["pass"]
    sig = login(user, password)
    endpoints = hostgroup2hostnames(user, sig, platform)
    raw = aggregate(user, sig, (ts - 300) , ts, endpoints) # 5mins ago  - now 
    #print json.dumps(raw)
    print formatting(raw, platform, endpoints, ts)
