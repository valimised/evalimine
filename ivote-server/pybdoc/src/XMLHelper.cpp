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


#include "Signature.h"
#include "XMLHelper.h"

void addXMLEncapsulatedX509Certificate(xercesc::DOMDocument *doc,
					xercesc::DOMNode *root,
					bdoc::X509Cert& x509,
					const char *id)
{
	xercesc::DOMElement *x509val =
		doc->createElement(
			xercesc::XMLString::transcode(
					"EncapsulatedX509Certificate"));

	std::vector<unsigned char> der = x509.encodeDER();
	xml_schema::Base64Binary b64(&der[0], der.size());

	x509val->setTextContent(
			xercesc::XMLString::transcode(b64.encode().c_str()));

	x509val->setAttribute(
			xercesc::XMLString::transcode("Id"),
			xercesc::XMLString::transcode(id));

	root->appendChild(x509val);
}

void addXMLCertificateValues(xercesc::DOMDocument *doc,
				xercesc::DOMNode *root,
				bdoc::X509Cert& ocspCert,
				bdoc::X509Cert& issuerCert)
{
	xercesc::DOMNode *certificatevalues =
		doc->createElement(
			xercesc::XMLString::transcode("CertificateValues"));

	addXMLEncapsulatedX509Certificate(doc, certificatevalues,
						ocspCert, "S0-RESPONDER_CERT");

	addXMLEncapsulatedX509Certificate(doc, certificatevalues,
						issuerCert, "S0-CA_CERT");

	root->appendChild(certificatevalues);
}

void addXMLRevocationValues(xercesc::DOMDocument *doc,
				xercesc::DOMNode *root,
				xml_schema::Base64Binary& resp)
{
	xercesc::DOMNode *revocationvalues =
		doc->createElement(
			xercesc::XMLString::transcode("RevocationValues"));

	xercesc::DOMNode *ocspvalues =
		doc->createElement(
			xercesc::XMLString::transcode("OCSPValues"));

	xercesc::DOMElement *encapsulatedocsp =
		doc->createElement(
			xercesc::XMLString::transcode(
						"EncapsulatedOCSPValue"));

	encapsulatedocsp->setAttribute(
					xercesc::XMLString::transcode("Id"),
					xercesc::XMLString::transcode("N0"));

	encapsulatedocsp->setTextContent(
				xercesc::XMLString::transcode(
						resp.encode().c_str()));

	ocspvalues->appendChild(encapsulatedocsp);
	revocationvalues->appendChild(ocspvalues);
	root->appendChild(revocationvalues);
}

void addXMLDigestMethodAndAlgorithm(xercesc::DOMDocument *doc,
					xercesc::DOMNode *root,
					xml_schema::Base64Binary& dig,
					const std::string& methuri)
{
	xercesc::DOMElement *digestmethod =
		doc->createElement(
			xercesc::XMLString::transcode("DigestMethod"));

	digestmethod->setAttribute(
			xercesc::XMLString::transcode("Algorithm"),
			xercesc::XMLString::transcode(methuri.c_str()));

	digestmethod->setAttribute(
		xercesc::XMLString::transcode("xmlns"),
		xercesc::XMLString::transcode(
			bdoc::Signature::DSIG_NAMESPACE.c_str()));

	xercesc::DOMElement *digestvalue =
		doc->createElement(
			xercesc::XMLString::transcode("DigestValue"));

	digestvalue->setTextContent(
		xercesc::XMLString::transcode(dig.encode().c_str()));

	digestvalue->setAttribute(
			xercesc::XMLString::transcode("xmlns"),
			xercesc::XMLString::transcode(
				bdoc::Signature::DSIG_NAMESPACE.c_str()));

	root->appendChild(digestmethod);
	root->appendChild(digestvalue);
}

void addXMLCompleteCertificateRefs(xercesc::DOMDocument *doc,
					xercesc::DOMNode *root,
					bdoc::X509Cert& incert,
					xml_schema::Base64Binary& dig,
					const std::string& methuri)
{

	xercesc::DOMNode *completecertrefs =
		doc->createElement(
			xercesc::XMLString::transcode(
						"CompleteCertificateRefs"));

	xercesc::DOMNode *certrefs =
		doc->createElement(xercesc::XMLString::transcode("CertRefs"));

	xercesc::DOMNode *cert =
		doc->createElement(xercesc::XMLString::transcode("Cert"));

	xercesc::DOMNode *certdigest =
		doc->createElement(
			xercesc::XMLString::transcode("CertDigest"));

	addXMLDigestMethodAndAlgorithm(doc, certdigest, dig, methuri);

	xercesc::DOMElement *x509name = doc->createElement(
			xercesc::XMLString::transcode("X509IssuerName"));

	x509name->setTextContent(
				xercesc::XMLString::transcode(
					incert.getIssuerName().c_str()));

	x509name->setAttribute(
			xercesc::XMLString::transcode("xmlns"),
			xercesc::XMLString::transcode(
				bdoc::Signature::DSIG_NAMESPACE.c_str()));

	xercesc::DOMElement *x509number =
		doc->createElement(
			xercesc::XMLString::transcode("X509SerialNumber"));

	std::ostringstream oss;
	oss << incert.getSerial();
	x509number->setTextContent(
			xercesc::XMLString::transcode(oss.str().c_str()));

	x509number->setAttribute(
			xercesc::XMLString::transcode("xmlns"),
			xercesc::XMLString::transcode(
				bdoc::Signature::DSIG_NAMESPACE.c_str()));

	xercesc::DOMNode *issuerserial =
			doc->createElement(
				xercesc::XMLString::transcode("IssuerSerial"));

	cert->appendChild(certdigest);
	issuerserial->appendChild(x509name);
	issuerserial->appendChild(x509number);
	cert->appendChild(issuerserial);

	certrefs->appendChild(cert);
	completecertrefs->appendChild(certrefs);
	root->appendChild(completecertrefs);
}

void addXMLCompleteRevocationRefs(xercesc::DOMDocument *doc,
					xercesc::DOMNode *root,
					bdoc::X509Cert& cert,
					xml_schema::Base64Binary& dig,
					const std::string& methuri,
					const std::string& producedAt)
{
	xercesc::DOMNode *dav =
		doc->createElement(
			xercesc::XMLString::transcode("DigestAlgAndValue"));

	addXMLDigestMethodAndAlgorithm(doc, dav, dig, methuri);

	xercesc::DOMElement *rid =
		doc->createElement(
			xercesc::XMLString::transcode("ResponderID"));

	xercesc::DOMElement *bn =
			doc->createElement(
				xercesc::XMLString::transcode("ByName"));

	bn->setTextContent(
			xercesc::XMLString::transcode(
				cert.getSubject().c_str()));

	xercesc::DOMElement *dt =
		doc->createElement(
			xercesc::XMLString::transcode("ProducedAt"));

	dt->setTextContent(xercesc::XMLString::transcode(producedAt.c_str()));

	xercesc::DOMElement *ocspid =
		doc->createElement(
			xercesc::XMLString::transcode("OCSPIdentifier"));

	ocspid->setAttribute(
		xercesc::XMLString::transcode("URI"),
		xercesc::XMLString::transcode("#N0"));

	xercesc::DOMNode *ocspref =
		doc->createElement(xercesc::XMLString::transcode("OCSPRef"));

	xercesc::DOMNode *ocsprefs =
		doc->createElement(xercesc::XMLString::transcode("OCSPRefs"));

	xercesc::DOMElement *revrefs =
		doc->createElement(
			xercesc::XMLString::transcode(
					"CompleteRevocationRefs"));

	rid->appendChild(bn);
	ocspid->appendChild(rid);
	ocspid->appendChild(dt);
	ocspref->appendChild(ocspid);
	ocspref->appendChild(dav);
	ocsprefs->appendChild(ocspref);
	revrefs->appendChild(ocsprefs);
	root->appendChild(revrefs);
}

