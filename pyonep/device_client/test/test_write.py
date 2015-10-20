"""
	Test file for testing various exosite write methods.
"""

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
	$ python -m test.test_write

	OR

	$ python -m unittest discover test
"""

# pylint: disable=R0201

import unittest
import pyonep.device_client
import ConfigParser, os
from time import sleep

USER_AGENT = 'exo_test_write'
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
		sleep(1)

	def tearDown(self):
		with open(self.test_cfg, 'r') as cfg:
			print(cfg.readlines())

	def test_1_http_write(self):
		""" Try to write to the 'none' dataport. 
		Verify we get an unauthorized response because we have no cik at this point. """
		print("STARTING TEST 1")
		test_msg = 'Will is pretty awesome.'
		dev = pyonep.device_client.Device(self.user_agent, self.test_cfg)
		dev._activate()
		self.assertTrue(dev.activated())
		resp = dev.http_write("none",test_msg)
		self.assertTrue(resp.success)
		sleep(1)
		resp = dev.http_read(['none'])
		self.assertTrue(resp.success)
		self.assertEquals(resp.body.split('=')[1], test_msg)






