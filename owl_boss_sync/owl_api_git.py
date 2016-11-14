#!/usr/bin/env python3
# coding:utf-8

import urllib.request
import json
import datetime
import hashlib
import yaml
import os
import logging

config_file = 'owl_conf.yaml'
gConf = {
    'owl_user': '',
    'owl_password': '',
    'owl_url': '',
    'boss_url': '',
    'testing_owl_url': '',
    'testing_boss_url': ''
}


class OwlAPIException(Exception):

    """
    OwlAPI exception class
    """
    pass


class OwlAPIObjectClass(object):

    """动态创建owl方法"""

    def __init__(self, name, parent):
        self.name = name
        self.parent = parent

    def __getattr__(self, attr):
        def owl_method(params=None, **kwargs):
            if params and kwargs:
                raise TypeError("Found both args and kwargs")

            return self.parent.do_request('{0}.{1}'.format(self.name, attr),
                                          params or kwargs)['result']

        return owl_method


class OwlAPI(object):

    """owl接口包装类，方便调用"""

    def __init__(self, _user, _passwd, _url):
        self.user = _user
        self.passwd = _passwd
        self.url = _url

    def __getattr__(self, attr):
        return OwlAPIObjectClass(attr, self)

    def do_request(self, method, params=None):
        request_json = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params or {},
            # "auth": "038e1d7b1735c6a5436ee9eae095879e",
            'id': '1',
        }

        logging.debug('Request json: ' + json.dumps(request_json))
        logging.info('Request json: ' + str(json.dumps(request_json))[:500])

        req = urllib.request.Request(self.url, json.dumps(request_json).encode())
        req.add_header('Content-Type', 'application/json-rpc')
        res = urllib.request.urlopen(req).read().decode()
        response_json = json.loads(res)

        logging.debug('Response json: ' + json.dumps(response_json))
        logging.info('Response json: ' + str(json.dumps(response_json, indent=4))[:500])

        if 'error' in response_json:
            msg = "Error : {json}".format(
                json=str(request_json))
            raise OwlAPIException(msg, '\n', response_json['error'])

        return response_json


def get_conf_info(conf_file_name):
    """获取配置信息"""
    conf_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), conf_file_name)
    with open(conf_file) as f:
        owl_conf = yaml.load(f)

    platforms = {}
    for temp in owl_conf:
        for plat in owl_conf[temp]:
            if plat in platforms:
                platforms[plat]['templates'].append(temp)

            else:
                platforms[plat] = {}
                platforms[plat]['templates'] = []

                platforms[plat]['templates'].append(temp)

    # 模板去重
    for plat in platforms:
        platforms[plat]['templates'] = set(platforms[plat]['templates'])
    return platforms

class OwlOperator(object):
    def __init__(self, _owl_user, _owl_password, _owl_url):
        self.api = OwlAPI(_owl_user, _owl_password, _owl_url)
        self.hosts = self.get_host()
        self.groups = self.get_host_group()
        self.templates = self.get_templates()

        self.name_to_gid = {i['groupname']: i['groupid'] for i in self.groups}
        self.gid_to_name = {i['groupid']: i['groupname'] for i in self.groups}

    # Method for query.
    def get_host(self):
        return self.api.host.get(output='extend', filter={"host": ["_all_"]})

    def get_host_group(self):
        return self.api.hostgroup.get(filter={"name": ["_all_"]})

    def get_templates(self):
        return self.api.template.get(filter={"name": ["_all_"]})

    def get_group_tids(self, groupname):
        templateids = [
            group['templateids'] for group in self.groups
            if group['groupname'] == groupname
        ][0]

        return templateids

    def name_to_tids(self, template_list):
        tids = []
        for t_name in template_list:
            tids += [
                template['templateid'] for template in self.templates
                if template['name'] == t_name
            ]

        return tids

    def plat_to_gid(self, p_list):
        gid_list = [
            group['groupid'] for group in self.groups
            if group['groupname'] in p_list
        ]
        return gid_list

    # Method for operation.
    def create_group(self, group_list):
        for group in group_list:
            self.api.hostgroup.create(name=group)

    def update_group(self, group_dict):
        for group in group_dict:
            group_id = self.plat_to_gid([group])[0]
            tids = [
                {'templateid': tid} for tid in group_dict[group]['templateids']
            ]
            self.api.hostgroup.update(groupid=group_id, templates=tids)

    def create_host(self, host_dict):
        for h in host_dict:
            interfaces = [{'ip': host_dict[h]['ip'][0], 'port': '10050'}]
            gid = [
                {'groupid': group['groupid']} for group in self.groups
                if group['groupname'] in host_dict[h]['platform']
            ]

            self.api.host.create(host=h, interfaces=interfaces, groups=gid)

    def update_host(self, host_dict):
        for h in host_dict:
            gids = [
                {'groupid': group['groupid']} for group in self.groups
                if group['groupname'] in host_dict[h]['platform']
            ]
            self.api.host.update(host=h, groups=gids)

def get_hostgroups_api(conf):
    if production:
        f = urllib.request.urlopen(conf['boss_url'])
    else:
        f = urllib.request.urlopen(conf['testing_boss_url'])

    data = json.loads(f.read().decode())
    hosts = data["result"]
    namePart = [
        item["name"] for item in hosts
    ]
    valuePart = [
        {
            'active': item["activate"],
            'ip': [item["ip"]],
            'ip_count': 1,
            'platform': item["platforms"].split(',') + ["Owl_Default_Group"]
        } for item in hosts
    ]
    res = dict(zip(namePart,valuePart))
    return res

