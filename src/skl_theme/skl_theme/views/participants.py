# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import Counter

from arche.views.base import BaseView
from pyramid.decorator import reify
from voteit.core import security
from voteit.core.models.interfaces import IMeeting
from voteit.core.views.control_panel import control_panel_link
from voteit.core.helpers import get_meeting_participants

from skl_theme.schemas import get_kommun_values
from skl_theme.schemas import _organisation_values


class ParticipantCriteria(BaseView):

    @reify
    def kommun_dict(self):
        return dict(get_kommun_values())

    @reify
    def org_dict(self):
        return dict(_organisation_values)

    @reify
    def participant_ids(self):
        return get_meeting_participants(self.context)

    def __call__(self):
        users = self.root['users']
        kommuner = Counter()
        organisationer = Counter()
        for userid in self.participant_ids:
            user = users[userid]
            kommuner[self.kommun_dict.get(user.kommun, 'Okänd')] += 1
            for org in user.organisation:
                organisationer[self.org_dict.get(org)] += 1
        return {
            'kommuner': kommuner,
            'organisationer': organisationer,
        }


def includeme(config):
    config.add_view_action(
        control_panel_link, 'control_panel_participants', 'participant_criteria',
        title="Kommuner och organisationer", view_name='participant_criteria'
    )
    config.add_view(
        ParticipantCriteria,
        context=IMeeting,
        name="participant_criteria",
        renderer="skl_theme:templates/participant_criteria.pt",
        permission=security.MODERATE_MEETING
    )
