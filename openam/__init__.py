#! /usr/bin/env python3
#
# https://gitlab.utu.fi/ttweb/exerciser/blob/master/openam.php
#
import os
import json
import pprint
import requests


class DotDict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
    def __missing__(self, key):
        """Return None if non-existing key is accessed"""
        return None

OPENAM = DotDict()
OPENAM.API_VERSION                      = '1.0'
OPENAM.LEGACY_APIS_ENABLED              = False
OPENAM.COOKIE_NAME                      = 'ssoUTUauth'
OPENAM.DOMAIN                           = '.utu.fi'
OPENAM.BASE_URL                         = 'https://sso.utu.fi/sso'
OPENAM.REALM                            = '/utu'
OPENAM.AUTHN_MODULE                     = ''
OPENAM.SERVICE_CHAIN                    = 'loginService'
# Wordpress....
OPENAM.WORDPRESS_ATTRIBUTES             = ['uid', 'mail']
OPENAM.WORDPRESS_ATTRIBUTES_USERNAME    = 'uid'
OPENAM.WORDPRESS_ATTRIBUTES_MAIL        = 'mail'
OPENAM.LOGOUT_TOO                       = 1
OPENAM.SUCCESS_REDIRECT                 = 'http://vm.utu.fi/'
OPENAM.DO_REDIRECT                      = True
OPENAM.DEBUG_ENABLED                    = False
OPENAM.DEBUG_FILE                       = "openAM.debug.txt"
OPENAM.SSLVERIFY                        = False
# OpenAM API endpoints
OPENAM.AUTHN_URI                        = '/json/authenticate'
OPENAM.ATTRIBUTES_URI                   = '/json/users/'
OPENAM.SESSION_URI                      = '/json/sessions/'
# Legacy
OPENAM.LEGACY_AUTHN_URI                 = '/identity/json/authenticate'
OPENAM.LEGACY_ATTRIBUTES_URI            = '/identity/json/attributes'
OPENAM.LEGACY_SESSION_VALIDATION        = '/identity/json/isTokenValid'
OPENAM.LEGACY_SESSION_LOGOUT            = '/identity/logout'
# Other constants
OPENAM.REALM_PARAM                      = 'realm'
OPENAM.SERVICE_PARAM                    = 'service'
OPENAM.MODULE_PARAM                     = 'module'
OPENAM.AUTH_TYPE                        = 'authIndexType'
OPENAM.AUTH_VALUE                       = 'authIndexValue'

config = {
    'OPENAM_API_VERSION':                       '1.0',
    'OPENAM_LEGACY_APIS_ENABLED':               False,
    'OPENAM_COOKIE_NAME':                       'ssoUTUauth',
    'DOMAIN':                                   '.utu.fi',
    'OPENAM_BASE_URL':                          'https://sso.utu.fi/sso',
    'OPENAM_REALM':                             '/utu',
    'OPENAM_AUTHN_MODULE':                      '',
    'OPENAM_SERVICE_CHAIN':                     'loginService',
    'OPENAM_WORDPRESS_ATTRIBUTES':              ['uid', 'mail'],    # HMMM..
    'OPENAM_WORDPRESS_ATTRIBUTES_USERNAME':     'uid',
    'OPENAM_WORDPRESS_ATTRIBUTES_MAIL':         'mail',
    'OPENAM_LOGOUT_TOO':                        1,
    'OPENAM_SUCCESS_REDIRECT':                  'http://vm.utu.fi/',
    'OPENAM_DO_REDIRECT':                       True,
    'OPENAM_DEBUG_ENABLED':                     False,
    'OPENAM_DEBUG_FILE':                        "openAM.debug.txt",
    'OPENAM_SSLVERIFY':                         False,
    # OpenAM API endpoints
    'OPENAM_AUTHN_URI':                         '/json/authenticate',
    'OPENAM_ATTRIBUTES_URI':                    '/json/users/',
    'OPENAM_SESSION_URI':                       '/json/sessions/',
    # Legacy
    'OPENAM_LEGACY_AUTHN_URI':                  '/identity/json/authenticate',
    'OPENAM_LEGACY_ATTRIBUTES_URI':             '/identity/json/attributes',
    'OPENAM_LEGACY_SESSION_VALIDATION':         '/identity/json/isTokenValid',
    'OPENAM_LEGACY_SESSION_LOGOUT':             '/identity/logout',
    # Other constants
    'REALM_PARAM':                              'realm',
    'SERVICE_PARAM':                            'service',
    'MODULE_PARAM':                             'module',
    'AUTH_TYPE':                                'authIndexType',
    'AUTH_VALUE':                               'authIndexValue'
}



# Hey, I just converted this - I did not write this...
def openam_debug(msg: str):
    print(msg)


#
# Pulls attributes from OpenAM using the existing session and username
#
def getAttributesFromOpenAM(tokenId, username, attributes):
    #Basically switches between modern and legacy functions.
    if not OPENAM.LEGACY_APIS_ENABLED:
        openam_debug('getAttributesFromOpenAM: LEGACY NOT ENABLED')
        return __getAttributesFromModernOpenAM(tokenId, username, attributes)
    #else:
    #    openam_debug('getAttributesFromOpenAM: LEGACY ENABLED')
    #    return __getAttributesFromLegacyOpenAM(tokenId, username, attributes)


