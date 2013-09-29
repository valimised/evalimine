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

import sys

if sys.version_info[0] != 2 or sys.version_info[1] != 7:
    raise Exception(
        'Vajalik on pythoni versioon 2.7 (praegune versioon: %s.%s)' % (
            sys.version_info[0], sys.version_info[1]))


def testrun():
    return (None <> os.environ.get('IVOTE_TEST_RUN'))

VERSION = "1"

# Serverite tüübid
APPTYPE_HES = "hes"
APPTYPE_HTS = "hts"
APPTYPE_HLR = "hlr"
APPTYPES = [APPTYPE_HES, APPTYPE_HTS, APPTYPE_HLR]

# HTTP protokolli parameetrid

HTTP_POST = "POST"
# Kliendi autentimissertifikaat sessioonis
HTTP_CERT = 'SSL_CLIENT_CERT'
# Info kliendi platvormi kohta sessioonis
HTTP_AGENT = 'HTTP_USER_AGENT'

# hääletamine
POST_EVOTE = "vote"
# isikukoodi järgi hääletamise fakti kontroll
POST_PERSONAL_CODE = "ik"
# valijate nimekirjade failide kooskõlalisuse räsi
POST_VOTERS_FILES_SHA1 = "hash"
# sessiooniidentifikaator
POST_SESS_ID = "session"

# Mobiil-ID telefoni number
POST_PHONENO = "phone"

# Mobiil-ID sessioon
POST_MID_POLL = "poll"

# Verification protocol
POST_VERIFY_VOTE = "vote"

# VR <-> HES protokolli tagastusväärtused
# Samad koodid ka talletusprotokollis HES <-> HTS

# Positiivne vastuse lipp
EVOTE_OK = '0'
# Vea lipp
EVOTE_ERROR = '1'
# Kasutaja serdi vea lipp
EVOTE_CERT_ERROR = '2'
# Kasutaja pole valijate nimekirjas
EVOTE_VOTER_ERROR = '3'
# Mobiil-ID ei ole veel vastust andnud
EVOTE_POLL = '4'
# Mobiil-ID sertifikaat ei ole hääletamiseks sobiv
EVOTE_MID_POLICY_ERROR = '5'
# Mobiil-ID komponendi viga
EVOTE_MID_ERROR = '6'


# HES <-> HTS vaheliste protokollide väärtused

# EVOTE kooskõlalisuse protokolli tagastusväärtused
EVOTE_CONSISTENCY_NO = '3'
EVOTE_CONSISTENCY_YES = '2'
EVOTE_CONSISTENCY_ERROR = '1'

# EVOTE korduvhääletuse protokolli tagastusväärtused
EVOTE_REPEAT_NO = '3'
EVOTE_REPEAT_YES = '4'
EVOTE_REPEAT_NOT_CONSISTENT = '2'
EVOTE_REPEAT_ERROR = '1'

# Verification protocol return values
VERIFY_OK = '0'
VERIFY_ERROR = '1'

COMMON = "common"
BDOC = "common/bdoc"
MIDSPOOL = "midspool"

TYPE_RH = 0
TYPE_KOV = 1
TYPE_RK = 2
TYPE_EUROPARLAMENT = 3

G_TYPES = {
    TYPE_RH: 'Rahvahääletus',
    TYPE_KOV: 'Kohalikud omavalitsused',
    TYPE_RK: 'Riigikogu',
    TYPE_EUROPARLAMENT: 'Europarlament'}

