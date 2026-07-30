from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from .views import CoverGeneratorView


@hooks.register("register_admin_urls")
def register_cover_generator_url():
    return [
        path(
            "cover-generator/",
            CoverGeneratorView.as_view(),
            name="cover_generator",
        ),
    ]


@hooks.register("register_admin_menu_item")
def register_cover_generator_menu_item():
    return MenuItem(
        _("Cover generator"),
        reverse("cover_generator"),
        icon_name="image",
        order=10000,
    )
