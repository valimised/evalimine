#!/bin/sh

. /etc/default/evote

PATH=$PATH:/usr/share/evote:$EVREG_BIN
export EVREG_CONFIG EVREG_BIN LANG LESSSECURE LESSCHARSET \
       PATH TMPDIR EVOTE_TMPDIR

# terminali käitumine
/bin/stty susp ^@

# umask
umask $UMASK

unicode_start

exec /usr/bin/python2.7 /usr/share/evote/evui.py 