#
# Pulls attributes from OpenAM using the existing session and username
#
def __getAttributesFromModernOpenAM(tokenId, username, attributes):
    #
    # Creates the proper OpenAM Attributes URL using the configured parameters
    #
    def createAttributesURL():
        attributes_url = OPENAM.BASE_URL + OPENAM.ATTRIBUTES_URI
        if not OPENAM.REALM and '/' != OPENAM.REALM:
            attributes_url = attributes_url.replace(
                '/users', OPENAM.REALM + '/users'
            )
        return attributes_url
    # 
    attributes_url = createAttributesURL()
    openam_debug(
        'getAttributesFromModernOpenAM: ATTRIBUTE URL: ' + str(attributes_url)
    )
    url = attributes_url + username + '?_fields=' + attributes
    openam_debug( 'getAttributesFromModernOpenAM: full url: ' + url )

    # Ouch... #################################################################
    response = requests.get(
        url,
        params = {'key': 'val'},
        headers = {
           OPENAM.COOKIE_NAME:  tokenId,
            'Content-Type':     'application/json'
        }
    )
    """
    ch = curl_init()
	curl_setopt($ch, CURLOPT_URL, $url);
	curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    /*TRUE to return the transfer as a string of the return value of curl_exec() instead of outputting it directly. */
	curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

	$response = array("body"=>curl_exec($ch));

	curl_close ($ch);
    """
    openam_debug(
        'getAttributesFromModernOpenAM: RAW ATTR RESPONSE: ' + str(response)
    )

    # Decode JSON response
    if response.status_code == 200:
        return response.json()
    else:
        return 0
    """
    $amResponse = json_decode( $response['body'], true );
	openam_debug( 'getAttributesFromModernOpenAM: ATTRIBUTE RESP: ' . print_r( $amResponse, true ) );
	if ( 200 == $response['response']['code'] ) {
		return $amResponse;
	} else {
		return 0;
	}

}
    """


#
# Select the attribute value :
#   if it's an array, we return the first value of it.
#   if not, we directly return the attribute value
#
def openam_get_attribute_value(attributes: list, attributeId: str) -> str:
    if( isinstance(attributes[attributeId], dict) ):
        return attributes[attributeId][0]
    else:
        return attributes[attributeId]



#
# Validate a session
#
def openam_sessionsdata(tokenId):

    response = requests.post(
        OPENAM.BASE_URL + OPENAM.SESSION_URI + tokenId,
        params = {
            'action':           'validate'
        },
        headers = {
            'Content-Type':     'application/json'
        },
        timeout = 3
    )
    print("URL: " + OPENAM.BASE_URL + OPENAM.SESSION_URI + tokenId)
    """
	$ch = curl_init();
	$url = OPENAM_BASE_URL . OPENAM_SESSION_URI . $tokenId . '?_action=validate';
	curl_setopt($ch, CURLOPT_URL, $url);
	curl_setopt($ch, CURLOPT_POST, 1);
	curl_setopt($ch, CURLOPT_POSTFIELDS, array());

	curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type' => 'application/json'));
	curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

	$isTokenValid_am_response = array("body"=>curl_exec($ch));

	curl_close ($ch);
    """
    if response.status_code == 200:
        try:
            # Raises ValueError if no JSON in body
            data = response.json()
        except ValueError:
            print("There is no JSON in the response body!")
            raise
    else:
        print("OpenAM response {}".format(response.status_code))
        print(response.text)
        try:
            print("JSON:")
            pprint.pprint(response.json())
        except:
            print("No JSON in the response body!")
        raise ValueError("OpenAM authentication FAILED!!")
    pprint.pprint(data)
    """
	openam_debug( 'openam_sessionsdata: isTokenValid_am_response ' . print_r( $isTokenValid_am_response, true ) );

	$response_string = $isTokenValid_am_response['body'];
	$response = json_decode( $response_string );

	if ( true == $response->valid ) {
		openam_debug( 'openam_sessionsdata: returning true from -> $response->valid' );

		$am_response = (array) $response;

		//openam_debug( 'openam_sessionsdata: am_response: ' . $am_response );

		return $am_response["uid"];
	}
    """

    return False



#
# Expect caller to have identified the need to authenticate AND
# to provide the cookie content
#
def openam_sso(tokenId: str) -> str:
    """Confirm if the SSO cookie for our domain contains valid authentication"""
    #if ( ( isset( $_GET['action'] ) && 'logout' == $_GET['action'] ) || ( isset( $_GET['loggedout'] ) && 'yes' == $_GET['loggedout'] ) ) {
    #   return;
    #}

    # if ( !isset( $_COOKIE[ OPENAM_COOKIE_NAME ] ) ) return;

    #$tokenId = $_COOKIE[ OPENAM_COOKIE_NAME ];
    # if ( empty( $tokenId ) ) return;
    if not tokenId:
        raise ValueError("SSO tokenID cannot be empty!")

    openam_debug( 'openam_auth: TOKENID: ' + tokenId )

    return openam_sessionsdata(tokenId)
    #if ( ! $uid = openam_sessionsdata( $tokenId ) ) return;
    #
    #return $uid;
    #
    #}

# chrome://settings/cookies/detail?site=utu.fi
#https://requests.readthedocs.io/en/master/api/#requests.Response
# https://gitlab.utu.fi/ttweb/exerciser/tree/master
if __name__ == '__main__':
    token = 'AQIC5wM2LY4SfczoFtxsflah-1X0Dy9qFWhm3_ouYtp-Uaw.*AAJTSQACMDIAAlNLABQtNDI4MzIwNjUyMzcwMDM1MTYzOQACUzEAAjA0*'
    openam_sso(token)
