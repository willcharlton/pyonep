"""
    Container module for RPC, HTTP and other API handler classes.
"""
#pylint: disable=R0903,W0232,C1001,W0312
import json
try:
    # python 2
    from urllib import unquote_plus, unquote
except:
    # python 3
    from urllib.parse import unquote_plus, unquote

class Http_ActivationCodes:
    """ Enum class for http response codes from Activation attempts.
        
        Copied from http://docs.exosite.com/http/#activate 04/16/2015
        HTTP/1.1 200 OK
        Date: <date>
        Server: <server>
        Connection: Keep-Alive
        Content-Length: <length>
        Content-Type: text/plain; charset=utf-8

        <cik>
        Response may also be:
        HTTP/1.1 404 Not Found if the client described by <vendor>, <model>,
            <sn> is not found on the system.
        HTTP/1.1 409 Conflict if the serial number is not enabled for activation.
        See HTTP Responses for a full list of responses

    """
    Timeout = 0
    OK = 200
    DeviceNotin1P = 403
    NotFound = 404
    NotEnabled = 409

class Http_ReadWriteCodes:
    """ Enum class for http response codes from dataport Read, Write and ReadWrite attempts.

        Copied from docs.exosite.com/data/#http 04/16/2015

        Typical HTTP response codes include:
        Code    Response        Description
        200     OK              Successful request, returning requested values
        204     No Content      Successful request, nothing will be returned
        4xx     Client Error    There was an error* with the request by the client
        401     Unauthorized    No or invalid CIK
        5xx     Server Error    There way an error with the request on the server

        * Note: aliases that are not found are not considered errors in the request.
        See the documentation for read, and write and Hybrid write/read for details.
    """
    Timeout = 0
    OK = 200
    NoContent = 204
    Unauthorized = 401
    ClientErrors = [ 400 ]+[ c for c in range(402, 500) ]
    ServerErrors = [ c for c in range(500, 600) ]

class Http_Response():
    """ Container class for http responses. """
    def __init__(self, responseCode, responseBody):
        self.code = responseCode
        self.body = responseBody
    def __repr__(self):
        return 'code: {!r}, body: {!r}'.format(self.code, self.body)

class Requests_Response():
    """ Container class for requests responses. """
    def __init__(self, response):
        self.code = response.status_code
        self.body = response.text
        self.iter_content = response.iter_content
    def __repr__(self):
        return 'code: {!r}, body: {!r}, iter_content: {!r}'.format(
            self.code, self.body, self.iter_content)

class ActivationHandler(object):
    """ Class to handle Device() activations.

        Input: Requests_Response() object generated from Exosite Activation Request.

        Object contains 'code', 'body', and 'activated' member variables.

            If successfully Activated, member variables will contain:
                code = 200
                body = '<cik>'
                activated = True
            If successfully Activated, but got a bad cik, member variables will contain:
                code = 200
                body = '<bad cik>'
                activated = False
            Otherwise:
                code = <http response code>
                body = 'an informative message'
                activated = False

        Example usage:
            activation_resp = exo_urllib2.ActivationHandler(
                                 exo.Exo().exosite_activate(    uuid,
                                                                vendor,
                                                                msg.model
                                                            )   )

            # determine whether or not provisioning/activation worked
            if(act_resp.activated):
                my_cik = act_resp.body
            else:
                print("Activation attempt FAILED: {!r}".format(act_resp.body))
    """
    def __init__(self, http_response):
        self.code = http_response.code
        self.body = http_response.body
        self.activated = False

        if self.code == Http_ActivationCodes.OK:
            if len(self.body) == 40:
                self.activated = True
        elif self.code == Http_ActivationCodes.NotFound:
            self.body = "Client described by <vendor>, <model>, <sn> is not found on the system."
        elif self.code == Http_ActivationCodes.DeviceNotin1P:
            self.body = "Received 403 from activation attempt. Device Not in 1P"
        elif self.code == Http_ActivationCodes.NotEnabled:
            self.body = "Received 409 from activation attempt. Device Not Enabled"
        elif self.code == Http_ActivationCodes.Timeout:
            self.body = "Request timed out"
        else:
            self.body = "Response code: {" + str(self.code) + "} :: Something went wrong."
    def __repr__(self):
        return 'Response code: {!r}, Response body: {!r}, Activation success: {!r}'.format(
                        self.code, self.body, self.activated)

class WriteHandler(object):
    """
TODO
    """
    def __init__(self, http_response):
        self.code = http_response.code
        self.body = http_response.body
        self.online = True
        self.success = False

        if self.code == Http_ReadWriteCodes.OK or self.code == Http_ReadWriteCodes.NoContent:
            self.success = True
        elif self.code == Http_ReadWriteCodes.Unauthorized:
            self.body = "No or invalid CIK."
        elif self.code in Http_ReadWriteCodes.ClientErrors:
            self.body = "Response code: {" + str(self.code) + "} :: \
There was an error* with the request by the client."
        elif self.code in Http_ReadWriteCodes.ServerErrors:
            self.body = "Response code: {" + str(self.code) + "} :: \
There way an error with the request on the server."
        elif self.code == Http_ReadWriteCodes.Timeout:
            self.online = False
    def __repr__(self):
        return 'Response code: {!r}, Response body: {!r}, success: {!r}'.format(
                        self.code, self.body, self.success)

class ReadHandler(object):
    """
Hard-wired to urllib.unquote(url).decode('utf-8') all
responses.
    """
    def __init__(self, http_response):
        self.code = http_response.code
        self.body = unquote_plus(http_response.body).decode('utf-8')
        self.online = True
        self.success = False

        if self.code == Http_ReadWriteCodes.OK or self.code == Http_ReadWriteCodes.NoContent:
            self.success = True
        elif self.code == Http_ReadWriteCodes.Unauthorized:
            self.body = "No or invalid CIK."
        elif self.code in Http_ReadWriteCodes.ClientErrors:
            self.body = "There was an error* with the request by the client."
        elif self.code in Http_ReadWriteCodes.ServerErrors:
            self.body = "There way an error with the request on the server."
        elif self.code == Http_ReadWriteCodes.Timeout:
            self.online = False
    def __repr__(self):
        return 'Response code: {!r}, Response body: {!r}, success: {!r}'.format(
                        self.code, self.body, self.success)

class ReadWriteHandler(object):
    """
Hard-wired to urllib.unquote(url).decode('utf-8') all
responses.
    """
    def __init__(self, http_response):
        self.code = http_response.code
        self.body = unquote(http_response.body).decode('utf-8')
        self.online = True
        self.success = False

        if self.code == Http_ReadWriteCodes.OK or self.code == Http_ReadWriteCodes.NoContent:
            self.success = True
        elif self.code == Http_ReadWriteCodes.Unauthorized:
            self.body = "No or invalid CIK."
        elif self.code in Http_ReadWriteCodes.ClientErrors:
            self.body = "There was an error* with the request by the client."
        elif self.code in Http_ReadWriteCodes.ServerErrors:
            self.body = "There way an error with the request on the server."
        elif self.code == Http_ReadWriteCodes.Timeout:
            self.online = False
    def __repr__(self):
        return 'Response code: {!r}, Response body: {!r}, success: {!r}'.format(
                        self.code, self.body, self.success)

class Rpc_Response():
    """ Container class for Exosite RPC reponse objects."""
    def __init__(self, return_code, headers, body):
        self.code = return_code
        self.headers = headers
        self.body = body
    def __repr__(self):
        return 'code: {!r}, headers: {!r}, body: {!r}'.format(
                self.code, self.headers, self.body)

class Rpc_JSONStatusCodes:
    """ Enum class for Exosite JSON RPC status codes."""
    OK = 'ok'

class Rpc_JSONErrorCodes:
    """ Enum class for Exosite JSON RPC error codes."""
    Form = 400
    Auth = 401
    Plat = 500
    ProcArgs = 501

class Rpc_Ternary:
    """ Ternary logic for Rpc API response objects. """
    false = False
    true = True
    partial = None

class RPC_RecordBatchHandler(object):
    """ RPC procedure 'recordbatch' returns JSON that  """
    def __init__(self, rpc_response, call_id):
        # print("Raw response from RPC: {!r}".format(str(rpc_response)))
        self.http_code = rpc_response.code
        self.body = unquote(rpc_response.body).decode('utf-8')
        self.error = None
        self.success = Rpc_Ternary.false
        self.auth = True
        self.failed_records = None
        try:
            self.body_obj = json.loads(self.body)
        except Exception:
            self.body_obj = None

        if self.body_obj is not None:
            if type(self.body_obj) is list:
                for call in self.body_obj:

                    # body can contain any RPC API procedure type, get the recordbatch one.
                    if call['id'] == call_id:
                        if 'status' in call:
                            status = call['status']
                            if Rpc_JSONStatusCodes.OK == status:
                                # set to Partial success if atleast 1 is successful
                                # promote to True, below if failed_records is None
                                self.success = Rpc_Ternary.true
                            else:
                                self.success = Rpc_Ternary.partial
                                self.failed_records = { 
                                    call['id']: [ record for record in status ]
                                }
                                print("Failed calls: {!r}".format(self.failed_records))

            # this check is here because the docs differentiate between
            # type dict and type list with certain error conditions, though
            # I have never seen this code actually used. ~Will 04/20/2015
            elif type(self.body_obj) is dict:
                # an error occurred
                self.success = Rpc_Ternary.false
                self.error = self.body_obj['error']
                code = self.error['code']
                if Rpc_JSONErrorCodes.Form == code:
                    pass
                elif Rpc_JSONErrorCodes.Auth == code:
                    self.auth = False
                elif Rpc_JSONErrorCodes.Plat == code:
                    pass
        else:
            if self.http_code == Http_ReadWriteCodes.Timeout:
                print("RPC Request timeout!")
            elif self.http_code == Rpc_JSONErrorCodes.Auth:
                self.auth = False
            else:
                # for now, I want to know if the response is improperly formatted JSON
                print("RPC_ReadHandler :: Improperly formatted JSON!!!")
    def __repr__(self):
        return 'http_code: {!r}, error: {!r}, success: {!r}, auth: {!r}, body: {!r}'.format(
                self.http_code, self.error, self.success, self.auth, self.body)

