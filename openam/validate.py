#! /usr/bin/env python3
#
#   OpenAM/UTU SSO - Validate authentication
#
#   validate.py
#   0.1.0   Jani Tammi  Initial version
#
#
#   Based on another feature rip (from WordPress OpenAM plugin);
#   https://gitlab.utu.fi/ttweb/exerciser/blob/master/openam.php
#
#   UTU SSO stores the authentication tokenId into a '.utu.fi' -domain
#   cookie named 'ssoUTUauth' (available for secure connections only).
#
#   By POST'ing to a REST API endpoint with URL parameter _action=validate,
#   we get either reply; { 'valid': False } or { 'valid': True, ... }.
#
#   Along with valid response, we will get UID (for example; 'jasata') and
#   'realm', which isn't very clear to me what it is or does.
#   {'realm': '/utu', 'uid': 'jasata', 'valid': True}
#
# https://requests.readthedocs.io/en/master/api/#requests.Response
# https://gitlab.utu.fi/ttweb/exerciser/tree/master
#
import json
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
OPENAM.COOKIE_NAME                      = 'ssoUTUauth'
OPENAM.BASE_URL                         = 'https://sso.utu.fi/sso'
OPENAM.SESSION_URI                      = '/json/sessions/'



def _getsession(tokenId: str) -> str:
    if not tokenId:
        return None
    response = requests.post(
        OPENAM.BASE_URL + OPENAM.SESSION_URI + tokenId,
        params = {
            '_action':           'validate'
        },
        headers = {
            'Content-Type':     'application/json'
        },
        timeout = 3
    )
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

def validate_session(tokenId: str) -> str:
    """Check if SSO tokenId (from cookie ssoUTUauth) contains valid authentication/session. This function returns an UID or None."""
    if OPENAM.COOKIE_NAME in request.cookies:
        return _getsession(request.cookies.get(OPENAM.COOKIE_NAME))
    
    #if ( ( isset( $_GET['action'] ) && 'logout' == $_GET['action'] ) || ( isset( $_GET['loggedout'] ) && 'yes' == $_GET['loggedout'] ) ) {
    #   return;
    #}

    # if ( !isset( $_COOKIE[ OPENAM_COOKIE_NAME ] ) ) return;

    #$tokenId = $_COOKIE[ OPENAM_COOKIE_NAME ];
    # if ( empty( $tokenId ) ) return;
    if not tokenId:
        raise ValueError("SSO tokenID cannot be empty!")

    openam_debug( 'openam_auth: TOKENID: ' + tokenId )







if __name__ == '__main__':
    # chrome://settings/cookies/detail?site=utu.fi
    token = 'AQIC5wM2LY4Sfcy_j6fPt4QY_utAejx3JgEUGq7uqZNcoH0.*AAJTSQACMDIAAlNLABQtNzA2MjU0MTQwOTgwMjQ0ODY4NQACUzEAAjAx*'
    openam_sso(token)


# EOF