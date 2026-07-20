from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField


@register_setting
class SiteSettings(BaseSiteSetting):
    footer_text = RichTextField(blank=True, features=["bold", "italic", "link"])
    contact_email = models.EmailField(blank=True)

    github_url = models.URLField(blank=True, verbose_name="GitHub URL")
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn URL")
    mastodon_url = models.URLField(blank=True, verbose_name="Mastodon URL")

    default_og_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Used for social sharing previews on pages that don't set their own image.",
    )

    panels = [
        FieldPanel("footer_text"),
        FieldPanel("contact_email"),
        MultiFieldPanel(
            [
                FieldPanel("github_url"),
                FieldPanel("linkedin_url"),
                FieldPanel("mastodon_url"),
            ],
            heading="Social links",
        ),
        FieldPanel("default_og_image"),
    ]

    class Meta:
        verbose_name = "Site settings"
