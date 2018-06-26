# -*- coding: utf-8 -*-
from voteit.core.models.user import User


def includeme(config):
    """ Add extra attributes to user profile."""
    User.kommun = None
    User.work_role = ""
