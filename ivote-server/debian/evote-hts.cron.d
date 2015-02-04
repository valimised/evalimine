# OCSP kontrollija
*/5 * * * *	hts /usr/share/evote/ocsp_checker.py > /dev/null 2>&1

# monitor
* * * * *	hts /usr/share/evote/hts_monitor.py > /dev/null 2>&1

# Purges expired verification vote ID-s
2-59/5 * * * *	www-data /usr/share/evote/purge_otps.py > /dev/null 2>&1
