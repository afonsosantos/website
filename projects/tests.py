import datetime

from django.core.cache import cache
from django.test import TestCase
from wagtail.models import Page, Site

from home.models import HomePage
from projects.models import ProjectIndexPage, ProjectPage


class ProjectIndexTests(TestCase):
    def setUp(self):
        root = Page.objects.get(id=1)
        home = HomePage(title="Home", slug="home-test")
        root.add_child(instance=home)
        Site.objects.filter(is_default_site=True).update(root_page=home)
        cache.clear()

        self.projects_index = ProjectIndexPage(title="Projects", slug="projects")
        home.add_child(instance=self.projects_index)

        self.featured = ProjectPage(
            title="Featured project",
            slug="featured-project",
            summary="summary",
            date=datetime.date(2024, 1, 1),
            featured=True,
        )
        self.projects_index.add_child(instance=self.featured)

        self.regular = ProjectPage(
            title="Regular project",
            slug="regular-project",
            summary="summary",
            date=datetime.date(2025, 1, 1),
            featured=False,
        )
        self.projects_index.add_child(instance=self.regular)

    def test_index_orders_featured_projects_first(self):
        response = self.client.get(self.projects_index.url)
        content = response.content.decode()
        self.assertLess(content.index("Featured project"), content.index("Regular project"))

    def test_project_page_only_creatable_under_project_index(self):
        self.assertEqual(ProjectPage.parent_page_types, ["projects.ProjectIndexPage"])
