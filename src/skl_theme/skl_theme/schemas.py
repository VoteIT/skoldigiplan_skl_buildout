# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import os
import re

import colander
import deform
from arche.interfaces import ISchemaCreatedEvent
from arche.schemas import UserSchema
from arche.schemas import FinishRegistrationSchema

from skl_theme.interfaces import IEffectSettings


kommuner_cached = {}

_HERE = os.path.abspath(os.path.dirname(__file__))


def get_kommun_values():
    if not kommuner_cached:
        with open(os.path.join(_HERE, 'data/kommuner.csv')) as csvfile:
            reader = csv.reader(csvfile, delimiter=str(','))
            for row in reader:
                try:
                    kom_id = int(row[0])
                except:
                    continue
                kommuner_cached[kom_id] = row[1]
    values = sorted(kommuner_cached.items(), key=lambda x: x[1].lower())
    values.insert(0, ("", "- Välj eller sök -"))
    return values


_organisation_values = (
    ('kommun', "Kommun"),
    ('kommunal_skola', "Kommunal skola"),
    ('fristaende_skola', "Fristående skola"),
    ('kommunal_huvudman', "Kommunal huvudman"),
    ('fristaende_huvudman', "Fristående huvudman"),
    ('myndighet', "Myndighet"),
    ('larosate', "Lärosäte"),
    ('annat_foretag', "Annat företag"),
    ('branschorganisation', "Branschorganisation"),
    ('ideell_organisation', "Ideell organisation"),
)


def inject_profile_extras(schema, event):
    schema.add(
        colander.SchemaNode(
            colander.Int(),
            name='kommun',
            title = "Vilken kommun är du verksam alternativt folkbokförd i?",
            widget=deform.widget.Select2Widget(values=get_kommun_values()),
        )
    )
    schema.add(
        colander.SchemaNode(
            colander.Set(),
            name='organisation',
            title="Vad beskriver bäst din organisation? Du kan välja flera.",
            widget=deform.widget.CheckboxChoiceWidget(values=_organisation_values),
        )
    )
    schema.add(
        colander.SchemaNode(
            colander.String(),
            name="free_text_org",
            title = "Om inget ovan passar kan du skriva organisation här",
            missing="",
        )
    )
    schema.add(
        colander.SchemaNode(
            colander.String(),
            name='work_role',
            title = "Vad har du för arbetsroll?",
            missing="",
        )
    )


def hashtag_text_validator(node, value):
    # Validation against one word per row, unicode chars okay but nothing else
    # Essentialy a valid hashtag without the #.
    pattern = re.compile('^[\w-]+$', re.UNICODE)
    for i, line in enumerate(value.splitlines()):
        if not pattern.match(line):
            raise colander.Invalid(node, 'Felaktig hashtag på rad {}'.format(i+1))


class EffectSettingsSchema(colander.Schema):
    effect_active = colander.SchemaNode(
        colander.Bool(),
        title="Aktivera knapp för effekter",
    )
    effect_actors = colander.SchemaNode(
        colander.String(),
        title="Aktörer",
        description="Skrivs som sammansatta ord, utan # eller andra specialtecken. En per rad.",
        widget=deform.widget.TextAreaWidget(rows=5),
        validator=hashtag_text_validator,
        missing="",
    )


@colander.deferred
def effect_actors_widget(node, kw):
    request = kw['request']
    settings = IEffectSettings(request.meeting)
    values = [(x, x) for x in settings.get('effect_actors', ())]
    return deform.widget.CheckboxChoiceWidget(
        values=values
    )


class EditEffectsSchema(colander.Schema):
    widget = deform.widget.FormWidget(template='voteit_form_inline')
    effect_time = colander.SchemaNode(
        colander.String(),
        title="Genomförandetid",
        widget=deform.widget.SelectWidget(values=(
            ("", "- Ingen vald -"),
            ("Kort", "Kort"),
            ("Medel", "Medel"),
            ("Lång", "Lång"),
        )),
        missing="",
    )
    effect_actors = colander.SchemaNode(
        colander.List(),
        title="Aktör(er)",
        description="Välj max 2 st. Om det är fler involverade kan det vara bra att "
                    "formulera förslag mer precist för de olika aktörerna.",
        widget=effect_actors_widget,
        validator=colander.Length(max=2),
        missing=()
    )


def includeme(config):
    config.add_subscriber(inject_profile_extras, [UserSchema, ISchemaCreatedEvent])
    config.add_subscriber(inject_profile_extras, [FinishRegistrationSchema, ISchemaCreatedEvent])
    config.add_schema('Meeting', EffectSettingsSchema, 'effect_settings')
    config.add_schema('Proposal', EditEffectsSchema, 'edit_effects')
