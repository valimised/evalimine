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

#pragma once

#include <time.h>
#include <string>

#include "xml/xmldsig-core-schema.hxx"

namespace bdoc
{
	namespace util
	{

		namespace date
		{
			std::string xsd2string(const xml_schema::DateTime& time);

			xml_schema::DateTime currentTime();
			xml_schema::DateTime makeDateTime(const std::time_t& time);
			xml_schema::DateTime makeDateTime(const struct tm& lt);
		}

	}
}

