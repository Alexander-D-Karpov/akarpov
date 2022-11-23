from django.urls import reverse

from akarpov.blog import models
from akarpov.users.models import User


def get_rating_bar(user: User, post):
    try:
        post_r = models.PostRating.objects.get(user=user, post=post)
    except models.PostRating.DoesNotExist:
        post_r = None
    url_up = reverse("blog:rate_post_up", kwargs={"slug": post.slug})
    url_down = reverse("blog:rate_post_down", kwargs={"slug": post.slug})
    if post.rating > 0:
        base = f"""<div class="danger
        col-auto align-self-center"> +{ post.rating }</div> """
    elif post.rating < 0:
        base = f"""<div class="
        col-auto align-self-center"> { post.rating }</div> """
    else:
        base = f"""<div class="gray fw-light
        col-auto align-self-center"> { post.rating }</div> """
    if post_r:
        if post_r.vote_up:
            return (
                f"""<div class="row g-0 col-auto d-flex justify-content-center text-center"><form method="post"
                action="{url_up}" class="col-auto align-self-center"><button
                class="btn border-0 btn-small"><i style="font-size: 1rem;" class="bi
                bi-arrow-up-circle-fill"></i></button></form> """
                + base
                + f"""<form method="post" action="{url_down}" class="col-auto align-self-center">
                <button class="btn border-0 btn-small"><i style="font-size: 1rem;" class="bi bi-arrow-down-circle"></i>
                </button></form></div>"""
            )
        else:
            return (
                f"""<div class="row g-0 col-auto d-flex justify-content-center text-center">
                <form method="post" action="{url_up}" class="col-auto align-self-center"><button
                class="btn border-0 btn-small"><i style="font-size: 1rem;" class="bi
                bi-arrow-up-circle"></i></button></form> """
                + base
                + f"""<form method="post" action="{url_down}" class="col-auto align-self-center">
                <button class="btn border-0 btn-small"><i style="font-size: 1rem;" class="bi bi-arrow-down-circle-fill">
                </i></button></form></div>"""
            )
    else:
        return (
            f"""<div class="row g-0 col-auto d-flex justify-content-center text-center">
            <form method="post" action="{url_up}" class="col-auto align-self-center"><button class="btn
            border-0 btn-small"><i style="font-size: 1rem;" class="bi bi-arrow-up-circle"></i></button></form> """
            + base
            + f"""<form method="post" action="{url_down}" class="col-auto align-self-center"><button class="btn border-0
            btn-small"><i style="font-size: 1rem;" class="bi bi-arrow-down-circle"></i></button></form></div>"""
        )
