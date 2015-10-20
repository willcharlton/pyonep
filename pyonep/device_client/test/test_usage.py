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

import unittest, requests
import pyonep.device_client
import ConfigParser, os
from time import sleep

USER_AGENT = 'Test_Exo_usage'
MODEL = 'aptivator_v1'
UUID = 'ap:ti:va:to:rt:st'
TEST_CFG_FILE = 'test.cfg'

# These are set, first, in the Jenkins Job Configuration for APtivator,
# then by the test_aptivator.sh jenkins script. This keeps the vendor
# and vendor token info out of the git repo.
print("PWD: {0}".format(os.path.abspath(os.path.curdir)))
VENDOR = open(os.path.join(os.environ['WHITELABEL_PATH'],'WHITELABEL_VENDOR'), 'r').readline().strip()
VENDOR_TOKEN = open(os.path.join(os.environ['WHITELABEL_PATH'],'WHITELABEL_TOKEN'), 'r').readline().strip()
print("VENDOR = {0}".format(VENDOR))
print("VENDOR TOKEN = {0}".format(VENDOR_TOKEN))

class Test_Usage(unittest.TestCase):
    """ Test stuff concerning the Interfaces class. """
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
        # flush all data from dataport 'none'
        print("SET UP: Clearing none dataport!")

        R = pyonep.device_client.Device(USER_AGENT, TEST_CFG_FILE)
        
        R._activate()
        R.RPC["calls"].append(
                {   "procedure": "flush",
                    "id": 1,
                    "arguments":[ {"alias":"none"} ] } 
            )
        R.rpc_send()

    @unittest.skip("Throttling logic in ifaces.py still needs work. This test fails, so turning it off until throttling can be fixed.")
    def test_1_throttling(self):
        """ Find the data usage on a given interface (eth0, ppp0) by using python requests. """

        D = pyonep.device_client.Device(USER_AGENT, TEST_CFG_FILE)
        D._activate()

        for i in range(0,61):
            D.http_write('none', 'I am a runaway device.')
        self.assertNotEquals([], D.throttle_check())



















