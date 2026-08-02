import json

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Same escaping Django's own `json_script` filter applies, so the JSON blob
# can't be broken out of by a `</script>` (or similar) sequence in a value.
_JSON_SCRIPT_ESCAPES = str.maketrans(
    {"<": "\\u003c", ">": "\\u003e", "&": "\\u0026"}
)


@register.simple_tag
def person_structured_data(site_settings, site_name, request):
    """Sitewide schema.org Person JSON-LD, so search engines can associate
    this site with the person it belongs to (Knowledge Panel, sameAs
    disambiguation against the linked GitHub/LinkedIn/Mastodon profiles)."""
    if not site_name:
        return ""

    same_as = [
        url
        for url in (
            getattr(site_settings, "github_url", ""),
            getattr(site_settings, "linkedin_url", ""),
            getattr(site_settings, "mastodon_url", ""),
        )
        if url
    ]

    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": site_name,
        "url": request.build_absolute_uri("/"),
    }
    if same_as:
        data["sameAs"] = same_as

    json_str = json.dumps(data).translate(_JSON_SCRIPT_ESCAPES)
    return mark_safe(json_str)
