# log
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

import os
import time
import fcntl
from operator import contains
import exception_msg
import ksum
import syslog
import singleton
import sessionid
import evcommon
import urllib

def log(msg):
    AppLog().log(msg)

def log_error(msg):
    AppLog().log_error(msg)

def log_exception():
    AppLog().log_exception()

def log_integrity(msg):
    AppLog().log_integrity(msg)

class RevLogFormat:

    def __init__(self):
        pass

    def keep(self):
        return True

    def message(self, args):

        oldtime = time.strptime(
                    args['timestamp'],
                    "%Y-%m-%dT%H:%M:%SZ")

        newtime = time.localtime()
        if contains(args, 'testtime'):
            newtime = time.strptime(
                    args['testtime'],
                    "%Y-%m-%dT%H:%M:%SZ")

        line = []
        line.append(args['tegevus'])
        line.append(args['isikukood'])
        line.append(args['nimi'])
        line.append(time.strftime("%Y%m%d%H%M%S", oldtime))
        line.append(time.strftime("%Y%m%d%H%M%S", newtime))
        line.append(args['operaator'])
        line.append(args['pohjus'])
        logstring = "\t".join(line)
        return logstring


class EvLogFormat:

    def __init__(self):
        pass

    def keep(self):
        return True

    def message(self, args):
        line = []
        # Üldvorming
        # aeg 14*14DIGIT
        if contains(args, 'timestamp'):
            line = [args['timestamp']]
        else:
            line = [time.strftime("%Y%m%d%H%M%S")]
        # Hääle räsi 28*28BASE64-CHAR
        if not contains(args, 'haal_rasi'):
            if contains(args, 'haal'):
                args['haal_rasi'] = ksum.votehash(args['haal'])
        line.append(args['haal_rasi'])

        # omavalitsuse-number 1*10DIGIT
        line.append(str(args['ringkond_omavalitsus']))
        # suhteline-ringkonna-number 1*10DIGIT
        line.append(str(args['ringkond']))
        if contains(args, 'jaoskond_omavalitsus'):
            # omavalitsuse-number 1*10DIGIT
            line.append(str(args['jaoskond_omavalitsus']))
        if contains(args, 'jaoskond'):
            # suhteline-valimisjaoskonna-number 1*10DIGIT
            line.append(str(args['jaoskond']))

        if args['tyyp'] in [1, 2, 3]:
            #*1valija-andmed =
            #isikukood 11*11DIGIT
            line.append(str(args['isikukood']))
        if args['tyyp'] == 2:
            # pohjus 1*100UTF-8-CHAR
            line.append(args['pohjus'])
        logstring = "\t".join(line)

        return logstring

    # Currently we only check for personal code
    # this can be extended to check anything
    def matches(self, data, line, count):

        # Skip version, identifier and logtype
        if count < 3:
            return False

        return (line.split("\t")[6][0:11] == data)


    # Currently we only cache by personal code
    # this can be extended to cache anything
    def cache(self, cc, key, line, count):

        # Skip version, identifier and logtype
        if count > 2:
            ik = line.split("\t")[6][0:11]
            cc[ik] = True


class AppLogFormat:

    def __init__(self, app = None):
        self.__app = app
        self.__elid = ''
        self.__pers_id = ''
        self.__sess = os.getpid()
        self.__psess = os.getppid()

    def set_elid(self, elid):
        self.__elid = elid

    def set_app(self, app):
        self.__app = app

    def set_person(self, person):
        self.__pers_id = person

    def keep(self):
        return False

    def message(self, args):
        logstring = "%s (%s:%d:%d:%s:%s:%s:%s): %s" % (
            time.strftime("%Y-%m-%d %H:%M:%S"),
            self.__app,
            self.__sess,
            self.__psess,
            sessionid.voting(),
            sessionid.apache(),
            self.__elid,
            self.__pers_id,
            args['message'])
        return logstring

