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
	$ python -m test.test_cfg

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

class test_incorrect_section(unittest.TestCase):
	""" Unittest to test incorrect section name in 
		cfg file. """
	def setUp(self):
		""" Setup for test. """
		self.test_cfg = 'test.cfg'
		cfg_parser = ConfigParser.RawConfigParser(allow_no_value=True)
		cfg_parser.add_section('foo')
		cfg_parser.set('foo','bar', 'Exosite!')
		cfg_parser.write(open(self.test_cfg, 'wb'))
	def tearDown(self):
		""" Remove test file. """
		os.remove(self.test_cfg)

	def test_incorrect_section(self):
		""" Just try to instantiate with bad cfg file. """
		with self.assertRaises(ConfigParser.NoSectionError):
			Device('exo_test_user_agent',
					self.test_cfg)

class no_cfg_file(unittest.TestCase):
	""" Unittest to test no cfg file. """

	def setUp(self):
		""" No setup needed. """
		pass
	def tearDown(self):
		""" No tear-down needed. """
		pass

	def test_no_cfg(self):
		""" Just try to instantiate with cfg file name
			that doesn't exist. """
		with self.assertRaises(ConfigParser.Error):
			Device('exo_test_user_agent',
					'some_non_existent_file.cfg')

class no_cik_option(unittest.TestCase):
	""" Unittest to test cfg file with no 'cik' option. """

	def setUp(self):
		""" Setup for test. """
		self.test_cfg = 'test.cfg'
		cfg_parser = ConfigParser.RawConfigParser(allow_no_value=True)
		cfg_parser.add_section(DeviceCfgSect.Device)
		cfg_parser.set(DeviceCfgSect.Device, DeviceCfgOpt.Model, 'a_model')
		cfg_parser.set(DeviceCfgSect.Device, DeviceCfgOpt.Vendor, 'a_vendor')
		cfg_parser.set(DeviceCfgSect.Device, DeviceCfgOpt.Uuid, 'aabbccdd')
		cfg_parser.write(open(self.test_cfg, 'wb'))
	def tearDown(self):
		""" Remove test file. """
		os.remove(self.test_cfg)

	def test_no_cik_in_cfg(self):
		""" With no 'cik' option in the cfg file, even if empty, 
			we should get a NoOptionError. """
		with self.assertRaises(ConfigParser.NoOptionError):
			Device('exo_test_user_agent',
					self.test_cfg)

class cfg_file_updates_as_does_Device(unittest.TestCase):
	""" Unittest to test cfg file with no 'cik' option. """

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

	def test_no_cik_in_cfg(self):
		""" Verify both member variable and cfg file option is 
			set appropriately. """
		device = Device('exo_test_user_agent',
					self.test_cfg)
		cik = 'a'*40
		device._set_cik(cik)
		self.assertEquals(cik, device.cik())
		self.assertEquals(cik, device._cfg_parser.get(DeviceCfgSect.Device, DeviceCfgOpt.Cik))



if __name__ == '__main__':
	unittest.main()
