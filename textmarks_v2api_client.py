"""
* TextMarks V2 API Client Library (Python). v2.65a.
* ---------------------------------------------------------------------------
*
* TextMarks provides a text-messaging platform you can integrate into
* your own applications to send and receive text messages to individual
* users or groups of users.
*
* For full online documentation, visit:
*   http://www.textmarks.com/api/
*   http://www.textmarks.com/
*
* The HTTP API that this library integrates with is NOT REQUIRED.
* You can do all kinds of wonderful things without this API and without
* writing any code at all.  However if you wish to automate and integrate
* TextMarks more deeply into your applications, this API may be useful.
*
* This optional Python client library provides one way to integrate with
* the platform's HTTP API from your Python applications.
*
* This library requires:
*  - Python 2.5 or greater.
*
* ---------------------------------------------------------------------------
* @author Dan Kamins [d k a m i n s A.T t e x t m a r k s D.O.T c o m]
* @package tmAPIClient
* ---------------------------------------------------------------------------
* Copyright (c) 2009, TextMarks Inc. All rights reserved.
* ---------------------------------------------------------------------------
*
* THIS PROGRAM IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OR
* CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED INCLUDING, WITHOUT
* LIMITATION, ANY WARRANTIES OR CONDITIONS OF TITLE, NON-INFRINGEMENT,
* MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.
*
* RECIPIENT IS SOLELY RESPONSIBLE FOR DETERMINING THE APPROPRIATENESS
* OF USING AND DISTRIBUTING THE PROGRAM AND ASSUMES ALL RISKS ASSOCIATED
* WITH ITS EXERCISE OF RIGHTS UNDER THIS AGREEMENT, INCLUDING BUT NOT
* LIMITED TO THE RISKS AND COSTS OF PROGRAM ERRORS, COMPLIANCE WITH
* APPLICABLE LAWS, DAMAGE TO OR LOSS OF DATA, PROGRAMS OR EQUIPMENT,
* AND UNAVAILABILITY OR INTERRUPTION OF OPERATIONS.
*
* NEITHER RECIPIENT NOR ANY CONTRIBUTORS SHALL HAVE ANY LIABILITY FOR
* ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
* DAMAGES (INCLUDING WITHOUT LIMITATION LOST PROFITS), HOWEVER CAUSED AND
* ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OR
* DISTRIBUTION OF THE PROGRAM OR THE EXERCISE OF ANY RIGHTS GRANTED
* HEREUNDER, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
*
"""

# ----------------------------------------------------------------------------

import urllib
import urllib2
try:
    import json                # introduced in Python 2.6
except:
    import simplejson as json  # same library - get it from http://pypi.python.org/pypi/simplejson/2.0.9

# ----------------------------------------------------------------------------

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class RPCTransportError(Error):
    """Exception raised for HTTP transport error (non-200 response).

    Attributes:
        code -- HTTP numeric response code
    """

    def __init__(self, code):
        self.code = code

class RPCResultError(Error):
    """Exception raised for non-successful result codes (from API execution).

    Attributes:
        code -- API numeric result code (rescode).
        msg -- API result message (resmsg).
    """

    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
        
    def __str__(self):
        return "ResultError #%d: %s" % (self.code, self.msg)

# ----------------------------------------------------------------------------

class Client(object):

    API_URL_BASE      = 'http://py1.api2.textmarks.com'

    def __init__(self, api_key=None, auth_user=None, auth_pass=None):
        """
        Create TextMarksV2APIClient around indicated authentication info (optional).
        
        api_key    string  ( register at https://www.textmarks.com/manage/account/profile/api_keys/ ). (None for none).
        auth_user  string  Phone# or TextMarks username to authenticate to API with. (None for none).
        auth_pass  string  TextMarks Password associated with sAuthUser. (None for none).
        """
        self.api_key = api_key
        self.auth_user = auth_user
        self.auth_pass = auth_pass

    def rpc_raw(self, package, method, args):
        """
        Make actual RPC call and return raw unparsed urllib2 response.

        package   string    API Package name, eg 'GroupLeader'.
        method    string    API Method name, eg 'broadcast_message'.
        args      dict      Parameters for the particular API method.
        
        Raises RPCTransportError.
        """
        def make_url():
            return "%s/%s/%s/" % (self.API_URL_BASE, package, method)
        def make_wire_args():
            iargs = {}
            if self.api_key:
                iargs['api_key'] = self.api_key
            if self.auth_user:
                iargs['auth_user'] = self.auth_user
            if self.auth_pass:
                iargs['auth_pass'] = self.auth_pass
            iargs.update(args)
            return dict(iargs)

        wire_args = make_wire_args()
        try:
            response = urllib2.urlopen(url=make_url(),
                                    data=urllib.urlencode(wire_args))
        except urllib2.HTTPError, e:
            raise RPCTransportError("RPC %s/%s got HTTP response code: %d" % (package, method, e.code))
        return response

    def rpc_json(self, package, method, args):
        """
        Make actual RPC call and return decoded response JSON data (with ['head'] and ['body']).
    
        package   string    API Package name, eg 'GroupLeader'.
        method    string    API Method name, eg 'broadcast_message'.
        args      dict      Parameters for the particular API method.
        
        Raises RPCTransportError or RPCResultError.
        """
        response = self.rpc_raw(package, method, args)
        data = json.loads(response.read())
        if data['head']['rescode'] != 0:
            raise RPCResultError(data['head']['rescode'], data['head']['resmsg'])
        return data


# ----------------------------------------------------------------------------


def example_usage():
    """Example code to demonstrate how you might call the API."""

    try:
        # Most basic echo test:
        print "Echo test..."
        tmapi = Client()
        resp = tmapi.rpc_json('Test', 'echo', {
            'str': "Hello world"
            })
        print resp

        # Check a keyword status:
        print "Keyword status test..."
        my_api_key = 'MyAPIKEY_12345678'
        keyword    = 'MYKEYWORD'
        tmapi = Client(api_key=my_api_key)
        resp = tmapi.rpc_json('Anybody', 'keyword_status', {
            'keyword': keyword
            })
        print resp
        print "Keyword Status Code: %s" % resp['body']['status']

        # Invite a user to join a TextMark group:
        print "Invite a user to join a TextMark group test...\n"
        my_api_key = 'MyAPIKEY_12345678'
        keyword    = 'MYKEYWORD'
        phone      = '4155551212'
        tmapi = Client(api_key=my_api_key)
        resp = tmapi.rpc_json('Anybody', 'invite_to_group', {
            'tm': keyword,
            'user': phone
            })
        print resp

        # Broadcast a message to a TextMark group:
        print "Broadcasting a message to a TextMark group test...\n"
        my_api_key = 'MyAPIKEY_12345678'
        my_textmarks_user = 'mytmuser'   # (or my TextMarks phone#)
        my_textmarks_pass = 'mytmp@$$word'
        keyword    = 'MYKEYWORD'
        message    = "This is an alert sent from the Python API Client. Did it work?"
        tmapi = Client(api_key=my_api_key, auth_user=my_textmarks_user, auth_pass=my_textmarks_pass)
        resp = tmapi.rpc_json('GroupLeader', 'broadcast_message', {
            'tm': keyword,
            'msg': message
            })
        print resp
    except (RPCTransportError, RPCResultError), e:
        print "Whoops... Exception caught!"
        print "Error code: %d" % e.code
        print "Exception: %s" % e

if __name__ == '__main__':
    example_usage()
    