#! /bin/sh
# Copyright: Eesti Vabariigi Valimiskomisjon
# (Estonian National Electoral Committee), www.vvk.ee
# Written in 2004-2013 by Cybernetica AS, www.cyber.ee
#
# This work is licensed under the Creative Commons
# Attribution-NonCommercial-NoDerivs 3.0 Unported License.
# To view a copy of this license, visit
# http://creativecommons.org/licenses/by-nc-nd/3.0/.

set -e

REGISTRY_DIR=/etc/evote/registry

ARGS_OK=0
while [ $# -gt 0 ]; do
	case $1 in
		common )
			INIT_COMMON=1
			ARGS_OK=1
			shift
		;;
		hes )
			INIT_HES=1
			ARGS_OK=1
			shift
		;;
		hts )
			INIT_HTS=1
			ARGS_OK=1
			shift
		;;
		*)
			ARGS_OK=0
			shift
		;;
	esac;
done;

if [ "${ARGS_OK}" = 0 ]; then
	CMDNAME=`basename $0`
	echo "Kasutamine: ${CMDNAME} [hts] [hes] [common]"
	exit 1
fi

# kataloog
if [ ! -d ${REGISTRY_DIR} ]; then
	mkdir ${REGISTRY_DIR}
	chown -R www-data:www-data ${REGISTRY_DIR}
fi

init() {
	EVREG_CONFIG=${REGISTRY_DIR}
	PYTHONPATH=/usr/share/evote/
	export EVREG_CONFIG PYTHONPATH
	su www-data -c "python2.7 -c 'import evote_testdata; evote_testdata.TestData().create_$1()'"
}

# common
if [ "${INIT_COMMON}" = 1 ]; then
	init common
fi

# hes
if [ "${INIT_HES}" = 1 ]; then
	init hes
fi

# hts
if [ "${INIT_HTS}" = 1 ]; then
	init hts
fi

# vim:set ts=4 sw=4:
