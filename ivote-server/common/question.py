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

import inputlists
import evcommon


class Question:

    def __init__(self, elid, root, reg):
        self._elid = elid
        self._reg = reg
        self._root = root

    def qname(self):
        return self._elid

    def set_type(self, qtype):
        if not qtype in evcommon.G_TYPES:
            raise Exception('Vigane hääletustüüp')
        self._reg.ensure_key(['common'])
        self._reg.create_integer_value(['common'], 'type', qtype)

    def get_type(self):
        return self._reg.read_integer_value(['common'], 'type').value

    def set_descr(self, descr):
        self._reg.create_string_value(['common'], 'description', descr)

    def choices_list(self, ed):
        return inputlists.ChoicesList(ed)

    def choices_proxy(self):
        if self._root == 'hes':
            return inputlists.ChoicesHES(self._reg)
        elif self._root == 'hts':
            return inputlists.ChoicesHTS(self._reg)
        else:
            return inputlists.ChoicesHLR(self._reg)

    def get_voter(self, ik):
        vl = None
        try:
            vl = inputlists.VotersList(self._root, self._reg)
            if not vl.has_voter(ik):
                return None
            return vl.get_voter(ik)
        finally:
            if vl is not None:
                vl.close()

    def reset_data(self):
        if self._reg.check([self._root, 'choices']):
            self._reg.reset_key([self._root, 'choices'])
        if self._reg.check([self._root, 'districts_1']):
            self._reg.delete_value([self._root], 'districts_1')
        if self._reg.check([self._root, 'districts_2']):
            self._reg.delete_value([self._root], 'districts_2')
        if self._reg.check([self._root, 'voters']):
            self._reg.reset_key([self._root, 'voters'])

    def create_keys(self, keys):
        for key in keys:
            if self._reg.check([key]):
                print 'Alamkataloog ' + key + ' on juba olemas. Jätan vahele'
            else:
                self._reg.create_key([key])
                print 'Loon alamkataloogi ' + key

    def create_revlog(self):
        self._reg.create_string_value(['common'], evcommon.REVLOG_FILE, "")
        self._reg.truncate_value(['common'], evcommon.REVLOG_FILE)
        filen = self._reg.path(['common', evcommon.REVLOG_FILE])
        header = evcommon.VERSION + '\n' + self._elid + '\n'
        out_f = file(filen, 'w')
        out_f.write(header)
        out_f.close()

    def truncate_log_file(self, lognr):
        logname = 'log%s' % lognr
        self._reg.create_string_value(['common'], logname, "")
        self._reg.truncate_value(['common'], logname)

    def can_vote(self, ik):
        return (self.get_voter(ik) is not None)

    def choices_to_voter(self, voter):
        ed = inputlists.Districts()
        ed.load(self._root, self._reg)
        rk_nimi = \
            ed.district_name(voter['ringkond_omavalitsus'], voter['ringkond'])
        ch = self.choices_proxy()
        return ch.district_choices_to_voter(voter, self._elid, rk_nimi)

# vim:set ts=4 sw=4 et fileencoding=utf8:
