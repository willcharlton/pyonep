"""
    Test execution instructions:
    $ ls 
        exo/
            README
            exo/
            setup.py
            test/
    $ pwd
    <basepath>/exo
    $ python -m test.test_rpc
    OR

    $ python -m unittest discover test
"""

# pylint: disable=R0201

import unittest, os
import pyonep.device_client
import pyonep.device_client.handlers as handlers
from time import sleep, time

USER_AGENT = 'Test_Exo_Rpc'
MODEL = 'aptivator_v1'
UUID = 'ap:ti:va:to:rt:st'
TEST_DEV_CFG_FILE = 'dev.cfg'

# These are set, first, in the Jenkins Job Configuration for APtivator,
# then by the test_aptivator.sh jenkins script. This keeps the vendor
# and vendor token info out of the git repo.
print("PWD: {0}".format(os.path.abspath(os.path.curdir)))
VENDOR = open(os.path.join(os.environ['WHITELABEL_PATH'],'WHITELABEL_VENDOR'), 'r').readline().strip()
VENDOR_TOKEN = open(os.path.join(os.environ['WHITELABEL_PATH'],'WHITELABEL_TOKEN'), 'r').readline().strip()
print("VENDOR = {0}".format(VENDOR))
print("VENDOR TOKEN = {0}".format(VENDOR_TOKEN))

