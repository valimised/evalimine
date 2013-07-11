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

#include "BDoc.h"
#include <new>
#include <iostream>

#include "crypto/Digest.h"
#include "crypto/X509CertStore.h"

bdoc::Buffer::Buffer()
{
	init();
}

bdoc::Buffer::~Buffer()
{
	reset();
}

void bdoc::Buffer::init()
{
	_buf = NULL;
	_len = 0;
}

void bdoc::Buffer::reset()
{
	if (_buf) {
		free(_buf);
	}
	init();
}

void bdoc::Buffer::set(const unsigned char* data, size_t len)
{
	reset();
	if ((len > 0) && (data != NULL)) {
		_buf = (unsigned char *)malloc(sizeof(unsigned char) * len); 

		if (_buf == NULL) {
			throw std::bad_alloc();
		}
		_len = len;
		memcpy(_buf, data, len);
	}
}

size_t bdoc::Buffer::len() const
{
	return _len;
}

const unsigned char* bdoc::Buffer::peek() const
{
	return _buf;
}

//
//

bdoc::ContainerInfo::ContainerInfo() : _hm(), _dm()
{
}

bdoc::ContainerInfo::~ContainerInfo()
{
	for (DataMap::const_iterator iter = _dm.begin(); iter != _dm.end(); iter++) {
		delete iter->second;
	}
}

unsigned int bdoc::ContainerInfo::documentCount() const
{
	return _dm.size();
}

void bdoc::ContainerInfo::setDocument(const std::string& uri, const unsigned char *buf, size_t len)
{
	_hm[uri] = false;
	Buffer *b = new Buffer();
	b->set(buf, len);
	_dm[uri] = b;
}

void bdoc::ContainerInfo::checkDocumentsBegin()
{
	for (HandleMap::iterator it1 = _hm.begin(); it1 != _hm.end(); it1++) {
		_hm[it1->first] = false;
	}
}

void bdoc::ContainerInfo::checkDocument(const std::string& uri, 
			const bdoc::dsig::DigestMethodType::AlgorithmType& alg,
			const bdoc::dsig::DigestValueType& dig)
{
	if ((_hm.count(uri) == 0) || (_dm.count(uri) == 0)) {
		errors.push_back(uri + " is unknown");
		return;
	}

	if (_hm[uri]) {
		errors.push_back(uri + " inspected more than once");
		return;
	}

	_hm[uri] = true;

	if (_dm[uri] == NULL) {
		errors.push_back(uri + " is invalid");
		return;
	}

	if (!bdoc::Digest::isSupported(alg)) {
		errors.push_back("Algorithm not supported: " + alg);
	}

	std::auto_ptr<bdoc::Digest> docDigest; // only this scope
	docDigest = bdoc::Digest::create(alg);
	docDigest->update(_dm[uri]->peek(), _dm[uri]->len());
	std::vector<unsigned char> docDigestBuf = docDigest->getDigest();
	const unsigned char* refDigest = reinterpret_cast<const unsigned char* >(dig.data());

	if (docDigestBuf.size() != dig.size()
		|| memcmp(&docDigestBuf[0], refDigest, docDigestBuf.size()) != 0) {
		errors.push_back("Digest");
	}
}

bool bdoc::ContainerInfo::checkDocumentsResult()
{
	for (HandleMap::iterator it = _hm.begin(); it != _hm.end(); it++) {
		if (!it->second) {
			errors.push_back("Unhandled document: " + it->first);
		}
	}

	return errors.empty();
}

//
//
//

bdoc::Configuration::Configuration() :
	schema_dir(),
	store(new bdoc::X509CertStore())
{
}

bdoc::Configuration::~Configuration()
{
	delete store;
}

void bdoc::Configuration::setSchemaDir(const char *path)
{
	schema_dir = path;
}

void bdoc::Configuration::addCertToStore(const char *path)
{
	store->addCert(path);
}

const char* bdoc::Configuration::getSchemaDir() const
{
	return schema_dir.c_str();
}

bdoc::X509CertStore* bdoc::Configuration::getCertStore()
{
	return store;
}

void bdoc::Configuration::addOCSPConf(const char *issuer,
	const char *url, const char *cert, long skew, long maxAge)
{
	OCSPConf a(url, cert, skew, maxAge);
	ocsp[issuer] = a;
}

bool bdoc::Configuration::hasOCSPConf(const std::string& issuer)
{
	return (ocsp.count(issuer) > 0);
}

const bdoc::OCSPConf& bdoc::Configuration::getOCSPConf(const std::string& issuer)
{
	return ocsp[issuer];
}

const char* bdoc::Configuration::getDigestURI() const
{
	return digest.c_str();
}

void bdoc::Configuration::setDigestURI(const char *uri)
{
	digest = uri;
}


//
//
//

bdoc::OCSPConf::OCSPConf() :
	url(),
	cert(),
	skew(0),
	maxAge(0)
{
}

bdoc::OCSPConf::OCSPConf(const char* u, const char* c, long s, long m) :
	url(u),
	cert(c),
	skew(s),
	maxAge(m)
{
}

bdoc::OCSPConf::OCSPConf(const OCSPConf& oc) :
	url(oc.url),
	cert(oc.cert),
	skew(oc.skew),
	maxAge(oc.maxAge)
{
}

bdoc::OCSPConf& bdoc::OCSPConf::operator=(OCSPConf& oc)
{
	url = oc.url;
	cert = oc.cert;
	skew = oc.skew;
	maxAge = oc.maxAge;
	return *this;
}

bdoc::OCSPConf::~OCSPConf()
{
}

