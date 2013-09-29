# OCSP kontrollija
*/5 * * * *	www-data /usr/share/evote/ocsp_checker.py

# monitor
*/1 * * * *	hts /usr/share/evote/hts_monitor.py

# Purges expired verification vote ID-s
2-59/5 * * * *	www-data /usr/share/evote/purge_otps.py
