from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index


class AboutPage(Page):
    intro = RichTextField(blank=True, features=["bold", "italic", "link"])
    profile_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    resume_pdf = models.ForeignKey(
        "wagtaildocs.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Resume (PDF)",
        help_text="Upload a downloadable PDF version of your resume.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("profile_image"),
        FieldPanel("resume_pdf"),
        InlinePanel("work_experiences", label="Work experience"),
        InlinePanel("education_entries", label="Education"),
        InlinePanel("skills", label="Skills"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    class Meta:
        verbose_name = "About page"

    def get_grouped_skills(self):
        skills = self.skills.all()
        groups = {}
        for skill in skills:
            groups.setdefault(skill.category, []).append(skill)
        return groups


class WorkExperience(Orderable):
    page = ParentalKey(AboutPage, on_delete=models.CASCADE, related_name="work_experiences")
    job_title = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    organization_url = models.URLField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(
        null=True, blank=True, help_text="Leave blank if this is your current role."
    )
    description = RichTextField(
        blank=True, features=["bold", "italic", "ul", "ol", "link"]
    )
    logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        FieldPanel("job_title"),
        FieldPanel("organization"),
        FieldPanel("organization_url"),
        FieldPanel("location"),
        MultiFieldPanel(
            [FieldPanel("start_date"), FieldPanel("end_date")],
            heading="Dates",
        ),
        FieldPanel("description"),
        FieldPanel("logo"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Work experience"
        verbose_name_plural = "Work experience"

    def __str__(self):
        return f"{self.job_title} at {self.organization}"


class EducationEntry(Orderable):
    page = ParentalKey(AboutPage, on_delete=models.CASCADE, related_name="education_entries")
    qualification = models.CharField(max_length=255)
    institution = models.CharField(max_length=255)
    institution_url = models.URLField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = RichTextField(
        blank=True, features=["bold", "italic", "ul", "ol", "link"]
    )

    panels = [
        FieldPanel("qualification"),
        FieldPanel("institution"),
        FieldPanel("institution_url"),
        MultiFieldPanel(
            [FieldPanel("start_date"), FieldPanel("end_date")],
            heading="Dates",
        ),
        FieldPanel("description"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Education entry"
        verbose_name_plural = "Education entries"

    def __str__(self):
        return f"{self.qualification}, {self.institution}"


class Skill(Orderable):
    CATEGORY_CHOICES = [
        ("languages", "Languages"),
        ("frameworks", "Frameworks & libraries"),
        ("tools", "Tools & platforms"),
        ("other", "Other"),
    ]

    page = ParentalKey(AboutPage, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="other"
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("category"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Skill"
        verbose_name_plural = "Skills"

    def __str__(self):
        return self.name

    def get_category_display_name(self):
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category)
