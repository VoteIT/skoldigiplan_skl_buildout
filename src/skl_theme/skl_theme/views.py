# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import Counter
import re

from arche.views.base import BaseView
from arche.views.base import DefaultEditForm
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.renderers import render
from pyramid.response import Response
from voteit.core import security
from voteit.core.helpers import get_meeting_participants
from voteit.core.models.interfaces import IMeeting
from voteit.core.models.interfaces import IProposal
from voteit.core.views.control_panel import control_panel_link

from skl_theme.interfaces import IEffectSettings
from skl_theme.schemas import EditEffectsSchema
from skl_theme.schemas import get_kommun_values
from skl_theme.schemas import _organisation_values
from skl_theme.security import EDIT_EFFECT_CATEGORY


def _effect_active(request):
    try:
        return request._effect_button_active
    except AttributeError:
        pass
    settings = dict(IEffectSettings(request.meeting))
    request._effect_button_active = effect_active = settings.get('effect_active', False)
    return effect_active


class EffectSettingsForm(DefaultEditForm):
    type_name = 'Meeting'
    schema_name = 'effect_settings'
    title = "Effektkategorier"

    def list_to_tags(self, text):
        result = set()
        for row in text.splitlines():
            row = row.strip()
            if not row:
                continue
            result.add(row)
        return sorted(result, key=lambda x: x.lower())

    def appstruct(self):
        appstruct = dict(IEffectSettings(self.context))
        if appstruct.get('effect_actors', None):
            appstruct['effect_actors'] = "\n".join(appstruct['effect_actors'])
        return appstruct

    def save_success(self, appstruct):
        appstruct['effect_actors'] = self.list_to_tags(appstruct['effect_actors'])
        settings = IEffectSettings(self.context)
        settings.update(appstruct)
        return HTTPFound(location=self.request.resource_url(self.context))

_eff_schema = EditEffectsSchema()
_effect_time_vals = set([x[0].lower() for x in _eff_schema['effect_time'].widget.values if x])
_eff_schema = None

def effect_action(context, request, va, **kw):
    if _effect_active(request):
        notice = False
        tags = set(context.tags)
        settings = dict(IEffectSettings(request.meeting))
        if not set([x.lower() for x in settings.get('effect_actors', ()) if x]) & tags:
            notice = True
        if not _effect_time_vals & tags:
            notice = True
        return render('skl_theme:templates/effect_action.pt',
                      {'context': context, 'title': va.title, 'notice': notice},
                      request=request)


class EditEffectsForm(DefaultEditForm):
    type_name = 'Proposal'
    schema_name = 'edit_effects'
    title = "Preciseringar"
    update_structure_tpl = 'voteit.core:templates/snippets/js_update_structure.pt'
    use_ajax = True

    def __call__(self):
        if not _effect_active(self.request):
            raise HTTPForbidden()
        return super(EditEffectsForm, self).__call__()

    @property
    def popover_id(self):
        return "#effect-edit-%s" % self.context.uid

    def _response(self, *args, **kw):
        return Response(self.render_template(self.update_structure_tpl, **kw))

    @reify
    def time_tags(self):
        return set([k for (k, v) in self.schema['effect_time'].widget.values if k])

    @reify
    def actors_tags(self):
        return set([k for (k, v) in self.schema['effect_actors'].widget.values if k])

    def appstruct(self):
        settings = dict(IEffectSettings(self.request.meeting))
        appstruct = {'effect_time': '', 'effect_actors': []}
        for k in self.time_tags:
            if k.lower() in self.context.tags:
                appstruct['effect_time'] = k
                break
        for k in settings.get('effect_actors', ()):
            if k.lower() in self.context.tags:
                appstruct['effect_actors'].append(k)
        return appstruct

    def save_success(self, appstruct):
        text = self.context.text
        current_tags = set(self.context.tags)
        effect_time = appstruct['effect_time']
        # First check any that shouldn't exist
        unwanted_tags = self.time_tags
        if effect_time in unwanted_tags:
            unwanted_tags.remove(effect_time)
        selected_actors = set(appstruct['effect_actors'])
        unwanted_tags.update(self.actors_tags - selected_actors)
        unwanted_tags = current_tags & set(map(lambda x: x.lower(), unwanted_tags))
        if unwanted_tags:
            for tag in unwanted_tags:
                search_crit = re.compile(r'(^|\s)#{}(\s|$)'.format(tag),
                                         re.IGNORECASE | re.UNICODE)
                text = search_crit.sub(' ', text)
            text = text.strip()
        new_tags = []
        if effect_time and effect_time.lower() not in current_tags:
            new_tags.append(effect_time)
        lowercased_selected_actors = set(map(lambda x: x.lower(), selected_actors))
        if lowercased_selected_actors - current_tags:
            # There are new actors, handle them with uppercase
            for tag in selected_actors:
                if tag.lower() not in current_tags:
                    new_tags.append(tag)
        if new_tags:
            # Inject new tags together with other tags, or on a news line
            last_line = text.splitlines()[-1]
            out = ""
            if last_line.startswith('#'):
                out += " "
            elif last_line:
                out += "\n"
            out += " ".join(['#%s' % x for x in new_tags])
            text += out
        self.context.update(text=text)
        return self._response(destroy_popover=self.popover_id,
                              load_target="#ai-proposals [data-load-target]",
                              scroll_to='[data-uid="%s"]' % self.context.uid)

    def cancel(self, *args):
        return self._response(destroy_popover=self.popover_id)

    cancel_success = cancel_failure = cancel


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
#         id="participant-edit-{uid}"


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
        control_panel_link, 'control_panel_proposal', 'effect_settings',
        title="Effektkategorier", view_name='effect_settings'
    )
    config.add_view(
        EffectSettingsForm,
        context=IMeeting,
        name="effect_settings",
        renderer="arche:templates/form.pt",
        permission=security.MODERATE_MEETING
    )
    config.add_view_action(
        effect_action,
        'metadata_listing', 'edit_effect',
        title="Precisering av förslag",
        permission=EDIT_EFFECT_CATEGORY,
        interface=IProposal,
        priority=1,
    )
    config.add_view(
        EditEffectsForm,
        context=IProposal,
        name='edit_effects',
        permission=EDIT_EFFECT_CATEGORY,
        renderer="arche:templates/form.pt"
    )
    config.add_view_action(
        participant_edit_proposal,
        'metadata_listing', 'edit_proposal',
        title="Redigera",
        interface=IProposal,
        priority=15,
    )
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
