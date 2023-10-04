from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import AutoSlugField
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import (
    FieldPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
)
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail import blocks
from wagtail.fields import StreamField
from wagtail.models import Orderable, Page
from wagtail.fields import RichTextField
# from wagtail.images. import ImageChooserPanel
from wagtail.snippets.models import register_snippet

from cms import blocks


class HomePage(Page):

    content = StreamField(
        [
            ("right_image_left_content", blocks.RightImageLeftText()),
            ("aboutapp", blocks.AboutApp()),
            ("count", blocks.Count()),
            ("appfeatures", blocks.AppFeatures()),
            ("pricing", blocks.Pricing()),
            ("carousel", blocks.Carousel()),
            ("leftimagerighttext", blocks.LeftImageRightText()),
            ("homeblog", blocks.HomeBlog()),
        ],
        null=True,
        blank=False,
        use_json_field=True,
    )

    content_panels = Page.content_panels + [FieldPanel("content")]


# class BlogCategory(models.Model):
#     name = models.CharField(max_length=255)
#     slug = models.SlugField(max_length=255)

#     def __str__(self):
#         return self.name

#     panels = [FieldPanel("name"), FieldPanel("slug")]

#     class Meta:
#         ordering = ["name"]

# register_snippet(BlogCategory)


class BlogListPage(RoutablePageMixin, Page):

    template = "cms/blog/blog_list_page.html"
    max_count = 1
    intro = RichTextField(blank=True)

    @route(r"^(?P<page_num>\d+)")
    def get_context(self, request, *args, **kwargs):
        # Update context to include only published posts, ordered by reverse-chron
        # request.session.clear()
        context = super().get_context(request, *args, **kwargs)

        all_posts = (
            BlogDetailPage.objects.live().public().order_by("-first_published_at")
        )

        paginator = Paginator(all_posts, 1)

        page = int(kwargs.get("page_num", 1))

        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)
        # context["category_count"] = BlogCategory.objects.annotate(
        #     num_posts=Count("blogdetailpage")
        # )
        context["posts"] = posts
        # context["categories"] = BlogCategory.objects.all()
        if kwargs.get("page_num"):
            return render(request, "cms/blog/blog_list_page.html", context)
        else:
            return context

    # @route(r"^category/(?P<cat_slug>[-\w]*)/$", name="category_view")
    # def category_view(self, request, cat_slug):
    #     context = self.get_context(request)
    #     category = BlogCategory.objects.get(slug=cat_slug)
    #     category_posts = (
    #         BlogDetailPage.objects.live().public().filter(category=category)
    #     )

    #     paginator = Paginator(category_posts, 10)

    #     # page = int(kwargs.get('page_num', 1))
    #     page = 1

    #     try:
    #         category_posts = paginator.page(page)
    #     except PageNotAnInteger:
    #         category_posts = paginator.page(1)
    #     except EmptyPage:
    #         category_posts = paginator.page(paginator.num_pages)

    #     context["category_posts"] = category_posts
    #     context["current_category"] = category
    #     return render(request, "blog/blog_category.html", context)

    # content_panels = Page.content_panels + [
    #     FieldPanel("intro", classname="full"),
    # ]


class BlogDetailPage(Page):
    template = "cms/blog/blog_detail_page.html"
    excerpt = RichTextField()
    # show_legend = models.BooleanField(default=False)
    # category = models.ForeignKey(BlogCategory, null=True, on_delete=models.SET_NULL)

    content = StreamField(
        [
            ("content_title", blocks.BlogContentTitleBlock()),
            ("code", blocks.BlogCodeBlock()),
            ("rich_text", blocks.BlogRichTextBlock()),
            ("image", blocks.BlogImageBlock()),
        ],
        null=True,
        blank=False,
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        # FieldPanel("category"),
        # FieldPanel("show_legend"),
        FieldPanel("excerpt"),
        FieldPanel("content"),
    ]


# ============================  Navigation Menu   ===============================================


@register_snippet
class Menu(ClusterableModel):
    """The main menu clusterable model."""

    title = models.CharField(_("link_title"), max_length=100)
    slug = AutoSlugField(populate_from="title", editable=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("title"),
                FieldPanel("slug"),
            ],
            heading="Menu",
        ),
        InlinePanel("menu_items", label="Menu Item"),
    ]

    def __str__(self):
        return self.title


class MenuItem(Orderable, ClusterableModel):
    """The First level menu of the Navigationbar."""

    link_title = models.CharField(_("link_title"), blank=True, null=True, max_length=50)
    link_url = models.CharField(max_length=500, blank=True)
    link_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.CASCADE,
    )
    open_in_new_tab = models.BooleanField(default=False, blank=True)

    page = ParentalKey("Menu", related_name="menu_items")

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("link_title"),
                FieldPanel("link_url"),
                PageChooserPanel("link_page"),
                FieldPanel("open_in_new_tab"),
            ],
            heading="MenuItem",
        ),
        InlinePanel("sub_menu_items", label="Sub Menu Item"),
    ]

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        elif self.link_url:
            return self.link_url
        return "#"

    @property
    def title(self):
        if self.link_page and not self.link_title:
            return self.link_page.title
        elif self.link_title:
            return self.link_title
        return "Missing Title"


class SubMenuItem(Orderable):
    """The Second level menu of the Navigationbar."""

    link_title = models.CharField(_("link_title"), blank=True, null=True, max_length=50)
    link_url = models.CharField(max_length=500, blank=True)
    link_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.CASCADE,
    )

    open_in_new_tab = models.BooleanField(default=False, blank=True)

    page = ParentalKey("MenuItem", related_name="sub_menu_items")

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("link_title"),
                FieldPanel("link_url"),
                PageChooserPanel("link_page"),
                FieldPanel("open_in_new_tab"),
            ],
            heading="SubMenuItem",
        ),
    ]

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        elif self.link_url:
            return self.link_url
        return "#"

    @property
    def title(self):
        if self.link_page and not self.link_title:
            return self.link_page.title
        elif self.link_title:
            return self.link_title
        return "Missing Title"


@register_setting
class SiteSettings(BaseSiteSetting):
    """Site settings for our custom website."""

    logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    github = models.URLField(blank=True, null=True, help_text="Github URL")
    twitter = models.URLField(blank=True, null=True, help_text="Twitter URL")
    linkedin = models.URLField(blank=True, null=True, help_text="linkedin URL")
    sitemap = models.URLField(blank=True, null=True, help_text="Sitemap rss.xml")
    panels = [
        MultiFieldPanel(
            [
                FieldPanel("github"),
                FieldPanel("twitter"),
                FieldPanel("linkedin"),
                FieldPanel("sitemap"),
                FieldPanel("logo"),
            ],
            heading="Site Settings",
        )
    ]