class RPC_ReadHandler(object):
    """ TODO """
    def __init__(self, rpc_response, call_id):
        # print("Raw response from RPC: {!r}".format(str(rpc_response)))
        self.http_code = rpc_response.code
        self.body = rpc_response.body
        self.error = None
        self.success = Rpc_Ternary.false
        self.auth = True
        self.read_value = None
        try:
            self.body_obj = json.loads(self.body)
        except Exception:
            self.body_obj = None
        if self.body_obj is not None:
            if type(self.body_obj) is list:
                for call in self.body_obj:

                    # body can contain any RPC API procedure type, get the recordbatch one.
                    if call['id'] == call_id:
                        if 'status' in call:
                            status = call['status']
                            if Rpc_JSONStatusCodes.OK == status:
                                self.success = Rpc_Ternary.true
                                # it's possible that there's noting in the dataport. In this case,
                                # we will see something like: {"id":3,"status":"ok","result":[]}
                                result = call["result"]
                                if len(result) > 0:
                                    # don't need timestamp/element-0
                                    _, self.read_value = result[0][0], result[0][1]
                        if 'error' in call:
                            self.success = Rpc_Ternary.false
                            self.error = call['error']
                            if Rpc_JSONErrorCodes.Auth == self.error['code']:
                                self.auth = False

                    if self.read_value != None:
                        self.success = Rpc_Ternary.true

            # this check is here because the docs differentiate between
            # type dict and type list with certain error conditions, though
            # I have never seen this code actually used. ~Will 04/20/2015
            elif type(self.body_obj) is dict:
                # an error occurred
                self.success = Rpc_Ternary.false
                self.error = self.body_obj['error']
                code = self.error['code']
                if Rpc_JSONErrorCodes.Form == code:
                    pass
                elif Rpc_JSONErrorCodes.Auth == code:
                    self.auth = False
                elif Rpc_JSONErrorCodes.Plat == code:
                    pass
        else:
            if self.http_code == Http_ReadWriteCodes.Timeout:
                print("RPC Request timeout!")
            else:
                # for now, I want to know if the response is improperly formatted JSON
                print("RPC_ReadHandler :: Improperly formatted JSON!!!")
    def __repr__(self):
        return 'http_code: {!r}, error: {!r}, success: {!r}, auth: {!r}, body: {!r}'.format(
                self.http_code, self.error, self.success, self.auth, self.body)

class RPC_WriteHandler(object):
    """ TODO """
    def __init__(self, rpc_response, call_id):
        # print("Raw response from RPC: {!r}".format(str(rpc_response)))
        self.http_code = rpc_response.code
        self.body = rpc_response.body
        self.error = None
        self.success = Rpc_Ternary.false
        self.auth = True
        try:
            self.body_obj = json.loads(self.body)
        except Exception:
            self.body_obj = None
        if self.body_obj is not None:
            if type(self.body_obj) is list:
                for call in self.body_obj:

                    # body can contain any RPC API procedure type, get the recordbatch one.
                    if call['id'] == call_id:
                        if 'status' in call:
                            status = call['status']
                            if Rpc_JSONStatusCodes.OK == status:
                                self.success =  Rpc_Ternary.true

            # this check is here because the docs differentiate between
            # type dict and type list with certain error conditions, though
            # I have never seen this code actually used. ~Will 04/20/2015
            elif type(self.body_obj) is dict:
                # an error occurred
                self.success = Rpc_Ternary.false
                self.error = self.body_obj['error']
                code = self.error['code']
                if Rpc_JSONErrorCodes.Form == code:
                    pass
                elif Rpc_JSONErrorCodes.Auth == code:
                    self.auth = False
                elif Rpc_JSONErrorCodes.Plat == code:
                    pass
        else:
            if self.http_code == Http_ReadWriteCodes.Timeout:
                print("RPC Request timeout!")
            else:
                # for now, I want to know if the response is improperly formatted JSON
                print("RPC_ReadHandler :: Improperly formatted JSON!!!")

