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
import os
import gdbm

import ticker
import formatutil
import evcommon

RINGKONNAD = 'districts_1'
DISTRICTS = 'districts_2'


def valiku_kood_key(arg):
    return int(arg.split('.')[1])


def valiku_kood_cmp(arg1, arg2):
    return arg1 - arg2


def input_list_error(name, lineno, etype, msg, line = None):
    lineno_txt = ''
    line_txt = ''

    if lineno != None:
        lineno_txt = ' LINENO(%d)' % lineno

    if line != None:
        line_txt = ' LINE(%s)' % line

    tmpl = '%(name)s %(error)s,%(lineno)s "%(msg)s"%(line)s'
    return tmpl % { 'name': name, 'error': etype, \
           'lineno': lineno_txt, 'msg': msg, 'line': line_txt  }

class InputList:

    def __init__(self):
        self.__ignore_errors = False
        self.__logard = None
        self.__tic = None
        self.__count = 0
        self.__elid = None
        self.__curline = None
        self.name = '<määramata>'

    def errother(self, msg):
        self._logit(
                input_list_error(
                    self.name, None,
                    'MUU VIGA', msg, self.__curline))

    def errform(self, msg):
        self._logit(
                input_list_error(
                    self.name, self.__count,
                    'FORMAAT', msg, self.__curline))

    def erruniq(self, msg):
        self._logit(
                input_list_error(
                    self.name, self.__count,
                    'UNIKAALSUS', msg, self.__curline))

    def errcons(self, msg):
        self._logit(
                input_list_error(
                    self.name, self.__count,
                    'KOOSKÕLA', msg, self.__curline))

    def attach_elid(self, elid):
        self.__elid = elid

    def ignore_errors(self):
        self.__ignore_errors = True

    def processed(self):
        return self.__count

    def dataline(self, line): # pylint: disable=W0613,R0201
        return False

    def attach_logger(self, logard):
        self.__logard = logard

    def _logit(self, err):
        #self.__elid
        #AppLog().log_error(err)
        if self.__logard:
            self.__logard.log_error(err)

    def current(self, line):
        self.__curline = None
        if line and len(line):
            self.__tic.tick(len(line))
            self.__curline = line.rstrip('\n')
            self.__count += 1
        return self.__curline

    def my_header(self, infile): # pylint: disable=W0613,R0201
        return True

    def _check_header(self, infile):

        retval = True
        line1 = self.current(infile.readline())
        if not line1 or not formatutil.is_versiooninumber(line1):
            self.errform('Versiooninumber')
            retval = False
        else:
            if evcommon.VERSION != line1:
                self.errcons('Versiooninumber pole %s' % evcommon.VERSION)
                retval = False

        line2 = self.current(infile.readline())
        if not line2 or not formatutil.is_valimiste_identifikaator(line2):
            self.errform('Valimiste identifikaator')
            retval = False
        else:
            if self.__elid != None:
                if self.__elid != line2:
                    self.errcons('Valimiste identifikaator pole %s'\
                        % self.__elid)
                    retval = False

        if not self.my_header(infile):
            retval = False

        return retval

    def checkuniq(self, line): # pylint: disable=W0613,R0201
        return False

    def _check_body(self, infile):
        retval = True

        while True:
            data = self.current(infile.readline())
            if data == None:
                break

            if self.dataline(data):
                if not self.checkuniq(data):
                    retval = False
            else:
                retval = False

            if ((not retval) and (not self.__ignore_errors)):
                return retval

        return retval

    def check_format(self, filename, msg=''):
        retval = True
        infile = None
        self.__tic = ticker.Ticker(os.stat(filename).st_size, msg)
        self.__count = 0
        self.__curline = None
        try:
            infile = open(filename, 'r')
            if not self._check_header(infile):
                retval = False
                if not self.__ignore_errors:
                    return retval
            if not self._check_body(infile):
                retval = False
            return retval
        finally:
            if not infile == None:
                infile.close()


