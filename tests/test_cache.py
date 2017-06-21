from unittest import TestCase
from unittest.mock import Mock

from wxmonitor.cache import Cache


class ProcessedCacheTests(TestCase):
    def test_can_add_status(self):

        mock_time = Mock()
        mock_time.return_value = 0

        cache = Cache(ttl=10)
        cache.add(Mock(val=42))

        self.assertEqual(len(cache), 1)

    def test_can_get_statuses(self):
        mock_time = Mock()
        mock_time.return_value = 0

        cache = Cache(ttl=10)
        sample = Mock(val=42)
        cache.add(sample)

        rtn = cache.get_statuses()
        self.assertListEqual(rtn, [sample])

    def test_does_expire_status(self):
        mock_time = Mock()
        mock_time.return_value = 0

        cache = Cache(ttl=10, timer=mock_time)
        cache.add(Mock(val=42))

        mock_time.return_value = 20
        cache.expire()

        self.assertEqual(len(cache), 0)