class LogFile:

    __filename = None

    def __init__(self, filename):
        self.__filename = filename

    def write(self, message):
        if (self.__filename):
            _af = file(self.__filename, 'a')
            try:
                fcntl.lockf(_af, fcntl.LOCK_EX)
                _af.write(message)
                _af.flush()
            finally:
                _af.close()

    def line_count(self): # pylint: disable=R0201
        line_count = 0
        try:
            os.stat(self.__filename)
        except OSError:
            return line_count

        try:
            _rf = open(self.__filename, 'r')
            for _ in _rf:
                line_count += 1
            return line_count
        finally:
            if (_rf):
                _rf.close()


    def contains(self, data, form):

        res = False
        if not os.access(self.__filename, os.F_OK):
            return res

        _f = None
        try:
            _f = file(self.__filename, 'r')
            fcntl.lockf(_f, fcntl.LOCK_SH)
            ii = 0
            for line in _f:
                if form.matches(data, line, ii):
                    res = True
                    break
                ii = ii + 1

        finally:
            if _f:
                _f.close()

        return res


    def cache(self, cc, key, form):

        if os.access(self.__filename, os.F_OK):
            _f = None
            try:
                _f = file(self.__filename, 'r')
                fcntl.lockf(_f, fcntl.LOCK_SH)

                ii = 0
                for line in _f:
                    form.cache(cc, key, line, ii)
                    ii = ii + 1

            finally:
                if _f != None:
                    _f.close()


class Logger(object):

    def __init__(self, ident=None):
        self.__last_message = ''
        self._log = None
        self._form = None
        self.__ident = ident
        self.__fac = syslog.LOG_LOCAL0
        syslog.openlog(facility=self.__fac)

    def set_format(self, form):
        self._form = form

    def set_logs(self, path):
        self._log = LogFile(path)

    def last_message(self):
        return self.__last_message

    def _log_syslog(self, prio):
        if self.__ident:
            syslog.openlog(ident=self.__ident, facility=self.__fac)
            syslog.syslog(prio, self.__last_message)
            syslog.closelog()
        else:
            syslog.syslog(prio | self.__fac, self.__last_message)

    def _do_log(self, level, **args):
        self.__last_message = self._form.message(args)
        if not self._form.keep():
            self.__last_message = urllib.quote(self.__last_message, \
                    ' !"#&\'()*+,-./:;<=>?@\[\]_|\t]äöüõÄÖÜÕ')

        self.__last_message += "\n"
        self._log.write(self.__last_message)
        self._log_syslog(level)

    def log_info(self, **args):
        self._do_log(syslog.LOG_INFO, **args)

    def log_err(self, **args):
        self._do_log(syslog.LOG_ERR, **args)

    def log_debug(self, **args):
        self._do_log(syslog.LOG_DEBUG, **args)

    def lines_in_file(self):
        return self._log.line_count()

    def contains(self, data):
        return self._log.contains(data, self._form)

    def cache(self, cc, key):
        self._log.cache(cc, key, self._form)


class AppLog(Logger):

    __metaclass__ = singleton.SingletonType

    def __init__(self):
        Logger.__init__(self)
        self._form = AppLogFormat()
        self.__log_i = LogFile(
                os.path.join(
                    evcommon.EVREG_CONFIG,
                    'common',
                    evcommon.APPLICATION_LOG_FILE))

        self.__log_e = LogFile(
                os.path.join(
                    evcommon.EVREG_CONFIG,
                    'common',
                    evcommon.ERROR_LOG_FILE))

        self.__log_d = LogFile(
                os.path.join(
                    evcommon.EVREG_CONFIG,
                    'common',
                    evcommon.DEBUG_LOG_FILE))

    def set_app(self, app, elid = None):
        #remove elid
        self._form.set_app(app)
        self._form.set_elid(elid)

    def set_person(self, person):
        self._form.set_person(person)

    def log(self, msg):
        #add elid
        self._log = self.__log_i
        self.log_info(message=msg)

    def log_error(self, msg):
        self._log = self.__log_e
        self.log_err(message=msg)

    def log_integrity(self, warns):
        msg = "FAILED: " + "; ".join(warns) if warns else "OK"
        self._log = self.__log_d
        self.log_debug(message=msg)

    def log_exception(self):
        self.log_error(exception_msg.trace())

# vim:set ts=4 sw=4 et fileencoding=utf8:
