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
import exception_msg
import hesdisp

def check_consistency():
    hes = hesdisp.HESDispatcher()
    res, msg = hes.hts_consistency_check()
    if res == evcommon.EVOTE_CONSISTENCY_YES:
        print 'HES ja HTS on kooskõlalised'
    elif res == evcommon.EVOTE_CONSISTENCY_NO:
        print 'HES ja HTS ei ole kooskõlalised'
    else:
        print 'Viga HES ja HTS kooskõlalisuse kontrollil (%s)' % msg

if __name__ == '__main__':
    #pylint: disable-msg=W0702
    try:
        check_consistency()
    except:
        sys.stderr.write('Viga HES ja HTS kooskõlalisuse kontrollil:' +
            exception_msg.trace() + '\n')
        sys.exit(1)

# vim:set ts=4 sw=4 et fileencoding=utf8:
