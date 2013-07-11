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

#include "OCSP.h"
#include <openssl/err.h>
#include "../StackException.h"

DECLARE_OPENSSL_RELEASE_STRUCT(OCSP_REQUEST)
DECLARE_OPENSSL_RELEASE_STRUCT(OCSP_RESPONSE)
DECLARE_OPENSSL_RELEASE_STRUCT(OCSP_BASICRESP)
DECLARE_OPENSSL_RELEASE_STRUCT(OCSP_CERTID)
DECLARE_OPENSSL_RELEASE_STRUCT(X509_EXTENSION)

bdoc::OCSP::OCSP(const std::string& url) :
	ssl(false), skew(0), maxAge(0),
	connection(NULL), ctx(NULL), ocspCerts(NULL)
{
	setUrl(url);
}

bdoc::OCSP::~OCSP()
{
	BIO_free_all(connection);
	SSL_CTX_free(ctx);
}

void bdoc::OCSP::setUrl(const std::string& _url)
{
	url = _url;
	char *_host = NULL, *_port = NULL, *_path = NULL;
	int sslFlag = 0;
	if (!OCSP_parse_url(const_cast<char*>(url.c_str()), &_host, &_port, &_path, &sslFlag)) {
		THROW_STACK_EXCEPTION("Incorrect OCSP URL provided: '%s'.", url.c_str());
	}
	ssl = sslFlag != 0;
	if (_host) {
		host = _host;
	}
	else {
		host.clear();
	}
	if (_port) {
		port = _port;
	}
	else {
		port.clear();
	}
	if (_path) {
		path = _path;
	}
	else {
		path = "/";
	}
	OPENSSL_free(_host);
	OPENSSL_free(_port);
	OPENSSL_free(_path);
}

void bdoc::OCSP::setOCSPCerts(STACK_OF(X509)* ocspCerts)
{
	this->ocspCerts = ocspCerts;
}

void bdoc::OCSP::setSkew(long skew)
{
	this->skew = skew;
}

void bdoc::OCSP::setMaxAge(long maxAge)
{
	this->maxAge = maxAge;
}

bdoc::OCSP::CertStatus bdoc::OCSP::checkCert(
		X509* cert, X509* issuer,
		const std::vector<unsigned char>& nonce)
{
	OCSP_REQUEST* req = NULL;
	OCSP_REQUEST_scope reqScope(&req);

	OCSP_RESPONSE* resp = NULL;
	OCSP_RESPONSE_scope respScope(&resp);
	return checkCert(cert, issuer, nonce, &req, &resp);
}

bdoc::OCSP::CertStatus bdoc::OCSP::checkCert(X509* cert, X509* issuer,
		const std::vector<unsigned char>& nonce,
		std::vector<unsigned char>& ocspResponseDER, tm& producedAt)
{
	OCSP_REQUEST* req = NULL;
	OCSP_REQUEST_scope reqScope(&req);

	OCSP_RESPONSE* resp = NULL;
	OCSP_RESPONSE_scope respScope(&resp);

	CertStatus certStatus = checkCert(cert, issuer, nonce, &req, &resp);

	int bufSize = i2d_OCSP_RESPONSE(resp, NULL);
	if (bufSize < 0) {
		THROW_STACK_EXCEPTION(
			"Failed to encode OCSP response to DER.");
	}

	ocspResponseDER.resize(bufSize);
	unsigned char* pBuf = &ocspResponseDER[0];
	bufSize = i2d_OCSP_RESPONSE(resp, &pBuf);
	if (bufSize < 0) {
		THROW_STACK_EXCEPTION(
			"Failed to encode OCSP response to DER.");
	}

	OCSP_BASICRESP* basic = OCSP_response_get1_basic(resp);
	OCSP_BASICRESP_scope basicScope(&basic);
	producedAt = convert(basic->tbsResponseData->producedAt);
	return certStatus;
}

