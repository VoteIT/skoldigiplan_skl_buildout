# -*- coding: utf-8 -*-
from calendar import timegm

from arche.views.base import BaseView
from arche.interfaces import IRoot
from pyramid.httpexceptions import HTTPForbidden
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.traversal import resource_path
from pyramid.view import view_config
from pyramid.view import view_defaults
from repoze.catalog.query import Eq
from voteit.core.helpers import get_meeting_participants
from voteit.core.models.interfaces import IMeeting


class APIKeyView(BaseView):
    """ Protect API views with API key (GET value) """
    def __init__(self, context, request):
        # Check present key
        settings = request.registry.settings
        skl_apikey = settings.get('skl.apikey', None)
        if not skl_apikey:
            raise HTTPForbidden("No API key configured")
        if skl_apikey != request.params.get('apikey', object()):
            raise HTTPForbidden("Wrong API key")
        super(APIKeyView, self).__init__(context, request)


@view_defaults(renderer='json', permission=NO_PERMISSION_REQUIRED)
class JSONViews(APIKeyView):
    """
        Has two main views:
        - /list_meetings.json - does exactly what you think :)
        - /<meeting-id>/export_meeting.json - Gets full meeting info including everything contained.
    """

    def _timestamp(self, value):
        if value is not None:
            return timegm(value.timetuple())

    def _common(self, obj):
        res = {
            'created': self._timestamp(obj.created),
            'path': resource_path(obj),
            'uid': obj.uid,
            'type_name': obj.type_name,
        }
        for ts_attr in ('start_time', 'end_time'):
            if hasattr(obj, ts_attr):
                res[ts_attr] = self._timestamp(getattr(obj, ts_attr, None))
        return res

    def _common_entry(self, obj):
        return {
            'tags': list(obj.tags),
            'creator': list(obj.creator),
            'text': obj.text,
        }

    def _count(self, obj, type_name):
        query = Eq('path', resource_path(obj)) & Eq('type_name', type_name)
        res = self.request.root.catalog.query(query)[0]
        return res.total

    def _meeting(self, meeting):
        res = self._common(meeting)
        res.update(
            title=meeting.title,
            manifest={},
            participants=list(get_meeting_participants(meeting)),
            invite_tickets={},
        )
        for tn in ('AgendaItem', 'Proposal', 'DiscussionPost', 'Poll'):
            res['manifest'][tn] = self._count(meeting, tn)
        res['manifest']['InviteTicket'] = len(meeting.invite_tickets)
        open_tkt = 0
        closed_tkt = 0
        for tkt in meeting.invite_tickets.values():
            if tkt.closed == None:
                open_tkt += 1
            else:
                closed_tkt += 1
        res['invite_tickets']['open'] = open_tkt
        res['invite_tickets']['closed'] = closed_tkt
        return res

    def _agenda_item(self, ai):
        res = self._common(ai)
        res.update(
            title=ai.title,
            manifest={},
        )
        for tn in ('Proposal', 'DiscussionPost', 'Poll'):
            res['manifest'][tn] = self._count(ai, tn)
        return res

    def _proposal(self, prop):
        res = self._common(prop)
        res.update(self._common_entry(prop))
        res['aid'] = prop.aid
        return res

    def _discussion_post(self, dp):
        res = self._common(dp)
        res.update(self._common_entry(dp))
        return res

    def _poll(self, poll):
        res = self._common(poll)
        res.update(
            title=poll.title,
            poll_plugin=poll.poll_plugin,
            manifest={'Vote': len(poll)},
        )
        return res

    def _export_contents(self, context):
        func = self.map_func.get(getattr(context, 'type_name', ''), None)
        if func is None:
            return
        result = func(context)
        if 'contents' not in result:
            result['contents'] = []
        for obj in context.values():
            res = self._export_contents(obj)
            if res:
                result['contents'].append(res)
        return result

    @view_config(context=IRoot, name='list_meetings.json')
    def list_meetings(self):
        """
        Return a list of all meetings.
        See _meeting for properties
        """
        result = []
        for meeting in self.context.values():
            if not IMeeting.providedBy(meeting):
                continue
            result.append(self._meeting(meeting))
        return result

    @view_config(context=IMeeting, name='export_meeting.json')
    def export_meeting(self):
        """ Export a specific meeting and everything (relevant) contained in it.

            Contained items will be at 'contents', according to this structure:

            Meeting
            -   Invite Tickets
            -   Agenda Item
                -   Discussion Post
                -   Poll
                    -   Vote
                -   Proposal

            Votes won't be included, but all other items will.

            A count for contained items in each context is available as 'manifest'.
        """
        return self._export_contents(self.context)

    @property
    def map_func(self):
        return {
            'AgendaItem': self._agenda_item,
            'Proposal': self._proposal,
            'DiscussionPost': self._discussion_post,
            'Poll': self._poll,
            'Meeting': self._meeting,
        }


def includeme(config):
    config.scan(__name__)
