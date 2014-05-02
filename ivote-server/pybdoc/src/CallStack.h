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

#pragma once
#include <string>
#include <vector>
#include <sstream>

namespace bdoc {

struct CallStackEntry {

	CallStackEntry() {
	}

	std::string to_string () const {
		std::ostringstream os;
		os << file << " " << function;
		return os.str();
	}

	std::string file;
	std::string function;

};

class CallStack {

	public:

		CallStack (const size_t num_discard = 0);

		virtual ~CallStack () throw();

		std::string to_string (const std::string& pre) const {
			std::ostringstream os;
			for (size_t i = 0; i < stack.size(); i++) {
				os << pre << "\t" << stack[i].to_string() << std::endl;
			}
			return os.str();
		}

		std::vector<CallStackEntry> stack;
};

}
