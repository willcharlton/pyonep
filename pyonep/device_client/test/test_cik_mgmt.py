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
	$ python -m test.test_cik_mgmt

	OR

	$ python -m unittest discover test

"""

# pylint: disable=R0201

import unittest, os
from pyonep.device_client import Device, DeviceCfgSect, DeviceCfgOpt
try:
    # python 2
    import ConfigParser
except:
    # python3
    import configparser as ConfigParser

class verify_device_activates_with_good_cik(unittest.TestCase):
	""" Unittest to veryfy Device() activation. """

	def setUp(self):
		""" Setup for test. """
		self.test_cfg = 'test.cfg'
		cfg_parser = ConfigParser.RawConfigParser(allow_no_value=True)
		cfg_parser.add_section(DeviceCfgSect.Device)
		cfg_parser.set(DeviceCfgSect.Device, DeviceCfgOpt.Model, 'a_model')
		cfg_parser.set(DeviceCfgSect.Device, DeviceCfgOpt.Vendor, 'a_vendor')
		cfg_parser.set(DeviceCfgSect.Device, DeviceCfgOpt.Uuid, 'aabbccdd')
		cfg_parser.set(DeviceCfgSect.Device, DeviceCfgOpt.Cik, '')
		cfg_parser.write(open(self.test_cfg, 'wb'))
	def tearDown(self):
		""" Remove test file. """
		os.remove(self.test_cfg)

	def test_good_cik(self):
		""" Verify Device() activates when it gets a good cik. """
		device = Device('exo_test_user_agent',
					self.test_cfg)
		cik = 'a'*40
		device._set_cik(cik)
		self.assertEquals(True, device.activated())

class verify_cik_management(unittest.TestCase):
	""" Unittest to test cik management. """

	def setUp(self):
		""" Setup for test. """
		self.test_cfg = 'test.cfg'
		cfg_parser = ConfigParser.RawConfigParser(allow_no_value=True)
		cfg_parser.add_section(DeviceCfgSect.Device)
		cfg_parser.set(DeviceCfgSect.Device, DeviceCfgOpt.Model, 'a_model')
		cfg_parser.set(DeviceCfgSect.Device, DeviceCfgOpt.Vendor, 'a_vendor')
		cfg_parser.set(DeviceCfgSect.Device, DeviceCfgOpt.Uuid, 'aabbccdd')
		cfg_parser.set(DeviceCfgSect.Device, DeviceCfgOpt.Cik, '')
		cfg_parser.write(open(self.test_cfg, 'wb'))
	def tearDown(self):
		""" Remove test file. """
		os.remove(self.test_cfg)

	def test_device_activates_with_good_cik_and_deactivates_with_bad_cik(self):
		""" Verify Device() activates when it gets a good cik and
			then deactivates when it gets a bad one. """
		device = Device('exo_test_user_agent',
					self.test_cfg)
		cik = 'a'*40
		device._set_cik(cik)
		self.assertEquals(True, device.activated())
		bad_cik = 'b'*39
		device._set_cik(bad_cik)
		self.assertEquals(False, device.activated())



if __name__ == '__main__':
	unittest.main()
