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

#include "X509Cert.h"
#include <string>
#include <vector>

namespace bdoc
{
	class X509CertStore
	{
		public:
			X509CertStore();
			~X509CertStore();

			void addCert(const std::string& path);

			X509_STORE* getCertStore() const;
			X509* getCert(const X509_NAME& subject) const;

		private:
			std::vector<X509*> certs;
	};
}

