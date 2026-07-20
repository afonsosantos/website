from django.core.cache import cache
from django.test import TestCase
from wagtail.models import Page, Site

from about.models import AboutPage, Skill
from home.models import HomePage


class AboutPageTests(TestCase):
    def setUp(self):
        root = Page.objects.get(id=1)
        home = HomePage(title="Home", slug="home-test")
        root.add_child(instance=home)
        Site.objects.filter(is_default_site=True).update(root_page=home)
        # Wagtail caches site root paths in the process cache, not the DB
        # transaction, so it survives across TestCase rollbacks unless
        # cleared explicitly.
        cache.clear()

        self.about_page = AboutPage(title="About", slug="about")
        home.add_child(instance=self.about_page)
        self.about_page.skills.add(
            Skill(name="Python", category="languages"),
            Skill(name="Django", category="frameworks"),
            Skill(name="Go", category="languages"),
        )
        self.about_page.save()

    def test_grouped_skills_groups_by_category(self):
        groups = self.about_page.get_grouped_skills()
        self.assertEqual({s.name for s in groups["languages"]}, {"Python", "Go"})
        self.assertEqual({s.name for s in groups["frameworks"]}, {"Django"})

    def test_page_renders(self):
        response = self.client.get(self.about_page.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python")
