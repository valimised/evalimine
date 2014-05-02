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


#include "Signature.h"
#include "XMLHelper.h"

void addXMLEncapsulatedX509Certificate(xercesc::DOMDocument *doc,
					xercesc::DOMNode *root,
					bdoc::X509Cert& x509,
					const char *id)
{
	xercesc::DOMElement *x509val =
		doc->createElementNS(
			xercesc::XMLString::transcode(
					XADES132_NAMESPACE),
			xercesc::XMLString::transcode(
					"xades:EncapsulatedX509Certificate"));

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
		doc->createElementNS(
			xercesc::XMLString::transcode(
					XADES132_NAMESPACE),
			xercesc::XMLString::transcode("xades:CertificateValues"));

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
		doc->createElementNS(
			xercesc::XMLString::transcode(
					XADES132_NAMESPACE),
			xercesc::XMLString::transcode("xades:RevocationValues"));

	xercesc::DOMNode *ocspvalues =
		doc->createElementNS(
			xercesc::XMLString::transcode(
					XADES132_NAMESPACE),
			xercesc::XMLString::transcode("xades:OCSPValues"));

	xercesc::DOMElement *encapsulatedocsp =
		doc->createElementNS(
			xercesc::XMLString::transcode(
					XADES132_NAMESPACE),
			xercesc::XMLString::transcode(
						"xades:EncapsulatedOCSPValue"));

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

