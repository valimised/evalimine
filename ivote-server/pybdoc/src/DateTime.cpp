/*
 * Copyright: Eesti Vabariigi Valimiskomisjon
 * (Estonian National Electoral Committee), www.vvk.ee
 * Derived work from libdicidocpp library
 * https://svn.eesti.ee/projektid/idkaart_public/trunk/libdigidocpp/
 * Written in 2011-2014 by Cybernetica AS, www.cyber.ee
 *
 * This work is licensed under the Creative Commons
 * Attribution-NonCommercial-NoDerivs 3.0 Unported License.
 * To view a copy of this license, visit
 * http://creativecommons.org/licenses/by-nc-nd/3.0/.
 * */

#include "DateTime.h"
#include "StackException.h"

#include <sstream>
#include <iomanip>

namespace bdoc
{
	namespace util
	{
		namespace date
		{
			/// Dedicated helper for converting xml-schema-style DateTyme into a Zulu-string.
			///
			/// @param time GMT time as code-synth xml-schema type.
			/// @return a string format of date-time e.g. "2007-12-25T14:06:01Z".
			std::string xsd2string(const xml_schema::DateTime& time)
			{
				std::stringstream stream;

				stream << std::setfill('0') << std::dec
					<< std::setw(4) << time.year()
					<< std::setw(2) << time.month()
					<< std::setw(2) << time.day()
					<< std::setw(2) << time.hours()
					<< std::setw(2) << time.minutes()
					<< std::setw(2) << time.seconds()
					;

				return stream.str();
			}

			void string2tm(const std::string& time, struct tm& tm)
			{
				char *res = strptime(time.c_str(), "%Y%m%d%H%M%S", &tm);
				if (res == NULL || *res != '\0') {
					THROW_STACK_EXCEPTION("Failed to parse time string %s", time.c_str());
				}
			}

			xml_schema::DateTime currentTime()
			{
				std::time_t t;
				time(&t);

				return makeDateTime(t);
			}

			xml_schema::DateTime makeDateTime(const std::time_t& time)
			{
				struct tm *lt = gmtime(&time);

				return makeDateTime(*lt);
			}


			xml_schema::DateTime makeDateTime(const struct tm& lt)
			{
				xml_schema::DateTime dateTime( lt.tm_year + 1900
											 , static_cast<unsigned short>( lt.tm_mon + 1 )
											 , static_cast<unsigned short>( lt.tm_mday )
											 , static_cast<unsigned short>( lt.tm_hour )
											 , static_cast<unsigned short>( lt.tm_min )
											 , lt.tm_sec
											 , 0 //zone +0h
											 , 0 ); //zone +0min

				return dateTime;
			}
		}
	}
}
