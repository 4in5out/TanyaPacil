import json
from django.test import TestCase
from django.urls import reverse

from apps.chat.models import ChatMessage
from apps.resources.models import Resource, ResourceCategory


class TanyaPacilFlowTests(TestCase):
    def setUp(self):
        self.cat = ResourceCategory.objects.create(name='DDP1 Python', icon='🐍')
        self.resource = Resource.objects.create(
            title='DDP1 Recursion Guide',
            category=self.cat,
            resource_type=Resource.TYPE_NOTE,
            summary='Base case and recursive case explanation.',
            extracted_text='Recursion requires a base case to avoid RecursionError in Python.',
        )

    def test_vn_home_page_loads(self):
        resp = self.client.get(reverse('chat:index'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Pak Chill')
        self.assertContains(resp, 'vn-dialogue-dock')

    def test_resources_api_returns_active_resources(self):
        resp = self.client.get(reverse('resources:list_api'))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['resources']), 1)
        self.assertEqual(data['resources'][0]['title'], 'DDP1 Recursion Guide')

    def test_chat_send_history_and_reset(self):
        send_resp = self.client.post(
            reverse('chat:send_api'),
            data=json.dumps({'message': 'How does recursion work in Python?'}),
            content_type='application/json',
        )
        self.assertEqual(send_resp.status_code, 200)
        payload = send_resp.json()
        self.assertIn('reply', payload)
        self.assertTrue(len(payload['citations']) >= 1)
        self.assertEqual(payload['citations'][0]['title'], 'DDP1 Recursion Guide')
        self.assertEqual(ChatMessage.objects.count(), 2)

        hist_resp = self.client.get(reverse('chat:history_api'))
        self.assertEqual(hist_resp.status_code, 200)
        self.assertEqual(len(hist_resp.json()['messages']), 2)

        reset_resp = self.client.post(reverse('chat:reset_api'))
        self.assertEqual(reset_resp.status_code, 200)
        self.assertEqual(reset_resp.json()['status'], 'reset')
