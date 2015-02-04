#!/usr/bin/python2.7
# -*- coding: UTF8 -*-

"""
Copyright: Eesti Vabariigi Valimiskomisjon
(Estonian National Electoral Committee), www.vvk.ee
Written in 2004-2014 by Cybernetica AS, www.cyber.ee

This work is licensed under the Creative Commons
Attribution-NonCommercial-NoDerivs 3.0 Unported License.
To view a copy of this license, visit
http://creativecommons.org/licenses/by-nc-nd/3.0/.
"""

import subprocess
from election import Election
import time
import bdocconfig
import evlog
import evcommon
import exception_msg


def check_ocsp():

    log = evlog.Logger()
    log.set_format(evlog.AppLogFormat('OCSPWD'))
    log.set_logs(Election().get_path(evcommon.OCSP_LOG_FILE))

    try:
        _conf = bdocconfig.BDocConfig()
        _conf.load(Election().get_bdoc_conf())
        _ocsp = _conf.get_ocsp_responders()

        for el in _ocsp:
            app = ('openssl ocsp -issuer "%s" -serial 123 -url "%s" -noverify'
                   % (_ocsp[el], el))

            pp = subprocess.Popen(app, shell=True, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, close_fds=True)
            is_ok = 0
            start = time.time()
            while True:
                line = pp.stdout.readline()
                if not line:
                    break
                if line.strip().find('This Update:') != -1:
                    is_ok = 1
            end = time.time()
            if is_ok:
                log.log_info(message='OCSP päringu tegemiseks kulus %5.2f sekundit' % (end - start))
            else:
                log.log_info(message='OCSP ei vasta')
    except:
        log.log_err(message=exception_msg.trace())


if __name__ == '__main__':
    try:
        check_ocsp()
    except:
        pass
    exit(0)

# vim:set ts=4 sw=4 et fileencoding=utf8:
