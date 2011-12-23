# -*- coding:utf-8 -*-
from AccessControl import Unauthorized

from five import grok

from zope.interface import Interface
from zope.site.hooks import getSite

from plone.uuid.interfaces import IUUID

from zope.annotation.interfaces import IAnnotations

from Products.CMFCore.utils import getToolByName

from collective.polls.config import COOKIE_KEY
from collective.polls.config import MEMBERS_ANNO_KEY


class IPolls(Interface):
    ''' '''

    def recent_polls(show_all=False, limit=5, kw={}):
        ''' Return recent polls'''
        pass

    def recent_polls_in_context(context, show_all=False, limit=5, kw={}):
        ''' Return recent polls in a given context '''
        pass

    def uid_for_poll(poll):
        ''' Return a uid for a poll '''
        pass

    def poll_by_uid(uid):
        ''' Return the poll for the given uid '''
        pass

    def voters_in_a_poll(poll):
        ''' list of voters in a poll '''
        pass

    def voted_in_a_poll(poll):
        ''' check if current user already voted '''
        pass

    def allowed_to_vote(poll):
        ''' vote in a poll '''
        pass

class Polls(grok.GlobalUtility):
    ''' Utility methods for dealing with polls '''

    grok.implements(IPolls)
    grok.provides(IPolls)
    grok.name('collective.polls')

    @property
    def ct(self):
        return getToolByName(getSite(), 'portal_catalog')

    @property
    def mt(self):
        return getToolByName(getSite(), 'portal_membership')

    @property
    def wt(self):
        return getToolByName(getSite(), 'portal_workflow')

    @property
    def member(self):
        return self.mt.getAuthenticatedMember()

    def _query_for_polls(self, **kw):
        ''' Use Portal Catalog to return a list of polls '''
        kw['portal_type'] = 'collective.polls.poll'
        results = self.ct.searchResults(**kw)
        return results

    def uid_for_poll(self, poll):
        ''' Return a uid for a poll '''
        return IUUID(poll)

    def recent_polls(self, show_all=False, limit=5, **kw):
        ''' Return recent polls in a given context '''
        kw['sort_on'] = 'created'
        kw['sort_order'] = 'reverse'
        kw['sort_limit'] = limit
        if not show_all:
            kw['review_state'] = 'open'
        results = self._query_for_polls(**kw)
        return results[:limit]

    def recent_polls_in_context(self, context, show_all=False, limit=5, **kw):
        ''' Return recent polls in a given context '''
        context_path = '/'.join(context.getPhysicalPath())
        kw['path'] = context_path
        results = self.recent_polls(show_all, limit, **kw)
        return results

    def poll_by_uid(self, uid):
        ''' Return the poll for the given uid '''
        if uid == 'latest':
            results = self.recent_polls(show_all=False, limit=1)
        else:
            kw = {'UID': uid}
            results = self._query_for_polls(**kw)
        if results:
            poll = results[0].getObject()
            return poll

    def voted_in_a_poll(self, poll, request=None):
        ''' check if current user already voted '''
        anonymous_allowed = poll.allow_anonymous
        member = self.member
        member_id = member.getId()
        if member_id:
            voters = poll.voters()
            return member_id in voters
        elif anonymous_allowed and request:
            poll_uid = request.cookies.get(COOKIE_KEY)
            return poll_uid and (self.uid_for_poll(poll) == poll_uid)
        else:
            # If we cannot be sure, we will block this user from voting again
            return True

    def allowed_to_vote(self, poll, request=None):
        ''' is current user allowed to vote in this poll ?'''
        review_state = self.wt.getInfoFor(poll, 'review_state')
        canView = self.mt.checkPermission('View', poll)
        if (canView and (review_state in ['open',])):
            # User must view the poll
            # and poll must be open to allow votes
            if not self.voted_in_a_poll(poll, request):
                # If user did not vote here, we allow him to vote
                return True
        # All other cases shall not pass
        raise Unauthorized
