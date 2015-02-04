# monitor
* * * * *	hes /usr/share/evote/hes_monitor.py > /dev/null 2>&1

# Purges expired voting sessions
2-59/5 * * * *	www-data /usr/share/evote/purge_sessions.py > /dev/null 2>&1
