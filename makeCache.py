#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pickle

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

def make_cache(path, save_path):
    cache = {
        'dirs': {},
        'stats': {},
    }

    dir_count = 0
    file_count = 0
    for d, dirs, files in os.walk(path):
        cache_path = d[len(path):] or '/'
        cache['dirs'][cache_path] = dirs + files
        cache['stats'][cache_path] = stat_to_dict(os.stat(d))
        dir_count += 1
        if dir_count % 10000 == 0:
            print('dir_count: ', dir_count)
        for f in files:
            file_path = os.path.join(d, f)
            cache_file_path = os.path.join(cache_path, f)
            cache['stats'][cache_file_path] = stat_to_dict(os.stat(file_path, follow_symlinks=False))
            if os.path.islink(file_path):
                cache['stats'][cache_file_path]['link'] = os.readlink(file_path)

            file_count += 1

            if file_count % 10000 == 0:
                print('file_count: ', file_count)


    print('正在写入缓存，共%d个目录, %d个文件' % (dir_count, file_count))
    with open(save_path, 'wb+') as out_file:
        pickle.dump(cache, out_file)
    print('构建目录缓存完成')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('save_path')
    args = parser.parse_args()

    make_cache(args.path, args.save_path)
