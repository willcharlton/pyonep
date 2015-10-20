"""
    Module for Interface() class.
"""
import os, time, logging
from traceback import print_exc

class ILC:
    """ Enum class for specifying the meaning of each column in the 
        ifaces log file. ILC stands for Ifaces Log Columns. """
    Cik      = 0
    Time     = 1
    Iface    = 2
    RqType   = 3
    Src      = 4
    Rx       = 5
    Tx       = 6
    RqTime   = 7

class Interfaces(object):
    """
        TODO
    """
    def __init__(self):
        self.ifaces_log_file = '/var/log/ifaces.log'
        self.proc_net_dev = '/proc/net/dev'
        self.ifaces = ['eth0', 'ppp0']
        self.LOG = logging.getLogger('ifaces')

    def interfaces(self):
        """ Parses self.proc_net_dev file to determine the amount of 
            rx and tx bytes for the current time. """
        ifaces = {}
        try:
            with open(self.proc_net_dev, 'r') as net_dev:
                lines = net_dev.readlines()
                lines = lines[2:] # the first two lines are column headers, get rid of them
                for line in lines:
                    line_split = line.split(' ')
                    line_split = [ x for x in line_split if x != '' ] # lots of elements that are empty after split
                    iface = line_split[0].replace(':', '').strip()
                    rx_bytes = int(line_split[1].strip())
                    tx_bytes = int(line_split[9].strip())
                    if iface in self.ifaces:
                        ifaces[iface] = {   'rx_bytes': rx_bytes,
                                            'tx_bytes': tx_bytes,
                                            'time': time.time() }
        except:
            # in order to make this quiet with respect to logging, just fail silently
            pass
        return ifaces

    def LOG_request(self, cik, rq_type, req_source, before_request, after_request):
        """ TODO """
        source = ''
        if rq_type == 'get':
            try:
                if req_source[0] == 'list_content':
                    get_source = 'list_content:'+str(req_source[1])
                elif req_source[0] =='get_content':
                    get_source = 'get_content:'+str(req_source[1])
                elif req_source[0] =='content_info':
                    get_source = 'content_info:'+str(req_source[1])
                elif req_source[0] =='read':
                    get_source = 'read:{0}'.format(req_source[1])
                source = get_source
            except:
                pass
        elif rq_type == 'post':
            try:
                if req_source[0] == 'write':
                    post_source = 'write:'
                    if isinstance(req_source[1], str): # usually the case when writing to multiple dataports
                        elems = req_source[1].split('&')
                        if len(elems) > 0:
                            dataports = [ e.split('=')[0] for e in elems ]
                            if len(dataports) > 0:
                                # just in case something really long gets in here, force it to 30 chars.
                                post_source +=','.join(dataports[0:30])
                    elif isinstance(req_source[1], dict):
                        post_source = 'dataports:'+','.join(req_source[3].keys())
                elif req_source[0] == 'readwrite':
                    post_source = 'READ:{0} WRITE:{1}'.format(req_source[1], req_source[2])
                elif req_source[0] == 'actvt':
                    post_source = 'actvt:'+str(req_source[1])
                elif req_source[0] == 'regen':
                    post_source = 'regen:'+str(req_source[1])
                source = post_source
            except:
                pass

        try:
            # since reading a file backwards is a memory intensive ordeal in python < 3, 
            # i'm using the following scheme to prepend new log entries to the file, instead of
            # appending them. The algorithm is to create a new file with a single line that 
            # contains the new log message, then concatenate the two together using shutil

            # TODO: actually, the best thing to do to throttle check would be to calculate the read/write 
            # frequency on the fly and keep an internal dict or something to compare them against
            # a pre-determined upper-limit.

            with open(self.ifaces_log_file, 'ab') as ifile:
                for iface in before_request.keys():
                    rx_cost = abs( after_request[iface]['rx_bytes'] - before_request[iface]['rx_bytes'] )
                    tx_cost = abs( after_request[iface]['tx_bytes'] - before_request[iface]['tx_bytes'] )
                    request_time = abs( after_request[iface]['time'] - before_request[iface]['time'] )
                    # the columns in this file write are decoded in interface_report().
                    # The order of these columns are specified in the ILC enum class.
                    # make sure this write() function matches the order in ILC enum class.
                    ifile.write('{0} :: {1:.4f} :: {2} :: {3} :: {4} :: {5} :: {6} :: {7}\n'.format(
                        cik, time.time(), iface, rq_type, source, rx_cost, tx_cost, request_time))
        except:
            # in order to make this quiet with respect to logging, just fail silently
            pass


    def interface_report(self):
        report = { self.ifaces[0]: {}, self.ifaces[1]: {} }

        if(os.path.exists(self.ifaces_log_file)):
            for line in open(self.ifaces_log_file, 'r'):
                try:
                    line_split = line.split('::')
                    iface = line_split[ILC.Iface].replace("'",'').strip()

                    # check to see if we care about this interface. 
                    if iface in self.ifaces:
                        src = line_split[ILC.Src]

                        # initialize report dict for given src
                        report[iface][src] = {} if src not in report[iface].keys()\
                                                            else report[iface][src]

                        rx = int(line_split[ILC.Rx].strip())
                        tx = int(line_split[ILC.Tx].strip())
                        rq_time = "{0:.1f}".format( float(line_split[ILC.RqTime].strip()) )

                        num = report[iface][src].get('num')
                        max_rx = report[iface][src].get('max_rx')
                        max_tx = report[iface][src].get('max_tx')
                        tot_rx = report[iface][src].get('tot_rx')
                        tot_tx = report[iface][src].get('tot_tx')
                        rq_time_max = report[iface][src].get('rq_time_max')
                        rq_time_avg = report[iface][src].get('rq_tm_avg')

                        num = num + 1 if num is not None else 1
                        max_rx = rx if max_rx < rx or max_rx is None else max_rx
                        max_tx = tx if max_tx < tx or max_tx is None else max_tx
                        tot_rx = tot_rx + rx if tot_rx is not None else rx
                        tot_tx = tot_tx + tx if tot_tx is not None else tx
                        rq_time_avg = (rq_time_avg + rq_time)/float(num) if rq_time_avg is not None else rq_time
                        rq_time_max = rq_time if rq_time_max < rq_time or rq_time_max is None else rq_time_max
                        type_ = line_split[ILC.RqType].replace("'",'').strip()

                        report[iface][src] = {  'num': num,
                                                'type': type_,
                                                'max_rx': max_rx,
                                                'max_tx': max_tx,
                                                'tot_rx': tot_rx,
                                                'tot_tx': tot_tx,
                                                'rq_time_max': rq_time_max,
                                                'rq_time_avg': rq_time_avg
                        }
                except:
                    self.LOG.error("Couldn't process ifaces log. Removing it and starting over...")
                    if os.path.exists(self.ifaces_log_file):
                        os.remove(self.ifaces_log_file)
        else:
            self.LOG.warning("{!r} doesn't exist!".format(self.ifaces_log_file))
        return report

    def throttle_check(self):
        """ Read the ifaces log file and determine whether or not a given device needs to
            be denied access to making internet calls. 

            Returns a list of ciks that qualify for throttling. """
        throttled_ciks = []
        ciks = {}
        if(os.path.exists(self.ifaces_log_file)):
            # read it backwards look for 1 hour of time between requests
            for line in reversed(open(self.ifaces_log_file, 'r').readlines()):
                try:
                    line_split = line.split('::')
                    cik = line_split[ILC.Cik].replace("'",'').strip()
                    tm = float( line_split[ILC.Time].strip() )

                    # this grabs the latest time a given cik made an Exosite call
                    if cik not in ciks.keys():
                        ciks[cik] = {}
                        ciks[cik]['tm'] = tm
                        ciks[cik]['num'] = 1

                    # compare the time with the latest time
                    if cik in ciks.keys():
                        ciks[cik]['num'] += 1
                        if float( ciks[cik]['tm'] ) - tm > 3600 and int( ciks[cik]['num'] ) > 60:
                            # don't append the cik if it's already in the list we're making 
                            _ = throttled_ciks.append(cik) if cik not in throttled_ciks else None
                except:
                    self.LOG.error("Couldn't process ifaces log: {0}.".format(print_exc()))
        else:
            self.LOG.warning("{!r} doesn't exist!".format(self.ifaces_log_file))

        return throttled_ciks





