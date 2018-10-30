# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from arche.interfaces import IRoot
from arche.security import groupfinder
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config
from pyramid.view import view_defaults
from repoze.catalog.query import Eq
from skl_theme.interfaces import IEffectSettings
from skl_theme.views.jsonapi import APIKeyView
from voteit.core.helpers import get_meeting_participants
from voteit.core.models.interfaces import IMeeting
from voteit.core.security import ROLE_VOTER


@view_defaults(context=IRoot, renderer='csv', permission=NO_PERMISSION_REQUIRED)
class CSVExports(APIKeyView):
    def get_voter_count(self, meeting):
        return len(list(meeting.local_roles.get_any_local_with(ROLE_VOTER)))

    @view_config(name='all_proposals.csv')
    def meetings(self):
        def proposals():
            for name, obj in self.context.items():
                if not IMeeting.providedBy(obj):
                    continue
                settings = dict(IEffectSettings(obj))
                effect_actors = set(str.lower() for str in settings.get('effect_actors', ()))
                result, docids = self.request.root.catalog.query(
                    Eq('path', self.request.resource_path(obj)) &
                    Eq('type_name', 'AgendaItem')
                )
                voter_count = self.get_voter_count(obj)
                for ai in self.request.resolve_docids(docids, perm=None):
                    result, polldocids = self.request.root.catalog.query(
                        Eq('path', self.request.resource_path(ai)) &
                        Eq('type_name', 'Poll')
                    )
                    polls = [poll for poll in self.request.resolve_docids(polldocids, perm=None) if poll.poll_plugin_name=='sorted_schulze' and poll.poll_result]
                    result, pdocids = self.request.root.catalog.query(
                        Eq('path', self.request.resource_path(ai)) &
                        Eq('type_name', 'Proposal')
                    )
                    for prop in self.request.resolve_docids(pdocids, perm=None):
                        tags = set(prop.tags)
                        effect_tags = effect_actors.intersection(tags)
                        other_tags = tags.difference(effect_tags)
                        position = voters = ''
                        for poll in polls:
                            if poll.poll_result:
                                winners = poll.poll_result['winners']
                                if prop.uid in winners:
                                    position = '{}/{}'.format(winners.index(prop.uid)+1, len(winners))
                                    voters = '{}/{}'.format(len(poll.ballots), voter_count)
                        yield([
                            obj.title,
                            ai.title,
                            prop.text,
                            ' '.join(prop.creator),
                            prop.created.strftime('%Y-%m-%d %H:%M'),
                            ' '.join(effect_tags),
                            ' '.join(other_tags),
                            position,
                            voters,
                        ])

        return {
            'header': [
                'Möte',
                'Dagordningspunkt',
                'Brödtext',
                'Förslagställare',
                'Tid',
                'Vem-taggar',
                'Alla taggar',
                'Rankning',
                'Antal röstande'
            ],
            'rows': proposals(),
        }


def includeme(config):
    config.scan(__name__)
