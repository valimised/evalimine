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

import evcommon
from election import Election

LOG1_STR = "Log1 - vastuvõetud häälte logi"
LOG2_STR = "Log2 - tühistatud häälte logi"
LOG3_STR = "Log3 - lugemisele minevate häälte logi"
LOG4_STR = "Log4 - kehtetute häälte logi"
LOG5_STR = "Log5 - arvestatud häälte logi"
APPLICATION_LOG_STR = "Rakenduse logi"
ERROR_LOG_STR = "Vigade logi"
DEBUG_LOG_STR = "Turvalogi"
OCSP_LOG_STR = "OCSP saadavuse logi"
VOTER_LIST_LOG_STR = "Valijate nimekirjade vigade logi"
REVLOG_STR = "Tühistamiste ja ennistamiste aruanne"
ELECTIONRESULT_ZIP_STR = "Hääletamistulemus (allkirjadega)"
ELECTIONRESULT_STR = "Hääletamistulemus (ringkondade kaupa)"
ELECTIONRESULT_STAT_STR = "Hääletamistulemus (jaoskondade kaupa)"
ELECTIONS_RESULT_STR = "Loendamisele minevate häälte nimekiri"
ELECTORSLIST_STR = "E-hääletanute nimekiri"
ELECTORSLIST_PDF_STR = "E-hääletanute nimekiri (PDF)"
STATUSREPORT_STR = "Vaheauditi aruanne"
REVREPORT_STR = "Tühistus-/ennistusavalduse impordi aruanne"


class EvFileTable:

    def __init__(self):
        self.__files = []

    def add_file(self, ffile):
        if ffile:
            self.__files.append(ffile)

    def get_existing_files(self, usebinary):

        ret = {}

        for el in self.__files:
            if el.exists() and (usebinary or not el.binary()):
                ret[el.name()] = el.path()

        return ret


IS_BINARY = True


class EvFile:

    def __init__(self, filename, uiname, regprefix, binary=False):
        self.__filename = filename
        self.__uiname = uiname
        self.__regprefix = regprefix
        self.__reg = Election().get_root_reg()
        self.__binary = binary

    def exists(self):
        return self.__reg.check(self.__regprefix + [self.__filename])

    def path(self):
        return self.__reg.path(self.__regprefix + [self.__filename])

    def name(self):
        return self.__uiname

    def binary(self):
        return self.__binary


def log1_file(elid):
    return EvFile(evcommon.LOG1_FILE, LOG1_STR, ['questions', elid, 'common'])


def log2_file(elid):
    return EvFile(evcommon.LOG2_FILE, LOG2_STR, ['questions', elid, 'common'])


def log3_file(elid):
    return EvFile(evcommon.LOG3_FILE, LOG3_STR, ['questions', elid, 'common'])


def log4_file(elid):
    return EvFile(evcommon.LOG4_FILE, LOG4_STR, ['questions', elid, 'common'])


def log5_file(elid):
    return EvFile(evcommon.LOG5_FILE, LOG5_STR, ['questions', elid, 'common'])


def revlog_file(elid):
    return EvFile(evcommon.REVLOG_FILE,
                  REVLOG_STR, ['questions', elid, 'common'])


def application_log_file():
    return EvFile(evcommon.APPLICATION_LOG_FILE,
                  APPLICATION_LOG_STR, ['common'])


def error_log_file():
    return EvFile(evcommon.ERROR_LOG_FILE,
                  ERROR_LOG_STR, ['common'])


def integrity_log_file():
    return EvFile(evcommon.DEBUG_LOG_FILE,
                  DEBUG_LOG_STR, ['common'])


def ocsp_log_file():
    return EvFile(evcommon.OCSP_LOG_FILE,
                  OCSP_LOG_STR, ['common'])


def voter_list_log_file():
    return EvFile(evcommon.VOTER_LIST_LOG_FILE,
                  VOTER_LIST_LOG_STR, ['common'])


def elections_result_file(elid):
    return EvFile(evcommon.ELECTIONS_RESULT_FILE,
                  ELECTIONS_RESULT_STR, ['questions', elid, 'hts', 'output'])


def electorslist_file(elid):
    return EvFile(evcommon.ELECTORSLIST_FILE, ELECTORSLIST_STR,
                  ['questions', elid, 'hts', 'output'])


def electorslist_file_pdf(elid):
    return EvFile(evcommon.ELECTORSLIST_FILE_PDF,
                  ELECTORSLIST_PDF_STR,
                  ['questions', elid, 'hts', 'output'], IS_BINARY)


def revreport_file(elid):
    return EvFile(evcommon.REVREPORT_FILE, REVREPORT_STR,
                  ['questions', elid, 'hts', 'output'])


def statusreport_file():
    return EvFile(evcommon.STATUSREPORT_FILE, STATUSREPORT_STR, ['common'])


def electionresult_zip_file(elid):
    return EvFile(evcommon.ELECTIONRESULT_ZIP_FILE,
                  ELECTIONRESULT_ZIP_STR,
                  ['questions', elid, 'hlr', 'output'], IS_BINARY)


def electionresult_file(elid):
    return EvFile(evcommon.ELECTIONRESULT_FILE,
                  ELECTIONRESULT_STR, ['questions', elid, 'hlr', 'output'])


def electionresultstat_file(elid):
    return EvFile(evcommon.ELECTIONRESULT_STAT_FILE,
                  ELECTIONRESULT_STAT_STR, ['questions', elid, 'hlr', 'output'])


def add_hts_files_to_table(elid, table):
    import os
    reg = Election().get_root_reg()
    if reg.check(['questions', elid, 'hts', 'output']):
        o_files = os.listdir(reg.path(['questions', elid, 'hts', 'output']))
        for of in o_files:
            if of.find("tokend.") == 0 and of.find(".sha256") == -1:
                table.add_file(
                    EvFile(of, of, ['questions', elid, 'hts', 'output']))

# vim:set ts=4 sw=4 et fileencoding=utf8:
