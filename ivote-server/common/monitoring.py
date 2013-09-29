#!/usr/bin/python2.7
# -*- coding: UTF8 -*-

"""
Copyright: Eesti Vabariigi Valimiskomisjon
(Estonian National Electoral Committee), www.vvk.ee
Written in 2004-2013 by Cybernetica AS, www.cyber.ee

This work is licensed under the Creative Commons
Attribution-NonCommercial-NoDerivs 3.0 Unported License.
To view a copy of this license, visit
http://creativecommons.org/licenses/by-nc-nd/3.0/.
"""

### depends on debian package python-psutil
import os, time, psutil, syslog

if __name__ == "__main__":
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    ldavg = str(os.getloadavg())
    mem = psutil.phymem_usage().percent
    vmem = psutil.virtmem_usage().percent
    disk = psutil.disk_usage("/").percent
    disk_io = psutil.disk_io_counters(perdisk=True)
    net_io = psutil.network_io_counters(pernic=True)

    lines = []
    lines.append("%s: ldavg:%s mem:%s%% vmem:%s%% disk:%s%%" % \
            (ts, ldavg, mem, vmem, disk))

    for disk in disk_io:
        lines.append("%s: %s %s" % (ts, disk, str(disk_io[disk])))

    for nic in net_io:
        lines.append("%s: %s %s" % (ts, nic, str(net_io[nic])))

    for line in lines:
        syslog.syslog(line)
