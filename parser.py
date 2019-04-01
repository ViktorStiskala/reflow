from decimal import Decimal

import re
from dateutil.parser import parse

RE_TS = r'(?P<ts_date>\w{3} \d{1,2}) (?P<ts_time>\d{2}:\d{2}:\d{2})'
RE_DIVIDER = re.compile(r' Deviation to abort.+? Play tune', re.DOTALL)


class Reflow:
    class Item:
        def __init__(self, match, start):
            self.timestamp = Reflow.get_date_from_match(match)
            self.timer = int(match.group('timer'))
            self.temp = Decimal(match.group('temp'))

        def __iter__(self):
            return iter((self.timestamp, self.timer, self.temp))

        def __repr__(self):
            return "('{s.timestamp}', '{s.timer}', '{s.temp}')".format(s=self)

    def __init__(self, data):
        self._data = data

        start = re.search(RE_TS + r' Cooled to desired temperature', self._data)
        reflow_start = re.search(RE_TS + r' Initialize timer to 15 seconds', self._data)
        reflow_end = re.search(RE_TS + r' Stop timer', self._data)

        self.date_started = self.get_date_from_match(start)
        self.date_reflow_started = self.get_date_from_match(reflow_start)
        self.date_reflow_ended = self.get_date_from_match(reflow_end)

    @classmethod
    def get_date_from_match(cls, match):
        return parse('{} {}'.format(
            match.group('ts_date'),
            match.group('ts_time')
        ))

    def get_reflow_profile(self):
        # Mar 17 21:11:14 312, 249.48, 0, 0
        m = re.finditer(RE_TS + r' (?P<timer>\d+), (?P<temp>\d{1,3}\.\d{2}), 0, 0', self._data, re.MULTILINE)

        start = None
        for match in m:
            if start is None:
                start = self.get_date_from_match(match)
            yield self.Item(match, start)


class ReflowLogParser:
    def __init__(self, path):
        self.path = path
        self.reflows = []

    def parse(self):
        if not self.reflows:
            with open(self.path, 'r') as f:
                data = f.read()

                self.reflows = [Reflow(item) for item in RE_DIVIDER.findall(data)]

