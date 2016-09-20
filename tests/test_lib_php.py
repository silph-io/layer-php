
import sys
import unittest

from mock import patch

sys.path.append('lib')

from charms.layer import php  # noqa: E402


class LibraryTest(unittest.TestCase):
    @patch('charms.layer.php._write_cfg')
    @patch('charms.layer.php._read_cfg')
    def test_configure(self, mrc, mwc):
        mrc.return_value = '''
pm.start_server = 10
pm.test = 1
;pm.alpha = beta
'''
        new_cfg = '''
pm.start_server = 20
;pm.test = 1
pm.alpha = alpha
'''

        cfg = {
            'pm.start_server': 20,
            'pm.test': False,
            'pm.alpha': 'alpha',
        }

        self.assertTrue(php.configure(cfg))

        mwc.assert_called_with(new_cfg)

    @patch('charms.layer.php._read_cfg')
    @patch('charms.layer.php.os')
    def test_socket(self, mos, mrc):
        mos.path.exists.return_value = True
        mrc.return_value = '''
pm.start_server = 10
pm.test = 1
listen = /tmp/socket/path.sock
;pm.alpha = beta
'''

        self.assertEqual('unix:/tmp/socket/path.sock', php.socket())

    @patch('charms.layer.php._read_cfg')
    @patch('charms.layer.php.os')
    def test_socket_addr(self, mos, mrc):
        mos.path.exists.return_value = False
        mrc.return_value = '''
pm.start_server = 10
pm.test = 1
listen = 10.0.0.1:9000
;pm.alpha = beta
'''

        self.assertEqual('10.0.0.1:9000', php.socket())

    @patch.object(php, 'run')
    def test_version(self, mrun):
        mrun.return_value = '7.0.1'
        self.assertEqual(['7', '0', '1'], php.version())

        mrun.return_value = '5.9.99'
        self.assertEqual(['5', '9', '99'], php.version())

    @patch('charms.layer.php.subprocess')
    def test_run(self, msp):
        p = msp.Popen.return_value

        p.communicate.return_value = (b'hello world', None)
        p.returncode = None

        self.assertEqual('hello world', php.run('echo("hello world");'))
        msp.Popen.assert_called_with(
            ['php', '-r', 'echo("hello world");'],
            stderr=msp.PIPE,
            stdout=msp.PIPE,
        )

    @patch('charms.layer.php.subprocess')
    def test_run_err(self, msp):
        p = msp.Popen.return_value

        p.communicate.return_value = (None, b'bzzzzzzrt')
        p.returncode = 1

        self.assertRaises(IOError, php.run, 'errrrr')

    @patch.dict(php.FPM_BIN, {'9': 'bin-exec'})
    @patch('charms.layer.php.service_restart')
    @patch('charms.layer.php.version')
    def test_restart(self, mv, msr):
        mv.return_value = ['9', '99']
        php.restart()
        msr.assert_called_with('bin-exec')

    @patch.dict(php.PREFIX, {'99': 'php99-{}'})
    @patch('charms.layer.php.version')
    def test_install(self, mv):
        mv.return_value = ['99', '9', '9000']
        self.assertEqual(['php99-mcrypt', 'php99-mysql'],
                         php.install('mcrypt', 'mysql'))

    @patch('charms.layer.php.lsb_release')
    def test_package(self, ml):
        ml.return_value = {'DISTRIB_CODENAME': 'xenial'}
        self.assertEqual('php-fpm', php.package())

        ml.return_value = {'DISTRIB_CODENAME': 'trusty'}
        self.assertEqual('php5-fpm', php.package())

        ml.return_value = {'DISTRIB_CODENAME': 'debian'}
        self.assertEqual('php5-fpm', php.package())
