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

#include <openssl/pem.h>
#include <openssl/err.h>

#include "X509CertStore.h"
#include "../StackException.h"

bdoc::X509CertStore::X509CertStore()
{
}

bdoc::X509CertStore::~X509CertStore()
{
	for (std::vector<X509*>::const_iterator iter = certs.begin(); iter != certs.end(); iter++) {
		X509_free(*iter);
	}
}

void bdoc::X509CertStore::addCert(const std::string& path)
{
	X509 *cert = bdoc::X509Cert::loadX509(path);

	if (cert) {
		certs.push_back(cert);
	}
}

X509_STORE* bdoc::X509CertStore::getCertStore() const
{
	X509_STORE* cert_store = X509_STORE_new();

	if (cert_store == NULL) {
		THROW_STACK_EXCEPTION("Failed to create X509_STORE");
	}

	for(std::vector<X509*>::const_iterator iter = certs.begin(); iter != certs.end(); iter++) {
		X509_STORE_add_cert(cert_store, *iter);
		// It is correct not to check retval
	}

	return cert_store;
}

X509* bdoc::X509CertStore::getCert(const X509_NAME& subject) const
{
	for(std::vector<X509*>::const_iterator iter = certs.begin(); iter != certs.end(); iter++) {
		if (X509_NAME_cmp(X509_get_subject_name(*iter), &subject) == 0) {
			return X509Cert::copyX509(*iter);
		}
	}

	return NULL;
}

