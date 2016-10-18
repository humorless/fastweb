#!/bin/bash

# 做 login, 可以取得 sig
queryAddr="10.20.30.40:1234"
#queryAddr="owl.fastweb.com.cn"
user=''     # fit your id  here  
pass=''             # fit your password here
curl -s "$queryAddr/api/v1/auth/login" -X POST -d "name=$user&password=$pass"


# 取得 hostgroup 的 host list
queryAddr="10.20.30.40:1234"
#queryAddr="owl.fastweb.com.cn"
user='laurence'
sig='7267430e8b8911e685840242ac12000b'
grp='["hostgrp"]'
curl -s "$queryAddr/api/v1/hostgroup/hosts" -X POST -d "cName=$user&cSig=$sig&hostgroups=$grp"



# 取得 counter 的值
queryAddr="10.20.30.40:9966"
#QueryAddr="query.owl.fastweb.com.cn"
jsonQuery='[{"counter":"cpu.idle","endpoint":"docker-agent"}]'
curl -s "$queryAddr/graph/last" -X POST -d $jsonQuery


