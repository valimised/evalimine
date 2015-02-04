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
import evcommon
import bdocconfig
import subprocess


def set_bdoc_conf(conf_dir):
    conf = bdocconfig.BDocConfig()
    conf.load(conf_dir)
    conf.save(Election().get_bdoc_conf())
    subprocess.check_call(['c_rehash', Election().get_bdoc_ca()])


def usage():
    """
    Laadib BDoc spetsiifilisi konfiguratsioonifaile.
    Sertifikaatide jaoks bdoc.conf.
    """

    if len(sys.argv) != 2:
        sys.stderr.write('Kasutamine: ' + sys.argv[0] + ' <conf_dir>\n')
        sys.exit(1)

    evcommon.checkfile(sys.argv[1])


def main_function():
    try:
        usage()
        set_bdoc_conf(sys.argv[1])
        Election().config_bdoc_done()
        print "Sertifikaatide konfiguratsiooni laadimine oli edukas."
    except SystemExit:
        sys.stderr.write('Konfiguratsiooni laadimine nurjus\n')
        sys.exit(1)
    except Exception as ex:
        Election().config_bdoc_done(False)
        sys.stderr.write('Konfiguratsiooni laadimine nurjus: %s\n' % str(ex))
        sys.exit(1)


if __name__ == '__main__':
    main_function()

# vim:set ts=4 sw=4 et fileencoding=utf8:
