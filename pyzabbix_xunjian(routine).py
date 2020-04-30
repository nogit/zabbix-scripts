# coding=utf-8

# import logging
# import sys
import time

from pyzabbix import ZabbixAPI

# 开启调试 Enable debugging
# stream = logging.StreamHandler(sys.stdout)
# stream.setLevel(logging.DEBUG)
# log = logging.getLogger('pyzabbix')
# log.addHandler(stream)
# log.setLevel(logging.DEBUG)

# 登录　Zabbix API login
zapi = ZabbixAPI("http://10.10.10.10/zabbix/")
zapi.login("user_name", "user_pass")

# 定义获取历史数据的时间数组 timestamp array
# 1.获取当天24个整点的时间
# retrieve_times = []
# day_time = int(time.time()) - int(time.time()) % 86400 + time.timezone
# for oclock in range(1, 25):
#     retrieve_times.append(day_time)
#     day_time += 3600

# 2.获取当前时间的历史数据，配合计划任务定时执行，提前3分钟以免zabbix还没有获取数据 3 minutes before current time
retrieve_times = [int(time.time()) - 180]


# 获取所有主机列表：retrieve all hosts
def gethosts():
    host_all = zapi.host.get(output=["hostid", "host"],
                             selectInterfaces=["ip", ]
                             )
    # 返回主机列表结果
    return host_all


# 获取指定主机指定监控指标 retrieve items of host
# CPU利用率：system.cpu.util
# 内存剩余百分比
# vm.memory.size[pavailable]
# 磁盘空间已用百分比：
# vfs.fs.size[/,pused]
def getitems(hostid):
    item_all = zapi.item.get(output=["itemid", "key_"],
                             hostids=[hostid],
                             search={"key_": ["system.cpu.util[,idle]",
                                              "vm.memory.size[pavailable]",
                                              "vfs.fs.size[*,pused]"]},
                             searchByAny=1,
                             searchWildcardsEnabled=1
                             )
    # 返回每个主机的监测指标
    return item_all


# 获取历史数据，第一个get默认从integer类型表获取 retrieve history data
def gethistory(theitem, data_recieve_time):
    historydata = zapi.history.get(itemids=[theitem],
                                   time_from=data_recieve_time,
                                   time_till=data_recieve_time + 120,
                                   output=['value'],
                                   limit='1',
                                   )

    # 如果integer表没有，则从float表取 retrieve from float table
    if not len(historydata):
        historydata = zapi.history.get(itemids=[theitem],
                                       time_from=data_recieve_time,
                                       time_till=data_recieve_time + 120,
                                       output=['value'],
                                       limit='1',
                                       history=0,
                                       )
    # 返回所有历史数据列表字典中的值
    return historydata[0]['value']


def xunjian():
    # 定义巡检表内容数组
    item_rows = []

    # 获取主机数组
    hosts = gethosts()

    # 循环处理每个主机
    for host in hosts:
        # 定义每个主机的内容字典
        host_rows = {'serverName': host['host'], 'serverIp': host['interfaces'][0]["ip"], 'serverData': {}}

        # 获取每个主机的监控指标数组
        items = getitems(host["hostid"])

        # 循环处理每个监控指标
        for item in items:
            datatype = item["key_"]
            host_rows['serverData'][datatype] = []

            # 循环获取每个时间点的数据
            for retrieve_time in retrieve_times:
                history_data = gethistory(item["itemid"], retrieve_time)
                host_rows['serverData'][datatype].append(history_data)

        # 每个主机内容放入整个巡检表内容中
        item_rows.append(host_rows)

    return item_rows


xunjian = xunjian()
print(xunjian)
