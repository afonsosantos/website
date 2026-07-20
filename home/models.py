from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from base.blocks import HomeStreamBlock


class HomePage(Page):
    sections = StreamField(HomeStreamBlock, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("sections"),
    ]

    subpage_types = [
        "about.AboutPage",
        "projects.ProjectIndexPage",
        "blog.BlogIndexPage",
        "contact.ContactPage",
    ]
