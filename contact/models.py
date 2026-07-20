from django import forms
from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.fields import RichTextField

HONEYPOT_FIELD_NAME = "hp_website"


class ContactFormField(AbstractFormField):
    page = ParentalKey(
        "contact.ContactPage", on_delete=models.CASCADE, related_name="form_fields"
    )


class ContactPage(AbstractEmailForm):
    intro = RichTextField(blank=True, features=["bold", "italic", "link"])
    thank_you_text = RichTextField(blank=True, features=["bold", "italic", "link"])

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel("intro"),
        InlinePanel("form_fields", label="Form fields"),
        FieldPanel("thank_you_text"),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("from_address"),
                        FieldPanel("to_address"),
                    ]
                ),
                FieldPanel("subject"),
            ],
            heading="Email notification",
        ),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    class Meta:
        verbose_name = "Contact page"

    def get_form_class(self):
        # Basic spam trap: a plain text field that's offscreen (not
        # display:none/type=hidden, which bots increasingly detect and skip)
        # and removed from the tab order, so sighted keyboard users and
        # screen reader users never encounter it, but simple bots that fill
        # in every field will.
        form_class = super().get_form_class()
        form_class.base_fields[HONEYPOT_FIELD_NAME] = forms.CharField(
            required=False,
            label="Leave this field blank",
            widget=forms.TextInput(
                attrs={"tabindex": "-1", "autocomplete": "off"}
            ),
        )
        return form_class

    def process_form_submission(self, form):
        if form.cleaned_data.get(HONEYPOT_FIELD_NAME):
            return None
        return super().process_form_submission(form)

    def render_email(self, form):
        del form.cleaned_data[HONEYPOT_FIELD_NAME]
        return super().render_email(form)
