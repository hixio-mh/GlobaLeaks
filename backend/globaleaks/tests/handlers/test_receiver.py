# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers import receiver
from globaleaks.orm import transact
from globaleaks.tests import helpers
from globaleaks.utils.utility import datetime_never


@transact
def set_expiration_of_all_rtips_to_unlimited(session):
    session.query(models.InternalTip).update({'expiration_date': datetime_never()})


class TestTipsCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.TipsCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):
        handler = self.request(user_id=self.dummyReceiver_1['id'], role='receiver')
        ret = yield handler.get()
        for idx in range(len(ret)):
            self.assertEqual(ret[idx]['file_count'], 2)
            self.assertEqual(ret[idx]['comment_count'], 3)
            self.assertEqual(ret[idx]['message_count'], 2)


class TestOperations(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.Operations

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_put_revoke_and_grant(self):
        rtips = yield receiver.get_receivertips(1, self.dummyReceiver_1['id'], helpers.USER_PRV_KEY, 'en')
        rtips_ids = [rtip['id'] for rtip in rtips]

        yield self.test_model_count(models.ReceiverTip, 4)

        data_request = {
            'operation': 'revoke',
            'args': {
              'receiver': self.dummyReceiver_2['id'],
              'rtips': rtips_ids
            }
        }

        handler = self.request(data_request, user_id=self.dummyReceiver_1['id'], role='receiver')
        yield handler.put()

        yield self.test_model_count(models.ReceiverTip, 2)

        data_request = {
            'operation': 'grant',
            'args': {
              'receiver': self.dummyReceiver_2['id'],
              'rtips': rtips_ids
            }
        }

        handler = self.request(data_request, user_id=self.dummyReceiver_1['id'], role='receiver')
        yield handler.put()

        yield self.test_model_count(models.ReceiverTip, 4)

    @inlineCallbacks
    def test_put_postpone(self):
        yield set_expiration_of_all_rtips_to_unlimited()

        rtips = yield receiver.get_receivertips(1, self.dummyReceiver_1['id'], helpers.USER_PRV_KEY, 'en')
        rtips_ids = [rtip['id'] for rtip in rtips]

        postpone_map = {}
        for rtip in rtips:
            postpone_map[rtip['id']] = rtip['expiration_date']

        data_request = {
            'operation': 'postpone',
            'args': {
                'rtips': rtips_ids
            }
        }

        handler = self.request(data_request, user_id=self.dummyReceiver_1['id'], role='receiver')
        yield handler.put()

        rtips = yield receiver.get_receivertips(1, self.dummyReceiver_1['id'], helpers.USER_PRV_KEY, 'en')

        for rtip in rtips:
            self.assertNotEqual(postpone_map[rtip['id']], rtip['expiration_date'])

    @inlineCallbacks
    def test_put_delete(self):
        rtips = yield receiver.get_receivertips(1, self.dummyReceiver_1['id'], helpers.USER_PRV_KEY, 'en')
        rtips_ids = [rtip['id'] for rtip in rtips]

        data_request = {
            'operation': 'delete',
            'args': {
                'rtips': rtips_ids
            }
        }

        handler = self.request(data_request, user_id=self.dummyReceiver_1['id'], role='receiver')
        yield handler.put()

        rtips = yield receiver.get_receivertips(1, self.dummyReceiver_1['id'], helpers.USER_PRV_KEY, 'en')

        self.assertEqual(len(rtips), 0)
