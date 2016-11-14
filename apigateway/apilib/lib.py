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
    "history" : 'http://10.20.30.40:9966/graph/history',
    "events" : "http://10.20.30.40:1234/api/v2/portal/eventcases/get",
}

real = {
    "login" : "http://owl.fastweb.com.cn/api/v1/auth/login",
    "hostgroup" : 'http://owl.fastweb.com.cn/api/v1/hostgroup/hosts',
    "history" : 'http://query.owl.fastweb.com.cn/graph/history',
    "events" : "http://owl.fastweb.com.cn/api/v2/portal/eventcases/get",
}

URL = real

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

def history(user, sig, startTs, endTs, endpoints, counters):
    url = URL["history"]
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

def formatAggre(raw, platform, endpoints, ts):
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

def apiAggregate(platform):
    conf = readConf()
    if len(conf) == 2:
        user = conf["user"]
        password = conf["pass"]
    else:
        return "read file error"    
    sig = login(user, password)
    endpoints = hostgroup2hostnames(user, sig, platform)
    ts = int(time.time()) # input
    counters = [
        "cpu.idle",
        "disk.io.util.max",
        "df.statistics.used.percent",
        "mem.memfree.percent",
        "net.if.out.bits/iface=eth_all"
    ]
    raw = history(user, sig, (ts - 300) , ts, endpoints, counters) # 5mins ago  - now 
    return formatAggre(raw, platform, endpoints, ts)

def alarmEvents(user, sig, startTs, endTs, platform, hostnameFilters):
    url = URL["events"]
    if startTs >= endTs:
        print " start timestamp bigger than end timestamp"
        sys.exit(1)
    
    payload = {
        "status": "PROBLEM,OK",
        "process": "ALL",
        "includeEvents": True,
        "limit": 2000,
        "startTime": startTs,
        "endTime":   endTs,
        "cName": user,
        "cSig": sig
    } 

    r = requests.post(url, payload)
    out = json.loads(r.text)

    #print json.dumps(out["data"]["eventCases"])
    result = []
    for i in out["data"]["eventCases"]:
        if i["hostname"] in hostnameFilters:
            item = {
                "hostname": i["hostname"],
                "ip": i["ip"],
                "content": i["content"],
                "metric": i["metric"]
            }
            result.append(item)

    final = {
        "platform": platform,
        "count": len(result),
        "timestamp": [startTs, endTs],
        "result": result
    }
    return json.dumps(final)

def apiAlarmEvents(startTs, endTs, platform):
    conf = readConf()
    if len(conf) == 2:
        user = conf["user"]
        password = conf["pass"]
    else:
        return "read file error"    

    sig = login(user, password)
    endpoints = hostgroup2hostnames(user, sig, platform)
    return alarmEvents(user, sig, startTs, endTs, platform, endpoints) 

def collect(values):
    res = [
            {
                "timestamp": item["timestamp"],
                "http.get.time": item["value"]
            } for item in values
        ]
    return res

def formatHttpGetTime(raw, platform, endpoints, ts):
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

def apiHttpGetTime(platform):
    conf = readConf()
    if len(conf) == 2:
        user = conf["user"]
        password = conf["pass"]
    else:
        return "read file error"    
    sig = login(user, password)
    endpoints = hostgroup2hostnames(user, sig, platform)
    ts = int(time.time()) # input
    counters = [
        "http.get.time",
    ]
    raw = history(user, sig, (ts - 300) , ts, endpoints, counters) # 5mins ago  - now 
    return formatHttpGetTime(raw, platform, endpoints, ts)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "lib.py returns the 5 minute average of five platform metrics."
        print "usage: ./lib.py  [platformName]"
        print "example: ./lib.py  c01.i01"
        sys.exit(1) 
    ts = int(time.time()) # input
    platform = sys.argv[1]     # input
    user = ""      # data
    password = ""    # data
    conf = readConf()
    if len(conf) == 2:
        user = conf["user"]
        password = conf["pass"]
    else:
        print "secret.yaml Error"
        sys.exit(1)
    sig = login(user, password)
    endpoints = hostgroup2hostnames(user, sig, platform)
    counters = [
        "cpu.idle",
        "disk.io.util.max",
        "df.statistics.used.percent",
        "mem.memfree.percent",
        "net.if.out.bits/iface=eth_all"
    ]
    raw = history(user, sig, (ts - 300) , ts, endpoints, counters) # 5mins ago  - now 
    print formatAggre(raw, platform, endpoints, ts)
