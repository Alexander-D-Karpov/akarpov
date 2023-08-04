from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from akarpov.blog.forms import PostForm
from akarpov.blog.models import Comment, Post, PostRating
from akarpov.blog.services import get_main_rating_posts, get_rating_bar


class PostDetailView(DetailView):
    model = Post
    slug_field = "slug"
    slug_url_kwarg = "slug"
    template_name = "blog/post.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            context["rating_bar"] = get_rating_bar(self.request.user, kwargs["object"])
        else:
            context["rating_bar"] = None
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.post_views += 1
        self.object.save(update_fields=["post_views"])
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


post_detail_view = PostDetailView.as_view()


class MainPostListView(ListView):
    model = Post
    template_name = "blog/list.html"

    def get_queryset(self):
        try:
            if (
                self.request.user.is_authenticated
                and not self.request.user.is_superuser
            ):
                posts = get_main_rating_posts() | Post.objects.filter(
                    creator=self.request.user
                )
            else:
                posts = get_main_rating_posts()

            params = self.request.GET
            if "tag" in params:
                posts = posts.filter(tags__name=params["tag"])
            return posts

        except Post.DoesNotExist:
            return Post.objects.none()


main_post_list_view = MainPostListView.as_view()


class PostListView(ListView):
    model = Post
    template_name = "blog/list.html"

    def get_queryset(self):
        try:
            posts = Post.objects.all()
            params = self.request.GET
            if "tag" in params:
                posts = posts.filter(tags__name=params["tag"])
            return posts
        except Post.DoesNotExist:
            return Post.objects.none()


post_list_view = PostListView.as_view()


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm

    def get_object(self):
        post = get_object_or_404(Post, slug=self.kwargs["slug"])
        if post.creator != self.request.user:
            raise PermissionDenied
        return post

    template_name = "blog/form.html"


post_update_view = PostUpdateView.as_view()


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm

    template_name = "blog/form.html"

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


post_create_view = PostCreateView.as_view()


@csrf_exempt
def rate_post_up(request, slug):
    if request.method == "POST":
        if request.user.is_authenticated:
            post = get_object_or_404(Post, slug=slug)
            try:
                post_r = PostRating.objects.get(user=request.user, post=post)
            except PostRating.DoesNotExist:
                post_r = None
            if post_r:
                if post_r.vote_up:
                    post_r.delete()
                else:
                    post_r.vote_up = not post_r.vote_up
                    post_r.save()
            else:
                PostRating.objects.create(user=request.user, post=post, vote_up=True)
    return HttpResponseRedirect(reverse("blog:post", kwargs={"slug": slug}) + "#rating")


@csrf_exempt
def rate_post_down(request, slug):
    if request.method == "POST":
        if request.user.is_authenticated:
            post = get_object_or_404(Post, slug=slug)
            try:
                post_r = PostRating.objects.get(user=request.user, post=post)
            except PostRating.DoesNotExist:
                post_r = None
            if post_r:
                if not post_r.vote_up:
                    post_r.delete()
                else:
                    post_r.vote_up = not post_r.vote_up
                    post_r.save()
            else:
                PostRating.objects.create(user=request.user, post=post, vote_up=False)
    return HttpResponseRedirect(reverse("blog:post", kwargs={"slug": slug}) + "#rating")


def comment(request, slug):
    if request.method == "POST":
        if request.user.is_authenticated:
            post = get_object_or_404(Post, slug=slug)
            if "body" not in request.POST or len(request.POST["body"]) > 100:
                raise ValidationError("incorrect body")
            Comment.objects.create(
                post=post, author=request.user, body=request.POST["body"]
            )

    return HttpResponseRedirect(
        reverse("blog:post", kwargs={"slug": slug}) + "#comments"
    )
