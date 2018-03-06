"""
Usage: main.py lookup <image>...
       main.py insert <image>...
"""
import sys
import multiprocessing
from collections import Counter
from os import cpu_count

import cv2
import redis
import numpy as np
from toolz.itertoolz import partition_all

from keypoints import compute_keypoints
from phash import triangles_from_keypoints, hash_triangles


def phash_triangles(img, triangles, batch_size=None):
    n = len(triangles)

    if batch_size is None:
        batch_size = n // cpu_count()

    array = np.asarray(triangles, dtype='d')
    tasks = [(img, array[i:i + batch_size]) for i in range(0, n, batch_size)]

    with multiprocessing.Pool(processes=cpu_count()) as p:
        for result in p.starmap(hash_triangles, tasks):
            yield from result


def insert(r, filename, hashes, batch_size=1000):
    n = 0

    for batch in partition_all(batch_size, hashes):
        pipe = r.pipeline()

        for key in batch:
            r.sadd(key, filename)

        pipe.execute()
        n += len(batch)

    print(f'added {n} fragments for {filename}')


def lookup(r, filename, hashes, batch_size=1000):
    count = Counter()

    for keys in partition_all(batch_size, hashes):
        pipe = r.pipeline()

        for key in keys:
            pipe.smembers(key)

        for result in pipe.execute():
            count.update(result)

    print(f'matches for {filename}:')

    for key, num in count.most_common():
        print(f'{num:<10d} {key.decode("utf-8")}')


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        exit(1)

    command, *filenames = sys.argv[1:]
    command = insert if command == 'insert' else lookup

    r = redis.StrictRedis(host='localhost', port=6379, db=0)

    for filename in filenames:
        print('loading', filename)
        img = cv2.imread(filename)

        keypoints = compute_keypoints(img)
        triangles = triangles_from_keypoints(keypoints, lower=50, upper=400)
        hashes = phash_triangles(img, triangles)

        command(r, filename, hashes)


if __name__ == '__main__':
    main()
