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

import os.path
import evreg
import time
import shutil
import ksum
import evcommon
import formatutil
import question
import protocol
import singleton

ELECTION_ID = 'electionid'

ETAPP_ENNE_HAALETUST = 1
ETAPP_HAALETUS = 2
ETAPP_TYHISTUS = 3
ETAPP_LUGEMINE = 4

G_STATES = {
        ETAPP_ENNE_HAALETUST: 'Seadistusperiood',
        ETAPP_HAALETUS: 'Hääletusperiood',
        ETAPP_TYHISTUS: 'Tühistusperiood',
        ETAPP_LUGEMINE: 'Lugemisperiood'}

HES_STATES = {
    ETAPP_ENNE_HAALETUST: ETAPP_HAALETUS,
    ETAPP_HAALETUS: ETAPP_LUGEMINE}

HTS_STATES = {
    ETAPP_ENNE_HAALETUST: ETAPP_HAALETUS,
    ETAPP_HAALETUS: ETAPP_TYHISTUS,
    ETAPP_TYHISTUS: ETAPP_LUGEMINE}

HLR_STATES = {
    ETAPP_ENNE_HAALETUST: ETAPP_LUGEMINE}


def create_registry():
    evreg.create_registry(evcommon.EVREG_CONFIG)


class ElectionState:

    __metaclass__ = singleton.SingletonType

    __reg = None

    def __init__(self):
        self.__reg = evreg.Registry(root=evcommon.EVREG_CONFIG)

    def _set(self, state):
        self.__reg.ensure_key(['common'])
        self.__reg.create_integer_value(['common'], 'state', state)

    def init(self):
        self._set(ETAPP_ENNE_HAALETUST)

    def has(self):
        return self.__reg.check(['common', 'state'])

    def get(self):
        if not self.has():
            self.init()
        return self.__reg.read_integer_value(['common'], 'state').value

    def str(self):
        _state = self.get()
        return G_STATES[_state]

    def election_on(self):
        return self.get() == ETAPP_HAALETUS

    def election_off_msg(self):
        if self.get() == ETAPP_ENNE_HAALETUST:
            return protocol.plain_error_election_off_before()
        return protocol.plain_error_election_off_after()

    def next(self):

        _oldstate = self.get()

        if _oldstate == ETAPP_LUGEMINE:
            return

        if Election().is_hes():
            _newstate = HES_STATES[_oldstate]
        elif Election().is_hts():
            _newstate = HTS_STATES[_oldstate]
        elif Election().is_hlr():
            _newstate = HLR_STATES[_oldstate]
        else:
            raise Exception('Puuduv serveritüüp')

        self._set(_newstate)

    def can_apply_changes(self):
        _state = self.get()
        return _state in [ETAPP_ENNE_HAALETUST, ETAPP_HAALETUS]

    def can_replace_candidates(self):
        _state = self.get()
        return _state in [ETAPP_ENNE_HAALETUST]

    def can_load_conf(self):
        _state = self.get()
        return _state in [ETAPP_ENNE_HAALETUST]


