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
    $ python -m test.Test_Device

    OR

    $ python -m unittest discover test
"""

# pylint: disable=R0201

import unittest, os
from time import sleep
import pyonep.device_client
try:
    # python 2
    import ConfigParser
except:
    # python3
    import configparser as ConfigParser

USER_AGENT = 'Test_Exo_write'
MODEL = 'aptivator_v1'
UUID = 'ap:ti:va:to:rt:st'
TEST_CFG_FILE = 'test.cfg'

# These are set, first, in the Jenkins Job Configuration for APtivator,
# then by the test_aptivator.sh .. script. This keeps the vendor
# and vendor token info out of the git repo.
print("PWD: {0}".format(os.path.abspath(os.path.curdir)))
VENDOR = open(os.path.join(os.environ['WHITELABEL_PATH'],'WHITELABEL_VENDOR'), 'r').readline().strip()
VENDOR_TOKEN = open(os.path.join(os.environ['WHITELABEL_PATH'],'WHITELABEL_TOKEN'), 'r').readline().strip()
print("VENDOR = {0}".format(VENDOR))
print("VENDOR TOKEN = {0}".format(VENDOR_TOKEN))

@unittest.skip("This test suite works, but needs to be converted to use cik_fountain.")
class Test_Device(unittest.TestCase):
    """ Unittest to test cfg file with no 'cik' option. """
    @classmethod
    def setUpClass(cls):
        # file should be ConfigParser compatible.
        open(TEST_CFG_FILE, 'wb').write("""[device]
cik = ''
model = {0}
vendor = {1}
uuid = {2}
""".format(MODEL, VENDOR, UUID))

        # it is probably wrong, philosophically, to used code you intend to
        # test in order to set up for that test, but I'm doing it anyways
        D = pyonep.device_client.Device(USER_AGENT, TEST_CFG_FILE)
        regen_success = D._http_regen(VENDOR_TOKEN)
        print("What happened here: {}".format(str(regen_success)))
        assert regen_success.code == 205

    @classmethod
    def tearDownClass(cls):
        """ Remove test file. """
        os.remove(TEST_CFG_FILE)

    def setUp(self):
        """ Setup for test. """
        print("Setting up for test.")
        self.test_cfg = TEST_CFG_FILE
        self.user_agent = USER_AGENT
        self.vendor_token = VENDOR_TOKEN
        # clear the dataport 'none' before each test
        self.Dev = pyonep.device_client.Device(self.user_agent, self.test_cfg)
        sleep(1)
        self.Dev.http_write('none', '')

    def tearDown(self):
        with open(self.test_cfg, 'r') as cfg:
            print(cfg.readlines())

    def test_1_not_activated(self):
        """ Try to write to the 'none' dataport. 
        Verify we get an unauthorized response because we have no cik at this point. """
        print("STARTING TEST 1")
        dev = pyonep.device_client.Device(self.user_agent, self.test_cfg)
        resp = dev.http_write('none', "this should fail with a 401")
        self.assertEquals(resp.code, 401)

    def test_2_handlers(self):
        """ Test the ReadHandler and WriteHandler classes from exo.exo. """
        print("STARTING TEST 2")
        dev = pyonep.device_client.Device(self.user_agent, self.test_cfg)
        hand = dev.http_write("none", "this should fail with a 401")
        self.assertEquals(hand.code, 401)
        self.assertFalse(hand.success)

        hand = dev.http_write("none", "this should fail with a 401")
        self.assertEquals(hand.code, 401)
        self.assertFalse(hand.success)


    def test_3_activation(self):
        """ With no 'cik' option in the cfg file, even if empty, 
            we should get a NoOptionError. """
        print("STARTING TEST 3")
        dev = pyonep.device_client.Device(self.user_agent, self.test_cfg)
        dev._activate()
        self.assertEquals(dev.activated(), True)
        resp = dev.http_write("none", "this should pass with a 204")
        self.assertEquals(resp.code, 204)


    def test_4_write_and_read(self):
        """ Test reading and writing with the Device() methods. """
        print("STARTING TEST 4")
        dev = pyonep.device_client.Device(self.user_agent, self.test_cfg)
        msg = 'exosite_is_awesome'
        sleep(1)
        resp = dev.http_write('none', msg)
        # it is possible that we wrote to the 'none' dataport less than a second ago
        # since the platform doesn't support sub-second writes, sleep
        print("write: {}".format(str(resp)))
        # the same seems to be true for reads?
        sleep(1)
        self.assertTrue(resp.success)
        resp = dev.http_read(['none'])
        print("read: {}".format(str(resp)))
        self.assertTrue(resp.success)
        # resp.body = u'none=exosite+is+awesome'
        msg_from_dataport = resp.body.split('=')[1]
        # msg_from_dataport = exosite+is+awesome
        self.assertEquals(msg_from_dataport, msg)

    def test_5_test_deactivation_after_corrupting_cik_and_trying_to_write_to_dataport(self):
        """ Test name pretty much says it all. """
        print("STARTING TEST 5")
        dev = pyonep.device_client.Device(self.user_agent, self.test_cfg)
        msg = 'this_should_not_work'
        sleep(1)
        original_cik = dev.cik()
        dev._set_activated(False)
        dev._set_cik('a'*40)
        dev.http_write('none', msg)
        self.assertEquals(False, dev.activated())
        dev._set_cik(original_cik)
        self.assertEquals(True, dev.activated())










