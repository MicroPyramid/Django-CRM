from django.db import models
from modelcluster.models import ClusterableModel
from wagtail.blocks import CharBlock, ListBlock, RichTextBlock, TextBlock
from wagtail import blocks
from wagtail.blocks import StructBlock
from wagtail.models import Orderable
from wagtail.fields import RichTextField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.models import register_snippet


class RightImageLeftText(blocks.StructBlock):
    heading = blocks.CharBlock(required=False)
    paragraph = blocks.RichTextBlock(required=False)
    image = ImageChooserBlock()
    links = blocks.ListBlock(
        blocks.StructBlock(
            [
                ("cta_url", blocks.URLBlock(required=False)),
                ("cta_page", blocks.PageChooserBlock(required=False)),
                (
                    "cta_text",
                    blocks.CharBlock(required=False, default="Submit", max_length="50"),
                ),
                ("cta_image", ImageChooserBlock(required=False)),
            ]
        )
    )

    class Meta:
        template = "cms/streams/right_image_left_content.html"
        icon = "image"
        label = "Right Image Left Content"


class AboutApp(blocks.StructBlock):
    heading = blocks.CharBlock(required=False)
    paragraph = blocks.RichTextBlock(required=False)
    image = ImageChooserBlock()
    sub_heading = blocks.CharBlock(required=False)
    sub_paragraph = blocks.RichTextBlock(required=False)
    cta_url = blocks.URLBlock(required=False)
    cta_page = blocks.PageChooserBlock(required=False)
    cta_text = blocks.CharBlock(required=False, default="Submit", max_length="50")
    links = blocks.ListBlock(
        blocks.StructBlock(
            [
                ("text", blocks.CharBlock(required=False)),
            ]
        )
    )

    class Meta:
        template = "cms/streams/aboutapp.html"
        icon = "image"
        label = "About App"


class Count(blocks.StructBlock):
    links = blocks.ListBlock(
        blocks.StructBlock(
            [
                ("count", blocks.CharBlock(required=False, default=85)),
                ("count_value", blocks.CharBlock(required=False)),
                ("text", blocks.CharBlock(required=False)),
            ]
        )
    )

    class Meta:
        template = "cms/streams/count.html"
        icon = "image"
        label = "Count"


class AppFeatures(blocks.StructBlock):
    heading = blocks.CharBlock(required=False)
    description = blocks.RichTextBlock(required=False)
    cards = blocks.ListBlock(
        blocks.StructBlock(
            [
                ("icon", blocks.CharBlock(required=False)),
                ("card_heading", blocks.CharBlock(required=False)),
                ("card_description", blocks.CharBlock(required=False)),
            ]
        )
    )

    class Meta:
        template = "cms/streams/app_features.html"
        icon = "image"
        label = "App Features"


class Pricing(blocks.StructBlock):
    heading = blocks.CharBlock(required=False)
    description = blocks.RichTextBlock(required=False)
    cards = blocks.ListBlock(
        blocks.StructBlock(
            [
                ("card_heading", blocks.CharBlock(required=False)),
                ("card_price", blocks.CharBlock(required=False)),
                ("card_description", blocks.RichTextBlock(required=False)),
                ("cta_url", blocks.URLBlock(required=False)),
                ("cta_page", blocks.PageChooserBlock(required=False)),
                (
                    "cta_text",
                    blocks.CharBlock(
                        required=False, default="Choose Plan", max_length="50"
                    ),
                ),
            ]
        )
    )

    class Meta:
        template = "cms/streams/pricing.html"
        icon = "image"
        label = "Pricing"


class Carousel(blocks.StructBlock):
    sliders = blocks.ListBlock(
        blocks.StructBlock(
            [
                ("description", blocks.RichTextBlock(required=False)),
                ("image", ImageChooserBlock()),
                ("author", blocks.CharBlock(required=False)),
                ("role", blocks.CharBlock(required=False)),
            ]
        )
    )

    class Meta:
        template = "cms/streams/carousel.html"
        icon = "image"
        label = "Carousel"


class LeftImageRightText(blocks.StructBlock):
    heading = blocks.CharBlock(required=False)
    paragraph = blocks.RichTextBlock(required=False)
    image = ImageChooserBlock()
    links = blocks.ListBlock(
        blocks.StructBlock(
            [
                ("cta_url", blocks.URLBlock(required=False)),
                ("cta_page", blocks.PageChooserBlock(required=False)),
                (
                    "cta_text",
                    blocks.CharBlock(required=False, default="Submit", max_length="50"),
                ),
                ("cta_image", ImageChooserBlock(required=False)),
            ]
        )
    )

    class Meta:
        template = "cms/streams/left_image_right_content.html"
        icon = "image"
        label = "Left Image Right Content"


class HomeBlog(blocks.StructBlock):
    heading = blocks.CharBlock(required=False)
    description = blocks.RichTextBlock(required=False)
    cards = blocks.ListBlock(
        blocks.StructBlock(
            [
                ("image", ImageChooserBlock()),
                ("blog_tag", blocks.CharBlock(required=False)),
                ("blog_heading", blocks.CharBlock(required=False)),
                ("cta_url", blocks.URLBlock(required=False)),
                ("cta_page", blocks.PageChooserBlock(required=False)),
                (
                    "cta_text",
                    blocks.CharBlock(
                        required=False, default="Read More", max_length="50"
                    ),
                ),
            ]
        )
    )

    class Meta:
        template = "cms/streams/home_blog.html"
        icon = "image"
        label = "Home Blog"


class BlogContentTitleBlock(CharBlock):
    title = CharBlock(required=True, help_text="add your title")

    class Meta:
        template = "cms/streams/blog/content_title.html"
        label = "Content Title"


class BlogCodeBlock(TextBlock):
    code = CharBlock(required=True, help_text="add your title")

    class Meta:
        template = "cms/streams/blog/code_block.html"
        label = "Code Block"


class BlogRichTextBlock(RichTextBlock):
    text = CharBlock(required=True, help_text="add your title")

    class Meta:
        template = "cms/streams/blog/rich_text.html"
        label = "Rich Text"


class BlogImageBlock(ImageChooserBlock):
    image = ImageChooserBlock(required=True, help_text="add your title")

    class Meta:
        template = "cms/streams/blog/image.html"
        label = "Image"
