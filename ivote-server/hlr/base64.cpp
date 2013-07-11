/*
 * Copyright: Eesti Vabariigi Valimiskomisjon
 * (Estonian National Electoral Committee), www.vvk.ee
 * Written in 2004-2013 by Cybernetica AS, www.cyber.ee
 *
 * This work is licensed under the Creative Commons
 * Attribution-NonCommercial-NoDerivs 3.0 Unported License.
 * To view a copy of this license, visit
 * http://creativecommons.org/licenses/by-nc-nd/3.0/.
 * */

#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

#include "base64.h"

void buffer_new(struct buffer_st *b)
{
    b->length = 512;
    b->data = (char *)malloc(sizeof(char)*(b->length));
    b->ptr = b->data;
    b->offset = 0;
}

void buffer_add(struct buffer_st *b, char c)
{
    *(b->ptr++) = c;
    b->offset++;
    if (b->offset == b->length) {
        b->length += 512;
        b->data = (char *)realloc(b->data, b->length);
        b->ptr = b->data + b->offset;
    }
}

void buffer_delete(struct buffer_st *b)
{
    free(b->data);
    b->length = 0;
    b->offset = 0;
    b->ptr = NULL;
    b->data = NULL;
}

void Base64::encode(struct buffer_st *b, const char *source, 
		int length, bool strip_new_line)
{
	unsigned char dtable[512];

    int i, hiteof = 0;
    int offset = 0;

    buffer_new(b);

    for (i = 0; i < 26; i++) {
        dtable[i] = 'A' + i;
        dtable[26 + i] = 'a' + i;
    }
    for (i = 0; i < 10; i++) {
        dtable[52 + i] = '0' + i;
    }
    dtable[62] = '+';
    dtable[63] = '/';

    while (!hiteof) {
        unsigned char igroup[3], ogroup[4];
        int c, n;

        igroup[0] = igroup[1] = igroup[2] = 0;
        for (n = 0; n < 3; n++) {
            c = *(source++);
            offset++;
            if (offset > length) {
                hiteof = 1;
                break;
            }
            igroup[n] = (unsigned char) c;
        }
        if (n > 0) {
            ogroup[0] = dtable[igroup[0] >> 2];
            ogroup[1] = dtable[((igroup[0] & 3) << 4) | (igroup[1] >> 4)];
            ogroup[2] = dtable[((igroup[1] & 0xF) << 2) | (igroup[2] >> 6)];
            ogroup[3] = dtable[igroup[2] & 0x3F];

            /* Replace characters in output stream with "=" pad
             * characters if fewer than three characters were
             * read from the end of the input stream. */

            if (n < 3) {
                ogroup[3] = '=';
                if (n < 2) {
                    ogroup[2] = '=';
                }
            }
            for (i = 0; i < 4; i++) {
                buffer_add(b, ogroup[i]);
                if (!strip_new_line && !(b->offset % 72)) {
					buffer_add(b, '\n');
                }
            }
        }
    }
	if (!strip_new_line) {
		buffer_add(b, '\n');
	}
}

void Base64::decode(struct buffer_st *bfr, const char *source, \
		int length)
{
	unsigned char dtable[512];


    int i;
    int offset = 0;
    int endoffile;
    int count;

    buffer_new(bfr);

    for (i = 0; i < 255; i++) {
        dtable[i] = 0x80;
    }
    for (i = 'A'; i <= 'Z'; i++) {
        dtable[i] = 0 + (i - 'A');
    }
    for (i = 'a'; i <= 'z'; i++) {
        dtable[i] = 26 + (i - 'a');
    }
    for (i = '0'; i <= '9'; i++) {
        dtable[i] = 52 + (i - '0');
    }
    dtable[(int)'+'] = 62;
    dtable[(int)'/'] = 63;
    dtable[(int)'='] = 0;

    endoffile = 0;

    /*CONSTANTCONDITION*/
    while (1) {
        unsigned char a[4], b[4], o[3];

        for (i = 0; i < 4; i++) {
            int c;
            while (1) {
                c = *(source++);
                offset++;
                if (offset > length) endoffile = 1;
                if (isspace(c) || c == '\n' || c == '\r') continue;
                break;
            }

            if (endoffile) {
                return;
            }

            if (dtable[c] & 0x80) {
                i--;
                continue;
            }
            a[i] = (unsigned char) c;
            b[i] = (unsigned char) dtable[c];
        }
        o[0] = (b[0] << 2) | (b[1] >> 4);
        o[1] = (b[1] << 4) | (b[2] >> 2);
        o[2] = (b[2] << 6) | b[3];
        i = a[2] == '=' ? 1 : (a[3] == '=' ? 2 : 3);
        count = 0;
        while (count < i) {
            buffer_add(bfr, o[count++]);
        }
        if (i < 3) {
            return;
        }
    }
}

