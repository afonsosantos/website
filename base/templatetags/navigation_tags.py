from django import template
from wagtail.models import Site

register = template.Library()


@register.inclusion_tag("base/includes/primary_nav.html", takes_context=True)
def primary_nav(context):
    request = context["request"]
    site = Site.find_for_request(request)
    menu_pages = site.root_page.get_children().live().in_menu() if site else []
    return {
        "menu_pages": menu_pages,
        "request": request,
    }