bdoc::OCSP::CertStatus bdoc::OCSP::checkCert(X509* cert, X509* issuer,
		const std::vector<unsigned char>& nonce,
		OCSP_REQUEST** req, OCSP_RESPONSE** resp)
{
	if (cert == NULL) {
		THROW_STACK_EXCEPTION("Can not check X.509 certificate, certificate is NULL pointer.");
	}

	if (issuer == NULL) {
		THROW_STACK_EXCEPTION("Can not check X.509 certificate, issuer certificate is NULL pointer.");
	}

	connect();

	*req = createRequest(cert, issuer, nonce);
	*resp = sendRequest(*req);
	return validateResponse(*req, *resp, cert, issuer);
}

void bdoc::OCSP::connect()
{
	BIO_free_all(connection);
	SSL_CTX_free(ctx);
	connection = NULL;
	ctx = NULL;

	connection = BIO_new_connect(const_cast<char*>(host.c_str()));
	if (connection == NULL) {
		THROW_STACK_EXCEPTION("Failed to create connection with host: '%s'", host.c_str());
	}

	if (!BIO_set_conn_port(connection, const_cast<char*>(port.c_str()))) {
		THROW_STACK_EXCEPTION("Failed to set port of the connection: %s", port.c_str());
	}

	if (ssl) {
		connectSSL();
	}

	if (!BIO_do_connect(connection)) {
		THROW_STACK_EXCEPTION("Failed to connect to host: '%s'", host.c_str());
	}
}

void bdoc::OCSP::connectSSL()
{
	ctx = SSL_CTX_new(SSLv23_client_method());
	if (!ctx) {
		THROW_STACK_EXCEPTION("Failed to create connection with host: '%s'", host.c_str());
	}
	SSL_CTX_set_mode(ctx, SSL_MODE_AUTO_RETRY);
	BIO *sconnection = BIO_new_ssl(ctx, 1);
	if (!sconnection) {
		THROW_STACK_EXCEPTION("Failed to create ssl connection with host: '%s'", host.c_str());
	}
	connection = BIO_push(sconnection, connection);
}

OCSP_REQUEST* bdoc::OCSP::createRequest(X509* cert, X509* issuer, const std::vector<unsigned char>& nonce)
{
	OCSP_REQUEST* req = OCSP_REQUEST_new(); OCSP_REQUEST_scope reqScope(&req);
	if (req == NULL) {
		THROW_STACK_EXCEPTION("Failed to create new OCSP request, out of memory?");
	}

	OCSP_CERTID* certId = OCSP_cert_to_id(NULL, cert, issuer);
	if (certId == NULL) {
		THROW_STACK_EXCEPTION("Failed to create ID from the certificate being checked.");
	}

	if (OCSP_request_add0_id(req, certId) == NULL) {
		THROW_STACK_EXCEPTION("Failed to add certificate ID to OCSP request.");
	}

	if (OCSP_request_add1_nonce(req, const_cast<unsigned char*>(&nonce[0]), nonce.size()) == 0) {
		THROW_STACK_EXCEPTION("Failed to add NONCE to OCSP request.");
	}

	// Remove request pointer from scope, so that it will not be destroyed.
	reqScope.p = NULL;

	return req;
}

OCSP_RESPONSE* bdoc::OCSP::sendRequest(OCSP_REQUEST* req)
{
	OCSP_RESPONSE* resp = 0;

	if (!(resp = OCSP_sendreq_bio(connection, const_cast<char*>(path.c_str()), req)))
			THROW_STACK_EXCEPTION("Failed to send OCSP request.");

	return resp;
}

