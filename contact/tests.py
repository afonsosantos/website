from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from wagtail.models import Page, Site

from contact.models import ContactFormField, ContactPage
from home.models import HomePage


class ContactPageSubmissionTests(TestCase):
    def setUp(self):
        root = Page.objects.get(id=1)
        self.home = HomePage(title="Home", slug="home-test")
        root.add_child(instance=self.home)
        Site.objects.filter(is_default_site=True).update(root_page=self.home)
        cache.clear()

        self.contact_page = ContactPage(
            title="Contact",
            slug="contact",
            to_address="owner@example.com",
            from_address="webmaster@example.com",
            subject="New contact form submission",
        )
        self.home.add_child(instance=self.contact_page)
        self.contact_page.form_fields.add(
            ContactFormField(label="Name", field_type="singleline", required=True, sort_order=0),
            ContactFormField(label="Email", field_type="email", required=True, sort_order=1),
            ContactFormField(label="Message", field_type="multiline", required=True, sort_order=2),
        )
        self.contact_page.save()

    def test_valid_submission_creates_record_and_sends_email(self):
        response = self.client.post(
            self.contact_page.url,
            {
                "name": "Test Visitor",
                "email": "visitor@example.com",
                "message": "Hello there.",
                "hp_website": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.contact_page.get_submission_class().objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["owner@example.com"])
        self.assertIn("Test Visitor", mail.outbox[0].body)
        self.assertNotIn("Leave this field blank", mail.outbox[0].body)

    def test_honeypot_filled_silently_drops_submission(self):
        response = self.client.post(
            self.contact_page.url,
            {
                "name": "Bot",
                "email": "bot@example.com",
                "message": "Spam.",
                "hp_website": "http://spam.example.com",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.contact_page.get_submission_class().objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
