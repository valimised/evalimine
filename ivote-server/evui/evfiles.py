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

import evcommon
from election import Election

class EvFileTable:

    def __init__(self):
        self.__files = []

    def add_file(self, ffile):
        if ffile:
            self.__files.append(ffile)

    def get_existing_files(self):

        ret = {}

        for el in self.__files:
            if el.exists():
                ret[el.name()] = el.path()

        return ret


class EvFile:

    def __init__(self, filename, uiname, regprefix):
        self.__filename = filename
        self.__uiname = uiname
        self.__regprefix = regprefix
        self.__reg = Election().get_root_reg()

    def exists(self):
        return self.__reg.check(self.__regprefix + [self.__filename])

    def path(self):
        return self.__reg.path(self.__regprefix + [self.__filename])

    def name(self):
        return self.__uiname


def log1_file(elid):
    return EvFile(evcommon.LOG1_FILE, \
                    evcommon.LOG1_STR, ['questions', elid, 'common'])

def log2_file(elid):
    return EvFile(evcommon.LOG2_FILE, \
                    evcommon.LOG2_STR, ['questions', elid, 'common'])

def log3_file(elid):
    return EvFile(evcommon.LOG3_FILE, \
                    evcommon.LOG3_STR, ['questions', elid, 'common'])

def log4_file(elid):
    return EvFile(evcommon.LOG4_FILE, \
                    evcommon.LOG4_STR, ['questions', elid, 'common'])

def log5_file(elid):
    return EvFile(evcommon.LOG5_FILE, \
                    evcommon.LOG5_STR, ['questions', elid, 'common'])

def revlog_file(elid):
    return EvFile(evcommon.REVLOG_FILE, \
                    evcommon.REVLOG_STR, ['questions', elid, 'common'])

def application_log_file():
    return EvFile(evcommon.APPLICATION_LOG_FILE, \
                    evcommon.APPLICATION_LOG_STR, ['common'])

def error_log_file():
    return EvFile(evcommon.ERROR_LOG_FILE, \
                    evcommon.ERROR_LOG_STR, ['common'])

def integrity_log_file():
    return EvFile(evcommon.DEBUG_LOG_FILE, \
                    evcommon.DEBUG_LOG_STR, ['common'])

def voter_list_log_file():
    return EvFile(evcommon.VOTER_LIST_LOG_FILE, \
                    evcommon.VOTER_LIST_LOG_STR, ['common'])

def elections_result_file(elid):
    return EvFile(evcommon.ELECTIONS_RESULT_FILE, \
                                        evcommon.ELECTIONS_RESULT_STR, \
                                        ['questions', elid, 'hts', 'output'])

def electorslist_file(elid):
    return EvFile(evcommon.ELECTORSLIST_FILE, evcommon.ELECTORSLIST_STR, \
                                        ['questions', elid, 'hts', 'output'])

def revreport_file(elid):
    return EvFile(evcommon.REVREPORT_FILE, evcommon.REVREPORT_STR, \
                                        ['questions', elid, 'hts', 'output'])

def statusreport_file():
    return EvFile(evcommon.STATUSREPORT_FILE, \
                    evcommon.STATUSREPORT_STR, ['common'])

def electionresult_file(elid):
    return EvFile(evcommon.ELECTIONRESULT_FILE, \
                                        evcommon.ELECTIONRESULT_STR, \
                                        ['questions', elid, 'hlr', 'output'])

def electionresultstat_file(elid):
    return EvFile(evcommon.ELECTIONRESULT_STAT_FILE, \
                                        evcommon.ELECTIONRESULT_STAT_STR, \
                                        ['questions', elid, 'hlr', 'output'])

def add_hts_files_to_table(elid, table):
    import os
    reg = Election().get_root_reg()
    if reg.check(['questions', elid, 'hts', 'output']):
        o_files = os.listdir(reg.path(['questions', elid, 'hts', 'output']))
        for of in o_files:
            if of.find("tokend.") == 0 and of.find(".sha1") == -1:
                table.add_file(EvFile(of, of, ['questions', elid, 'hts', 'output']))

# vim:set ts=4 sw=4 et fileencoding=utf8:
