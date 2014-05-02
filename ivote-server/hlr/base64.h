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


#ifndef BASE64_H
#define BASE64_H

struct buffer_st {
  char *data;
  int length;
  char *ptr;
  int offset;

  buffer_st()
  {
	data = NULL;
	length = 0;
	ptr = NULL;
	offset = 0;
  }
};


void buffer_new(struct buffer_st *b);
void buffer_add(struct buffer_st *b, char c);
void buffer_delete(struct buffer_st *b);


class Base64
{
	public:
		Base64() {}
		~Base64() {}

		void encode(struct buffer_st *b, const char *source,
				int length, bool strip_new_line = false);
		void decode(struct buffer_st *b, const char *source,
				int length);

	private:
		unsigned char dtable[512];
};

#endif

