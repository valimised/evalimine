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

#include "xml/XAdES.hxx"
#include "xml/xmldsig-core-schema.hxx"

#include <list>

namespace bdoc {


class Buffer;
class ContainerInfo;
class Configuration;
class X509CertStore;

typedef std::map<std::string, bool> HandleMap;
typedef std::map<std::string, Buffer*> DataMap;

class Buffer {

	public:

		Buffer();
		~Buffer();


		void set(const unsigned char* data, size_t len);

		size_t len() const;

		const unsigned char* peek() const;


	protected:

		void init();
		void reset();


	private:


		unsigned char *_buf;
		size_t _len;

};

class OCSPConf {

	public:

		OCSPConf();
		OCSPConf(const char* u, const char* c, long s, long m);
		OCSPConf(const OCSPConf& oc);
		OCSPConf& operator=(OCSPConf& oc);
		~OCSPConf();

		std::string url;
		std::string cert;
		long skew;
		long maxAge;

};

class Configuration {
	public:
		Configuration();
		~Configuration();

		void setSchemaDir(const char *path);
		void addCertToStore(const char *path);

		void addOCSPConf(const char *issuer, const char *url,
				const char *cert, long skew, long maxAge);

		bool hasOCSPConf(const std::string& issuer);
		const OCSPConf& getOCSPConf(const std::string& issuer);

		const char* getSchemaDir() const;
		bdoc::X509CertStore* getCertStore();

		const char* getDigestURI() const;
		void setDigestURI(const char *uri);

	private:

		std::map<std::string, OCSPConf> ocsp;
		std::string schema_dir;
		std::string digest;
		bdoc::X509CertStore *store;
};

class ContainerInfo {

	public:

		ContainerInfo();
		~ContainerInfo();

	unsigned int documentCount() const;

	void setDocument(const std::string& uri,
				const unsigned char *buf, size_t len);

	void checkDocumentsBegin();

	void checkDocument(const std::string& uri,
				const bdoc::dsig::DigestMethodType::AlgorithmType& alg,
				const bdoc::dsig::DigestValueType& dig);

	bool checkDocumentsResult();

	HandleMap _hm;
	DataMap _dm;

	std::list<std::string> errors;

};

}
