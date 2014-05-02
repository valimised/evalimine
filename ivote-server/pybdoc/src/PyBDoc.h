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
#include <list>

namespace bdoc {
	class ContainerInfo;
	class Configuration;
}

void initialize();
void terminate();


class CertificateData {

	public:
		CertificateData();
		CertificateData(const CertificateData& cd);
		CertificateData& operator=(const CertificateData& cd);
		~CertificateData();

		void decode(const unsigned char *buf, size_t len);

		std::string subject_name;
		std::string issuer_name;
		std::string serial_number;
		std::string modulus;
		std::string exponent;
};


class BDocVerifierResult {

	public:

		BDocVerifierResult();
		BDocVerifierResult(const BDocVerifierResult& bvr);
		BDocVerifierResult& operator=(const BDocVerifierResult& bvr);
		~BDocVerifierResult();

		bool result;
		std::string subject;
		std::string ocsp_time;
		std::string error;
		std::string signature;
		bool cert_is_valid;
		bool ocsp_is_good;
};

class BDocVerifier {

	public:

		BDocVerifier();
		~BDocVerifier();

		void setSchemaDir(const char *path);
		void addCertToStore(const char *path);

		void addOCSPConf(
			const char *issuer, const char *url,
			const char *cert, long skew, long maxAge);

		void setDigestURI(const char *uri);

		void setDocument(
			const unsigned char *buf, size_t len, const char* uri);

		const BDocVerifierResult verifyBESOffline(
					const char* xml, size_t xml_len);

		const BDocVerifierResult verifyInHTS(
					const char* xml, size_t xml_len);

		const BDocVerifierResult verifyTMOffline(
					const char* xml, size_t xml_len);

	private:

		bdoc::ContainerInfo *bdoc;
		bdoc::Configuration *conf;

};

class ChallengeVerifierImpl;

class ChallengeVerifier {

	public:

		ChallengeVerifier();
		~ChallengeVerifier();

		bool isChallengeOk();

		void setCertificate(const unsigned char *buf, size_t len);
		void setChallenge(const unsigned char *buf, size_t len);
		void setSignature(const unsigned char *buf, size_t len);

		std::string error;

	private:

		ChallengeVerifierImpl *impl;
};