bdoc::OCSP::CertStatus bdoc::OCSP::validateResponse(OCSP_REQUEST* req, OCSP_RESPONSE* resp, X509* cert, X509* issuer)
{
	// Check OCSP response status code.
	int respStatus = OCSP_response_status(resp);
	switch (respStatus) {
		case OCSP_RESPONSE_STATUS_SUCCESSFUL: break;
		case OCSP_RESPONSE_STATUS_UNAUTHORIZED:
			{
			THROW_STACK_EXCEPTION("OCSP request failed: OCSP request unauthorized");
			}
		default:
			THROW_STACK_EXCEPTION("OCSP request failed, response status: 0x%02X", respStatus);
	}

	OCSP_BASICRESP* basic = OCSP_response_get1_basic(resp);
	OCSP_BASICRESP_scope basicScope(&basic);
	if (basic == NULL) {
		THROW_STACK_EXCEPTION("Incorrect OCSP response.");
	}

	if (OCSP_check_nonce(req, basic) <= 0) {
		THROW_STACK_EXCEPTION("Incorrect NONCE field value.");
	}

	if (ocspCerts == NULL) {
		THROW_STACK_EXCEPTION("OCSP responder certificate not configured.");
	}

	// NOINTERN is necessary because of a weird bug in cert verification
	int res = OCSP_basic_verify(basic, ocspCerts, NULL, OCSP_TRUSTOTHER | OCSP_NOINTERN);
	if (res <= 0) {
		THROW_STACK_EXCEPTION("OCSP responder certificate not found or not valid.");
	}

	OCSP_CERTID* certId = OCSP_cert_to_id(0, cert, issuer);
	OCSP_CERTID_scope certIdScope(&certId);
	int certStatus = -1;
	int reason = -1;
	ASN1_GENERALIZEDTIME *producedAt = NULL, *thisUpdate = NULL, *nextUpdate = NULL;
	if (!OCSP_resp_find_status(basic, certId, &certStatus, &reason, &producedAt, &thisUpdate, &nextUpdate)) {
		THROW_STACK_EXCEPTION("Failed to get status code from OCSP response.");
	}

	if (!OCSP_check_validity(thisUpdate, nextUpdate, skew, maxAge)) {
		THROW_STACK_EXCEPTION("OCSP response not in valid time slot.");
	}

	// Return certificate status.
	switch (certStatus) {
		default:
			THROW_STACK_EXCEPTION("OCSP response contains unknown certificate status code.");
		case V_OCSP_CERTSTATUS_UNKNOWN:
			return UNKNOWN;
		case V_OCSP_CERTSTATUS_GOOD:
			return GOOD;
		case V_OCSP_CERTSTATUS_REVOKED:
			return REVOKED;
	}
}

void bdoc::OCSP::verifyResponse(const std::vector<unsigned char>& ocspResponseDER) const
{
	BIO * bio = BIO_new_mem_buf(const_cast<unsigned char*>(&ocspResponseDER[0]), ocspResponseDER.size());
	BIO_scope bioScope(&bio);

	OCSP_RESPONSE * resp = d2i_OCSP_RESPONSE_bio(bio, NULL);
	OCSP_RESPONSE_scope respScope(&resp);

	OCSP_BASICRESP* basic = OCSP_response_get1_basic(resp);
	OCSP_BASICRESP_scope basicScope(&basic);

	if (ocspCerts == NULL) {
		THROW_STACK_EXCEPTION("OCSP responder certificate not configured.");
	}
	int res = OCSP_basic_verify(basic, ocspCerts, NULL, OCSP_TRUSTOTHER | OCSP_NOINTERN);
	if (res <= 0) {
		THROW_STACK_EXCEPTION("OCSP responder certificate not found or not valid.");
	}
}

std::vector<unsigned char> bdoc::OCSP::getNonce(const std::vector<unsigned char>& ocspResponseDER) const
{
	BIO * bio = BIO_new_mem_buf(const_cast<unsigned char*>(&ocspResponseDER[0]), ocspResponseDER.size());
	BIO_scope bioScope(&bio);

	OCSP_RESPONSE * resp = d2i_OCSP_RESPONSE_bio(bio, NULL);
	OCSP_RESPONSE_scope respScope(&resp);

	OCSP_BASICRESP* basic = OCSP_response_get1_basic(resp);
	OCSP_BASICRESP_scope basicScope(&basic);

	int resp_idx = OCSP_BASICRESP_get_ext_by_NID(basic, NID_id_pkix_OCSP_Nonce, -1);
	X509_EXTENSION* resp_ext = OCSP_BASICRESP_get_ext(basic, resp_idx);// X509_EXTENSION_scope x509ExtScope(&resp_ext);

	int r = i2d_ASN1_OCTET_STRING(resp_ext->value, NULL);

	std::vector<unsigned char> nonceAsn1(r);

	unsigned char * t = &nonceAsn1[0];
	i2d_ASN1_OCTET_STRING(resp_ext->value, &t);

	std::vector<unsigned char> nonce;

	if (((r > 4) && (nonceAsn1[2] == V_ASN1_OCTET_STRING))
		&& (nonceAsn1[3] == r-4))//length is r-4
	 {
		nonce.resize(r-4);
		std::copy(&nonceAsn1[4], &nonceAsn1[4]+r-4, nonce.begin());
		return nonce;
	}
	else if (((r > 2) && (nonceAsn1[0] == V_ASN1_OCTET_STRING))
			&& (nonceAsn1[1] == r-2))//length is length - DER header len
	{
		nonce.resize(r-2);
		std::copy(&nonceAsn1[2], &nonceAsn1[2]+r-2, nonce.begin());
		return nonce;
	}
	else {
		return nonceAsn1;
	}
}

/**
 * Extract date time value from ASN1_GENERALIZEDTIME struct.
 *
 * @param asn1Time ASN.1 generalized time struct.
 * @return returned extracted time.
 * @throws Exception exception is throws if the time is in incorrect format.
 */
tm bdoc::OCSP::convert(ASN1_GENERALIZEDTIME* asn1Time)
{
	char* t = reinterpret_cast<char*>(asn1Time->data);

	if (asn1Time->length < 12) {
		THROW_STACK_EXCEPTION("Date time field value shorter than 12 characters: '%s'", t);
	}

	tm time;
	time.tm_isdst = 0;

	// Accept only GMT time.
	if (t[asn1Time->length - 1] != 'Z') {
		THROW_STACK_EXCEPTION("Time value is not in GMT format: '%s'", t);
	}

	for(int i = 0; i< asn1Time->length - 1; i++) {
		if ((t[i] > '9') || (t[i] < '0')) {
			THROW_STACK_EXCEPTION("Date time value in incorrect format: '%s'", t);
		}
	}

	// Extract year.
	time.tm_year = ((t[0]-'0')*1000 + (t[1]-'0')*100 + (t[2]-'0')*10 + (t[3]-'0')) - 1900;

	// Extract month.
	time.tm_mon = ((t[4]-'0')*10 + (t[5]-'0')) - 1;
	if ((time.tm_mon > 11) || (time.tm_mon < 0)) {
		THROW_STACK_EXCEPTION("Month value incorrect: %d", (time.tm_mon + 1));
	}

	// Extract day.
	time.tm_mday = (t[6]-'0')*10 + (t[7]-'0');
	if ((time.tm_mday > 31) || (time.tm_mday < 1)) {
		THROW_STACK_EXCEPTION("Day value incorrect: %d", time.tm_mday);
	}

	// Extract hour.
	time.tm_hour = (t[8]-'0')*10 + (t[9]-'0');
	if ((time.tm_hour > 23) || (time.tm_hour < 0)) {
		THROW_STACK_EXCEPTION("Hour value incorrect: %d", time.tm_hour);
	}

	// Extract minutes.
	time.tm_min = (t[10]-'0')*10 + (t[11]-'0');
	if ((time.tm_min > 59) || (time.tm_min < 0)) {
		THROW_STACK_EXCEPTION("Minutes value incorrect: %d", time.tm_min);
	}

	// Extract seconds.
	time.tm_sec = 0;
	if (asn1Time->length >= 14 && (t[12] >= '0') && (t[12] <= '9') && (t[13] >= '0') && (t[13] <= '9')) {
		time.tm_sec = (t[12]-'0')*10 + (t[13]-'0');
		if ((time.tm_sec > 59) || (time.tm_sec < 0)) {
			THROW_STACK_EXCEPTION("Seconds value incorrect: %d", time.tm_sec);
		}
	}

	return time;
}