class Test_Rpc(unittest.TestCase):
    """ Unittest to test various scenarios with the RPC API implemented in pyonep.device_client. """
    @classmethod
    def setUpClass(cls):
        # file should be ConfigParser compatible.
        open(TEST_DEV_CFG_FILE, 'wb').write("""[device]
cik = ''
model = {0}
vendor = {1}
uuid = {2}
""".format(MODEL, VENDOR, UUID))

        # it is probably wrong, philosophically, to used code you intend to
        # test in order to set up for that test, but I'm doing it anyways
        D = pyonep.device_client.Device(USER_AGENT, TEST_DEV_CFG_FILE)
        regen_success = D._http_regen(VENDOR_TOKEN)
        print("What happened here: {}".format(str(regen_success)))
        assert regen_success.code == 205

    @classmethod
    def tearDownClass(cls):
        """ Remove test file. """
        os.remove(TEST_DEV_CFG_FILE)
        # os.remove(TEST_CFG_FILE)

    def setUp(self):
        # flush all data from dataport 'none'
        print("SET UP: Clearing none dataport!")

        R = pyonep.device_client.Device(USER_AGENT, TEST_DEV_CFG_FILE)
        
        R._activate()
        R.RPC["calls"].append(
                {   "procedure": "flush",
                    "id": 1,
                    "arguments":[ {"alias":"none"} ] } 
            )
        R.rpc_send()

    def test_1_RPC_1_recordbatch_call_success(self):
        """ TODO """
        Test_ID = 1
        print("\n\nSTARTING TEST {!r}".format(Test_ID))
        R = pyonep.device_client.Device(USER_AGENT, TEST_DEV_CFG_FILE)
        data = { int(time() - 10): 'dummy+data' }
        Test_ID = R.add_rpc_recordbatch('none', data)
        recordbatch_response = handlers.RPC_RecordBatchHandler( R.rpc_send(), Test_ID )
        self.assertEquals(recordbatch_response.http_code, handlers.Http_ReadWriteCodes.OK)
        self.assertEquals(recordbatch_response.error, None)
        self.assertEquals(recordbatch_response.success, handlers.Rpc_Ternary.true)
        self.assertTrue(R.activated())
        self.assertEquals(None, recordbatch_response.failed_records)

    def test_2_RPC_2_calls_that_works(self):
        """ TODO """
        Test_ID = 2
        print("\n\nSTARTING TEST {!r}".format(Test_ID))
        R = pyonep.device_client.Device(USER_AGENT, TEST_DEV_CFG_FILE)
        
        now = int(time())
        data = { now - 60: 'one minute ago', now - 2*60: 'two minutes ago' }
        Test_ID = R.add_rpc_recordbatch('none', data)
        recordbatch_response = handlers.RPC_RecordBatchHandler( R.rpc_send(), Test_ID )
        self.assertEquals(recordbatch_response.http_code, handlers.Http_ReadWriteCodes.OK)
        self.assertEquals(recordbatch_response.error, None)
        self.assertEquals(recordbatch_response.success, handlers.Rpc_Ternary.true)
        self.assertTrue(R.activated())
        self.assertEquals(None, recordbatch_response.failed_records)

    def test_3_RPC_2_calls_1_that_fails(self):
        """ TODO """
        Test_ID = 3
        print("\n\nSTARTING TEST {!r}".format(Test_ID))
        R = pyonep.device_client.Device(USER_AGENT, TEST_DEV_CFG_FILE)
        
        now = int(time())
        timestamp_that_fails = "blah dee blah"
        data = { timestamp_that_fails: 'now, then', now - 2*62: '64 seconds ago' }
        Test_ID = R.add_rpc_recordbatch('none', data)
        recordbatch_response = handlers.RPC_RecordBatchHandler( R.rpc_send(), Test_ID )
        self.assertEquals(recordbatch_response.http_code, handlers.Http_ReadWriteCodes.OK)
        self.assertEquals(recordbatch_response.error, None)
        self.assertNotEquals(recordbatch_response.success, handlers.Rpc_Ternary.true)
        self.assertTrue(R.activated())
        self.assertFalse(None == recordbatch_response.failed_records)
        self.assertIn(timestamp_that_fails, recordbatch_response.failed_records[Test_ID][0])

    def test_4_RPC_bad_call_should_return_dict(self):
        """ TODO """
        Test_ID = 4
        print("\n\nSTARTING TEST {!r}".format(Test_ID))
        R = pyonep.device_client.Device(USER_AGENT, TEST_DEV_CFG_FILE)
        
        R._cik = 'a'*40 # force OneP to return a dict by corrupting cik
        print(R.cik())
        now = int(time()) - 60
        # timestamp_that_fails = "blo da bleer"
        data = { now: 'there is no way this should work' }
        Test_ID = R.add_rpc_recordbatch('dataport_that_doesnt_exist', data)
        recordbatch_response = handlers.RPC_RecordBatchHandler( R.rpc_send(), Test_ID )
        print(str(recordbatch_response))
        self.assertEquals(recordbatch_response.http_code, handlers.Http_ReadWriteCodes.OK)
        print(recordbatch_response.error)
        self.assertNotEquals(recordbatch_response.error, None)
        self.assertEquals(recordbatch_response.success, handlers.Rpc_Ternary.false)
        self.assertTrue(None == recordbatch_response.failed_records)
        self.assertFalse(recordbatch_response.auth)

    def test_5_read_succeeds_but_recordbatch_fails(self):
        """ TODO """
        Test_ID = 5
        print("\n\nSTARTING TEST {!r}".format(Test_ID))
        data_to_read_back = 'm++  test_5 12354'
        R = pyonep.device_client.Device(USER_AGENT, TEST_DEV_CFG_FILE)
        R.http_write('none', data_to_read_back)
        sleep(1.1)
        
        read_ID = R.add_rpc_read('none')
        timestamp_that_fails = "blerp dum dee bleek"
        data = { timestamp_that_fails: 'i wish everything were easy' }
        recbatch_ID = R.add_rpc_recordbatch('none', data)
        rpc_resp = R.rpc_send()
        recordbatch_response = handlers.RPC_RecordBatchHandler( rpc_resp, recbatch_ID )
        read_resp = handlers.RPC_ReadHandler(rpc_resp, read_ID)
        # check http code
        self.assertEquals(recordbatch_response.http_code, handlers.Http_ReadWriteCodes.OK)
        self.assertEquals(read_resp.http_code, handlers.Http_ReadWriteCodes.OK)

        # check error
        self.assertEquals(recordbatch_response.error, None)
        self.assertEquals(read_resp.error, None)

        # check success
        self.assertEquals(recordbatch_response.success, handlers.Rpc_Ternary.partial)
        self.assertEquals(read_resp.success, handlers.Rpc_Ternary.true)

        self.assertTrue(R.activated())

        # check data
        self.assertFalse(None == recordbatch_response.failed_records)
        self.assertIn(timestamp_that_fails, recordbatch_response.failed_records[recbatch_ID][0])
        self.assertEquals(data_to_read_back, read_resp.read_value)

    def test_6_read_succeeds_write_succeeds_record_batch_succeeds(self):
        """ TODO """
        Test_ID = 6
        print("\n\nSTARTING TEST {!r}".format(Test_ID))
        data_to_read_back = 'con permiso mi amigo'
        R = pyonep.device_client.Device(USER_AGENT, TEST_DEV_CFG_FILE)
        R.http_write('none', data_to_read_back)
        sleep(1.1)
        
        read_ID = R.add_rpc_read('none')
        timestamp = int(time() - 300)
        data = { timestamp: 'si senor' }
        recbatch_ID = R.add_rpc_recordbatch('none', data)
        speak_english = 'stop speaking spanish. k?'
        write_ID = R.add_rpc_write('none', speak_english)
        rpc_resp = R.rpc_send()
        recordbatch_response = handlers.RPC_RecordBatchHandler( rpc_resp, recbatch_ID )
        read_resp = handlers.RPC_ReadHandler(rpc_resp, read_ID)
        write_resp = handlers.RPC_WriteHandler(rpc_resp, write_ID)

        # check http code
        self.assertEquals(recordbatch_response.http_code, handlers.Http_ReadWriteCodes.OK)
        self.assertEquals(read_resp.http_code, handlers.Http_ReadWriteCodes.OK)
        self.assertEquals(write_resp.http_code, handlers.Http_ReadWriteCodes.OK)

        # check error
        self.assertEquals(recordbatch_response.error, None)
        self.assertEquals(read_resp.error, None)
        self.assertEquals(write_resp.error, None)

        # check success
        self.assertEquals(recordbatch_response.success, handlers.Rpc_Ternary.true)
        self.assertEquals(read_resp.success, handlers.Rpc_Ternary.true)
        self.assertEquals(write_resp.success, handlers.Rpc_Ternary.true)

        self.assertTrue(R.activated())

        # check data
        self.assertTrue(None == recordbatch_response.failed_records)
        self.assertEquals(data_to_read_back, read_resp.read_value)

        sleep(1.1)
        read_hand = R.http_read(['none'])
        self.assertEquals(speak_english, read_hand.body.split('=')[1] )

    @unittest.skip("Still need to finish writing this.")
    def test_7_read_multiple_dataports(self):
        """ TODO """
        Test_ID = 7
        print("\n\nSTARTING TEST {!r}".format(Test_ID))
        data_to_read_back = 'this should go to dataport "none"...'
        upd_intvl = 300
        R = pyonep.device_client.Device(USER_AGENT, TEST_DEV_CFG_FILE)
        write_handler = R.http_write_multiple( {'none': data_to_read_back, 'update_interval': upd_intvl })
        self.assertTrue(write_handler.success)

        sleep(1.1)
        
        none_ID = R.add_rpc_read( 'none' )
        upd_int_ID = R.add_rpc_read( 'update_interval' )
        rpc_resp = R.rpc_send()
        print(str(handlers.RPC_ReadHandler(rpc_resp, none_ID)))
        print(str(handlers.RPC_ReadHandler(rpc_resp, upd_int_ID)))

    def test_8_recordbatch_twice_with_same_timestamp_and_second_recordbatch_fails(self):
        """ TODO """
        Test_ID = 8
        print("\n\nSTARTING TEST {!r}".format(Test_ID))
        R = pyonep.device_client.Device(USER_AGENT, TEST_DEV_CFG_FILE)
        
        # now = int(time())
        timestamp = 5
        data = { timestamp: 'this should work just fine' }
        Test_ID = R.add_rpc_recordbatch('none', data)
        recordbatch_response = handlers.RPC_RecordBatchHandler( R.rpc_send(), Test_ID )

        self.assertEquals(recordbatch_response.http_code, handlers.Http_ReadWriteCodes.OK)
        self.assertEquals(recordbatch_response.error, None)
        self.assertEquals(recordbatch_response.success, handlers.Rpc_Ternary.true)
        self.assertTrue(R.activated())
        self.assertTrue(None == recordbatch_response.failed_records)

        data = { timestamp: 'this should not work because theres already an entry with this timestamp' }
        Test_ID = R.add_rpc_recordbatch('none', data)
        recordbatch_response = handlers.RPC_RecordBatchHandler( R.rpc_send(), Test_ID )

        self.assertEquals(recordbatch_response.http_code, handlers.Http_ReadWriteCodes.OK)
        self.assertEquals(recordbatch_response.error, None)
        self.assertEquals(recordbatch_response.success, handlers.Rpc_Ternary.partial)
        self.assertTrue(R.activated())
        print(recordbatch_response.failed_records)
        self.assertIn(timestamp, [ rec[0] for rec in recordbatch_response.failed_records[Test_ID] ] )




# TODO: write test cases that try to read and write to dataports that don't exist.



# TODO: write test cases for invalid ciks and check whether the self.auth flag works as designed.



