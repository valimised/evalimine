/*
 * Copyright: Eesti Vabariigi Valimiskomisjon
 * (Estonian National Electoral Committee), www.vvk.ee
 * Written in 2004-2014 by Cybernetica AS, www.cyber.ee
 *
 * This work is licensed under the Creative Commons
 * Attribution-NonCommercial-NoDerivs 3.0 Unported License.
 * To view a copy of this license, visit
 * http://creativecommons.org/licenses/by-nc-nd/3.0/.
 * */


#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#define BUFFER_SIZE (16 * 1024)

int countLines(const char *filen)
{

	int lines = 0;
	size_t bytes_read = 0;
	char buf[BUFFER_SIZE + 1];
	int fd = -1;

	fd = open (filen, O_RDONLY);
	if (fd == -1) {
		lines = -1;
		goto error;
        }

	while ((bytes_read = read(fd, buf, BUFFER_SIZE)) > 0) {
		char *p = buf;

		if (bytes_read < 0) {
			lines = -1;
			goto error;
		}

		while ((p = (char *)memchr(p, '\n', (buf + bytes_read) - p))) {
			++p;
			++lines;
		}
	}

error:

	if (fd != -1) {
		if (close (fd) != 0) {
			lines = -1;
		}
	}

	return lines;
}

