# -*- coding:utf-8 -*-
from five import grok

from Acquisition import aq_parent

from Products.CMFCore.interfaces import IActionSucceededEvent

from collective.polls.content.poll import IPoll

from collective.polls.config import PERMISSION_VOTE

ALL_ROLES = ['Anonymous', 'Contributor', 'Editor', 'Manager', 'Member',
             'Reader', 'Reviewer', 'Site Administrator']


@grok.subscribe(IPoll, IActionSucceededEvent)
def fix_permissions(poll, event):
    ''' This subscriber will fix permission on poll object if
        allow_anonymous is enabled
    '''
    if event.action in ['open', ]:
        parent = aq_parent(poll)
        parent_view_roles = parent.rolesOfPermission('View')
        parent_view_roles = [r['name'] for r in parent_view_roles
                                       if r['selected']]
        # Poll has been opened
        allow_anonymous = poll.allow_anonymous
        if ('Anonymous' in parent_view_roles) and allow_anonymous:
            poll.manage_permission(PERMISSION_VOTE,
                                   ALL_ROLES,
                                   acquire=0)