# Logifailid
LOG1_FILE = "log1"
LOG2_FILE = "log2"
LOG3_FILE = "log3"
LOG4_FILE = "log4"
LOG5_FILE = "log5"
APPLICATION_LOG_FILE = "ivoting_app_log"
ERROR_LOG_FILE = "ivoting_err_log"
DEBUG_LOG_FILE = "ivoting_debug_log"
OCSP_LOG_FILE = "ivoting_ocsp_log"
VOTER_LIST_LOG_FILE = "valijate_nimekirjade_vigade_logi"
REVLOG_FILE = "tuhistamiste_ennistamiste_logi"
ELECTIONRESULT_FILE = "haaletamistulemus"
ELECTIONRESULT_SHA1_FILE = "haaletamistulemus.sha1"
ELECTIONRESULT_STAT_FILE = "haaletamistulemusjaosk"
ELECTIONRESULT_STAT_SHA1_FILE = "haaletamistulemusjaosk.sha1"
ELECTIONS_RESULT_FILE = "loendamisele_minevate_haalte_nimekiri"
ELECTIONS_RESULT_SHA1_FILE = "loendamisele_minevate_haalte_nimekiri.sha1"
ELECTORSLIST_FILE = "haaletanute_nimekiri"
ELECTORSLIST_SHA1_FILE = "haaletanute_nimekiri.sha1"
ELECTORSLIST_FILE_TMP = "haaletanute_nimekiri_tmp"
STATUSREPORT_FILE = "HTSi_vaheauditi_aruanne"
REVREPORT_FILE = "tuhistamiste_ennistamiste_aruanne"
REVREPORT_SHA1_FILE = "tuhistamiste_ennistamiste_aruanne.sha1"

LOG1_STR = "Vastuvõetud häälte logi (Log1)"
LOG2_STR = "Tühistatud häälte logi (Log2)"
LOG3_STR = "Lugemisele minevate häälte logi (Log3)"
LOG4_STR = "Kehtetute häälte logi (Log4)"
LOG5_STR = "Arvestatud häälte logi (Log5)"
APPLICATION_LOG_STR = "Rakenduse logi"
ERROR_LOG_STR = "Vigade logi"
DEBUG_LOG_STR = "Turvalogi"
VOTER_LIST_LOG_STR = "Valijate nimekirjade vigade logi"
REVLOG_STR = "Tühistamiste ja ennistamiste aruanne"
ELECTIONRESULT_STR = "Hääletamistulemus (ringkondade kaupa)"
ELECTIONRESULT_STAT_STR = "Hääletamistulemus (jaoskondade kaupa)"
ELECTIONS_RESULT_STR = "Loendamisele minevate häälte nimekiri"
ELECTORSLIST_STR = "E-hääletanute nimekiri"
STATUSREPORT_STR = "Vaheauditi aruanne"
REVREPORT_STR = "Tühistus-/ennistusavalduse impordi aruanne"

# konfigureerimist träkkivad lipud
INIT_CONF_DONE = "init_conf_done"
CONFIG_BDOC_DONE = "config_bdoc_done"
CONFIG_HTH_DONE = "config_hth_done"
CONFIG_MID_DONE = "config_mid_done"
CONFIG_SERVER_DONE = "config_server_done"
CONFIG_HSM_DONE = "config_hsm_done"
CONFIG_HLR_INPUT_DONE = "config_hlr_input_done"

VOTERS_LIST_IS_DISABLED = "voters_list_is_disabled"

# registri juurikas
import os

try:
    EVREG_CONFIG = os.environ['EVREG_CONFIG']
except KeyError:
    EVREG_CONFIG = '/var/evote/registry'

def burn_buff():
    return os.path.join(os.environ["HOME"], "burn_buff")

def checkfile(filename):
    if not os.access(filename, os.F_OK):
        sys.stderr.write('Faili ' + filename + ' ei eksisteeri\n')
        sys.exit(1)
    if not os.access(filename, os.R_OK):
        sys.stderr.write('Faili ' + filename + ' ei saa lugeda\n')
        sys.exit(1)


def touch_file(path):
    touch_f = file(path, 'w')
    touch_f.close()

def file_cmp(a, b, prefix): # pylint: disable=C0103
    if a == b:
        return 0

    if a == prefix:
        return -1

    if b == prefix:
        return 1

    ai = int(a.split('.')[2])
    bi = int(b.split('.')[2])
    return ai - bi

def access_cmp(a, b): # pylint: disable=C0103
    return file_cmp(a, b, 'access.log')

def error_cmp(a, b): # pylint: disable=C0103
    return file_cmp(a, b, 'error.log')

def get_apache_log_files():
    accesslog = []
    errorlog = []
    for filename in os.listdir('/var/log/apache2'):
        if filename.startswith('access.log'):
            accesslog.append(filename)
        if filename.startswith('error.log'):
            errorlog.append(filename)

    accesslog.sort(access_cmp)
    errorlog.sort(error_cmp)
    return accesslog, errorlog


# vim:set ts=4 sw=4 et fileencoding=utf8:
