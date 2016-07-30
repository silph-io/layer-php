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

from charms.layer import php


@when_not('php.configured')
def install_phpfpm():
    cfg_map = {
        'php-max-children': 'pm.max_children',
        'php-start-servers': 'pm.start_servers',
        'php-min-spare-servers': 'pm.min_spare_servers',
        'php-max-spare-servers': 'pm.max_spare_servers',
        'php-max-requests': 'pm.max_requests',
    }

    c = config()
    php_cfg = {cfg_map[k]: v for k, v in c.items() if k in cfg_map}

    restart = php.configure(php_cfg)
    set_state('php.configured')

    if restart:
        php.restart()

    set_state('php.ready')


@when('config.changed')
def configure_phpfpm():
    remove_state('php.configured')
