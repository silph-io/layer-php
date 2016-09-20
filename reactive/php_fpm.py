from charmhelpers.core.hookenv import (
    config,
    status_set,
)

from charms.reactive import (
    when,
    when_not,
    set_state,
    remove_state,
)

from charms import apt
from charms.layer import php
from charms.layer import options


@when_not('apt.installed.{}'.format(php.package()[0]))
@when_not('apt.installed.{}'.format(php.package()[1]))
def install():
    apt.queue_install(php.package())


@when('apt.installed.{}'.format(php.package()[0]))
@when_not('php.installed')
def packages():
    status_set('maintenance', 'installing php packages')
    try:
        php.install(*options('php-fpm').get('packages'))
    except:
        status_set('maintenance',
                   'Unable to install packages, trying again soon...')
    else:
        set_state('php.installed')


@when('php.installed')
@when_not('php.configured')
def configure():
    cfg_map = {
        'php-max-children': 'pm.max_children',
        'php-start-servers': 'pm.start_servers',
        'php-min-spare-servers': 'pm.min_spare_servers',
        'php-max-spare-servers': 'pm.max_spare_servers',
        'php-max-requests': 'pm.max_requests',
    }

    c = config()
    php_cfg = {cfg_map[k]: v for k, v in c.items() if k in cfg_map}
    php_cfg['listen'] = '127.0.0.1:7777'

    # Only restart php-fpm if we changed configuration
    restart = php.configure(php_cfg)
    set_state('php.configured')

    if restart:
        php.restart()

    set_state('php.ready')


@when('php.configured')
@when('stats.connected')
@when_not('stats.configured')
def enable_stats(stats):
    cfg = {
        'pm.status_path': '/php-status',
        'ping.path': '/php-ping',
        'ping.response': 'pong',
    }

    restart = php.configure(cfg)
    set_state('php.configured')

    if restart:
        php.restart()

    stats.configure(7777, cfg['pm.status_path'], cfg['ping.path'],
                    cfg['ping.response'])


@when('config.changed')
def change_config():
    remove_state('php.configured')
