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
import formatutil
import zipfile
import StringIO
import time
from operator import itemgetter


def _file2pdf(input_fn, output_fn):
    import subprocess

    error = False
    errstr = ''
    try:
        retcode = subprocess.call(\
            ["rst2pdf", "-s", "dejavu", input_fn, "-o", output_fn, "-v"])
        if retcode != 0:
            error = True
    except OSError, ose:
        error = True
        errstr += str(ose)

    if error:
        try:
            os.unlink(output_fn)
        except:
            pass

        raise Exception(retcode, errstr)



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

    def _write_atomic(self, filename, data):
        tmp_name = filename + '.partial'
        try:
            _f = open(tmp_name, 'w')
            fcntl.lockf(_f, fcntl.LOCK_EX)
            _f.write(data)
            _f.flush()
            os.fsync(_f.fileno())
            _f.close()
            os.rename(tmp_name, filename)
        except Exception, (errno, errstr):
            evlog.log_error("Faili '%s' kirjutamine nurjus" % filename)
            raise Exception(errno, errstr)

    def talleta_haal(self, **args):
        haale_rasi = ksum.votehash(args['vote'])
        user_key = htscommon.get_user_key(args['signercode'])
        self._reg.ensure_key(user_key)
        voter = args['valija']
        vote_file = htscommon.valid_votefile_name(args['timestamp'])
        user_key.append(vote_file)
        filename = self._reg.path(user_key)

        frm = evlog.EvLogFormat()
        logline = frm.logstring(
            tyyp=0,
            haal_rasi=haale_rasi,
            timestamp=args['timestamp'],
            jaoskond=voter['jaoskond'],
            jaoskond_omavalitsus=voter['jaoskond_omavalitsus'],
            ringkond=voter['ringkond'],
            ringkond_omavalitsus=voter['ringkond_omavalitsus'],
            isikukood=args['signercode'],
            nimi=voter['nimi'],
            reanumber=voter['reanumber'])

        outdata = StringIO.StringIO()
        outzip = zipfile.ZipFile(outdata, 'w')
        outzip.writestr(htscommon.ZIP_BDOCFILE, args['signedvote'])
        outzip.writestr(htscommon.ZIP_LOGFILE, logline)
        outzip.close()
        self._write_atomic(filename, outdata.getvalue())


    def get_vote_for_result(self, logline, fname):
        res = None
        try:
            elems = logline.split('\t')
            code = elems[6]
            user_key = htscommon.get_user_key(code)
            fn = self._reg.path(user_key + [fname])
            bdoc = htsbase.get_vote(fn)
            if bdoc:
                haal = bdoc.documents["%s.evote" % self._elid]
                voter = htscommon.get_logline_voter(logline)
                b64haal = base64.b64encode(haal).strip()
                res = [voter['jaoskond_omavalitsus'], voter['jaoskond'], \
                    voter['ringkond_omavalitsus'], voter['ringkond'], b64haal]
        except:
            evlog.log_exception()

        return res


    def __write_masinloetav(self, jaoskonnad):

        # sortimine:
        # Kov-jsk numbriliselt -> hääletajad ridade kaupa

        ret = 0
        kov_jsk = jaoskonnad.keys()
        kov_jsk.sort(jaoskonnad_cmp)

        of = htscommon.LoggedFile(\
            self._reg.path(\
                ['hts', 'output', evcommon.ELECTORSLIST_FILE]))
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

        tmp_path = self._reg.path(\
                ['hts', 'output', evcommon.ELECTORSLIST_FILE_TMP])

        pdf_path = self._reg.path(\
                ['hts', 'output', evcommon.ELECTORSLIST_FILE_PDF])

        outfile = htscommon.LoggedFile(tmp_path)
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

        _file2pdf(tmp_path, pdf_path)
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


    def get_log_lines(self, root, path):
        log_lines = []
        for vote_file in path:
            if htscommon.VALID_VOTE_PATTERN.match(vote_file):
                inzip = None
                lline = None
                try:
                    lname = root + '/' + vote_file
                    inzip = zipfile.ZipFile(lname, 'r')
                    lline = inzip.read(htscommon.ZIP_LOGFILE)
                except:
                    lline = None
                    evlog.log_error("Viga hääle käitlemisel: " + lname)
                    evlog.log_exception()

                if inzip:
                    inzip.close()

                if lline:
                    log_lines.append((lline, vote_file))

        return log_lines


    def tyhistusperioodi(self):

        vc_valid = 0
        vc_autor = 0

        jaoskonnad = {}
        jaoskonnad_rev = {}
        self.__load_jaoskonnad(jaoskonnad, jaoskonnad_rev)
        tic = ticker.Counter(\
            'Hääli:', '\tArvesse minevaid: %d\tKorduvaid: %d')
        tic.start('Koostan e-hääletanute nimekirja:')

        for path in os.walk(self._reg.path(['hts', 'votes'])):
            root = path[0]
            code = root.split('/').pop()

            if not formatutil.is_isikukood(code):
                continue

            log_lines = self.get_log_lines(root, path[2])

            if len(log_lines) > 0:
                log_lines.sort(key=itemgetter(0))
                latest = log_lines.pop()
                vc_autor += len(log_lines)
                vc_valid += 1

                voter = htscommon.get_logline_voter(latest[0])
                jaoskonnad_rev['%s\t%s\t%s\t%s' % (\
                    voter['jaoskond_omavalitsus'], \
                    voter['jaoskond'], voter['ringkond_omavalitsus'], \
                    voter['ringkond'])].append(voter)

            tic.tick(1, vc_valid, vc_autor)

        tic.finish()

        valijaid1 = self.__write_masinloetav(jaoskonnad_rev)
        valijaid2 = self.__write_inimloetav(jaoskonnad)
        if not (valijaid1 == valijaid2):
            self._errmsg = 'Viga nimekirjade koostamisel'
            raise Exception(self._errmsg)

        return vc_valid + vc_autor, vc_autor, valijaid1


    def lugemisperioodi(self):

        r_votes = 0
        v_votes = 0
        a_votes = 0
        b_votes = 0

        self._reg.ensure_no_key(\
            ['hts', 'output', evcommon.ELECTIONS_RESULT_FILE])

        vf = htscommon.LoggedFile(\
            self._reg.path(\
                ['hts', 'output', evcommon.ELECTIONS_RESULT_FILE]))
        vf.open('a')
        vf.write(evcommon.VERSION + "\n")
        vf.write(self._elid + "\n")

        l1_lines = []
        l2_lines = []
        l3_lines = []

        tic = ticker.Counter(\
            'Hääli:', '\tKehtivaid: %d\tAvalduse alusel tühistatuid: %d')
        tic.start('Koostan loendamisele minevate häälte nimekirja')

        nowstr = time.strftime("%Y%m%d%H%M%S")

        for path in os.walk(self._reg.path(['hts', 'votes'])):
            root = path[0]
            code = root.split('/').pop()

            if not formatutil.is_isikukood(code):
                continue

            log_lines = self.get_log_lines(root, path[2])

            if len(log_lines) > 0:
                log_lines.sort(key=itemgetter(0), reverse=True)
                new = None
                for lines in log_lines:
                    old = lines[0].rsplit('\t', 2)[0]
                    notime = old.split('\t', 1)[1]
                    fn = lines[1]
                    voteforres = self.get_vote_for_result(old, fn)
                    if voteforres:
                        l1_lines.append(old)
                        if new == None:
                            ur, reason, tim = self.is_user_revoked(code)
                            if ur:
                                l2_lines.append("%s\t%s\t%s" % (tim, notime, reason))
                                r_votes += 1
                            else:
                                vf.write('\t'.join(voteforres) + '\n')
                                v_votes += 1
                                l3_lines.append("%s\t%s" % (nowstr, notime))
                        else:
                            autor = new.split('\t')
                            l2_lines.append("%s\t%s\tkorduv e-hääl: %s" % \
                                    (autor[0], notime, autor[1]))
                            a_votes += 1
                        new = old
                    else:
                        b_votes += 1

                tic.tick(1, v_votes, r_votes)

        vf.close()
        ksum.store(vf.name())
        tic.finish()

        l1_lines.sort()
        self.save_log(l1_lines, '1')
        l2_lines.sort()
        self.save_log(l2_lines, '2')
        l3_lines.sort()
        self.save_log(l3_lines, '3')
        return v_votes, r_votes, a_votes, b_votes


    def load_revoke(self, input_list, operator):
        good_list = []
        bad_list = []
        for el in input_list:
            code = el[0]
            if not self.haaletanud(code):
                bad_list.append(el)
                evlog.log_error('Isik koodiga %s ei ole hääletanud' % code)
                continue

            revoked, reason, _ = self.is_user_revoked(code)
            if revoked:
                bad_list.append(el)
                evlog.log_error(\
                    'Kasutaja isikukoodiga %s hääl on juba tühistatud' % code)
            else:
                # vajalik lugemisele minevate häälte nimistu koostamiseks
                self.revoke_vote(el, operator)
                good_list.append(el)

        return good_list, bad_list


    def load_restore(self, input_list, operator):
        good_list = []
        bad_list = []
        for el in input_list:
            code = el[0]
            if not self.haaletanud(code):
                bad_list.append(el)
                evlog.log_error('Isik koodiga %s ei ole hääletanud' % code)
                continue

            revoked, reason, _ = self.is_user_revoked(code)
            if (not revoked):
                bad_list.append(el)
                evlog.log_error(\
                    'Isik koodiga %s ei ole oma häält tühistanud' % code)
                continue
            else:
                self.restore_vote(el, operator)
                good_list.append(el)

        return good_list, bad_list


if __name__ == '__main__':
    print "No main"

# vim:set ts=4 sw=4 et fileencoding=utf8:
