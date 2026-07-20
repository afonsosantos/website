from django.db import models
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.models import Orderable, Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from base.blocks import BodyStreamBlock


@register_snippet
class Technology(ClusterableModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("icon"),
    ]

    class Meta:
        verbose_name = "Technology"
        verbose_name_plural = "Technologies"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProjectIndexPage(Page):
    intro = models.TextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["projects.ProjectPage"]

    class Meta:
        verbose_name = "Projects index page"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        projects = (
            ProjectPage.objects.child_of(self)
            .live()
            .order_by("-featured", "-date")
        )
        context["projects"] = projects
        return context


class ProjectPage(Page):
    summary = models.CharField(
        max_length=255,
        help_text="A short one-line summary. Also used as the fallback meta description.",
    )
    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    body = StreamField(BodyStreamBlock, blank=True)
    technologies = ParentalManyToManyField("projects.Technology", blank=True)
    repo_url = models.URLField(blank=True, verbose_name="Repository URL")
    live_url = models.URLField(blank=True, verbose_name="Live demo URL")
    date = models.DateField(help_text="Used for ordering and display.")
    featured = models.BooleanField(
        default=False, help_text="Featured projects are highlighted on the home page."
    )

    content_panels = Page.content_panels + [
        FieldPanel("summary"),
        FieldPanel("cover_image"),
        MultiFieldPanel(
            [FieldPanel("repo_url"), FieldPanel("live_url")],
            heading="Links",
        ),
        FieldPanel("technologies"),
        MultiFieldPanel(
            [FieldPanel("date"), FieldPanel("featured")],
            heading="Metadata",
        ),
        FieldPanel("body"),
        InlinePanel("gallery_images", label="Gallery images"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("summary"),
        index.SearchField("body"),
    ]

    parent_page_types = ["projects.ProjectIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Project page"


class ProjectGalleryImage(Orderable):
    page = ParentalKey(ProjectPage, on_delete=models.CASCADE, related_name="gallery_images")
    image = models.ForeignKey(
        "wagtailimages.Image", on_delete=models.CASCADE, related_name="+"
    )
    caption = models.CharField(max_length=255, blank=True)
    alt_text = models.CharField(
        max_length=255,
        help_text="Describe the image for screen reader users.",
    )

    panels = [
        FieldPanel("image"),
        FieldPanel("caption"),
        FieldPanel("alt_text"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Gallery image"
