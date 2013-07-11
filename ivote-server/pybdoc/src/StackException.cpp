/*
 * Copyright: Eesti Vabariigi Valimiskomisjon
 * (Estonian National Electoral Committee), www.vvk.ee
 * Derived work from libdicidocpp library
 * https://svn.eesti.ee/projektid/idkaart_public/trunk/libdigidocpp/
 * Written in 2011-2013 by Cybernetica AS, www.cyber.ee
 *
 * This work is licensed under the Creative Commons
 * Attribution-NonCommercial-NoDerivs 3.0 Unported License.
 * To view a copy of this license, visit
 * http://creativecommons.org/licenses/by-nc-nd/3.0/.
 * */

#include <cstring>
#include <cstdio>
#include <sstream>
#include "StackException.h"

std::string bdoc::formatArgList(const char* fmt, va_list args)
{
	if (!fmt) {
		return "";
	}

	int result = -1;
	int length = 256;
	char* buffer = NULL;
	while (result == -1) {
		if (buffer) {
			delete [] buffer;
			buffer = NULL;
		}
		buffer = new char [length + 1];
		memset(buffer, 0, length + 1);
		result = vsnprintf(buffer, length, fmt, args);
		length *= 2;
	}

	std::string s(buffer);
	delete [] buffer;
	return s;
}

std::string bdoc::format(const char* fmt, ...)
{
	va_list args;
	va_start(args, fmt);
	std::string s = formatArgList(fmt, args);
	va_end(args);
	return s;
}

