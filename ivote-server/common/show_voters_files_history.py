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

from election import Election

def main_function():

    try:

        if Election().is_hes():
            server = 'hes'
        elif Election().is_hts():
            server = 'hts'
        else:
            raise Exception('Vigane serveri tüüp')

        election_ids = Election().get_questions()

        if len(election_ids) == 0:
            print "Valijanimekirju pole laaditud"
        else:
            election_ids.sort()
            for el_i in election_ids:
                print "%s" % el_i
                reg_i = Election().get_sub_reg(el_i, [server])
                if not reg_i.check(['voters_files']):
                    print "\tValijanimekirju pole laaditud"
                    continue

                file_list = reg_i.list_keys(['voters_files'])
                file_list.sort()
                if len(file_list) == 0:
                    print "\tValijanimekirju pole laaditud"
                else:
                    prefix_len = 8 + 1 + 14 + 1
                    j = 1
                    added_total = 0
                    for vf_i in file_list:
                        file_date = vf_i[0:4] + "." + vf_i[4:6] + \
                            "." + vf_i[6:8] + " " + vf_i[8:10] + \
                            ":" + vf_i[10:12] + ":" + vf_i[12:14]
                        file_name = vf_i[15:]
                        if len(file_name) > prefix_len:
                            file_name = file_name[prefix_len:]
                        print "\t%02d. %s - %s" % (j, file_date, file_name)
                        j += 1

                        # nimekirja kokkulugemine
                        _rf = file(reg_i.path(['voters_files', vf_i]), "r")
                        line = _rf.readline()      # päise 1. rida
                        line = _rf.readline()      # päise 2. rida
                        filetype = _rf.readline()  # päise 3. rida
                        added = 0
                        removed = 0
                        while 1:
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
                            "\t    Faili tüüp: %s\n" % filetype.strip() + \
                            "\t    Lisamisi %d, " % added + \
                                  "eemaldamisi %d\n" % removed + \
                            "\t    Kokku peale laadimist: %d" % added_total

    except Exception, ex:
        print 'Viga valijanimekirjade uuenduste ajaloo kuvamisel: ' + str(ex)
        sys.exit(1)


if __name__ == '__main__':
    main_function()


# vim:set ts=4 sw=4 et fileencoding=utf8:
