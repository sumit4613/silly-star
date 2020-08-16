from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone
from model_utils.models import TimeStampedModel
from django.utils.text import gettext_lazy as _


class PublishedManager(models.Manager):
    """
    Manager to return Published Posts
    """

    def get_queryset(self):
        return super(PublishedManager, self).get_queryset().filter(status="published")


class Post(TimeStampedModel):
    """
    Concrete model for Posts
    """

    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("published", "Published"),
    )
    title = models.CharField(verbose_name=_("Title"), max_length=250)
    slug = models.SlugField(max_length=250, unique_for_date="publish")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blog_posts"
    )
    body = models.TextField(verbose_name=_("Body"))
    publish = models.DateTimeField(verbose_name=_("Published On"), default=timezone.now)
    status = models.CharField(
        verbose_name=_("Status"), max_length=10, choices=STATUS_CHOICES, default="draft"
    )

    objects = models.Manager()
    published = PublishedManager()

    def get_absolute_url(self):
        return reverse(
            "blog:post_detail",
            args=[self.publish.year, self.publish.month, self.publish.day, self.slug],
        )

    class Meta:
        ordering = ("-publish",)

    def __str__(self):
        return self.title
