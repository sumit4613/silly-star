from django.contrib.postgres.search import (
    SearchVector,
    SearchQuery,
    SearchRank,
    TrigramSimilarity,
)
from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from taggit.models import Tag

from .forms import EmailPostForm, CommentForm, SearchForm
from .models import Post


# First try fbv
def post_list(request, tag_slug=None):
    """
    Post List View
    """
    object_list = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 3)  # 3 posts in each page
    page = request.GET.get("page")
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range deliver last page of results
        posts = paginator.page(paginator.num_pages)
    return render(
        request, "blog/post/list.html", {"page": page, "posts": posts, "tag": tag}
    )


# then go to cbv
class PostListView(ListView):
    """
    Post List View
    """

    queryset = Post.published.all()
    context_object_name = "posts"
    paginate_by = 3
    template_name = "blog/post/list.html"


def post_detail(request, year, month, day, post):
    """
    Post Detail View
    """
    post = get_object_or_404(
        Post,
        slug=post,
        status="published",
        publish__year=year,
        publish__month=month,
        publish__day=day,
    )
    # List of active comments for the following post
    comments = post.comments.filter(active=True)
    new_comment = None
    if request.method == "POST":
        # A comment was posted
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Create a comment object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # Assign the current post to the comment
            new_comment.post = post
            # Save the comment to the database
            new_comment.save()
    else:
        comment_form = CommentForm()
    # List of similar posts
    # retrieve list of IDs for the tags of the current post
    post_tags_ids = post.tags.values_list("id", flat=True)
    # get all posts that contain any these tags, exluding the current post
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    # count aggregation function generated a calculated field that contains number of tags
    similar_posts = similar_posts.annotate(same_tags=Count("tags")).order_by(
        "-same_tags", "-publish"
    )[:4]
    return render(
        request,
        "blog/post/detail.html",
        {
            "post": post,
            "comments": comments,
            "new_comment": new_comment,
            "comment_form": comment_form,
            "similar_posts": similar_posts,
        },
    )


def post_share(request, post_id):
    """
    Share Post through email
    """
    # retrieve id
    post = get_object_or_404(Post, id=post_id, status="published")
    sent = False

    if request.method == "POST":
        # Form was submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Form fields passed validation
            data = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{data['name']} recommends you to read {post.title}"
            message = f"Read the awesome post {post.title} at {post_url}\n\n {data['name']}'s comments: {data['comments']}"
            send_mail(subject, message, "admin@sillystar.com", [data["to"]])

            sent = True
    else:
        form = EmailPostForm()
    return render(
        request, "blog/post/share.html", {"post": post, "form": form, "sent": sent}
    )


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if "query" in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data["query"]
            # search_vector = SearchVector("title", "body")
            search_vector = SearchVector("title", weight="A") + SearchVector(
                "body", weight="B"
            )
            search_query = SearchQuery(query)
            # basic full text search method
            # results = Post.published.annotate(
            #     search=SearchVector("title", "body")
            # ).filter(search=query)
            # Weighting queries/ stemming and ranking results method
            # results = (
            #     Post.published.annotate(
            #         search=search_vector, rank=SearchRank(search_vector, search_query)
            #     )
            #     # .filter(search=search_query)
            #     .filter(rank__gte=0.3)
            #     .order_by("-rank")
            # )
            # trigram similarity method
            # pg_trgm extension is required
            # CREATE EXTENSION pg_trgm;
            results = (
                Post.published.annotate(similarity=TrigramSimilarity("title", query))
                .filter(similarity__gt=0.1)
                .order_by("-similarity")
            )
    return render(
        request,
        "blog/post/search.html",
        {"form": form, "query": query, "results": results},
    )
