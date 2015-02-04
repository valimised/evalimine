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

import os
import sys
import subprocess


def usage():
    print 'Kasutamine:'
    print '    %s <repo> <deb directory> <i386|amd64>' % sys.argv[0]
    print 'Tulemus - <repo>.iso ja kataloogis <repo> debiani repositoorium'
    print 'HOIATUS: kustutab esimese sammuna kataloogi <repo>'
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        usage()

    if not sys.argv[3] in ['i386', 'amd64']:
        usage()

    repo = sys.argv[1].rstrip('/')
    debs = sys.argv[2]
    platform = sys.argv[3]
    binpath = 'dists/wheezy/evote/binary-%s' % platform
    fullrepo = '%s/%s' % (repo, binpath)

    print 'Kustutan vana repositooriumi (%s)' % repo
    subprocess.call('rm -rf %s' % repo, shell = True)

    print 'Loon uue kataloogistruktuuri (%s)' % fullrepo
    os.makedirs(fullrepo)

    print 'Kopeerin *.deb failid (%s %s)' % (debs, fullrepo)
    cmd = 'cp %s/*.deb %s' % (debs, fullrepo)
    subprocess.call(cmd, shell = True)

    print 'Lähtestan repositooriumi'
    out_f = open('%s/Packages.gz' % fullrepo, 'wb')
    p1 = subprocess.Popen(['dpkg-scanpackages', binpath, '/dev/null'],
                                        stdout = subprocess.PIPE, cwd = repo)
    p2 = subprocess.Popen(['gzip', '-9c'], stdin = p1.stdout, stdout = out_f)
    p2.communicate()
    out_f.close()

    print 'Valmendan ketta'
    os.makedirs('%s/%s' % (repo, '.disk'))
    out_f = open('%s/%s/info' % (repo, '.disk'), 'wb')
    out_f.write('E-hääletamissüsteem')
    out_f.close()
    subprocess.call('genisoimage -input-charset utf8 -r -J -o %s.iso %s' %
                                                    (repo, repo), shell = True)

# vim:set ts=4 sw=4 et fileencoding=utf8:
