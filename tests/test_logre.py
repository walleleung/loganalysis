#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division

import unittest
from datetime import datetime, timedelta

from loganalysis import utils
from loganalysis import logre


class TupleRegexTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2014, 1, 1, 0, 0, 0)

    def test_preprocess(self):
        expected = r'^.*?\tfail\t.*?\tblah\t?.*?$'
        actual = logre.compile_tuple_pattern(r'{{1:fail}} {{3:blah}}')
        self.assertEqual(expected, actual)

    def test_encode(self):
        expected = '2014-01-01T00:00:00.000000\tfail\tblah'
        actual = logre.encode_tuple([self.now + timedelta(0), 'fail', 'blah'])
        self.assertEqual(
            expected,
            actual
        )

    def test_match(self):
        log = [
            (self.now + timedelta(0), 'fail', 'a'),
            (self.now + timedelta(1), 'success', 'a'),
            (self.now + timedelta(2), 'fail', 'b'),
            (self.now + timedelta(3), 'success', 'a', 'blah'),
            (self.now + timedelta(4), 'successful', 'a'),
            (self.now + timedelta(5), 'success', 'b'),
        ]
        p = logre.TupleRegex(r'{{1:success}} {{2:a}}')
        expected = [
            (self.now + timedelta(1), 'success', 'a'),
            (self.now + timedelta(3), 'success', 'a', 'blah'),
        ]
        actual = list(p.finditer(log))
        self.assertListEqual(expected, actual)


class LogRegexTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2014, 1, 1, 0, 0, 0)

    def test_preprocess(self):
        expected = r'(^\d+\t.*?\tA\t.*?\tB(\t.+)?\n){2}(^\d+\t.*?\tC(\t.+)?\n)'
        actual = logre.compile_pattern(
            r'[[ {{1:A}} {{3:B}} ]]{2}'
            r'[[ {{1:C}} ]]'
        )
        self.assertEqual(expected, actual)

    def test_encode(self):
        log = [
            (self.now + timedelta(0), 'fail'),
            (self.now + timedelta(1), 'success'),
        ]
        actual = logre.encode(log)
        expected = '\n'.join([
            '0\t2014-01-01T00:00:00.000000\tfail',
            '1\t2014-01-02T00:00:00.000000\tsuccess',
            '',
        ])
        self.assertEqual(expected, actual)

    def test_match(self):
        log = [
            # should match
            (self.now + timedelta(0), 'fail', 'blah'),
            (self.now + timedelta(1), 'fail', 'blah'),
            (self.now + timedelta(2), 'success', 'blah'),

            # should not match: there's only one fail log
            (self.now + timedelta(3), 'fail', 'blah'),
            (self.now + timedelta(4), 'success', 'blah'),

            # should match
            (self.now + timedelta(5), 'fail', 'blah'),
            (self.now + timedelta(6), 'fail', 'blah'),
            (self.now + timedelta(7), 'fail', 'blah'),
            (self.now + timedelta(8), 'success', 'blah'),

            # should not match: the 2nd column should be "fail" but "failure"
            (self.now + timedelta(9), 'failure', 'blah'),
            (self.now + timedelta(10), 'failure', 'blah'),
            (self.now + timedelta(11), 'success', 'blah'),
        ]
        p = logre.LogRegex(
            r'[[ {{1:fail}} ]]{2,}'
            r'[[ {{1:success}} ]]'
        )
        matches = list(p.finditer(log))

        self.assertEqual(2, len(matches))
        self.assertEqual(
            (
                (self.now + timedelta(0), 'fail', 'blah'),
                (self.now + timedelta(1), 'fail', 'blah'),
                (self.now + timedelta(2), 'success', 'blah'),
            ),
            matches[0]
        )
        self.assertEqual(
            (
                (self.now + timedelta(5), 'fail', 'blah'),
                (self.now + timedelta(6), 'fail', 'blah'),
                (self.now + timedelta(7), 'fail', 'blah'),
                (self.now + timedelta(8), 'success', 'blah'),
            ),
            matches[1]
        )

    def test_logregex_with_sessionization(self):
        log = [
            (self.now + timedelta(0), 'alan', 'login'),
            (self.now + timedelta(1), 'alan', 'dosomething'),
            (self.now + timedelta(2), 'alan', 'acquired', 'legend'),
            (self.now + timedelta(3), 'brad', 'login'),
            (self.now + timedelta(4), 'brad', 'acquired', 'rare'),
            (self.now + timedelta(5), 'cate', 'login'),
            (self.now + timedelta(6), 'brad', 'logout'),
            (self.now + timedelta(7), 'cate', 'acquired', 'unique'),
            (self.now + timedelta(8), 'cate', 'logout'),
            (self.now + timedelta(9), 'cate', 'login'),
        ]

        # Sessionize
        sessions = utils.sessionize(log, 0, 1, timedelta(10))

        # A pattern to find sessions containing a legend or an unique item
        # acquisition
        p = logre.LogRegex(
            # 2nd column is "login"
            r'[[ {{2:login}} ]]'
            # zero or more lines
            r'[[ ]]*?'
            # 2nd column is "acquired" and 3rd column is "legend" or "unique"
            r'[[ {{2:acquired}} {{3:(legend|unique)}} ]]'
            # zero or more lines
            r'[[ ]]*?'
            # 2nd column is "logout", but the entire row is optional
            r'[[ {{2:logout}} ]]?'
        )

        # There should be two sessions
        expected = [
            (
                (self.now + timedelta(0), 'alan', 'login'),
                (self.now + timedelta(1), 'alan', 'dosomething'),
                (self.now + timedelta(2), 'alan', 'acquired', 'legend'),
            ),
            (
                (self.now + timedelta(5), 'cate', 'login'),
                (self.now + timedelta(7), 'cate', 'acquired', 'unique'),
                (self.now + timedelta(8), 'cate', 'logout'),
            ),
        ]
        actual = list(p.finditer_m(session for user, session in sessions))
        self.assertEqual(expected, actual)
