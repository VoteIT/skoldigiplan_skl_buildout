# -*- coding: utf-8 -*-
from voteit.core import security as vcsec


EDIT_EFFECT_CATEGORY = "Edit effect category"


def includeme(config):
    aclreg = config.registry.acl
    prop_published = aclreg['Proposal:published']
    prop_published.add(vcsec.ROLE_ADMIN, EDIT_EFFECT_CATEGORY)
    prop_published.add(vcsec.ROLE_MODERATOR, EDIT_EFFECT_CATEGORY)
    prop_published.add(vcsec.ROLE_OWNER, EDIT_EFFECT_CATEGORY)
    # Allow users to edit their proposals within SKL, if the prop is published
    prop_published.add(vcsec.ROLE_OWNER, vcsec.EDIT)
