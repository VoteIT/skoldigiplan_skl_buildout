# -*- coding: utf-8 -*-
from arche.interfaces import IObjectUpdatedEvent
from arche.interfaces import IObjectAddedEvent
from arche.utils import AttributeAnnotations
from voteit.core.models.interfaces import IMeeting, IProposal
from voteit.core.models.user import User
from zope.component import adapter
from zope.interface import implementer

from skl_theme.interfaces import IEffectSettings


@implementer(IEffectSettings)
@adapter(IMeeting)
class EffectSettings(AttributeAnnotations):
    attr_name = '_skl_effect_settings'


def includeme(config):
    """ Add extra attributes to user profile."""
    User.kommun = None
    User.organisation = ()
    User.free_text_org = ""
    User.work_role = ""
    config.registry.registerAdapter(EffectSettings)