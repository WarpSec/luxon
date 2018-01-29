#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 Christiaan Frans Rademan.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holders nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
import os
import sys
import argparse
import hashlib
import site
from pkg_resources import (resource_stream, resource_listdir,
                           resource_isdir, resource_exists)

from luxon import metadata
from luxon import g
from luxon.core.servers.web import server as web_server
from luxon.utils.imports import import_module
from luxon.core.config import Config

def _create_dir(path, new):
    new = os.path.normpath('%s%s' % (path, new))
    if not os.path.exists(new):
        os.makedirs(new)
        print('Created directory: %s' % new)

def _copy_file(module, path, src, dst, update=True):
    try:
        import_module(module)
    except ImportError as e:
        print("Import Error %s\n%s" % (module, e))
        exit()

    dst = os.path.normpath("%s/%s" % (path, dst))
    if resource_exists(module, src):
        src_file = resource_stream(module, src).read()
        if not os.path.exists(dst):
            with open(dst, 'wb') as handle:
                handle.write(src_file)
                print("Created %s" % dst)
        else:
            if update is False:
                dst = "%s.default" % (dst,)
                if not os.path.exists(dst):
                    with open(dst, 'wb') as handle:
                        handle.write(src_file)
                        print("Created %s" % dst)
            else:
                src_sig = hashlib.md5(src_file)
                dst_file = open(dst, 'rb').read()
                dst_sig = hashlib.md5(dst_file)
                if src_sig.hexdigest() != dst_sig.hexdigest():
                    with open(dst, 'wb') as handle:
                        handle.write(src_file)
                        print("Updated %s" % dst)

def _recursive_copy(local, module, path):
    if resource_isdir(module, path):
        for filename in resource_listdir(module, path):
            fullname = path + '/' + filename
            if resource_isdir(module, fullname):
                _create_dir(local, '/%s' % filename)
                _recursive_copy("%s/%s" % (local, filename), module, fullname)
            else:
                _copy_file(module, local, fullname, filename)



def setup(args):
    path = os.path.abspath(args.path)
    pkg = args.pkg

    if pkg == 'luxon':
        print("Your suppose to install luxon applications not luxon itself")
        exit()

    _copy_file(pkg, path, 'settings.ini', 'settings.ini', False)
    _copy_file(pkg, path, 'wsgi.py', 'wsgi.py', False)
    _create_dir('', '%s/static' % path)
    _create_dir('', '%s/static/%s' % (path, pkg))
    _create_dir('', '%s/templates/%s' % (path, pkg))
    _recursive_copy('%s/static' % path, pkg, 'static')


def server(args):
    web_server(app_root=args.path, ip=args.ip, port=args.port)

def db(args):
    app_root = os.path.abspath(args.path)
    site.addsitedir(os.path.abspath(os.path.curdir))
    os.chdir(app_root)
    with open(app_root.rstrip('/') + '/wsgi.py', 'r') as wsgi_file:
        exec_g = {}
        exec(wsgi_file.read(), exec_g, exec_g)

    for Model in g.models:
        model = Model()
        model.sync_db()

def main(argv):
    description = metadata.description + ' ' + metadata.version
    print("%s\n" % description)

    parser = argparse.ArgumentParser(description=description)
    group = parser.add_mutually_exclusive_group(required=True)

    parser.add_argument('path',
                        help='Application root path')

    group.add_argument('-d',
                       dest='funcs',
                       action='append_const',
                       const=db,
                       help='Create/Update Database')

    group.add_argument('-i',
                       dest='pkg',
                       help='Install/Update application in path specified')

    group.add_argument('-s',
                       dest='funcs',
                       action='append_const',
                       const=server,
                       help='Start Internal Testing Server (requires gunicorn)')

    parser.add_argument('--ip',
                       help='Binding IP Address (127.0.0.1)',
                       default='127.0.0.1')

    parser.add_argument('--port',
                        help='Binding Port (8080)',
                        default='8080')

    args = parser.parse_args()

    if args.funcs is not None:
        for func in args.funcs:
            func(args)

    if args.pkg is not None:
        setup(args)

def entry_point():
    """Zero-argument entry point for use with setuptools/distribute."""
    raise SystemExit(main(sys.argv))


if __name__ == '__main__':
    entry_point()
