#!/usr/bin/env python
#!-*- coding:utf8 -*-

import requests
import time
import json
import sys


def login(name, password):
    url = "http://owl.fastweb.com.cn/api/v1/auth/login"
    payload = {
        'name': name,
        'password': password
    }
    r = requests.post(url, payload)
    out = json.loads(r.text)
    return out["data"]["sig"]

def hostgroup2hostnames(user, sig, hostgroup):
    url = 'http://owl.fastweb.com.cn/api/v1/hostgroup/hosts'
    payload = {
        'cName': user,
        'cSig': sig,
        'hostgroups': hostgroup
    }

    r = requests.post(url, payload)
    out = json.loads(r.text)
    res = []
    for i in out["data"]["hosts"]:
        res.append(i["hostname"])
    return res

def history(user, sig, ts, platform, hostnameFilters):
    url = "http://owl.fastweb.com.cn/api/v2/portal/eventcases/get"
    payload = {
        "status": "PROBLEM,OK",
        "process": "ALL",
        "includeEvents": True,
        "limit": 2000,
        "startTime": ts - 86400,
        "endTime":   ts,
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
        "timestamp": ts,
        "result": result
    }
    print json.dumps(final)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "usage: history.py [timestamp] [platformName]"
        print "example: history.py 1478764076 c01.i01"
        sys.exit(1) 
    #ts = int(time.time()) # input
    #platform = "c06.i06"  # input
    ts = int(sys.argv[1])      # input
    platform = sys.argv[2]     # input
    user = ""      # data
    password = ""    # data
    sig = login(user, password) 
    hostnameFilters = hostgroup2hostnames(user, sig, platform)
    history(user, sig, ts, platform, hostnameFilters)
