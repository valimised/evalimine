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

#include <xercesc/dom/DOM.hpp>
#include "xml/xmldsig-core-schema.hxx"
#include "xml/XAdES.hxx"
#include "crypto/X509Cert.h"

void addXMLEncapsulatedX509Certificate(xercesc::DOMDocument *doc,
					xercesc::DOMNode *root,
					bdoc::X509Cert& x509,
					const char *id);

void addXMLCertificateValues(xercesc::DOMDocument *doc,
				xercesc::DOMNode *root,
				bdoc::X509Cert& ocspCert,
				bdoc::X509Cert& issuerCert);

void addXMLRevocationValues(xercesc::DOMDocument *doc,
				xercesc::DOMNode *root,
				xml_schema::Base64Binary& resp);


