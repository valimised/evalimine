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

import sys
import exception_msg
from election import Election

NOT_DEFINED_STR = "pole määratud"


def usage():
    print 'Kasutamine: ' + sys.argv[0] + ' get|(set <hts> <htspath> <htsverifypath>)'
    sys.exit(1)


def execute(ip, path, verify):
    Election().set_hts_ip(ip)
    Election().set_hts_path(path)
    Election().set_hts_verify_path(verify)
    Election().config_hth_done()


#pylint: disable-msg=W0702

def main_function():
    if len(sys.argv) < 2:
        usage()

    if sys.argv[1] == 'get' or sys.argv[1] == 'set':

        if sys.argv[1] == 'get':
            try:
                hts_ip = Election().get_hts_ip()
            except:
                hts_ip = NOT_DEFINED_STR

            try:
                hts_path = Election().get_hts_path()
            except:
                hts_path = NOT_DEFINED_STR

            try:
                hts_verify = Election().get_hts_verify_path()
            except:
                hts_verify = NOT_DEFINED_STR

            print "HTS IP: %s" % hts_ip
            print "HTS path: %s" % hts_path
            print "HTS verification path: %s" % hts_verify
        else:
            try:
                if len(sys.argv) != 5:
                    usage()
                execute(sys.argv[2], sys.argv[3], sys.argv[4])
            except:
                Election().config_hth_done(False)
                sys.stderr.write("HTSi konfigureerimine nurjus: %s\n" \
                    % exception_msg.trace())
                sys.exit(1)
    else:
        print 'Operatsioon ei ole teostatav'
        sys.exit(1)


if __name__ == '__main__':
    main_function()


# vim:set ts=4 sw=4 et fileencoding=utf8:
