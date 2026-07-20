import datetime

from django.core.cache import cache
from django.test import TestCase
from wagtail.models import Page, Site

from blog.models import BlogCategory, BlogIndexPage, BlogPage
from home.models import HomePage


class BlogFilteringTests(TestCase):
    def setUp(self):
        root = Page.objects.get(id=1)
        home = HomePage(title="Home", slug="home-test")
        root.add_child(instance=home)
        Site.objects.filter(is_default_site=True).update(root_page=home)
        cache.clear()

        self.blog_index = BlogIndexPage(title="Blog", slug="blog")
        home.add_child(instance=self.blog_index)

        self.django_category = BlogCategory.objects.create(name="Django", slug="django")
        self.other_category = BlogCategory.objects.create(name="Other", slug="other")

        self.django_post = BlogPage(
            title="A Django post", slug="a-django-post", date=datetime.date.today(), intro="intro"
        )
        self.blog_index.add_child(instance=self.django_post)
        self.django_post.categories.add(self.django_category)
        self.django_post.tags.add("python")
        self.django_post.save()

        self.other_post = BlogPage(
            title="An other post", slug="an-other-post", date=datetime.date.today(), intro="intro"
        )
        self.blog_index.add_child(instance=self.other_post)
        self.other_post.categories.add(self.other_category)
        self.other_post.save()

    def test_index_lists_all_live_posts_by_default(self):
        response = self.client.get(self.blog_index.url)
        self.assertContains(response, "A Django post")
        self.assertContains(response, "An other post")

    def test_category_filter_narrows_results(self):
        response = self.client.get(self.blog_index.url, {"category": "django"})
        self.assertContains(response, "A Django post")
        self.assertNotContains(response, "An other post")

    def test_tag_filter_narrows_results(self):
        response = self.client.get(self.blog_index.url, {"tag": "python"})
        self.assertContains(response, "A Django post")
        self.assertNotContains(response, "An other post")
