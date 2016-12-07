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
    "speed" : 'http://10.20.30.40:9966/api/hosts',
}

real = {
    "login" : "http://owl.fastweb.com.cn/api/v1/auth/login",
    "hostgroup" : 'http://owl.fastweb.com.cn/api/v1/hostgroup/hosts',
    "speed" : 'http://query.owl.fastweb.com.cn/api/hosts',
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

def speed(endpoints):
    endpoint_list = ",".join(endpoints)
    url = URL["speed"]+ "/" + endpoint_list + "/nic-out-speed"
    r = requests.get(url)
    out = json.loads(r.text)
    return out


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
        print "query.py returns the 5 minute average of five platform metrics."
        print "usage: ./nic_out_speed.py [platformName]"
        print "example: ./nic_out_speed.py c01.i01"
        sys.exit(1) 
    platform = sys.argv[1]     # input
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
    raw = speed(endpoints) # 5mins ago  - now
    raw["platform"] = platform
    print json.dumps(raw)
