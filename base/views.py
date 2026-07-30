from django.views.generic import TemplateView


class CoverGeneratorView(TemplateView):
    """Admin-only tool for generating on-brand blog/project cover images
    (gradient background + title text, matching the site's own design
    tokens) without needing an external design tool."""

    template_name = "base/admin/cover_generator.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Cover generator"
        context["header_icon"] = "image"
        return context