class Districts(InputList):

    def __init__(self):
        InputList.__init__(self)
        self.name = 'Jaoskonnad/ringkonnad'
        self.district_list = {}
        self.__jsk = {}
        self.__ring = {}
        self.__ring_kov = {}

    def _check_ringkond(self, lst):
        key = '\t'.join(lst[1:3])
        value = lst[3]
        if key in self.__ring:
            self.erruniq('Lisatav ringkond olemas')
            return False
        self.__ring[key] = value
        self.__ring_kov[key] = set([])
        return True

    def _check_jaoskond(self, lst):
        key = '\t'.join(lst[1:5])
        value = (lst[5], lst[6])
        if key in self.district_list:
            self.erruniq('Lisatav valimisjaoskond ringkonnas olemas')
            return False

        # Eesti sisene jaoskonna kood on unikaalne
        key2 = '\t'.join(lst[1:3])
        if key2 in self.__jsk and not key2 == '0\t0':
            self.erruniq('Lisatav valimisjaoskond globaalselt olemas')
            return False

        ring_key = '\t'.join(lst[3:5])
        if not ring_key in self.__ring:
            self.errcons('Jaoskonda lisatakse olematusse ringkonda')
            return False

        self.__ring_kov[ring_key].add(lst[1])
        self.__jsk[key2] = 1
        self.district_list[key] = value
        return True

    def checkuniq(self, line):
        lst = line.split('\t')
        if lst[0] == 'ringkond':
            return self._check_ringkond(lst)
        return self._check_jaoskond(lst)

    def dataline(self, line):
        lst = line.split('\t')
        if lst[0] == 'ringkond':
            return self._dataline_ringkond(lst)

        elif lst[0] == 'valimisjaoskond':
            return self._dataline_jaoskond(lst)

        else:
            self.errform('Kirje tüüp')
            return False

    def _dataline_ringkond(self, lst):
        if len(lst) != 4:
            self.errform('Kirjete arv real')
            return False

        if not formatutil.is_ringkonna_number_kov_koodiga(lst[1], lst[2]):
            self.errform('Ringkonna number KOV koodiga')
            return False

        if not formatutil.is_ringkonna_nimi(lst[3]):
            self.errform('Ringkonna nimi')
            return False

        return True

    def _dataline_jaoskond(self, lst):
        if len(lst) != 7:
            self.errform('Kirjete arv real')
            return False

        if not formatutil.is_jaoskonna_number_kov_koodiga(\
                lst[1], lst[2]):
            self.errform('Valimisjaoskonna number KOV koodiga')
            return False

        if not formatutil.is_ringkonna_number_kov_koodiga(lst[3], lst[4]):
            self.errform('Ringkonna number KOV koodiga')
            return False

        if not formatutil.is_jaoskonna_nimi(lst[5]):
            self.errform('Valimisjaoskonna nimi')
            return False

        if not formatutil.is_maakonna_nimi(lst[6]):
            self.errform('Maakonna nimi')
            return False

        return True

    def create(self, root, reg):
        # Kustutame vanad ringkondade ja jaoskondade nimekirjad, kui on.
        if reg.check([root, RINGKONNAD]):
            reg.delete_value([root], RINGKONNAD)
        if reg.check([root, DISTRICTS]):
            reg.delete_value([root], DISTRICTS)

        c_ring = len(self.__ring)
        c_dist = len(self.district_list)

        r_value = ''
        for el in self.__ring:
            r_value += el + '\t' + self.__ring[el] + '\n'

        d_value = ''
        for el in self.district_list:
            d_value += el + '\t' + self.district_list[el][0] + '\t' + \
                self.district_list[el][1] + '\n'

        reg.ensure_key([root])
        reg.create_string_value([root], RINGKONNAD, r_value.strip())
        reg.create_string_value([root], DISTRICTS, d_value.strip())
        return c_ring, c_dist

    def load(self, root, reg):
        if not reg.check([root, DISTRICTS]):
            raise Exception('Ei leia valimisjaoskondade faili')

        if not reg.check([root, RINGKONNAD]):
            raise Exception('Ei leia valimisringkondade faili')

        d_data = reg.read_string_value([root], DISTRICTS).value
        r_data = reg.read_string_value([root], RINGKONNAD).value

        lines = d_data.split('\n')
        for line in lines:
            if line == '':
                continue
            lst = line.split('\t')
            self.district_list['\t'.join(lst[0:4])] = (lst[4], lst[5])

        lines = r_data.split('\n')
        for line in lines:
            if line == '':
                continue
            lst = line.split('\t')
            self.__ring['\t'.join(lst[0:2])] = lst[2]

    def has_ring(self, key):
        return ('\t'.join(key) in self.__ring)

    def has_dist(self, key):
        return ('\t'.join(key) in self.district_list)

    def is_kov_in_ring(self, key, kov):
        return kov in self.__ring_kov['\t'.join(key)]

    def district_name(self, ov_nber, s_rk_nber):
        key = [ov_nber, s_rk_nber]
        if not self.has_ring(key):
            raise Exception('Vigased andmed')
        return self.__ring['\t'.join(key)]


class ChoicesBase:

    def __init__(self, reg):
        self.reg = reg
        self.choices_key = None
        self.__sep = '_'

    def reset_choices(self):
        self.reg.reset_key(self.choices_key)

    def choice_name(self, v1, v2):
        return '%s%s%s' % (v1, self.__sep, v2)


class ChoicesHLR(ChoicesBase):

    _TEMPLATE = 'template'

    def __init__(self, reg):
        ChoicesBase.__init__(self, reg)
        self.choices_key = ['hlr', 'choices']

    def create_tree(self, chlist):

        def _distribute_by_districts():
            for _u in chlist:
                _tmp = chlist[_u].split('\t', 3)
                key = '_'.join((_tmp[3].split('\t')))
                if not key in choices_by_districts:
                    choices_by_districts[key] = []
                choices_by_districts[key].append(_tmp[0])

        choices_by_districts = {}
        _distribute_by_districts()
        alld = Districts()
        alld.load('hlr', self.reg)

        ticker_ = ticker.Ticker(len(alld.district_list),
                'Paigaldan valikuid: ')

        for dist in alld.district_list:
            d_lst = dist.split('\t')
            district = self.choice_name(d_lst[0], d_lst[1])
            ringkond = self.choice_name(d_lst[2], d_lst[3])
            if not ringkond in choices_by_districts:
                choices_by_districts[ringkond] = []
            self._create_district(d_lst[2], ringkond, district, choices_by_districts[ringkond])
            ticker_.tick()


    def _create_district(self, ringkond_code, ringkond, district, choices):
        ringkond_key = self.choices_key + [ringkond]
        district_key = self.choices_key + [ringkond, district]
        self.reg.ensure_key(ringkond_key)
        self.reg.ensure_key(district_key)
        self.reg.create_integer_value(district_key, ringkond_code + '.kehtetu', 0)
        for choice in choices:
            self.reg.create_integer_value(district_key, choice, 0)



class ChoicesHES(ChoicesBase):

    def __init__(self, reg):
        ChoicesBase.__init__(self, reg)
        self.choices_key = ['hes', 'choices']

    def district_choices_to_voter(self, voter, quest, distr_name):
        choi_list = self.district_choices(\
            voter['ringkond_omavalitsus'], voter['ringkond'])
        res = ''
        for elem in choi_list:
            res = res + \
                '\t'.join([quest, voter['ringkond'], distr_name, elem]) + '\n'
        return res

    def district_choices(self, v1, v2):
        sub = self.choice_name(v1, v2)
        return \
            self.reg.read_string_value(self.choices_key, sub).value.split('\n')

    def _add_choice(self, dist, choi, sorting_order):
        sub = self.choice_name(dist[0], dist[1])
        data = ''
        for el in sorting_order:
            data += el + '\t' + choi[el][0] + '\t' + choi[el][1] + '\n'
        self.reg.create_string_value(self.choices_key, sub, data.rstrip('\n'))

    def create_tree(self, chlist):

        def _distribute_by_districts():
            for _u in chlist:
                _tmp = chlist[_u].split('\t', 3)
                if not _tmp[3] in districts:
                    districts[_tmp[3]] = {}
                districts[_tmp[3]][_tmp[0]] = _tmp[1:3]

        districts = {}
        _distribute_by_districts()
        sorted_choices = []
        for el in districts:
            sorted_choices = districts[el].keys()
            sorted_choices.sort(valiku_kood_cmp, valiku_kood_key)
            self._add_choice(el.split('\t'), districts[el], sorted_choices)


class ChoicesHTS(ChoicesHES):

    def __init__(self, reg):
        ChoicesHES.__init__(self, reg)
        self.choices_key = ["hts", "choices"]


class ChoicesList(InputList):

    def __init__(self, jsk=None):
        InputList.__init__(self)
        self.name = 'Valikute nimekiri'
        self.uniq = {}
        self.jsk = jsk

    def checkuniq(self, line):
        lst = line.split('\t')
        key = lst[0]
        if key in self.uniq:
            self.erruniq('Lisatav valik juba olemas')
            return False
        self.uniq[key] = line
        return True

    def dataline(self, line):
        lst = line.split('\t')
        return self._dataline_form(lst) and self._dataline_cons(lst)

    def _dataline_form(self, lst):
        if not len(lst) == 5:
            self.errform('Kirjete arv real')
            return False

        if not formatutil.is_valiku_kood(lst[0]):
            self.errform('Valiku kood')
            return False

        if not formatutil.is_valiku_nimi(lst[1]):
            self.errform('Valiku nimi')
            return False

        if not formatutil.is_valimisnimekirja_nimi(lst[2]):
            self.errform('Valimisnimekirja nimi')
            return False

        if not formatutil.is_ringkonna_number_kov_koodiga(lst[3], lst[4]):
            self.errform('Ringkonna number KOV koodiga')
            return False

        return True

    def _dataline_cons(self, lst):
        if not (lst[0].split('.')[0] == lst[3]):
            self.errcons('Ringkonna KOV kood')
            return False

        if self.jsk:
            ring = [lst[3], lst[4]]
            if not self.jsk.has_ring(ring):
                self.errcons('Olematu ringkond')
                return False
            kov = lst[0].split('.')[0]
            if (not kov == '0') and (not self.jsk.is_kov_in_ring(ring, kov)):
                self.errcons('KOV vales ringkonnas')
                return False
        return True

    def create(self, adder, msg=''): # pylint: disable=W0613
        adder.reset_choices()
        c_choice = len(self.uniq)
        adder.create_tree(self.uniq)
        return c_choice


class EPChoicesHES(ChoicesBase):

    def __init__(self, reg):
        ChoicesBase.__init__(self, reg)
        self.choices_key = ['hes', 'choices']

    def district_choices_to_voter(self, voter, quest, distr_name):
        choi_list = \
            self.district_choices(\
                voter['ringkond_omavalitsus'], voter['ringkond'])
        res = ''
        for elem in choi_list:
            choice = elem.split('\t')
            if choice[0] == 'valik':
                res = res + \
                    '\t'.join([quest, voter['ringkond'], \
                        distr_name, choice[1], choice[2]]) + '\n'
            else:
                res = res + '\t'.join([quest, '', choice[2], choice[1]]) + '\n'
        return res

    def district_choices(self, v1, v2):
        sub = self.choice_name(v1, v2)
        return \
            self.reg.read_string_value(self.choices_key, sub).value.split('\n')

    def _add_choice(self, dist, choi, sorting_order):
        sub = self.choice_name(dist[0], dist[1])
        data = ''
        for el in sorting_order:
            data += choi[el]['valik'] + '\n'
            for kand in choi[el]['kandidaadid']:
                data += kand + '\n'
        self.reg.create_string_value(self.choices_key, sub, data.rstrip())

    def create_tree(self, chlist):

        def _distribute_by_districts():
            for _u in chlist:
                _tmp = chlist[_u]['valik'].split('\t', 3)
                if not _tmp[3] in districts:
                    districts[_tmp[3]] = {}
                districts[_tmp[3]][_u] = chlist[_u]

        districts = {}
        _distribute_by_districts()
        sorted_choices = []
        for el in districts:
            sorted_choices = districts[el].keys()
            sorted_choices.sort(valiku_kood_cmp, valiku_kood_key)
            self._add_choice(el.split('\t'), districts[el], sorted_choices)


class EPChoicesHTS(EPChoicesHES):

    def __init__(self, reg):
        EPChoicesHES.__init__(self, reg)
        self.choices_key = ["hts", "choices"]


class EPChoicesHLR(ChoicesBase):

    def __init__(self, reg):
        ChoicesBase.__init__(self, reg)
        self.choices_key = ['hlr', 'choices']

    def create_tree(self, chlist):
        for el in chlist:
            choice = chlist[el]['valik'].split('\t', 3)
            self._add_choice(choice[1], choice[3].split('\t'))

    def _add_choice(self, valiku_kood, ringkond):
        sub = self.choice_name(ringkond[0], ringkond[1])
        key = self.choices_key + [sub]
        if self.reg.ensure_key(key):
            self.reg.create_integer_value(key, ringkond[0] + '.kehtetu', 0)
        self.reg.create_integer_value(key, valiku_kood, 0)


class EPChoicesList(InputList):

    def __init__(self, jsk=None):
        InputList.__init__(self)
        self.name = 'EP valikute nimekiri'
        self.uniq = {}
        self.jsk = jsk

    def checkuniq(self, line):
        lst = line.split('\t')
        key = lst[1]
        if lst[0] == 'valik':
            if key in self.uniq:
                self.erruniq('Lisatav valik juba olemas')
                return False
            self.uniq[key] = {'valik': line, 'kandidaadid': []}
        else:
            if key in self.uniq:
                self.uniq[key]['kandidaadid'].append(line)
            else:
                self.errcons('Puudub kandidaadile vastav valik')
                return False
        return True

    def dataline(self, line):
        lst = line.split('\t')
        if lst[0] == 'valik':
            return self._dataline_valik(lst)

        elif lst[0] == 'kandidaat':
            return self._dataline_kandidaat(lst)

        else:
            self.errform('Kirje tüüp')
            return False

    def _dataline_valik(self, lst):
        if len(lst) != 5:
            self.errform('Kirjete arv real')
            return False

        if not formatutil.is_valiku_kood(lst[1]):
            self.errform('Valiku kood')
            return False

        if not formatutil.is_valiku_nimi(lst[2]):
            self.errform('Valiku nimi')
            return False

        if not formatutil.is_ringkonna_number_kov_koodiga(lst[3], lst[4]):
            self.errform('Ringkonna number KOV koodiga')
            return False

        if self.jsk:
            if not self.jsk.has_ring([lst[3], lst[4]]):
                self.errcons('Olematu ringkond')
                return False

        return True

    def _dataline_kandidaat(self, lst):
        if len(lst) != 3:
            self.errform('Kirjete arv real')
            return False

        if not formatutil.is_valiku_kood(lst[1]):
            self.errform('Valiku kood')
            return False

        if not formatutil.is_valiku_nimi(lst[2]):
            self.errform('Kandidaadi nimi')
            return False

        return True

    def create(self, adder, msg=''): # pylint: disable=W0613
        adder.reset_choices()
        c_choice = len(self.uniq)
        adder.create_tree(self.uniq)
        return c_choice


class VotersList(InputList):

    def __init__(self, root, reg, jsk=None):
        InputList.__init__(self)
        self.name = 'Valijate nimekiri'
        self.reg = reg
        self.__rdbi = {}
        self.__add = {}
        self.__del = {}
        self.algne = False
        self.voterskey = [root, 'voters']
        self.jsk = jsk

    def close(self):
        for el in self.__rdbi:
            self.__rdbi[el].close()
        self.__rdbi = {}

    def dataline(self, line):
        lst = line.split('\t')
        return self._dataline_form(lst) and self._dataline_cons(lst)

    def _dataline_form(self, lst): # pylint: disable=R0911
        if len(lst) != 9:
            self.errform('Kirjete arv real')
            return False

        if not formatutil.is_isikukood(lst[0]):
            self.errform('Isikukood')
            return False

        if not formatutil.is_nimi(lst[1]):
            self.errform('Valija nimi')
            return False

        if not lst[2] in ['lisamine', 'kustutamine']:
            self.errform('Kirje tüüp')
            return False

        if not formatutil.is_jaoskonna_number_kov_koodiga(\
                lst[3], lst[4]):
            self.errform('Valimisjaoskonna number KOV koodiga')
            return False

        if not formatutil.is_ringkonna_number_kov_koodiga(lst[5], lst[6]):
            self.errform('Ringkonna number KOV koodiga')
            return False

        if not formatutil.is_rea_number_voi_tyhi(lst[7]):
            self.errform('Rea number')
            return False

        return True

    def _dataline_cons(self, lst):
        if lst[2] == 'lisamine' and lst[8] != '':
            self.errcons('Lisamiskirjel on põhjus')
            return False

        if self.algne:
            if not lst[2] == 'lisamine':
                self.errcons('Algne nimekiri lubab vaid lisamisi')
                return False
        else:
            if lst[2] == 'kustutamine':
                pohjused = ['tokend', 'jaoskonna vahetus', 'muu', '']
                if not lst[8] in pohjused:
                    self.errcons('Põhjus ei ole ' + str(pohjused))
                    return False

        if self.jsk != None \
            and not self.jsk.has_dist([lst[3], lst[4], lst[5], lst[6]]):
            self.errcons('Olematu jaoskond')
            return False

        return True

    def checkuniq(self, line):
        lst = line.split('\t')
        if lst[2] == 'lisamine':
            if lst[0] in self.__add:
                self.errcons('Lisatav isik olemas')
                return False
            else:
                self.__add[lst[0]] = line
        else:
            if lst[0] in self.__del:
                self.errcons('Mitmekordne eemaldamine')
                return False
            else:
                self.__del[lst[0]] = line
        return True

    def my_header(self, infile):
        data = self.current(infile.readline())
        if data == 'algne':
            self.algne = True
        elif data == 'muudatused':
            self.algne = False
        else:
            self.errform('Faili tüüp')
            return False
        return True

    def __db(self, voter_id):
        if not voter_id[10] in self.__rdbi:
            self.__rdbi[voter_id[10]] = \
                gdbm.open(self._dbname(int(voter_id[10])), 'r')
        return self.__rdbi[voter_id[10]]

    def __has_voter(self, voter_id):
        # Siin kontrollime hääletajate nimekirja kontrollimise lippu.
        # Kui lipp on tõene, siis hääletajate nimekirja ei kontrolli ning
        # lubame kõigil hääletada, vajalik VVK'le süsteemi testimiseks/demomiseks

        from election import Election
        if (Election().is_voters_list_disabled()):
            return True

        try:
            db = self.__db(voter_id)
            return db.has_key(voter_id)
        except: # pylint: disable=W0702
            return False

    def has_voter(self, voter_id):
        if not formatutil.is_isikukood(voter_id):
            return False
        return self.__has_voter(voter_id)

    def __get_dummy_voter(self, voter_id):
        id_codes = ["00000000000", "00000000001", "00000000002", \
                "00000000003", "00000000004", "00000000005", \
                "00000000006", "00000000007", "00000000008", "00000000009"]
        id_code = voter_id
        for i in id_codes:
            db = self.__db(i)
            if len(db) == 0:
                continue
            else:
                id_code = db.keys()[0]
            voter = db[id_code].split('\t')
            ret = {
                'nimi': 'XXX YYY', # pylint: disable=W0511
                'jaoskond_omavalitsus': voter[3],
                'jaoskond': voter[4],
                'ringkond_omavalitsus': voter[5],
                'ringkond': voter[6],
                'reanumber': ''}
            return ret
        return None

    def __get_voter(self, voter_id):
        db = self.__db(voter_id)
        voter = db[voter_id].split('\t')
        if len(voter) == 7:
            voter.append('')
        ret = {
                'nimi': voter[1],
                'jaoskond_omavalitsus': voter[3],
                'jaoskond': voter[4],
                'ringkond_omavalitsus': voter[5],
                'ringkond': voter[6],
                'reanumber': voter[7]}
        return ret

    def get_voter(self, voter_id):
        # Siin kontrollime hääletajate nimekirja kontrollimise lippu.
        # Kui lipp on tõene, siis hääletajate nimekirja ei kontrolli ning
        # hääletaja saab olema esimeses leitud ringkonnast.

        from election import Election
        if (Election().is_voters_list_disabled()):
            return self.__get_dummy_voter(voter_id)
        return self.__get_voter(voter_id)

    def _dbname(self, iid):
        return self.reg.path(self.voterskey + ['gdmdb%d' % iid])

    def create(self, msg=''):

        dbi = {}
        try:
            self.close()
            self.reg.ensure_key(self.voterskey)
            for i in range(0, 10):
                dbi[str(i)] = gdbm.open(self._dbname(i), 'cf')

            c_add = len(self.__add)
            c_del = len(self.__del)

            _t = ticker.Ticker(c_add + c_del, msg)

            for el in self.__del:
                db = dbi[el[10]]
                del db[el]
                _t.tick()

            for el in self.__add:
                line = self.__add[el]
                db = dbi[el[10]]
                db[el] = line
                _t.tick()

            return c_add, c_del

        finally:
            print 'Sulgen baase'
            for el in dbi:
                dbi[el].close()
                print '.',
                sys.stdout.flush()
            print

    # Hetkel on tokend püsiv, s.t kui me lisame vaikeväärtusele midagi
    # (mida me ka teeme), siis on need muudatused ka järgmisel
    # vaikeväärtuse kasutusel alles.
    def check_muudatus(self, msg, el_on, tokend):
        """Kontrollib sisendandmete vastuolulisust valijate nimekirja
        muutmise korral. Andmed on vastuolulised järgmistel juhtudel:
        1. lisatav kasutaja on nimekirjas olemas
        2. kustutatavat kasutajat pole nimekirjas

        Kõik ebasobivad kirjed korjatakse self.__add ja self.__del
        listidest ära, sest kontroll tehakse lõpuni.
        """

        retval = True
        if self.algne:
            retval = False
            self.errother('Valijate nimekirja tüüp peab olema "muudatused"')

        _t = ticker.Ticker(len(self.__add) + len(self.__del), msg)

        tmp_del = self.__del.copy()
        tmp_add = self.__add.copy()

        for el in tmp_del:
            line = tmp_del[el]
            if not self.__has_voter(el):
                retval = False
                self.errother(
                    'Kustutatavat isikut %s pole valijate nimekirjas' % el)
                del self.__del[el]
            else:
                if el_on:
                    # hääletusperioodi ajal omab tähendust tõkend
                    _v = line.split('\t')
                    if _v[8] == 'tokend':
                        tokend[_v[0]] = [_v[1], _v[3], _v[4], _v[5], _v[6]]
            _t.tick()

        for el in tmp_add:
            line = tmp_add[el]
            if self.__has_voter(el) and not el in self.__del:
                retval = False
                self.errother(
                    'Lisatav isik %s on juba valijate nimekirjas' % el)
                del self.__add[el]

            _t.tick()

        return retval


if __name__ == '__main__':

    print 'No main'

# vim:set ts=4 sw=4 et fileencoding=utf8:
