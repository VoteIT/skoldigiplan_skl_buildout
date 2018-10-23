# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from voteit.core import security
from voteit.core.models.interfaces import IProposal


def participant_edit_proposal(context, request, va, **kw):
    if not request.is_moderator and request.has_permission(security.EDIT, context):
        return """<a href="{url}"
         title="Redigera förslag"
         role="button"
         class="btn btn-default btn-xs"
         data-placement="bottom"
         data-external-popover-loaded="false">
        <span class="text-primary">
          &nbsp;<span class="glyphicon glyphicon-edit"></span>&nbsp;
        </span>
      </a>""".format(url = request.resource_url(context, 'edit'), uid=context.uid)


def includeme(config):
    config.add_view_action(
        participant_edit_proposal,
        'metadata_listing', 'edit_proposal',
        title="Redigera",
        interface=IProposal,
        priority=15,
    )
