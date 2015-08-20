#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import unittest
from datetime import datetime, timedelta

from loganalysis import utils


class SessionizingTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now()
        self.timeout = timedelta(5)

    def test_empty(self):
        log = iter([])
        self.assertListEqual(
            [],
            list(utils.sessionize(log, 0, 1, self.timeout))
        )

    def test_single_user_single_session(self):
        log = iter([
            (self.now + timedelta(0), 'alan', 'login'),
            (self.now + timedelta(1), 'alan', 'stage/1'),
            (self.now + timedelta(2), 'alan', 'stage/2'),
        ])
        actual = list(utils.sessionize(log, 0, 1, self.timeout))

        expected = [
            ('alan', [
                (self.now + timedelta(0), 'alan', 'login'),
                (self.now + timedelta(1), 'alan', 'stage/1'),
                (self.now + timedelta(2), 'alan', 'stage/2'),
            ]),
        ]
        self.assertListEqual(expected, actual)

    def test_single_user_multiple_sessions(self):
        log = iter([
            # Session #1
            (self.now + timedelta(0), 'alan', 'login'),
            (self.now + timedelta(1), 'alan', 'stage/1'),

            # Session #2
            (self.now + timedelta(6), 'alan', 'stage/2'),
            (self.now + timedelta(7), 'alan', 'stage/3'),
        ])
        actual = list(utils.sessionize(log, 0, 1, self.timeout))

        expected = [
            ('alan', [
                (self.now + timedelta(0), 'alan', 'login'),
                (self.now + timedelta(1), 'alan', 'stage/1'),
            ]),
            ('alan', [
                (self.now + timedelta(6), 'alan', 'stage/2'),
                (self.now + timedelta(7), 'alan', 'stage/3'),
            ]),
        ]
        self.assertListEqual(expected, actual)

    def test_multiple_users_multiple_sessions(self):
        log = iter([
            (self.now + timedelta(0), 'alan', 'login'),
            (self.now + timedelta(1), 'alan', 'stage/1'),
            (self.now + timedelta(1), 'brad', 'stage/1'),
            (self.now + timedelta(3), 'brad', 'stage/2'),
            (self.now + timedelta(6), 'alan', 'stage/2'),
            (self.now + timedelta(7), 'alan', 'stage/3'),
            (self.now + timedelta(8), 'brad', 'stage/3'),
        ])
        actual = list(utils.sessionize(log, 0, 1, self.timeout))
        actual_alan = [
            (cid, sessions) for cid, sessions in actual if cid == 'alan'
        ]
        actual_brad = [
            (cid, sessions) for cid, sessions in actual if cid == 'brad'
        ]

        expected_alan = [
            ('alan', [
                (self.now + timedelta(0), 'alan', 'login'),
                (self.now + timedelta(1), 'alan', 'stage/1'),
            ]),
            ('alan', [
                (self.now + timedelta(6), 'alan', 'stage/2'),
                (self.now + timedelta(7), 'alan', 'stage/3'),
            ]),
        ]
        self.assertListEqual(expected_alan, actual_alan)

        expected_brad = [
            ('brad', [
                (self.now + timedelta(1), 'brad', 'stage/1'),
                (self.now + timedelta(3), 'brad', 'stage/2'),
            ]),
            ('brad', [
                (self.now + timedelta(8), 'brad', 'stage/3'),
            ]),
        ]
        self.assertListEqual(expected_brad, actual_brad)

    def test_yield_order(self):
        # brad's session should be yielded before alan's 2nd session.
        log = iter([
            (self.now + timedelta(0), 'alan', 'login'),
            (self.now + timedelta(1), 'brad', 'login'),
            (self.now + timedelta(2), 'alan', 'stage/1'),
            # <- alan's session timeout
            # <- brad's session timeout
            (self.now + timedelta(7), 'alan', 'stage/2'),
            # <- alan's 2nd session timeout
            (self.now + timedelta(12), 'alan', 'stage/3'),
            # <- alan's 3nd session timeout
        ])
        actual = [
            cid for cid, sessions in utils.sessionize(log, 0, 1, self.timeout)
        ]
        expected = ['alan', 'brad', 'alan', 'alan']
        self.assertListEqual(expected, actual)


