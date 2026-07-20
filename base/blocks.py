from wagtail import blocks
from wagtail.embeds.blocks import EmbedBlock as WagtailEmbedBlock
from wagtail.images.blocks import ImageChooserBlock


class ImageBlock(blocks.StructBlock):
    """An image with mandatory alt text, so content authors can't
    accidentally publish an inaccessible image."""

    image = ImageChooserBlock()
    alt_text = blocks.CharBlock(
        required=True,
        max_length=255,
        help_text="Describe the image for screen reader users. Required.",
    )
    caption = blocks.CharBlock(required=False, max_length=255)

    class Meta:
        icon = "image"
        template = "base/blocks/image_block.html"


class QuoteBlock(blocks.StructBlock):
    quote = blocks.CharBlock(required=True, max_length=255)
    attribution = blocks.CharBlock(required=False, max_length=255)

    class Meta:
        icon = "openquote"
        template = "base/blocks/quote_block.html"


class RichTextBlock(blocks.RichTextBlock):
    class Meta:
        icon = "pilcrow"
        template = "base/blocks/rich_text_block.html"
        # Keep authored heading hierarchy predictable - h1 is owned by the
        # page template, so only allow h2-h4 inside body content.
        features = [
            "h2",
            "h3",
            "h4",
            "bold",
            "italic",
            "ol",
            "ul",
            "link",
            "document-link",
        ]


class HeadingBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True, max_length=255)
    size = blocks.ChoiceBlock(
        choices=[("h2", "H2"), ("h3", "H3"), ("h4", "H4")],
        default="h2",
    )

    class Meta:
        icon = "title"
        template = "base/blocks/heading_block.html"


class EmbedBlock(blocks.StructBlock):
    url = WagtailEmbedBlock(required=True)
    caption = blocks.CharBlock(required=False, max_length=255)

    class Meta:
        icon = "media"
        template = "base/blocks/embed_block.html"


class BodyStreamBlock(blocks.StreamBlock):
    """Reusable freeform body content, shared by blog posts and project
    pages."""

    heading = HeadingBlock()
    paragraph = RichTextBlock()
    image = ImageBlock()
    quote = QuoteBlock()
    embed = EmbedBlock()


class ButtonBlock(blocks.StructBlock):
    text = blocks.CharBlock(required=True, max_length=100)
    page = blocks.PageChooserBlock(required=False)
    external_url = blocks.URLBlock(required=False, label="External URL")

    class Meta:
        icon = "link"

    def clean(self, value):
        result = super().clean(value)
        if not result.get("page") and not result.get("external_url"):
            raise blocks.StructBlockValidationError(
                block_errors={
                    "page": blocks.ValidationError(
                        "Choose a page or provide an external URL."
                    )
                }
            )
        return result


class HeroBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True, max_length=255)
    subheading = blocks.CharBlock(required=False, max_length=255)
    image = ImageChooserBlock(required=False)
    image_alt_text = blocks.CharBlock(
        required=False,
        max_length=255,
        help_text="Describe the image for screen reader users. Leave blank only if the image is purely decorative.",
    )
    button = ButtonBlock(required=False)

    class Meta:
        icon = "home"
        template = "base/blocks/hero_block.html"


class FeaturedProjectsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=False, max_length=255, default="Featured projects")
    count = blocks.IntegerBlock(default=3, min_value=1, max_value=12)

    class Meta:
        icon = "folder-open-inverse"
        template = "base/blocks/featured_projects_block.html"

    def get_context(self, value, parent_context=None):
        from projects.models import ProjectPage

        context = super().get_context(value, parent_context=parent_context)
        context["projects"] = (
            ProjectPage.objects.live()
            .order_by("-featured", "-date")[: value["count"]]
        )
        return context


class LatestPostsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=False, max_length=255, default="Latest posts")
    count = blocks.IntegerBlock(default=3, min_value=1, max_value=12)

    class Meta:
        icon = "doc-full"
        template = "base/blocks/latest_posts_block.html"

    def get_context(self, value, parent_context=None):
        from blog.models import BlogPage

        context = super().get_context(value, parent_context=parent_context)
        context["posts"] = BlogPage.objects.live().order_by("-date")[: value["count"]]
        return context


class CallToActionBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True, max_length=255)
    text = blocks.CharBlock(required=False, max_length=255)
    button = ButtonBlock(required=True)

    class Meta:
        icon = "plus"
        template = "base/blocks/cta_block.html"


class HomeStreamBlock(blocks.StreamBlock):
    hero = HeroBlock()
    featured_projects = FeaturedProjectsBlock()
    latest_posts = LatestPostsBlock()
    call_to_action = CallToActionBlock()
    heading = HeadingBlock()
    paragraph = RichTextBlock()
    image = ImageBlock()
