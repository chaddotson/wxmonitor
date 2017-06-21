from unittest import TestCase

from wxmonitor.graphing import get_rgb


class GetRGBTests(TestCase):
    def test_get_rgb_val_eq_min(self):
        rgb = get_rgb(0, 0, 100)
        self.assertListEqual(rgb, [0, 0, 1])

    def test_get_rgb_val_eq_max(self):
        rgb = get_rgb(100, 0, 100)
        self.assertListEqual(rgb, [1, 0, 0])

    def test_get_rgb_val_eq_mid(self):
        rgb = get_rgb(50, 0, 100)
        self.assertListEqual(rgb, [0, 1, 0])

    def test_get_rgb_val_eq_mid(self):
        rgb = get_rgb(50, 0, 100)
        self.assertListEqual(rgb, [0, 1, 0])

    def test_get_rgb_interp_low(self):
        rgb = get_rgb(25, 0, 100)
        self.assertListEqual(rgb, [0, 0.5, 0.5])

    def test_get_rgb_interp_high(self):
        rgb = get_rgb(75, 0, 100)
        self.assertListEqual(rgb, [0.5, 0.5, 0])