class StateMachineTest(unittest.TestCase):
    def test_simple_login_and_out(self):
        table = {
            ('anonymous', 'login'): ('welcome', 'logged-in'),
            ('anonymous', 'logout'): ('not logged-in yet', 'anonymous'),
            ('logged-in', 'login'): ('already logged-in', 'loggined-in'),
            ('logged-in', 'logout'): ('good-bye', 'anonymous'),
        }

        self.assertListEqual(
            ['welcome', 'good-bye'],
            list(utils.fsm(['login', 'logout'], 'anonymous', table))
        )
        self.assertListEqual(
            ['welcome', 'already logged-in'],
            list(utils.fsm(['login', 'login'], 'anonymous', table))
        )
        self.assertListEqual(
            ['not logged-in yet'],
            list(utils.fsm(['logout'], 'anonymous', table))
        )

    def test_complex_case(self):
        now = datetime.now()
        timeout = timedelta(5)
        table = {
            # (current_state, event):        (action, next_state)
            ('init', 'rnd_track'):        (None, 'rnd_wait'),
            ('init', 'trial'):            (None, 'fxd_started'),
            ('init', 'retire'):           (('fxd', 'retire'), 'init'),

            ('rnd_wait', 'rnd_track'):    (('rnd', 'finish'), 'rnd_wait'),
            ('rnd_wait', 'trial'):        (None, 'rnd_started'),
            ('rnd_wait', 'retire'):       (('rnd', 'retire'), 'init'),
            ('rnd_wait', 'i_chngr'):      (('rnd', 'i_chngr'), 'rnd_started'),
            ('rnd_wait', 's_chngr'):      (('rnd', 's_chngr'), 'rnd_started'),
            ('rnd_wait', None):           (('rnd', 'finish'), 'init'),

            ('rnd_started', 'rnd_track'): (('rnd', 'finish'), 'init'),
            ('rnd_started', 'trial'):     (('rnd', 'finish'), 'fxd_started'),
            ('rnd_started', 'retire'):    (('rnd', 'retire'), 'init'),
            ('rnd_started', 'i_chngr'):   (('rnd', 'i_chngr'), 'rnd_started'),
            ('rnd_started', 's_chngr'):   (('rnd', 's_chngr'), 'rnd_started'),
            ('rnd_started', None):        (('rnd', 'finish'), 'init'),

            ('fxd_started', 'rnd_track'): (('fxd', 'finish'), 'rnd_wait'),
            ('fxd_started', 'trial'):     (('fxd', 'finish'), 'fxd_started'),
            ('fxd_started', 'retire'):    (('fxd', 'retire'), 'init'),
            ('fxd_started', 'i_chngr'):   (('fxd', 'i_chngr'), 'fxd_started'),
            ('fxd_started', 's_chngr'):   (('fxd', 's_chngr'), 'fxd_started'),
            ('fxd_started', None):        (('fxd', 'finish'), 'init'),
        }
        log = iter([
            (now + timedelta(0), 'alan', 'trial'),
            (now + timedelta(1), 'alan', 'i_chngr'),
            (now + timedelta(2), 'brad', 'rnd_track'),
            (now + timedelta(3), 'alan', 'retire'),
            (now + timedelta(4), 'brad', 'rnd_track'),
            (now + timedelta(5), 'cate', 'retire'),
            (now + timedelta(6), 'cate', 'rnd_track'),
            (now + timedelta(7), 'cate', 's_chngr'),
            (now + timedelta(8), 'alan', 'retire'),
        ])
        expected_actions = [
            ('alan', 0, 'fxd', 'i_chngr'),
            ('alan', 0, 'fxd', 'retire'),
            ('brad', 1, 'rnd', 'finish'),
            ('brad', 1, 'rnd', 'finish'),
            ('cate', 2, 'fxd', 'retire'),
            ('cate', 2, 'rnd', 's_chngr'),
            ('cate', 2, 'rnd', 'finish'),
            ('alan', 3, 'fxd', 'retire')
        ]
        actual_actions = list(
            (cid, session_id, action_category, action)
            for session_id, (cid, session) in enumerate(
                utils.sessionize(log, 0, 1, timeout)
            )
            for action_category, action in utils.fsm(
                (row[2] for row in session), 'init', table
            )
        )
        self.assertListEqual(expected_actions, actual_actions)
