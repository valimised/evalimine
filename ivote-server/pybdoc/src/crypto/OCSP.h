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

#include "OpenSSLHelpers.h"
#include <openssl/ocsp.h>
#include <openssl/x509.h>
#include <openssl/ssl.h>

#include <string>
#include <vector>

namespace bdoc
{
	class OCSP
	{
	public:
		enum CertStatus { GOOD, REVOKED, UNKNOWN };

		OCSP(const std::string &url);
		~OCSP();

		void setOCSPCerts(STACK_OF(X509)* ocspCerts);
		void setSkew(long skew);
		void setMaxAge(long maxAge);
		CertStatus checkCert(X509* cert, X509* issuer, const std::vector<unsigned char>& nonce);
		CertStatus checkCert(X509* cert, X509* issuer, const std::vector<unsigned char>& nonce,
				std::vector<unsigned char>& ocspResponseDER, tm& producedAt);
		void verifyResponse(const std::vector<unsigned char>& ocspResponseDER) const;
		std::vector<unsigned char> getNonce(const std::vector<unsigned char>& ocspResponseDER) const;

	private:
		void setUrl(const std::string& url);
		CertStatus checkCert(X509* cert, X509* issuer, const std::vector<unsigned char>& nonce,
				OCSP_REQUEST** req, OCSP_RESPONSE** resp);
		void connect();
		void connectSSL();
		OCSP_REQUEST* createRequest(X509* cert, X509* issuer, const std::vector<unsigned char>& nonce);
		OCSP_RESPONSE* sendRequest(OCSP_REQUEST* req);
		CertStatus validateResponse(OCSP_REQUEST* req, OCSP_RESPONSE* resp, X509* cert, X509* issuer);

		static tm convert(ASN1_GENERALIZEDTIME* time);

		std::string url, host, port, path;
		bool ssl;

		long skew;
		long maxAge;

		BIO *connection;
		SSL_CTX *ctx;
		X509* ocspCert;
		STACK_OF(X509)* ocspCerts;
	};
}

