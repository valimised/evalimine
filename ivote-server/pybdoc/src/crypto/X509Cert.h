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

#include <openssl/x509.h>
#include <string>
#include <vector>
#include <list>
#include <ctime>

namespace bdoc
{
	class X509Cert
	{

	public:

		static X509* copyX509(X509* cert);
		static X509* loadX509(const std::string& path);

		static STACK_OF(X509)* loadX509Stack(const std::string& path);

		X509Cert();
		X509Cert(X509* cert);
		X509Cert(const unsigned char* bytes, size_t len);
		X509Cert(const X509Cert& copy);
		~X509Cert();
		X509Cert& operator=(const X509Cert& copy);
		X509* getX509() const;

		std::vector<unsigned char> encodeDER() const;
		std::string getSerial() const;
		X509_NAME* getIssuerNameAsn1() const;
		std::string getIssuerName() const;
		std::string getSubject() const;
		std::string getRsaModulus() const;
		std::string getRsaExponent() const;

		bool verifySignature(int digestMethod, int digestSize,
			std::vector<unsigned char> digest,
			std::vector<unsigned char> signature);

		bool isValid() const;
		bool verify(X509_STORE* aStore, struct tm* tm) const;
		int compareIssuerToString(std::string) const;

	protected:
		EVP_PKEY* getPublicKey() const;

		X509* cert;
	private:
		static std::string toString(X509_NAME* name);

	};
}