def dump(input):
    for item in input:
        print(item, input[item])

class Judge(object):

    """用于比对源期望数据和owl中的数据是否一致"""

    def __init__(self, source, owl, conf):
        # b=boss, c=config, o=owl
        self.owl = owl
        #self.b_host = source.host
        # 原本取自 BOSS API 產生的 host list, 可以用 dump(source.host)來看出結果。
        #dump(source.host)
        self.b_host= get_hostgroups_api(conf)
        # 透過 query API 產生的 host list，可以用 dump(get_owl_query_api())來看出結果。
        #dump(get_owl_query_api())
        platforms = get_conf_info(config_file)
        self.c_group = self.add_ids(platforms)
        #self.c_group = self.add_ids(source.platforms)
        self.o_host = owl.hosts
        self.o_group = owl.groups

    def do_sync(self):
        self.group_sync()
        self.host_sync()

    def add_ids(self, conf_info):
        added_dict = {}
        for group in conf_info:
            templateids = self.owl.name_to_tids(conf_info[group]['templates'])
            added_dict[group] = conf_info[group]
            added_dict[group]['templateids'] = templateids

        return added_dict

    def host_clean(self):
        clean_hosts = {}
        for host in self.o_host:
            hostname = host['hostname']
            controlled = False

            for groupid in host['groups']:
                group_name = self.owl.gid_to_name[groupid['groupid']]
                if group_name in self.c_group:
                    controlled = True

            if controlled and hostname not in self.b_host:
                clean_hosts[hostname] = {'platform': []}

        return clean_hosts

    def group_sync(self):
        (less_groups, diff_groups) = self.group_comparison()

        # print 'less_groups', len(less_groups)
        # print 'owl groups count', len(self.o_group), self.o_group[:10]

        if less_groups:
            self.owl.create_group(less_groups)

        if diff_groups:
            self.owl.update_group(diff_groups)

    def host_sync(self):
        clean_hosts = self.host_clean()
        (less_hosts, diff_hosts) = self.host_comparison()

        if clean_hosts:
            self.owl.update_host(clean_hosts)

        if diff_hosts:
            self.owl.update_host(diff_hosts)

        if less_hosts:
            # tmp = {}
            # count = 0
            # for i in less_hosts:
            #     # if len(less_hosts[i]['platform']) > 1:
            #         tmp[i] = less_hosts[i]
            #         count += 1
            #         if count >= 1:
            #             break
            self.owl.create_host(less_hosts)

    def group_comparison(self):
        o_groups = [i['groupname'] for i in self.o_group]
        less_groups = []
        diff_groups = {}
        for group in self.c_group:
            if group in o_groups:
                changed = self.group_has_changed(group)
                if changed:
                    diff_groups[group] = self.c_group[group]

                else:
                    # 无变化主机组无需操作
                    pass
            else:
                less_groups.append(group)

        return less_groups, diff_groups

    def host_comparison(self):
        less_hosts = {}
        diff_hosts = {}
        owl_hostnames = [i['hostname'] for i in self.o_host]
        for host in self.b_host:
            if host in owl_hostnames:

                if self.has_changed(host):
                    diff_hosts[host] = self.b_host[host]
                else:
                    # 无变化的设备无需任何操作
                    pass

            else:
                less_hosts[host] = self.b_host[host]

        # print 'Boss total/ not in owl count:', len(self.b_host), len(less_hosts), len(self.o_host)

        return less_hosts, diff_hosts

    def group_has_changed(self, groupname):
        owl_templateids = self.owl.get_group_tids(groupname)
        conf_templateids = self.c_group[groupname]['templateids']

        if set(owl_templateids) != set(conf_templateids):
            changed = True
        else:
            changed = False

        return changed

    def has_changed(self, hostname):
        owl_host = [i for i in self.o_host if i['hostname'] == hostname][0]

        boss_gids = self.owl.plat_to_gid(self.b_host[hostname]['platform'])
        owl_gids = [oh['groupid'] for oh in owl_host['groups']]

        if set(boss_gids) != set(owl_gids):
            return True
        else:
            return False


class Logger(object):

    def __init__(self):
        pass

    @staticmethod
    def make_config():
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            # filename='myapp.log'
                            # filemode='w')
                            )

debug_hosts = False
debug_platforms = False
production = True

def main():
    Logger.make_config()

    with open("secret.yaml", 'r') as stream:
        try:
            gConf = yaml.load(stream)
            #print(gConf)
        except yaml.YAMLError as exc:
            print(exc)
            exit(1)

    if debug_hosts:
        hosts = get_hostgroups_api(gConf)
        print(json.dumps(hosts))
        exit(0)

    if debug_platforms:
        platforms = get_conf_info(config_file)
        print(platforms)
        exit(0)

    if production:
        owl = OwlOperator(gConf['owl_user'], gConf['owl_password'], gConf['owl_url'])
    else:
        owl = OwlOperator(gConf['owl_user'], gConf['owl_password'], gConf['testing_owl_url'])

    judge = Judge(None, owl, gConf)
    judge.do_sync()


if __name__ == '__main__':
    main()
