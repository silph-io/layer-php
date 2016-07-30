
import os
import re
import subprocess

from charmhelpers.core.host import service_restart


FPM_PATH = {
    '7': '/etc/php/7.0/fpm/pool.d/',
    '5': '/etc/php5/fpm/pool.d/',
}

FPM_BIN = {
    '7': 'php7.0-fpm',
    '5': 'php5-fpm',
}

PACKAGES = {
    'xenial': [
        'php-fpm',
    ],
    'trusty': [
        'php5-fpm',
    ],
}

PREFIX = {
    '7': 'php-{}',
    '5': 'php5-{}',
}


def _as_text(bytestring):
    """Naive conversion of subprocess output to Python string"""
    return bytestring.decode("utf-8", "replace")


def _read_cfg():
    cfg_file = os.path.join(FPM_PATH[version()[0]], 'www.conf')
    with open(cfg_file) as f:
        return f.read()


def _write_cfg(contents):
    cfg_file = os.path.join(FPM_PATH[version()[0]], 'www.conf')
    with open(cfg_file, 'w') as f:
        f.truncate()  # clear the contents just to be safe
        f.write(contents)


def configure(cfg):
    new = _read_cfg()
    # if KEY: s/;?KEY = .*/KEY = VAL/ else s/;KEY = (.*)/;KEY = {0}/
    for key, val in cfg.items():
        p = re.compile(';?{} = (.*)'.format(re.escape(key)))
        if not val:
            new = p.sub(r';{} = \1'.format(key), new)
            continue

        new = p.sub('{} = {}'.format(key, val), new)

    changed = (new != _read_cfg())
    _write_cfg(new)

    return changed


def socket():
    s = None
    c = _read_cfg()
    m = re.search('^listen = (.*)$', c, re.MULTILINE)
    if m:
        s = m.group(1)

    if os.path.exists(s):
        return 'unix:{}'.format(s)

    return s


def restart():
    service_restart(FPM_BIN[version()[0]])


def version():
    ver = run("echo(explode('-', phpversion())[0]);")
    return (ver.split('.'))


def run(cmd):
    cmd = ['php', '-r', cmd]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode:
        raise IOError("php command `{!r}` failed:\n"
                      "{}".format(cmd, _as_text(err)))
    return _as_text(out)


def install(*modules):
    tpl = PREFIX.get(version()[0], 'php-{}')
    packages = [tpl.format(module) for module in modules]
    return packages
