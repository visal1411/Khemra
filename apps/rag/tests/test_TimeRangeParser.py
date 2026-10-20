from datetime import timedelta

from django.test import SimpleTestCase

from apps.rag.utils.TimeRangeParser import TimeRangeParser


class TimeRangeParserTest(SimpleTestCase):
    def test_parse_and_format_roundtrip(self):
        start, end = TimeRangeParser.parse("00:10 - 00:19")
        self.assertEqual(start, timedelta(seconds=10))
        self.assertEqual(end, timedelta(seconds=19))
        self.assertEqual(TimeRangeParser.format(start, end), "00:10 - 00:19")

    def test_hours(self):
        start, end = TimeRangeParser.parse("59:50 - 01:00:05")
        self.assertEqual(TimeRangeParser.format(start, end), "59:50 - 01:00:05")

    def test_empty(self):
        self.assertEqual(TimeRangeParser.parse(""), (None, None))
        self.assertEqual(TimeRangeParser.format(None, None), "")

    def test_invalid(self):
        for bad in ("abc", "00:10", "00:10 - x", "1:2:3:4 - 5"):
            with self.assertRaises(ValueError):
                TimeRangeParser.parse(bad)
