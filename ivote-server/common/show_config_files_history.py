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

import sys
import evcommon
from election import Election
import ksum


def date_name(fn):
    file_date = fn[0:4] + "." + fn[4:6] + "." + fn[6:8] + " " + fn[8:10] + \
        ":" + fn[10:12] + ":" + fn[12:14]
    file_name = fn[15:]
    return file_date, file_name


def print_dgst(dgst):
    nn = 8
    chunks = [dgst[ii:ii + nn] for ii in range(0, len(dgst), nn)]
    ii = 0
    while ii < len(chunks):
        c1 = chunks[ii] if ii < len(chunks) else ''
        ii += 1
        c2 = chunks[ii] if ii < len(chunks) else ''
        ii += 1
        c3 = chunks[ii] if ii < len(chunks) else ''
        ii += 1
        c4 = chunks[ii] if ii < len(chunks) else ''
        ii += 1
        print "\t    %s %s %s %s" % (c1, c2, c3, c4)


def process_district_files(reg):
    if not reg.check([evcommon.DISTRICT_FILES]):
        print "\tJaoskondade nimekirja pole laaditud"
        return

    file_list = sorted(reg.list_keys([evcommon.DISTRICT_FILES]))
    if len(file_list) == 0:
        print "\tJaoskondade nimekirja pole laaditud"
    else:
        print "\tJaoskondade nimekiri"
        j = 1
        for ff_i in file_list:
            file_date, file_name = date_name(ff_i)
            print "\t%02d. %s - %s" % (j, file_date, file_name)
            dgst = ksum.compute(reg.path([evcommon.DISTRICT_FILES, ff_i]))
            print_dgst(dgst.upper())
            j += 1


def process_candidate_files(reg):
    if not reg.check([evcommon.CANDIDATE_FILES]):
        print "\n\tValikute nimekirja pole laaditud"
        return

    file_list = sorted(reg.list_keys([evcommon.CANDIDATE_FILES]))
    if len(file_list) == 0:
        print "\n\tValikute nimekirja pole laaditud"
    else:
        print "\n\tValikute nimekiri"
        j = 1
        for ff_i in file_list:
            file_date, file_name = date_name(ff_i)
            print "\t%02d. %s - %s" % (j, file_date, file_name)
            dgst = ksum.compute(reg.path([evcommon.CANDIDATE_FILES, ff_i]))
            print_dgst(dgst.upper())
            j += 1


def process_voters_files(reg):
    if not reg.check([evcommon.VOTERS_FILES]):
        print "\n\tValijanimekirju pole laaditud"
        return

    file_list = sorted(reg.list_keys([evcommon.VOTERS_FILES]))
    if len(file_list) == 0:
        print "\n\tValijanimekirju pole laaditud"
    else:
        print "\n\tValijanimekirjad"
        j = 1
        added_total = 0
        for ff_i in file_list:
            file_date, file_name = date_name(ff_i)
            print "\t%02d. %s - %s" % (j, file_date, file_name)
            dgst = ksum.compute(reg.path([evcommon.VOTERS_FILES, ff_i]))
            print_dgst(dgst.upper())
            j += 1

            # nimekirja kokkulugemine
            _rf = file(reg.path([evcommon.VOTERS_FILES, ff_i]), "r")
            line = _rf.readline()      # päise 1. rida
            line = _rf.readline()      # päise 2. rida
            filetype = _rf.readline()  # päise 3. rida
            added = 0
            removed = 0
            while True:
                line = _rf.readline()
                if len(line) == 0:
                    break
                fields = line.split("\t")
                if fields[2] == "lisamine":
                    added += 1
                    added_total += 1
                else:
                    removed += 1
                    added_total -= 1
            print \
                "\t    %s: " % filetype.strip().capitalize() + \
                "lisamisi %d, " % added + "eemaldamisi %d\n" % removed + \
                "\t    Kokku peale laadimist: %d\n" % added_total


def process_elid(elid):
    print "%s" % elid
    reg_i = Election().get_sub_reg(elid, [Election().get_server_str()])

    process_district_files(reg_i)
    process_candidate_files(reg_i)
    if not Election().is_hlr():
        process_voters_files(reg_i)


def main_function():

    try:
        election_ids = Election().get_questions()
        if len(election_ids) == 0:
            print "Sätteid pole laaditud"
        else:
            election_ids.sort()
            for el_i in election_ids:
                process_elid(el_i)

    except Exception as ex:
        print 'Viga valijanimekirjade uuenduste ajaloo kuvamisel: ' + str(ex)
        sys.exit(1)


if __name__ == '__main__':
    main_function()


# vim:set ts=4 sw=4 et fileencoding=utf8:
