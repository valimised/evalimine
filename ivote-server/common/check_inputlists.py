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

import getopt
import sys
import inputlists
import evcommon


class BufferedLog:

    # pylint: disable-msg=R0903

    def __init__(self):
        pass

    def log_error(self, msg):
        # pylint: disable-msg=R0201
        # no error
        print msg


def usage():
    sys.stderr.write('Kasutamine: ' + sys.argv[0] +
        ' -d <jaoskondade-fail> -c <valikute-fail> -v <valijate-fail>\n'
        'NB! Failid ei ole BDOC failid, vaid tekstifailid.\n')


def check_inputlists(args):

    ed = None
    ch = None
    vl = None

    dist_f = None
    choices_f = None
    voters_f = None

    try:
        opts, args = getopt.getopt(args[1:], "d:c:v:h")
    except getopt.GetoptError as err:
        print str(err)
        usage()
        sys.exit(2)

    for option, value in opts:
        if option == "-v":
            voters_f = value
            evcommon.checkfile(voters_f)
        elif option == "-c":
            choices_f = value
            evcommon.checkfile(choices_f)
        elif option == "-d":
            dist_f = value
            evcommon.checkfile(dist_f)
        elif option == "-h":
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    if (not dist_f) and (not choices_f) and (not voters_f):
        usage()
        sys.exit()

    blog = BufferedLog()

    if dist_f:
        ed = inputlists.Districts()
        ed.attach_logger(blog)
        if not ed.check_format(dist_f, 'Kontrollin jaoskondade nimekirja: '):
            print "Jaoskondade nimekiri ei vasta nõuetele"
        else:
            print "Jaoskondade nimekiri OK"

    if choices_f:
        ch = inputlists.ChoicesList(ed)
        ch.attach_logger(blog)
        if not ch.check_format(choices_f, 'Kontrollin valikute nimekirja: '):
            print "Valikute nimekiri ei vasta nõuetele"
        else:
            print "Valikute nimekiri OK"

    if voters_f:
        vl = inputlists.VotersList(None, None, ed)
        vl.attach_logger(blog)
        vl.ignore_errors()
        if not vl.check_format(voters_f, 'Kontrollin valijate nimekirja: '):
            print "Valijate nimekiri ei vasta nõuetele"
        else:
            print "Valijate nimekiri OK"


if __name__ == '__main__':
    check_inputlists(sys.argv)


# vim:set ts=4 sw=4 et fileencoding=utf8:
