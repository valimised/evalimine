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

import bdocpythonutils
import ksum
import ticker
import os
import htscommon
import base64
import inputlists
import fcntl
import evcommon
import htsbase
import evlog

def jaoskonnad_cmp(jsk1, jsk2):
    list1 = jsk1.split('\t')
    list2 = jsk2.split('\t')
    for i in range(4):
        i1 = int(list1[i])
        i2 = int(list2[i])
        if (i1 != i2):
            return i1 - i2
    return 0

def reanumber_cmp(el1, el2):

    has_el1 = False
    has_el2 = False

    int_el1 = 0
    int_el2 = 0

    try:
        int_el1 = int(el1['reanumber'])
        has_el1 = True
    except:
        has_el1 = False

    try:
        int_el2 = int(el2['reanumber'])
        has_el2 = True
    except:
        has_el2 = False

    if has_el1:
        if has_el2:
            return int_el1 - int_el2
        else:
            return -1
    else:
        if has_el2:
            return 1
        else:
            return 0

    return 0


class HTS(htsbase.HTSBase):

    def __init__(self, elid):
        htsbase.HTSBase.__init__(self, elid)

    def talleta_haal(self, **args):

        # Hääle tühistamisel on põhjuseks
        # tühistamise põhjustanud hääle räsi
        haale_rasi = ksum.votehash(args['vote'])
        self.__tyhista_korduv_haal(args['signercode'], haale_rasi)
        user_key = htscommon.get_user_key(args['signercode'])
        self._reg.ensure_key(user_key)
        voter = args['valija']
        vote_file = htscommon.valid_votefile_name(args['timestamp'], voter)
        user_key.append(vote_file)
        filename = self._reg.path(user_key)

        try:
            _f = file(filename, 'w')
            fcntl.lockf(_f, fcntl.LOCK_EX)
            _f.write(args['signedvote'])
            _f.flush()
            _f.close()
        except Exception, (errno, errstr):
            evlog.log_error("Faili '%s' kirjutamine nurjus" % filename)
            raise Exception(errno, errstr)

        self._log1.log_info(
            tyyp=1,
            haal_rasi=haale_rasi,
            jaoskond=voter['jaoskond'],
            jaoskond_omavalitsus=voter['jaoskond_omavalitsus'],
            ringkond=voter['ringkond'],
            ringkond_omavalitsus=voter['ringkond_omavalitsus'],
            isikukood=args['signercode'])

    def __tyhista_korduv_haal(self, code, haale_rasi):

        user_key = htscommon.get_user_key(code)
        if not self._reg.check(user_key):
            return

        flist = self._reg.list_keys(user_key)
        for elem in flist:
            if htscommon.VALID_VOTE_PATTERN.match(elem):
                rev_name = htscommon.change_votefile_name(\
                    elem, htscommon.BAUTOREVOKED)
                old_name = self._reg.path(user_key + [elem])
                new_name = self._reg.path(user_key + [rev_name])

                bdoc = bdocpythonutils.BDocContainer()
                bdoc.load(old_name)
                profile = bdocpythonutils.ManifestProfile('TM')
                bdoc.validate(profile)

                vote = bdoc.documents["%s.evote" % self._elid]
                voter = htscommon.get_votefile_voter(elem)
                vote_time = htscommon.get_votefile_time(elem)

                # logimine
                self._log2.log_info(
                    tyyp=2,
                    haal_rasi=ksum.votehash(vote),
                    jaoskond=voter['jaoskond'],
                    jaoskond_omavalitsus=voter['jaoskond_omavalitsus'],
                    ringkond=voter['ringkond'],
                    ringkond_omavalitsus=voter['ringkond_omavalitsus'],
                    isikukood=code,
                    pohjus='korduv e-hääl: ' + haale_rasi)
                self._revlog.log_info(
                    tegevus='korduv e-hääl',
                    isikukood=code,
                    nimi=voter['nimi'],
                    timestamp=vote_time,
                    operaator='',
                    pohjus=haale_rasi)

                os.rename(old_name, new_name)

    def talletaja(self, ik):
        vl = None
        try:
            vl = inputlists.VotersList('hts', self._reg)
            if not vl.has_voter(ik):
                return None
            ret = vl.get_voter(ik)
            return ret
        finally:
            if vl != None:
                vl.close()
                vl = None

    def __write_masinloetav(self, jaoskonnad):

        # sortimine:
        # Kov-jsk numbriliselt -> hääletajad ridade kaupa

        ret = 0
        kov_jsk = jaoskonnad.keys()
        kov_jsk.sort(jaoskonnad_cmp)

        of = htscommon.LoggedFile(\
            self._reg.path(\
                ['hts', 'output', evcommon.ELECTORSLIST_FILE]), self)
        of.open('w')
        of.write(evcommon.VERSION + "\n")
        of.write(self._elid + "\n")

        for jsk in kov_jsk:
            if (len(jaoskonnad[jsk])):
                jaoskonnad[jsk].sort(reanumber_cmp)
                for voter in jaoskonnad[jsk]:
                    outline = '%s\t%s\t%s\t%s\t%s\n' % (
                                voter['jaoskond_omavalitsus'],
                                voter['jaoskond'],
                                voter['reanumber'],
                                voter['isikukood'],
                                voter['nimi'])
                    of.write(outline)
                    ret = ret + 1

        of.close()
        ksum.store(of.name())
        return ret

    def __write_inimloetav(self, jaoskonnad):

        # sortimine:
        #  Maakond -> Vald -> Kov-jsk numbriliselt -> hääletajad ridade kaupa

        ret = 0
        outfile = htscommon.LoggedFile(\
            self._reg.path(\
                ['hts', 'output', evcommon.ELECTORSLIST_FILE_TMP]), self)
        outfile.open('w')

        # ReStructuredText jalus leheküljenumbritega
        outfile.write(".. footer::\n\tLk ###Page###\n\n")

        description = ''
        try:
            description = \
                self._reg.read_string_value(['common'], 'description').value
        except:
            description = self._elid

        maakonnad = jaoskonnad.keys()
        import locale
        try:
            locale.setlocale(locale.LC_COLLATE, 'et_EE.UTF-8')
            maakonnad.sort(locale.strcoll)
        except:
            maakonnad.sort()

        dot_line = "---------------------------------------" + \
                   "--------------------------------------"
        for mk in maakonnad:
            vallad = jaoskonnad[mk].keys()
            vallad.sort(locale.strcoll)
            for vald in vallad:
                kov_jsk = jaoskonnad[mk][vald].keys()
                kov_jsk.sort(jaoskonnad_cmp)
                for jsk in kov_jsk:
                    outfile.write('E-hääletanute nimekiri\n\n')
                    outfile.write('%s\n\n' % description)
                    outfile.write('%s\n\n' % jaoskonnad[mk][vald][jsk][0])
                    outfile.write('| %s\n| %-15s%-16s%s\n| %s\n\n' % \
                        (dot_line, 'Nr val nimek', \
                        'Isikukood', 'Nimi', dot_line))

                    if (len(jaoskonnad[mk][vald][jsk][1])):
                        jaoskonnad[mk][vald][jsk][1].sort(reanumber_cmp)
                        for voter in jaoskonnad[mk][vald][jsk][1]:
                            outline = '| %-15s%-16s%s\n' % (
                                voter['reanumber'],
                                voter['isikukood'],
                                voter['nimi'])
                            outfile.write(outline)
                            ret = ret + 1
                    else:
                        outfile.write(\
                            '<<< Jaoskonnas pole ühtegi e-häält >>>\n')
                    outfile.write('\n.. raw:: pdf\n\n\tPageBreak\n\n')

        outfile.close()
        return ret

    def __load_jaoskonnad(self, jsk, jsk_rev):
        dist = inputlists.Districts()
        dist.load(evcommon.APPTYPE_HTS, self._reg)
        # jaoskonnad = {
        #   'maakonna nimi': {
        #      'vald': {
        #         kov-jsk: ['jaoskonna string', [hääletajate list]]
        #       }
        #     }
        #   }
        #
        # jaoskonnad_rev viitab otse jaoskondadele

        for i in dist.district_list:

            split_district = dist.district_list[i][0].rsplit(',', 1)

            mk = dist.district_list[i][1]
            jsk_nr = '\t'.join(i.split('\t')[0:2])
            if jsk_nr == '0\t0':
                mk = 'ZZZ'

            if not  mk in jsk:
                jsk[mk] = {}

            vald = split_district[0]
            if mk == 'ZZZ':
                vald = 'ZZZ'

            if not vald in jsk[mk]:
                jsk[mk][vald] = {}

            if not i in jsk[mk][vald]:
                jsk[mk][vald][i] = [dist.district_list[i][0], []]
            else:
                self._errmsg = 'Viga andmestruktuurides (%s)' % jsk_nr
                raise Exception(self._errmsg)

            jsk_rev[i] = jsk[mk][vald][i][1]


    def tyhistusperioodi(self):

        pc_cache = {}
        vc = htscommon.VoteCounter()
        self._log1.cache(pc_cache, 'isikukood')
        jaoskonnad = {}
        jaoskonnad_rev = {}
        self.__load_jaoskonnad(jaoskonnad, jaoskonnad_rev)
        tic = ticker.Counter(\
            'Hääli:', '\tArvesse minevaid: %d\tKorduvaid: %d')
        tic.start('Koostan e-hääletanute nimekirja:')
        for path in os.walk(self._reg.path(['hts', 'votes'])):
            root = path[0]
            for vote_file in path[2]:
                if htscommon.VALID_VOTE_PATTERN.match(vote_file):
                    code = root.split('/').pop()
                    if not code in pc_cache:
                        self._errmsg = \
                            "Serveri andmestruktuurid ei ole kooskõlalised"
                        raise Exception(self._errmsg)

                    voter = htscommon.get_votefile_voter(vote_file)
                    voter['isikukood'] = code
                    jaoskonnad_rev['%s\t%s\t%s\t%s' % (\
                        voter['jaoskond_omavalitsus'], \
                        voter['jaoskond'], voter['ringkond_omavalitsus'], \
                        voter['ringkond'])].append(voter)
                    vc.inc_valid()
                elif htscommon.AUTOREVOKED_VOTE_PATTERN.match(vote_file):
                    vc.inc_autorevoked()
                else:
                    vc.inc_unknown()
                tic.tick(1, vc.valid(), vc.autorevoked())

        tic.finish()

        valijaid1 = self.__write_masinloetav(jaoskonnad_rev)
        valijaid2 = self.__write_inimloetav(jaoskonnad)
        if not (valijaid1 == valijaid2):
            self._errmsg = 'Viga nimekirjade koostamisel'
            raise Exception(self._errmsg)

        return vc.valid() + vc.autorevoked(), vc.autorevoked(), valijaid1

    def __handle_userrevoked(self, root, vote_file):

        code = root.split('/').pop()
        user_key = htscommon.get_user_key(code)

        fn = self._reg.path(user_key + [vote_file])

        bdoc = bdocpythonutils.BDocContainer()
        bdoc.load(fn)
        profile = bdocpythonutils.ManifestProfile('TM')
        bdoc.validate(profile)
        haal = bdoc.documents["%s.evote" % self._elid]

        voter = htscommon.get_votefile_voter(vote_file)
        pohjus = self._reg.read_string_value(user_key, 'reason').value
        self._log2.log_info(
            tyyp=2,
            haal_rasi=ksum.votehash(haal),
            jaoskond=voter['jaoskond'],
            jaoskond_omavalitsus=voter['jaoskond_omavalitsus'],
            ringkond=voter['ringkond'],
            ringkond_omavalitsus=voter['ringkond_omavalitsus'],
            isikukood=code,
            pohjus=pohjus)

    def __handle_valid(self, root, vote_file):

        code = root.split('/').pop()
        user_key = htscommon.get_user_key(code)
        fn = self._reg.path(user_key + [vote_file])

        bdoc = bdocpythonutils.BDocContainer()
        bdoc.load(fn)
        profile = bdocpythonutils.ManifestProfile('TM')
        bdoc.validate(profile)
        haal = bdoc.documents["%s.evote" % self._elid]

        voter = htscommon.get_votefile_voter(vote_file)
        b64haal = base64.b64encode(haal).strip()

        self._log3.log_info(
            tyyp=3,
            haal_rasi=ksum.votehash(haal),
            jaoskond=voter['jaoskond'],
            jaoskond_omavalitsus=voter['jaoskond_omavalitsus'],
            ringkond=voter['ringkond'],
            ringkond_omavalitsus=voter['ringkond_omavalitsus'],
            isikukood=code)

        return [voter['jaoskond_omavalitsus'], voter['jaoskond'],
            voter['ringkond_omavalitsus'], voter['ringkond'], b64haal]

    def lugemisperioodi(self):

        r_votes = 0
        v_votes = 0

        self._reg.ensure_no_key(\
            ['hts', 'output', evcommon.ELECTIONS_RESULT_FILE])

        vf = htscommon.LoggedFile(\
            self._reg.path(\
                ['hts', 'output', evcommon.ELECTIONS_RESULT_FILE]), self)
        vf.open('a')
        vf.write(evcommon.VERSION + "\n")
        vf.write(self._elid + "\n")

        tic = ticker.Counter(\
            'Hääli:', '\tKehtivaid: %d\tAvalduse alusel tühistatuid: %d')
        tic.start('Koostan loendamisele minevate häälte nimekirja')
        for path in os.walk(self._reg.path(['hts', 'votes'])):
            root = path[0]
            for vote_file in path[2]:
                if htscommon.VALID_VOTE_PATTERN.match(vote_file):
                    v_votes += 1
                    res = self.__handle_valid(root, vote_file)
                    vf.write('\t'.join(res) + '\n')
                elif htscommon.USERREVOKED_VOTE_PATTERN.match(vote_file):
                    r_votes += 1
                    self.__handle_userrevoked(root, vote_file)
                elif htscommon.AUTOREVOKED_VOTE_PATTERN.match(vote_file):
                    pass
                elif htscommon.REVOKE_REASON_PATTERN.match(vote_file):
                    pass
                else:
                    pass

                tic.tick(1, v_votes, r_votes)

        tic.finish()
        vf.close()
        ksum.store(vf.name())
        return v_votes, r_votes


if __name__ == '__main__':
    print "No main"

# vim:set ts=4 sw=4 et fileencoding=utf8:
