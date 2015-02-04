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
import subprocess
import re
import bdocconfig
import os
import tempfile
import shutil


def check_bdoc_conf(conf_dir):

    tmpdir = None

    try:
        conf = bdocconfig.BDocConfig()
        conf.load(conf_dir)

        dirname = tempfile.mkdtemp()
        conf.save(dirname)

        cacerts1 = set()
        cadir = "%s/ca" % dirname
        for root, dirs, files in os.walk(cadir):
            for el in files:
                cacerts1.add(el)

        processed = subprocess.check_output(['c_rehash', cadir])
        lines = processed.split('\n')

        cacerts2 = set()
        for line in lines:
            m = re.match(r"(.*) => (.*)", line)
            if m:
                cacerts2.add(m.group(1))

        return cacerts1.difference(cacerts2)
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir)


def usage():
    """
    Kontrollib BDoc konfiguratsiooni.
    """

    if len(sys.argv) != 2:
        sys.stderr.write('Kasutamine: ' + sys.argv[0] +
            ' <conf_dir>\n')
        sys.exit(1)

    evcommon.checkfile(sys.argv[1])


def main_function():
    try:
        usage()
        certs = check_bdoc_conf(sys.argv[1])

        if len(certs) == 0:
            print 'Konfiguratsiooni kontroll-laadimine õnnestus'
        else:
            print 'Probleemsed serdid: ', certs

    except SystemExit:
        sys.stderr.write('Konfiguratsiooni kontroll nurjus\n')
        sys.exit(1)
    except Exception as ex:
        sys.stderr.write('Konfiguratsiooni kontroll nurjus: %s\n' % str(ex))
        sys.exit(1)


if __name__ == '__main__':
    main_function()

# vim:set ts=4 sw=4 et fileencoding=utf8:
