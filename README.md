缓存目录列表到文件，再用fuse加载到别的机器上，用来配合overlay2加rsync实现增量备份到其它设备。