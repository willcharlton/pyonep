""" Module containing Exosite and HTTP classes, variables, and methods for use in
    device applications. """

# pylint: disable=I0011,W0312,R0903,C1001,R0201,W0232

import requests, time, logging, sys
from pyonep.device_client.ifaces import Interfaces
from pyonep.device_client.constants import formatter
from pyonep.device_client import handlers
try:
    # python 2
    from urllib import unquote_plus, quote_plus, unquote, urlencode
except:
    # python 3
    from urllib.parse import unquote_plus, quote_plus, unquote, urlencode
try:
    # python 2
    import ConfigParser
except:
    # python3
    import configparser as ConfigParser
import os, json
from pyonep.device_client.__version__ import __version__ as VERSION
try:
    # python3
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
# http_client.HTTPConnection.debuglevel = 0



class DeviceCfgSect:
    """ Enum for cfg file sections. """
    Device = 'device'

class DeviceCfgOpt:
    """ Enum for cfg file options """
    Cik = 'cik'
    Model = 'model'
    Vendor = 'vendor'
    Uuid = 'uuid'
    ActRtryInt = 'activation_retry_interval' # optional, Device() comes with default value

class Device(Interfaces):
    """
TODO
    """
    def __init__(self, user_agent, cfg_file):
        Interfaces.__init__(self)
        self.__version__ = VERSION
        self._cik = None
        self._model = None
        self._vendor = None
        self._uuid = None
        self._activated = False
        self._online = True
        self._cfg_parser = ConfigParser.RawConfigParser(allow_no_value=True)
        self._cfg_file = cfg_file
        self.LOG = logging.getLogger('device')
        streamh = logging.StreamHandler(sys.stdout) if len(self.LOG.handlers) == 0 else None
        if streamh is not None:
            streamh.setFormatter(formatter)
            self.LOG.addHandler(streamh)
        self.LOG.setLevel(logging.INFO)
        self._last_activate_try_time = 0.0
        # give it a default that can be overridden by cfg file
        self._activation_retry_interval = 300.0
        self._USER_AGENT = user_agent
        self._TIMEOUT_SECS = 15


        # BANDWIDTH THROTTLING VARS
        self._last_req_tm = 0.0
        self._throttle_period = 60*15 # 15 minutes
        # algorithm: if now - last_req_tm < _throttle_period, throttle
        # TODO: just need to figure out to get APtivator to know who's being throttled...

        self.LOG.debug("Initializing...")
        self.update_device_from_cfg()

        
        self._use_ssl = True
        self._url =             lambda: 'http{0}://{1}.m2.exosite.com/'.format('s',self._vendor) if self._use_ssl \
                                        else 'http://{0}.m2.exosite.com/'.format(self._vendor)
        self._rpc_process_url = lambda: self._url()+'onep:v1/rpc/process'
        self._rpc_content_type = 'application/json; charset=utf-8'
        self._rpc_id = 1

        self.RPC = {
                "calls": []
        }

        self._activate_url      = lambda: self._url() + 'provision/activate'
        self._content_url   = lambda: self._url() + 'provision/download?'
        self._stack_alias_url   = lambda: self._url() + 'onep:v1/stack/alias'
        self._http_accept       = 'application/x-www-form-urlencoded; charset=utf-8'
        self._http_content_type = 'application/x-www-form-urlencoded; charset=utf-8'

    def __repr__(self):
        """ Return dict to enable dynamic JSON object creation with
            objects subclassing Device(). """
        return {    'version': self.__version__ ,
                    'model':    self._model,
                    'vendor':   self._vendor,
                    'uuid':     self._uuid }
    def __str__(self):
        """ So we can print self representation by calling str(self). """
        return json.dumps(self.__repr__())

    def no_ssl(self):
        """ Turns off the usage of SSL in HTTP API."""
        self._use_ssl = False
    def use_ssl(self):
        """ Turns on the usage of SSL in HTTP API."""
        self._use_ssl = True

    def set_http_debug(self, enable):
        """ Sets http_client debug level when 'enable' is set to True. """
        if enable == True:
            http_client.HTTPConnection.debuglevel = 1
        else:
            http_client.HTTPConnection.debuglevel = 0

    def _http_listContent(self):
        """ Method for retrieving a list of Content area contents. """
        headers = { 'User-Agent' : self._USER_AGENT,
                    'X-Exosite-CIK' : self.cik()
                    }
        url= self._content_url()    +'vendor=' + quote_plus(self.vendor())\
                                        + '&model=' + quote_plus(self.model())
        request = self.send_get(url, headers, req_info=('list_content', self.model()))
        return request

    def _http_getContent(self, content_id):
        """ Method to retrieve specific content from Content area. """
        headers = { 'User-Agent' : self._USER_AGENT,
                    'X-Exosite-CIK' : self.cik()
                    }
        url= self._content_url()    +'vendor=' + quote_plus(self.vendor())\
                                        + '&model=' + quote_plus(self.model())\
                                        + '&id=' + quote_plus(content_id)
        return self.send_get(url, headers, req_info=('get_content', content_id))

    def _http_getContentInfo(self, content_id):
        """ Method to retrieve information on Content area content. """
        headers = { 'User-Agent' : self._USER_AGENT,
                    'X-Exosite-CIK' : self.cik()
                    }
        url= self._content_url()    +'info=true&vendor=' + quote_plus(self.vendor())\
                                        + '&model=' + quote_plus(self.model())\
                                        + '&id=' + quote_plus(content_id)

        return self.send_get(url, headers, req_info=('content_info', content_id))

    def _http_read(self, readList):
        '''
            readList: List of data sources to read from
        '''
        headers = { 'User-Agent' : self._USER_AGENT,
                    'X-Exosite-CIK' : self.cik(),
                    'Accept' : self._http_accept
                    }
        url= self._stack_alias_url()
        if len(readList) > 0:
            url = url + '?'
            for v in readList:
                url = url + quote_plus(v) + '&'
            # trim trailing '&'
            url = url[:-1]
        else:
            raise Exception('Tried to read from Exosite, but no alias given')
        return handlers.ReadHandler(self.send_get(url, headers, req_info=('read', readList)))

    def _http_long_poll(self, dataport, timeout_ms, modify_ts=None):
        '''
            readList: List of data sources to read from
        '''
        headers = { 'User-Agent' : self._USER_AGENT,
                    'X-Exosite-CIK' : self.cik(),
                    'Accept' : self._http_accept,
                    'Request-Timeout': str(timeout_ms)
                    }
        if modify_ts is not None:
            headers['If-Modified-Since'] = str(modify_ts)

        url= self._stack_alias_url()

        url = url + '?' + quote_plus(dataport)

        return handlers.ReadHandler(
                                    self.send_get(  url, 
                                                    headers, 
                                                    timeout=timeout_ms/1000,
                                                    req_info=('long_poll', dataport)
                                    )
                )

    def _http_write_dict(self, writeDict):
        """ Wrapper function for http_write.
            url_encodes a python dictionary and calls
            http_write.
            Cannot handle nested dicts. """
        body = urlencode(writeDict)
        resp = self._http_write(body)
        return resp

    def _http_write(self, body):
        """ Method to write to a device dataport. """
        headers = { 'User-Agent' : self._USER_AGENT,
                    'X-Exosite-CIK' : self.cik(),
                    'Content-Type' : self._http_content_type,
                    'Content-Length' : str(len(body))
                    }
        url= self._stack_alias_url()
        return handlers.WriteHandler(self.send_post(url, headers, body, req_info=('write', body)))

    def _http_readwrite(self, readList, writeDict):
        '''
            device: Device() object
            readList: List of data source to read from
            writeDict: Dictionary of k,v to write to.  (Do not url encode)
        '''
        body = urlencode(writeDict)
        headers = { 'User-Agent' : self._USER_AGENT,
                    'X-Exosite-CIK' : self.cik(),
                    'Accept' : self._http_accept,
                    'Content-Type' : self._http_content_type,
                    'Content-Length' : str(len(body))
                    }
        url= self._stack_alias_url()
        if len(readList) > 0:
            url = url + '?'
            for v in readList:
                url = url + quote_plus(v) + '&'
            url = url[:-1] # strip off last '&'
        return handlers.ReadWriteHandler(   self.send_post( url,
                                                            headers,
                                                            body,
                                                            req_info=(  'readwrite',
                                                                        readList,
                                                                        writeDict.keys()
                                                            )
                                            )
                )

    def _http_activate(self):
        """ Method to activate device.
            Returns ActivationHandler() object. """
        body =  'vendor=' + self.vendor()\
                + '&model=' + self.model()\
                + '&sn=' + self.uuid()

        headers = { 'User-Agent' : self._USER_AGENT,
                    'Content-Type' : self._http_content_type,
                    'Content-Length' : str(len(body))
                    }
        url= self._url() + 'provision/activate'
        return handlers.ActivationHandler(
                    self.send_post( url, headers, body, req_info=('actvt', self.uuid()))
                )

    def _http_regen(self, vendor_token):
        """ Method to regenerate CIK for a given device, deactivate client,
            and open 24 hour window for device to call activate. 

            This method is really only here for testing and development purposes because
            we NEVER ship a unit with the Vendor Token.
            """
        body = 'enable=true'

        headers = { 'User-Agent' : self._USER_AGENT,
                    'Content-Type' : self._http_content_type,
                    'Accept': 'text/plain, text/csv, application/x-www-form-urlencoded',
                    'Content-Length' : str(len(body)),
                    'X-Exosite-Token' : vendor_token
                    }
        url= self._url() +  'provision/manage/model/'\
                            + self.model() + '/' + self.uuid()
        return self.send_post(url, headers, body, req_info=('regen', self.uuid()))

    def url_decode(self, obj):
        """ Helper function to urllib.url_decode objects read from dataports. """
        return unquote_plus(obj)

    def send_get(self, url, headers, req_info, timeout=None):
        """ Method wrapper for requests.get().
        Input req_info: a tuple describing the type of request. Used for data usage 
                        logging and statistics collection.
         """
        before_request = self.interfaces()
        try:
            response = requests.get(    url,
                                        headers=headers,
                                        timeout=self._TIMEOUT_SECS if timeout is None else timeout,
                                        verify=True )
            after_request = self.interfaces()
        except Exception as e:
            self.LOG.debug("Caught exception {!r}".format(str(e)))
            # Treat all exceptions as Timeouts.
            # funky way of giving Requests_Response the object members it needs to perform its duties.
            return handlers.Requests_Response(type( 'requests_override',(object,),
                                                {'status_code': handlers.Http_ReadWriteCodes.Timeout,
                                                'text': str(e),
                                                'iter_content': None}))

        get_source = url
        if req_info != None:
            get_source = req_info

        self.LOG_request(self.cik(), 'get', get_source, before_request, after_request)
        return handlers.Requests_Response(response)

    def send_post(self, url, headers, body, req_info):
        """ Method wrapper for requests.post() """
        before_request = self.interfaces()
        try:
            self.LOG.debug("url = {!r} :: body = {!r}".format(url, body))
            response = requests.post(   url,
                                        data=body,
                                        headers=headers,
                                        timeout=self._TIMEOUT_SECS,
                                        verify=True )
            after_request = self.interfaces()
        except Exception as e:
            self.LOG.debug("Caught exception {!r}".format(str(e)))
            # Treat all exceptions as Timeouts.
            # funky way of giving Requests_Response the object members it needs to perform its duties.
            return handlers.Requests_Response(type( 'requests_override',(object,),
                                                {'status_code': handlers.Http_ReadWriteCodes.Timeout,
                                                'text': str(e),
                                                'iter_content': None}))
        post_source = req_info+(body,) if body is not None else req_info
        if req_info == None:
            post_source = url
        self.LOG_request(self.cik(), 'post', post_source, before_request, after_request)
        return handlers.Requests_Response(response)

    def cik(self):
        """ Protected member getter. """
        return self._cik
    def _set_cik(self, cik):
        """ Protected member setter. Sets instance member and cfg file."""
        if not self.activated():
            if(len(cik) == 40):
                self._cik = cik
                self.dump_to_device_cfg(DeviceCfgSect.Device, DeviceCfgOpt.Cik, self._cik)
                self._set_activated(True)
                self.LOG.debug("Got good cik: {!r}".format(cik[0:8]+'*'*32))
            else:
                self.LOG.debug("Not setting improper CIK: {!r}".format(cik))
        else:
            if self.cik() == cik:
                self.LOG.debug("Not setting cik since since the one in memory is the same.")
                self.LOG.debug("Setting 'activated' to True.")
                self._set_activated(True)
            elif(len(cik) != 40):
                self.LOG.debug("ERROR: Not setting new, improper CIK: {!r}".format(cik))
                self.LOG.debug("ERROR: DEACTIVATING Device: {!r}".format(
                                                                str(self)))
                self._set_activated(False)
    def model(self):
        """ Protected member getter. """
        return self._model
    def _set_model(self, model):
        """ Protected member setter. Sets instance member and cfg file."""
        self._model = model
        self.dump_to_device_cfg(DeviceCfgSect.Device, DeviceCfgOpt.Model, self._model)
    def vendor(self):
        """ Protected member getter. """
        return self._vendor
    def _set_vendor(self, vendor):
        """ Protected member setter. Sets instance member and cfg file."""
        self._vendor = vendor
        self.dump_to_device_cfg(DeviceCfgSect.Device, DeviceCfgOpt.Vendor, self._vendor)
    def uuid(self):
        """ Protected member getter. """
        return self._uuid
    def _set_uuid(self, uuid):
        """ Protected member setter. Sets instance member and cfg file."""
        self._uuid = uuid
        self.dump_to_device_cfg(DeviceCfgSect.Device, DeviceCfgOpt.Uuid, self._uuid)
    def activated(self):
        """ Protected member getter. """
        return self._activated
    def _set_activated(self, val):
        """ Protected member setter. """
        assert bool == type(val)
        self._activated = val
    def activation_retry_interval(self):
        """ Protected member getter. """
        return self._activation_retry_interval
    def _set_activation_retry_interval(self, interval):
        """ Protected member setter. """
        self._activation_retry_interval = interval
        self.dump_to_device_cfg(DeviceCfgSect.Device,
                                DeviceCfgOpt.ActRtryInt,
                                self._activation_retry_interval)
    def cfg_file(self):
        """ Protected member getter. """
        return self._cfg_file
    def _activate(self):
        """ Instead of over-riding http_activate(), here is
            logic to deal with activating self. """
        now = time.time()
        act_diff = now - self._last_activate_try_time
        if act_diff >= self.activation_retry_interval():
            if not self.activated():
                self._last_activate_try_time = now
                act_handler = self._http_activate()
                if(act_handler.activated):
                    self._set_cik(act_handler.body)
                else:
                    self.LOG.debug("Activation for {!r} failed: {!r}".format(
                        str(self) ,str(act_handler))
                    )
            else:
                self.LOG.debug("Already activated.")
        else:
            # don't print a log message. devices subclassing this will have messy log files
            pass
            # self.LOG.debug("Waiting for {0} seconds before trying to activate again".format(
            #                               self.activation_retry_interval() - act_diff))
    def http_write(self, dataport, value):
        """ Member function that uses WriteHandler(). """
        body = { dataport: value }
        self.LOG.debug("Writing '{0}'' to dataport {1}".format(value, dataport))
        write_hand = self._http_write(body)
        if(write_hand.success):
            pass
        elif(write_hand.code == handlers.Http_ReadWriteCodes.Unauthorized):
            self.LOG.debug("BAD CIK. Setting activated = False.\
Unable to write {!r} to dataport {!r}: {!r}".format(body, dataport, str(write_hand)))
            self._set_activated(False)
        else:
            self.LOG.debug("Error when trying to write {!r} to dataport {!r}: {!r}".format(
                                        body, dataport, str(write_hand)))
        self._online = write_hand.online
        return write_hand

    # TODO: can probably be the default, but adding this instead of refactoring exo_write in
    # order to maintain compatibility with other products.
    def http_write_multiple(self, write_dict):
        """ Member function that uses WriteHandler(). """
        # body = ''
        # for dataport in write_dict.keys():
        #   body += '{0}={1}&'.format(dataport, write_dict[dataport])
        # body = body[:-1] # strip off last '&'
        self.LOG.debug("Writing {0}".format(write_dict))
        write_hand = self._http_write_dict(write_dict)
        if(write_hand.success):
            pass
        elif(write_hand.code == handlers.Http_ReadWriteCodes.Unauthorized):
            self.LOG.debug("BAD CIK. Setting activated = False.\
Unable to write {!r}: {!r}".format(write_dict, str(write_hand)))
            self._set_activated(False)
        else:
            self.LOG.debug("Error when trying to write {!r}: {!r}".format(
                                        write_dict, str(write_hand)))
        self._online = write_hand.online
        return write_hand

    def http_read(self, readList):
        """ Member function that utilizes ReadHandler(). """
        read_hand = self._http_read(readList)
        if(read_hand.success):
            pass
        elif(read_hand.code == handlers.Http_ReadWriteCodes.Unauthorized):
            self.LOG.debug("BAD CIK. Setting activated = False.\
Unable to read {!r}: {!r}".format(read_hand, str(read_hand)))
            self._set_activated(False)
        else:
            self.LOG.debug("Error when trying to read from dataport(s) {!r}: {!r}".format(
                                        readList, str(read_hand)))
        self._online = read_hand.online
        return read_hand

    def http_read_write(self, readList, writeDict):
        """ Member function that utilizes ReadWriteHandler(). """
        readwrite_hand = self._http_readwrite(readList, writeDict)
        if(readwrite_hand.success):
            pass
        elif(readwrite_hand.code == handlers.Http_ReadWriteCodes.Unauthorized):
            self.LOG.debug("BAD CIK. Setting activated = False.\
Unable to read {!r} nor write {!r}: {!r}".format(readList, writeDict, str(readwrite_hand)))
            self._set_activated(False)
        else:
            self.LOG.debug("Error when trying to read from dataport(s) {!r} and write {!r}: {!r}".format(
                                        readList, writeDict, str(readwrite_hand)))
        self._online = readwrite_hand.online
        return readwrite_hand

    def add_rpc_read(self, dataport):
        """ Current design does NOT implement the following as configurable:
                - starttime: uses default of number = 0
                - endtime:   uses default of <current unix time>
                - sort:      uses default of desc
                - limit:     uses default of 1
                - selection: uses default of all
         """
        ID = self._rpc_id
        self._rpc_id+=1

        call = {
                    "procedure": "read",
                    "id": ID,
                    "arguments": [
                        # []
                    ]
                }

        call["arguments"].append( { "alias": dataport } )
        call["arguments"].append( { } ) # here's where you'd implement the stuff in docstring

        self.RPC["calls"].append(call)

        return ID

    def add_rpc_write(self, dataport, value):
        """ TODO """
        ID = self._rpc_id
        self._rpc_id+=1

        call = {
                    "procedure": "write",
                    "id": ID,
                    "arguments": [
                    ]
                }

        call["arguments"].insert(0, { "alias": dataport } )
        call["arguments"].append(value)
        self.RPC["calls"].append(call)

        return ID

    def add_rpc_recordbatch(self, dataport, args_dict):
        """ Implements the recordbatch rpc api.
            Caller must provide <timestamp> in args_dict.
            args_dict should take the form:

                {   <timestamp0>: "some_data",
                    <timestamp1>: "some_other_data",
                    ...,
                    <timestampN>: "the_last_of_the_data"
                }
        """
        ID = self._rpc_id
        self._rpc_id+=1
        call = {
                    "procedure": "recordbatch",
                    "id": ID,
                    "arguments": [
                        []
                    ]
                }


        for timestamp in args_dict.keys():
            arg = json.dumps(args_dict[timestamp])
            call["arguments"][0].append( [ timestamp, arg ] )


        call["arguments"].insert(0, { "alias": dataport } )
        self.RPC["calls"].append(call)
        return ID

    def rpc_send(self):
        """
            Converts python data to JSON, sends the RPC request and then clears the
            'calls' element of the RPC.
        """
        self.RPC["auth"] = {"cik": self.cik()}
        rpc = json.dumps(self.RPC)

        headers =   {   'User-Agent' : self._USER_AGENT,
                        'Content-Type': self._rpc_content_type,
                        'Content-Length': len(str(rpc)),
                    }

        url= self._rpc_process_url()
        before_request = self.interfaces()
        try:
            response = requests.post(   url,
                                        data=rpc,
                                        headers=headers,
                                        timeout=self._TIMEOUT_SECS,
                                        verify=True )
            after_request = self.interfaces()
        except Exception as e:
            return handlers.Rpc_Response(0, '', str(e))
        self.LOG_request(self.cik(), 'rpc_post', url, before_request, after_request)
        self.RPC['calls'] = []
        return handlers.Rpc_Response(response.status_code, response.headers, response.text)

    def udp_write(self, write_dict):
        """
            Implementation of the soon-to-be-deprecated udp API.

            Input: a dictionary. Keys are the dataport names and the value
                    are the values to write to the given dataport.

            Example:
                D = exo.exo.Device('A-User-Agent', '/path/to/cfg.file')
                D.udp_write( { 'my_dataport': json.dumps(some_data_i_need) } )
        """
        from socket import socket, AF_INET, SOCK_DGRAM
        PORT = 18494
        HOST = '{0}.m2.exosite.com'.format(self.vendor())
        msg = "cik={0}".format(self.cik())
        for dataport in write_dict.keys():
            msg+="&{0}={1}".format(dataport, write_dict[dataport])
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.connect((HOST, PORT))
        sock.send(msg)
        sock.close()

    def update_device_from_cfg(self):
        """ Updates Device instance with values from cfg. """
        self.LOG.debug("Updating member variables from config file: {!r}".format(
                                                    self.cfg_file()))
        self._cfg_parser.read(self.cfg_file())
        self._set_cik(      self._cfg_parser.get(   DeviceCfgSect.Device, DeviceCfgOpt.Cik))
        self._set_model(        self._cfg_parser.get(   DeviceCfgSect.Device, DeviceCfgOpt.Model))
        self._set_vendor(   self._cfg_parser.get(   DeviceCfgSect.Device, DeviceCfgOpt.Vendor))
        self._set_uuid(     self._cfg_parser.get(   DeviceCfgSect.Device, DeviceCfgOpt.Uuid))
        if self._cfg_parser.has_option(DeviceCfgSect.Device, DeviceCfgOpt.ActRtryInt):
            self._set_activation_retry_interval(    self._cfg_parser.getfloat(DeviceCfgSect.Device,
                                                                        DeviceCfgOpt.ActRtryInt)
            )

    def dump_to_device_cfg(self, section, option, value):
        """ Utility to dump configuration data to the instance cfg file. """  
        if(os.path.exists(self.cfg_file())):
            with open(self.cfg_file(), 'r') as cfg:
                self._cfg_parser.readfp(cfg)
                if(self._cfg_parser.has_section(section)):
                    self._cfg_parser.set(section, option, value)
                else:
                    self.LOG.debug("Unable to dump: '{!r}' '{!r}' '{!r}'".format(
                                                section, option, value))
                    return # don't bother writing it, we didn't update anything.
            # When power was lost to the 400AP, cfg files would end up empty.
            # write to a tmp file, then copy it over to avoid this problem
            SAFE_BKP = os.path.join(os.path.dirname(
                    os.path.abspath(self._cfg_file)), 'SAFE_BKP.cfg'
            )
            with open(SAFE_BKP, 'wb') as cfg_safe_bkp:
                self._cfg_parser.write(cfg_safe_bkp)
            if len(open(SAFE_BKP, 'r').readlines()) > 1:
                os.rename(SAFE_BKP, self._cfg_file)
            else:
                self.LOG.debug("Backup state file was garbage.")
        else:
            self.LOG.debug("Can't find configuration file: {!r}".format(self.cfg_file()))

