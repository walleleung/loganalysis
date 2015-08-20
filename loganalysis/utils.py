# -*- coding: utf-8 -*-
"""A collection of utility functions"""

from collections import OrderedDict
from itertools import chain


def sessionize(log, ts_index, cid_index, timeout):
    """
    Groups a log stream into sessions

    Let's say Alan and Brad played a game simultaneously::

        >>> from datetime import datetime, timedelta
        >>> log = [
        ...     (datetime(2015, 1, 1, 0, 10, 0), 'alan', 'login'),
        ...     (datetime(2015, 1, 1, 0, 11, 0), 'alan', 'stage/1'),
        ...     (datetime(2015, 1, 1, 0, 11, 0), 'brad', 'stage/1'),
        ...     (datetime(2015, 1, 1, 0, 12, 0), 'alan', 'stage/2'),
        ...     (datetime(2015, 1, 1, 0, 13, 0), 'brad', 'stage/2'),
        ...     (datetime(2015, 1, 1, 0, 17, 0), 'alan', 'stage/3'),
        ...     (datetime(2015, 1, 1, 0, 18, 0), 'alan', 'stage/4'),
        ...     (datetime(2015, 1, 1, 0, 19, 0), 'brad', 'stage/3'),
        ... ]

    The function takes the log and yields sessionized logs::

        >>> timestamp_column = 0
        >>> user_column = 1
        >>> timeout = timedelta(minutes=5)
        >>> sessions = list(sessionize(log, 0, 1, timeout))

    Since we defined session timeout as 5 minutes, ``sessions`` should contain
    four sessions, two for Alan and another two for Brad::

        >>> len(sessions)
        4

    Each session in `sessions` is a :class:`tuple` with two elements. The first
    element of the tuple is an user id, and the second is a list containing
    subset of the log belongs to the session::

        >>> user_id, session = sessions[1]
        >>> user_id
        'brad'
        >>> session == [log[2], log[4]]
        True

    Note that the function takes an `iterable` and returns `generator`. It can
    be used to process a real-time stream of events with an arbitrary length,
    such as system log.

    :param log: an iterable containing zero or more tuples
    :type  log: iterable
    :param ts_index: index of timestamp column
    :type  ts_index: int
    :param cid_index: index of client id column
    :type  cid_index: int
    :param timeout: session timeout
    :type  timeout: :class:`~datetime.timedelta`

    :return: generator of tuples composed of (cid, sessions)
    """
    sessions = OrderedDict()

    for row in log:
        cur_ts = row[ts_index]

        # Yield expired sessions
        for cid, session in sessions.items():
            if not _check_session_timeout(session, cur_ts, timeout):
                # Since items in sessions are ordered by updated time,
                # we don't have to look futher
                break
            yield cid, session[1]
            del sessions[cid]

        # Create or get session
        cid = row[cid_index]
        if cid not in sessions:
            session = [None, []]
            sessions[cid] = session
        else:
            session = sessions[cid]

        session[0] = cur_ts
        session[1].append(row)

    # If there are non-empty session logs, flush them.
    for cid, session in sessions.items():
        if len(session[1]) > 0:
            yield cid, session[1]


def _check_session_timeout(session, cur_ts, timeout):
    return session[0] is not None and cur_ts - session[0] >= timeout


def fsm(events, init_state, table):
    """
    Simple finite state machine.

    "table" is a instance of dict whose keys and values take following
    form:

    *  key: (current state, event)
    *  value: (action, next state)

    `None` in "event" represents the termination event, and `None` in "action"
    represents a state-transition without action.

    For example, following table represents a state-machine with two events
    (login, logout) and two states (anonymous, logged-in)::

        >>> table = {
        ...     ('anonymous', 'login'): ('welcome', 'logged-in'),
        ...     ('anonymous', 'logout'): ('not logged-in yet', 'anonymous'),
        ...     ('logged-in', 'login'): ('already logged-in', 'loggined-in'),
        ...     ('logged-in', 'logout'): ('good-bye', 'anonymous'),
        ... }

    If an initial state is `anonymous`, and two `login` events occur
    successively, then the state machine defined in the above table yields
    `welcome` for the first `login` event, and then yields `already logged-in`
    for the second one::

        >>> events = fsm(['login', 'login'], 'anonymous', table)
        >>> next(events)
        'welcome'
        >>> next(events)
        'already logged-in'

    Since the function takes an `iterable` and returns `generator`, it can be
    used to process a real-time stream of events with an arbitrary length, such
    as system log.

    :param events: an iterable containing events
    :type  events: iterable
    :param init_state: initial state of FSM
    :type  init_state: str
    :param table: state-transition table
    :type  table: dict
    """
    cur_state = init_state

    for event in chain(events, [None]):
        key = (cur_state, event)
        if key not in table:
            continue
        action, next_state = table[key]
        if action:
            yield action
        cur_state = next_state
