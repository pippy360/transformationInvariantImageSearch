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

from .keypoints import compute_keypoints
from .phash import triangles_from_keypoints, hash_triangles


def phash_triangles(img, triangles, batch_size=None):
    n = len(triangles)

    if batch_size is None:
        batch_size = n // cpu_count()

    array = np.asarray(triangles, dtype='d')
    tasks = [(img, array[i:i + batch_size]) for i in range(0, n, batch_size)]
    results = []

    with multiprocessing.Pool(processes=cpu_count()) as p:
        for result in p.starmap(hash_triangles, tasks):
            results += result

    return results


def pipeline(r, data, chunk_size):
    npartitions = len(data) // chunk_size
    pipe = r.pipeline()

    for chunk in np.array_split(data, npartitions or 1):
        yield pipe, chunk


def insert(chunks, filename):
    n = 0

    for pipe, keys in chunks:
        for key in keys:
            pipe.sadd(key, filename)

        n += sum(pipe.execute())

    print(f'added {n} fragments for {filename}')


def lookup(chunks, filename):
    count = Counter()

    for pipe, keys in chunks:
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
    try:
        r.ping
    except redis.ConnectionError:
        print('You need to install redis.')
        return

    for filename in filenames:
        print('loading', filename)
        img = cv2.imread(filename)

        keypoints = compute_keypoints(img)
        triangles = triangles_from_keypoints(keypoints, lower=50, upper=400)
        hashes = phash_triangles(img, triangles)
        chunks = pipeline(r, hashes, chunk_size=1e5)

        print()
        command(chunks, filename)


if __name__ == '__main__':
    main()
