#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

import os
import sys
import logging
import pickle

from errno import ENOENT
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

if not hasattr(__builtins__, 'bytes'):
    bytes = str


class FakeList(LoggingMixIn, Operations):
    def __init__(self, cache_path):
        self.cache = pickle.load(open(cache_path, 'rb'))
        print('读取缓存完成')
        self.fd = 1

    def getattr(self, path, fh=None):
        if path not in self.cache['stats']:
            raise FuseOSError(ENOENT)

        return self.cache['stats'][path]

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        return ''
        # return self.data[path][offset:offset + size]

    def readdir(self, path, fh):
        if path not in self.cache['dirs']:
            raise FuseOSError(ENOENT)

        return ['.', '..'] + self.cache['dirs'][path]

    def readlink(self, path):
        return self.cache['stats'][path]['link']

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)


def stat_to_dict(s):
    return {
        'st_mode': s.st_mode,
        'st_ino': s.st_ino,
        'st_dev': s.st_dev,
        'st_nlink': s.st_nlink,
        'st_uid': s.st_uid,
        'st_gid': s.st_gid,
        'st_size': s.st_size,
        'st_atime': s.st_atime,
        'st_mtime': s.st_mtime,
        'st_ctime': s.st_ctime
    }


def build_cache(dir_path, cache_file):
    cache = {
        'dirs': {},
        'stats': {},
    }

    # 删除结尾的 /
    if dir_path.endswith('/') and dir_path != '/':
        dir_path = dir_path[:-1]

    dir_count = 0
    file_count = 0
    for d, dirs, files in os.walk(dir_path):
        cache_path = d[len(dir_path):] or '/'
        cache['dirs'][cache_path] = dirs + files
        cache['stats'][cache_path] = stat_to_dict(os.stat(d))
        dir_count += 1
        if dir_count % 10000 == 0:
            print('dir_count: ', dir_count)
        for f in files:
            file_path = os.path.join(d, f)
            cache_file_path = os.path.join(cache_path, f)
            cache['stats'][cache_file_path] = stat_to_dict(
                os.stat(file_path, follow_symlinks=False))
            if os.path.islink(file_path):
                cache['stats'][cache_file_path]['link'] = os.readlink(
                    file_path)

            file_count += 1

            if file_count % 10000 == 0:
                print('file_count: ', file_count)

    print('正在写入缓存，共%d个目录, %d个文件' % (dir_count, file_count))
    with open(cache_file, 'wb+') as out_file:
        pickle.dump(cache, out_file)
    print('构建目录缓存完成')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    mount_parser = subparsers.add_parser('mount', help='挂载')
    mount_parser.set_defaults(which='mount')
    mount_parser.add_argument(
        '-d', action='store_true', dest='debug', default=False, help='是否开启调试')
    mount_parser.add_argument('mountpoint', help='挂载点')
    mount_parser.add_argument('cache_file', help='缓存文件')
    build_parser = subparsers.add_parser('build', help='构建缓存')
    build_parser.set_defaults(which='build')
    build_parser.add_argument('dir_path', help='要缓存的目录')
    build_parser.add_argument('cache_file', help='缓存文件')

    args = parser.parse_args()
    if getattr(args, 'which', 'help') == 'help':
        parser.print_help()
        sys.exit(0)

    if args.which == 'mount':
        logging.basicConfig(
            level=logging.DEBUG if args.debug else logging.INFO)
        fuse = FUSE(
            FakeList(args.cache_file),
            args.mountpoint,
            foreground=True if args.debug else False,
            allow_other=True)

    if args.which == 'build':
        build_cache(args.dir_path, args.cache_file)