class Election:

    __metaclass__ = singleton.SingletonType

    reg = None

    def __init__(self):
        self.reg = evreg.Registry(root=evcommon.EVREG_CONFIG)

    def get_voters_files_sha1(self):
        if self.reg.check(['common', 'voters_files_sha1']):
            return \
                self.reg.read_string_value(\
                    ['common'], 'voters_files_sha1').value
        return ''

    def init_keys(self):
        self.reg.ensure_key(['common'])

    def is_hes(self):
        return self.reg.check(['common', 'hes'])

    def is_hts(self):
        return self.reg.check(['common', 'hts'])

    def is_hlr(self):
        return self.reg.check(['common', 'hlr'])

    def set_server_str(self, srvstr):
        if srvstr in evcommon.APPTYPES:
            self.reg.ensure_key(['common', srvstr])
        else:
            raise Exception('Vigane serveri tüüp')

    def get_server_str(self):
        if self.is_hes():
            return 'hes'
        elif self.is_hts():
            return 'hts'
        elif self.is_hlr():
            return 'hlr'
        else:
            raise Exception('Vigane serveri tüüp')

    def copy_voters_file(self, elid, server, voters_file):

        voters_files = 'voters_files'
        _r = self.get_sub_reg(elid, [server])
        _r.ensure_key([voters_files])

        time_str = time.strftime("%Y%m%d%H%M%S")
        copy_voters_file = _r.path([voters_files, time_str + '_' + \
            os.path.basename(voters_file)])
        shutil.copyfile(voters_file, copy_voters_file)

        voters_file_sha1 = ksum.compute(voters_file)
        voters_file_hashes = ['common', 'voters_file_hashes']
        self.reg.ensure_key(voters_file_hashes)
        self.reg.create_string_value(voters_file_hashes, voters_file_sha1, '')

        voters_files_sha1 = \
            ksum.compute_voters_files_sha1(self.reg.path(voters_file_hashes))
        self.reg.create_string_value(['common'], \
            'voters_files_sha1', voters_files_sha1)

    def get_bdoc_conf(self):
        return self.reg.path([evcommon.BDOC])

    def get_bdoc_ca(self):
        return self.reg.path([evcommon.BDOC, 'ca'])

    def get_hsm_token_name(self):
        return self.reg.read_string_value(['common', 'hsm'], 'tokenname').value

    def get_hsm_priv_key(self):
        return \
            self.reg.read_string_value(['common', 'hsm'], 'privkeylabel').value

    def get_pkcs11_path(self):
        return self.reg.read_string_value(['common', 'hsm'], 'pkcs11').value

    def set_hsm_token_name(self, val):
        self.reg.ensure_key(['common', 'hsm'])
        self.reg.create_string_value(['common', 'hsm'], 'tokenname', val)

    def set_hsm_priv_key(self, val):
        self.reg.ensure_key(['common', 'hsm'])
        self.reg.create_string_value(['common', 'hsm'], 'privkeylabel', val)

    def set_pkcs11_path(self, val):
        self.reg.ensure_key(['common', 'hsm'])
        self.reg.create_string_value(['common', 'hsm'], 'pkcs11', val)

    def get_path(self, afile):
        return self.reg.path(['common', afile])

    def get_hts_ip(self):
        return self.reg.read_ipaddr_value(['common'], 'htsip').value

    def set_hts_ip(self, ip):
        self.reg.ensure_key(['common'])
        self.reg.create_ipaddr_value(['common'], 'htsip', ip)

    def get_hts_path(self):
        return self.reg.read_string_value(['common'], 'htspath').value.rstrip()

    def set_hts_path(self, path):
        self.reg.ensure_key(['common'])
        self.reg.create_string_value(['common'], 'htspath', path)

    def get_hts_verify_path(self):
        return self.reg.read_string_value(['common'], 'htsverifypath').value.rstrip()

    def set_hts_verify_path(self, path):
        self.reg.ensure_key(['common'])
        self.reg.create_string_value(['common'], 'htsverifypath', path)

    def get_verification_time(self):
        return self.reg.read_integer_value(['common'], 'verification_time').value

    def set_verification_time(self, time):
        self.reg.ensure_key(['common'])
        self.reg.create_integer_value(['common'], 'verification_time', time)

    def get_verification_count(self):
        return self.reg.read_integer_value(['common'], 'verification_count').value

    def set_verification_count(self, count):
        self.reg.ensure_key(['common'])
        self.reg.create_integer_value(['common'], 'verification_count', count)

    def get_questions_obj(self, root):
        qlist = self.get_questions()
        ret = []
        for elem in qlist:
            quest = question.Question(elem, root, self.get_sub_reg(elem))
            ret.append(quest)
        return ret

    def get_questions(self):
        if self.reg.check(['questions']):
            return self.reg.list_keys(['questions'])
        return []

    def count_questions(self):
        return len(self.get_questions())

    def has_id(self, elid):
        return self.reg.check(['questions', elid])

    def get_sub_reg(self, elid, sub=['']): # pylint: disable=W0102
        if self.has_id(elid):
            return \
                evreg.Registry(root=self.reg.path(['questions', elid] + sub))
        raise \
            Exception('Ei ole lubatud valimiste identifikaator \"%s\"' % elid)

    def get_root_reg(self):
        return self.reg

    def delete_question(self, elid):
        self.reg.delete_key(['questions', elid])
        if self.count_questions() == 0:
            self.init_conf_done(False)

    def new_question(self, el_id, el_type, el_desc):
        if formatutil.is_valimiste_identifikaator(el_id):
            key = ['questions', el_id, 'common']
            self.reg.ensure_key(key)
            self.reg.create_string_value(key, ELECTION_ID, el_id)
            quest = question.Question(el_id, None, \
                evreg.Registry(root=self.reg.path(['questions', el_id])))
            g_common_keys = ['common/rights', 'common/logs']
            quest.create_keys(g_common_keys)
            quest.set_type(int(el_type))
            quest.set_descr(el_desc)
            return quest
        else:
            raise Exception('Vigase formaadiga valimiste identifikaator')

    def restore_init_status(self):
        if self.is_hes():
            self.reg.truncate_value(['common'], evcommon.APPLICATION_LOG_FILE)
            self.reg.truncate_value(['common'], evcommon.ERROR_LOG_FILE)
            self.reg.truncate_value(['common'], evcommon.VOTER_LIST_LOG_FILE)
            self.reg.truncate_value(['common'], evcommon.DEBUG_LOG_FILE)
            self.reg.ensure_no_key(['common', 'nonewvoters'])
        if self.is_hts():
            self.reg.truncate_value(['common'], evcommon.APPLICATION_LOG_FILE)
            self.reg.truncate_value(['common'], evcommon.ERROR_LOG_FILE)
            self.reg.truncate_value(['common'], evcommon.OCSP_LOG_FILE)
            self.reg.truncate_value(['common'], evcommon.STATUSREPORT_FILE)
            self.reg.truncate_value(['common'], evcommon.VOTER_LIST_LOG_FILE)
            for i in self.get_questions():
                quest = question.Question(i, 'hts', self.get_sub_reg(i))
                quest.create_log_files()
                quest.create_revlog()
                self.reg.delete_sub_keys(['questions', i, 'hts', 'votes'])
                self.reg.delete_sub_keys(['questions', i, 'hts', 'output'])
        if self.is_hlr():
            pass

    def get_election_type_str(self, el_id):
        return evcommon.G_TYPES[self.get_sub_reg(el_id)\
                .read_integer_value(['common'], 'type').value]

    def _do_flag(self, flag, do_set):
        if do_set:
            self.reg.ensure_key(flag)
        else:
            self.reg.ensure_no_key(flag)

    def is_config_bdoc_done(self):
        return self.reg.check(['common', evcommon.CONFIG_BDOC_DONE])

    def config_bdoc_done(self, done=True):
        self._do_flag(['common', evcommon.CONFIG_BDOC_DONE], done)

    def is_config_hth_done(self):
        return self.reg.check(['common', evcommon.CONFIG_HTH_DONE])

    def config_hth_done(self, done=True):
        self._do_flag(['common', evcommon.CONFIG_HTH_DONE], done)

    def is_init_conf_done(self):
        return self.reg.check(['common', evcommon.INIT_CONF_DONE])

    def init_conf_done(self, done=True):
        self._do_flag(['common', evcommon.INIT_CONF_DONE], done)

    def is_config_hsm_done(self):
        return self.reg.check(['common', evcommon.CONFIG_HSM_DONE])

    def config_hsm_done(self, done=True):
        self._do_flag(['common', evcommon.CONFIG_HSM_DONE], done)

    def is_config_hlr_input_done(self):
        for elid in self.get_questions():
            if not self.is_config_hlr_input_elid_done(elid):
                return False
        return True

    def is_config_hlr_input_elid_done(self, elid):
        return \
            self.reg.check(['questions', elid, 'common', \
                evcommon.CONFIG_HLR_INPUT_DONE])

    def config_hlr_input_elid_done(self, elid, done=True):
        self._do_flag(['questions', elid, 'common', \
            evcommon.CONFIG_HLR_INPUT_DONE], done)

    def is_config_server_done(self):
        for elid in self.get_questions():
            if not self.is_config_server_elid_done(elid):
                return False
        return True

    def is_config_server_elid_done(self, elid):
        return self.reg.check(['questions', elid, 'common', \
            evcommon.CONFIG_SERVER_DONE])

    def config_server_elid_done(self, elid, done=True):
        self._do_flag(['questions', elid, 'common', \
            evcommon.CONFIG_SERVER_DONE], done)

    def is_voters_list_disabled(self):
        return self.reg.check(['common', evcommon.VOTERS_LIST_IS_DISABLED])

    def is_hes_configured(self):
        return self.is_config_hth_done() and self.is_config_bdoc_done() and \
            self.is_config_server_done() and self.is_init_conf_done() and \
            self.is_config_mid_done()

    def is_hts_configured(self):
        return self.is_config_bdoc_done() and \
            self.is_config_server_done() and self.is_init_conf_done() and \
            self.is_config_verification_done()

    def is_hlr_configured(self):
        return self.is_config_bdoc_done() and \
            self.is_config_server_done() and self.is_config_hsm_done() and \
            self.is_init_conf_done()

    def toggle_check_voters_list(self, enable):
        self._do_flag(['common', evcommon.VOTERS_LIST_IS_DISABLED], \
            (not enable))

    def get_mid_url(self):
        return self.reg.read_string_value(['common', 'mid'], 'url').value

    def get_mid_name(self):
        return self.reg.read_string_value(['common', 'mid'], 'name').value

    def get_mid_messages(self):
        a_msg = self.reg.read_string_value(['common', 'mid'], 'auth_msg').value
        s_msg = self.reg.read_string_value(['common', 'mid'], 'sign_msg').value
        return a_msg, s_msg

    def set_mid_conf(self, url, name, auth_msg, sign_msg):
        try:
            self.reg.ensure_key(['common', 'mid'])
            self.reg.create_string_value(['common', 'mid'], 'url', url)
            self.reg.create_string_value(['common', 'mid'], 'name', name)
            self.reg.create_string_value(\
                                    ['common', 'mid'], 'auth_msg', auth_msg)
            self.reg.create_string_value(\
                                    ['common', 'mid'], 'sign_msg', sign_msg)
            self.config_mid_done()
        except:
            self.config_mid_done(False)
            raise

    def config_mid_done(self, done=True):
        self._do_flag(['common', evcommon.CONFIG_MID_DONE], done)

    def is_config_mid_done(self):
        return self.reg.check(['common', evcommon.CONFIG_MID_DONE])

    def can_vote(self, ik):
        questions = self.get_questions_obj('hes')
        for quest in questions:
            if quest.can_vote(ik):
                return True
        return False

    def refuse_new_voters(self):
        self.reg.ensure_key(['common', 'nonewvoters'])

    def allow_new_voters(self):
        return not self.reg.check(['common', 'nonewvoters'])

    def is_config_verification_done(self):
        try:
            self.get_verification_time()
            self.get_verification_count()
            return True
        except (IOError, LookupError):
            return False


if __name__ == '__main__':
    pass


# vim:set ts=4 sw=4 et fileencoding=utf8:
