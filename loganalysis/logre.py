# -*- coding: utf-8 -*-
"""
A simple extension of a regular expression to denote a pattern across multiple
lines.
"""

import re
from datetime import datetime


_P_ROW = re.compile(r'\[\[(.+?)\]\]([^\[]*)')
_P_COL = re.compile(r'\{\{(\d+):(.+?)\}\}')
_DEFAULT_TIME_FORMAT = u'%Y-%m-%dT%H:%M:%S.%f'


class TupleRegex(object):
    def __init__(self, p, col_sep='\t'):
        self._col_sep = col_sep
        self._compiled_p = re.compile(compile_tuple_pattern(p, col_sep))

    def finditer(self, logs):
        return (
            log for log in logs
            if self._compiled_p.match(encode_tuple(log, self._col_sep))
        )


def compile_tuple_pattern(p, col_sep='\t'):
    """Turn TupleRegex pattern into plain regex pattern"""
    regex_parts = []
    matches = list(re.finditer(_P_COL, p))
    last_index = 0
    for m in matches:
        index, pattern = m.groups()
        index = int(index)

        while last_index < index:
            regex_parts.append(r'.*?')
            last_index += 1

        regex_parts.append(pattern)
        last_index += 1

    encoded_col_sep = col_sep.encode('unicode-escape').decode('utf-8')
    return r'^' + encoded_col_sep.join(regex_parts) + r'\t?.*?$'


def encode_tuple(row, sep='\t'):
    encoded = []
    for token in row:
        if type(token) == datetime:
            encoded.append(token.strftime(_DEFAULT_TIME_FORMAT))
        else:
            encoded.append(token)
    return sep.join(encoded)


class LogRegex(object):
    def __init__(self, p, col_sep='\t'):
        self._col_sep = col_sep
        self._compiled_p = re.compile(compile_pattern(p, col_sep), re.M)

    def finditer(self, log):
        return (m for m in self.finditer_m([log]))

    def finditer_m(self, logs):
        """Performs finditer() on a list of multiple logs, each log in a list
        usually represents a single session."""
        for log in logs:
            matches = self._compiled_p.finditer(encode(log))
            for m in matches:
                yield tuple(
                    log[int(i)]
                    for i in re.findall(r'^(\d+)\t', m.group(), re.M)
                )


def compile_pattern(p, col_sep='\t'):
    """Turn LogRegex pattern into plain regex pattern"""
    row_regexes = []

    # Each row in LogRegex pattern
    m_rows = list(re.finditer(_P_ROW, p))
    for m_row in m_rows:
        row_regexes.append(r'(^')
        cols, modifier = m_row.groups()
        last_index = 0

        col_regexes = ['\d+']

        # Each col in LogRegex's row pattern
        m_cols = list(re.finditer(_P_COL, cols))
        for m_col in m_cols:
            index, pattern = m_col.groups()
            index = int(index)

            while last_index < index:
                col_regexes.append(r'.*?')
                last_index += 1

            col_regexes.append(pattern)
            last_index += 1

        encoded_col_sep = col_sep.encode('unicode-escape').decode('utf-8')
        row_regexes.append(
            encoded_col_sep.join(col_regexes) +
            r'(\t.+)?\n)' +
            modifier
        )

    return ''.join(row_regexes)


def encode(log, sep='\t'):
    """Turn log into single string so that the log can be matched using
    LogRegex pattern"""
    return '\n'.join(
        str(i) + sep + encode_tuple(row, sep)
        for i, row in enumerate(log)
    ) + '\n'
