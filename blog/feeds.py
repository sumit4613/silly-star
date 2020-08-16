from django.contrib.syndication.views import Feed
from django.template.defaultfilters import truncatewords
from django.urls import reverse_lazy

from blog.models import Post


class LatestPostsFeed(Feed):
    title = "Silly Star"
    link = reverse_lazy("blog:post_list")
    description = "New Posts of my Blog"

    def items(self):
        return Post.published.all()[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return truncatewords(item.body, 30)
