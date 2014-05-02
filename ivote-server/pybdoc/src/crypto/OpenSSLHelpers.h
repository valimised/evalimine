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

#include <openssl/bio.h>
#include <openssl/x509.h>

#define DECLARE_OPENSSL_RELEASE_STRUCT(type) \
struct type##_scope \
{ \
	type** p; \
	type##_scope(type** p) { this->p = p; } \
	~type##_scope() { if(p && *p) { type##_free(*p); *p = NULL; } } \
};

#define DECLARE_OPENSSL_RELEASE_STACK(type) \
struct type##Stack_scope \
{ \
	STACK_OF(type)** p; \
	type##Stack_scope(STACK_OF(type)** p) { this->p = p; } \
	~type##Stack_scope() { if(p && *p) { sk_##type##_free(*p); *p = NULL; } } \
};

DECLARE_OPENSSL_RELEASE_STRUCT(BIO)
DECLARE_OPENSSL_RELEASE_STRUCT(X509)
DECLARE_OPENSSL_RELEASE_STRUCT(RSA)
DECLARE_OPENSSL_RELEASE_STRUCT(X509_STORE)
DECLARE_OPENSSL_RELEASE_STRUCT(X509_STORE_CTX)
DECLARE_OPENSSL_RELEASE_STACK(X509)

