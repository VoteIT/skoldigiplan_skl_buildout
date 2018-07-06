# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import argparse
from collections import Counter

from pyramid.paster import bootstrap
from skl_theme.schemas import get_kommun_values
from voteit.core.security import ROLE_VOTER, find_role_userids


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("config_uri", help="Paster ini file to load settings from")
    parser.add_argument("meeting", help="Meeting name")
    args = parser.parse_args()
    env = bootstrap(args.config_uri)
    root = env['root']
    request = env['request']
    meeting = root[args.meeting]
    kommuner = dict(get_kommun_values())


    kommun_counter = Counter()

    for userid in find_role_userids(meeting, ROLE_VOTER):
        user = root['users'][userid]
        print kommuner.get(user.kommun, '').ljust(40), user.work_role

    env['closer']()

