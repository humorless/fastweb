#!/usr/bin/env python
#!-*- coding:utf8 -*-
import time
from bottle import route, run
from apilib import lib

@route('/hello')
def hello():
    return "hello"

@route('/aggregate/<platform>')
def aggregate(platform):
    return lib.apiAggregate(platform)

@route('/http_get_time/<platform>')
def aggregate(platform):
    return lib.apiHttpGetTime(platform)

@route('/alarm_events/<platform>')
def aggregate(platform):
    ts = int(time.time())
    return lib.apiAlarmEvents(ts - 86400*3, ts, platform)

run(host='10.20.30.40', port=8085, debug=True)
