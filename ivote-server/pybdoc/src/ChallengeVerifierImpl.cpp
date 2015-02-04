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

#include <string.h>

#include <openssl/err.h>
#include <openssl/evp.h>
#include <openssl/x509.h>

#include "ChallengeVerifierImpl.h"
#include "crypto/X509Cert.h"

#define CHALLENGE_LEN		20

ChallengeVerifierImpl::ChallengeVerifierImpl()
	: certificate(), challenge(), signature(), error()
{
}

ChallengeVerifierImpl::~ChallengeVerifierImpl()
{
}

bool ChallengeVerifierImpl::isChallengeOk()
{
	const unsigned char *certp;
	X509 *x509 = NULL;
	bool ok = false;

	if (challenge.len() != CHALLENGE_LEN) {
		error = "Invalid input challenge";
		goto end;
	}

	certp = certificate.peek();
	x509 = d2i_X509(NULL, &certp, certificate.len());
	if (!x509) {
		error = "Error decoding certificate: ";
		error += ERR_reason_error_string(ERR_get_error());
		goto end;
	}

	{
		bdoc::X509Cert x509cert(x509);
		std::vector<unsigned char> digest(
				challenge.peek(), challenge.peek() + challenge.len());
		std::vector<unsigned char> sig(
				signature.peek(), signature.peek() + signature.len());

		const EVP_MD *md = EVP_sha1();
		ok = x509cert.verifySignature(EVP_MD_type(md), EVP_MD_size(md),
				digest, sig);
	}

	end:
	if (x509) X509_free(x509);

	return ok;
}
