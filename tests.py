try:
    import gevent
except ImportError:
    gevent = None

import datetime
import functools
import sys
import threading
import unittest

from simple import Client
from simple import QueueServer


TEST_HOST = '127.0.0.1'
TEST_PORT = 31339


def run_queue_server():
    server = QueueServer(host=TEST_HOST, port=TEST_PORT,
                         use_gevent=gevent is not None)
    if gevent is not None:
        t = gevent.spawn(server.run)
    else:
        t = threading.Thread(target=server.run)
        t.daemon = True
        t.start()
    return t


class KeyPartial(object):
    def __init__(self, client, key):
        self.client = client
        self.key = key
    def __getattr__(self, attr):
        return functools.partial(getattr(self.client, attr), self.key)


class TestSimpleDatabase(unittest.TestCase):
    def setUp(self):
        self.c = Client(host=TEST_HOST, port=TEST_PORT)
        self.c.connect()

    def tearDown(self):
        self.c.close()

    def test_list(self):
        lq = KeyPartial(self.c, 'queue')

        lq.lpush('i1')
        lq.lpush('i2')
        lq.rpush('i3')
        lq.rpush('i4')
        result = lq.lrange(0)
        self.assertEqual(result, [b'i2', b'i1', b'i3', b'i4'])

        self.assertEqual(lq.lpop(), b'i2')
        self.assertEqual(lq.rpop(), b'i4')
        self.assertEqual(lq.llen(), 2)

        self.assertEqual(lq.lrem('i3'), 1)
        self.assertEqual(lq.lrem('i3'), 0)

        lq.lpush('a1', 'a2', 'a3', 'a4')
        self.assertEqual(lq.lindex(2), b'a2')

        lq.lset(2, 'x')
        self.assertEqual(lq.lrange(1, 3), [b'a3', b'x'])

        lq.ltrim(1, 4)
        self.assertEqual(lq.lrange(0), [b'a3', b'x', b'a1'])
        self.assertEqual(lq.lflush(), 3)

    def test_kv(self):
        kp = KeyPartial(self.c, 'k1')
        kp.set(['alpha', 'beta', 'gamma'])
        self.assertEqual(kp.get(), [b'alpha', b'beta', b'gamma'])

        res = kp.append(['pi', 'omega'])
        self.assertEqual(res, [b'alpha', b'beta', b'gamma', b'pi', b'omega'])

    def test_incr_decr(self):
        self.assertEqual(self.c.incr('i'), 1)
        self.assertEqual(self.c.decr('i'), 0)
        self.assertEqual(self.c.incrby('i2', 3), 3)
        self.assertEqual(self.c.incrby('i2', 2), 5)


if __name__ == '__main__':
    run_queue_server()
    unittest.main(argv=sys.argv)
