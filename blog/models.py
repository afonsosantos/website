from django.core.paginator import Paginator
from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from base.blocks import BodyStreamBlock


@register_snippet
class BlogCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
    ]

    class Meta:
        verbose_name = "Blog category"
        verbose_name_plural = "Blog categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "blog.BlogPage", on_delete=models.CASCADE, related_name="tagged_items"
    )


class BlogIndexPage(Page):
    intro = models.TextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["blog.BlogPage"]

    class Meta:
        verbose_name = "Blog index page"

    def get_posts(self):
        return BlogPage.objects.child_of(self).live().order_by("-date")

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        posts = self.get_posts()

        tag = request.GET.get("tag")
        if tag:
            posts = posts.filter(tags__slug=tag)

        category_slug = request.GET.get("category")
        if category_slug:
            posts = posts.filter(categories__slug=category_slug)

        paginator = Paginator(posts, 10)
        page_number = request.GET.get("page")
        context["posts"] = paginator.get_page(page_number)
        context["current_tag"] = tag
        context["current_category"] = category_slug
        # Only categories actually used by a live post under this index -
        # an empty category isn't a useful filter.
        context["all_categories"] = BlogCategory.objects.filter(
            blogpage__in=self.get_posts()
        ).distinct()
        return context


class BlogPage(Page):
    date = models.DateField(
        "Post date", help_text="Displayed publication date; can be backdated."
    )
    intro = models.CharField(max_length=255)
    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    body = StreamField(BodyStreamBlock, blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    categories = ParentalManyToManyField("blog.BlogCategory", blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("intro"),
        FieldPanel("cover_image"),
        FieldPanel("body"),
        FieldPanel("tags"),
        FieldPanel("categories"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
        index.FilterField("date"),
    ]

    parent_page_types = ["blog.BlogIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Blog page"
        ordering = ["-date"]
