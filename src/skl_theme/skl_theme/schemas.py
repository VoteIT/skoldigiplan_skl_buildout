# -*- coding: utf-8 -*-
import csv
import os

import colander
import deform
from arche.interfaces import ISchemaCreatedEvent
from arche.schemas import UserSchema
from arche.schemas import FinishRegistrationSchema


kommuner_cached = {}

_HERE = os.path.abspath(os.path.dirname(__file__))


def get_kommun_values():
    if not kommuner_cached:
        with open(os.path.join(_HERE, 'data/kommuner.csv')) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                try:
                    kom_id = int(row[0])
                except:
                    continue
                kommuner_cached[kom_id] = row[1]
    values = sorted(kommuner_cached.items(), key=lambda x: x[1].lower())
    values.insert(0, ("", "- Välj eller sök -"))
    return values


def inject_profile_extras(schema, event):
    schema.add(
        colander.SchemaNode(
            colander.Int(),
            name='kommun',
            title = "Vilken kommun är du verksam i?",
            widget=deform.widget.Select2Widget(values=get_kommun_values()),
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


def includeme(config):
    config.add_subscriber(inject_profile_extras, [UserSchema, ISchemaCreatedEvent])
    config.add_subscriber(inject_profile_extras, [FinishRegistrationSchema, ISchemaCreatedEvent])
