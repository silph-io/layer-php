

import unittest

from mock import patch, MagicMock, call

from reactive import php_fpm  # noqa: E402


class MockConfig(MagicMock):
    _d = {'prev': {}, 'cur': {}}

    def previous(self, k):
        return self._d['prev'].get(k)

    def get(self, k, default=None):
        return self._d['cur'].get(k, default)

    def items(self):
        return self._d['cur'].items()


class ReactiveTestCase(unittest.TestCase):
    patches = ['set_state', 'config', 'remove_state', 'status_set']
    callables = {'config': MockConfig}

    def setUp(self):
        for p in self.patches:
            c = self.callables.get(p, MagicMock)
            a = 'reactive.php_fpm.{}'.format(p)
            setattr(self, '{}_mock'.format(p),
                    patch(a, new_callable=c).start())
        super(ReactiveTestCase, self).setUp()

    def tearDown(self):
        for p in self.patches:
            getattr(self, '{}_mock'.format(p)).stop()
        super(ReactiveTestCase, self).tearDown()


class ReactiveTest(ReactiveTestCase):
    @patch('reactive.php_fpm.php')
    def test_install(self, mp):
        self.config_mock._d['cur'] = {
            'php-max-children': '10',
            'php-start-servers': '5',
            'php-min-spare-servers': '2',
        }

        mp.configure.return_value = False
        php_fpm.configure()
        mp.configure.assert_called_with({
            'pm.max_children': '10',
            'pm.start_servers': '5',
            'pm.min_spare_servers': '2',
        })

        self.set_state_mock.assert_has_calls([
            call('php.configured'),
            call('php.ready'),
        ])

    @patch('reactive.php_fpm.php')
    def test_install_restart(self, mp):
        self.config_mock._d['cur'] = {
            'php-max-children': '10',
            'php-start-servers': '5',
            'php-min-spare-servers': '2',
        }

        mp.configure.return_value = True
        php_fpm.configure()
        mp.configure.assert_called_with({
            'pm.max_children': '10',
            'pm.start_servers': '5',
            'pm.min_spare_servers': '2',
        })

        self.set_state_mock.assert_has_calls([
            call('php.configured'),
            call('php.ready'),
        ])

    def test_configure(self):
        php_fpm.change_config()
        self.remove_state_mock.assert_called_with('php.configured')
