from akarpov.blog.models import Comment, CommentRating, Post, PostRating
from akarpov.users.models import User


def update_comment_rate(comment: Comment, user: User, vote_up: bool):
    """Creates and updates comments' rating"""
    comment_rate = CommentRating.objects.filter(user=user, comment=comment)

    if comment_rate.exists():
        comment_rate = comment_rate[0]

        if comment_rate.vote_up == vote_up:
            return comment_rate
        elif vote_up:
            comment_rate.comment.rating += 2
        else:
            comment_rate.comment.rating -= 2
        comment_rate.vote_up = vote_up

        comment_rate.comment.save(update_fields=["rating"])
        comment_rate.save(update_fields=["vote_up"])
        return comment_rate
    else:
        comment_rate = CommentRating.objects.create(
            user=user, comment=comment, vote_up=vote_up
        )
        if vote_up:
            comment_rate.comment.rating += 1
        else:
            comment_rate.comment.rating -= 1

        comment_rate.comment.save(update_fields=["rating"])

    return comment_rate


def update_post_rating(post: Post, user: User, rating: int):
    """Creates and updates posts' rating"""
    if old_rate := PostRating.objects.filter(
        post=post,
        user=user,
    ):
        old_rate = old_rate[0]
        if old_rate.rating != rating:

            rating_ex = post.rating_exactly - old_rate.rating + rating
            post.rating_exactly = rating_ex
            post.rating = round(rating_ex / post.rating_count, 2)
            old_rate.rating = rating

            post.save(update_fields=["rating_count", "rating_exactly", "rating"])
            old_rate.save(update_fields=["rating"])
        return old_rate
    else:
        rating_ex = post.rating_exactly + rating
        post.rating_exactly = rating_ex
        post.rating = round(rating_ex / (post.rating_count + 1), 2)
        post.rating_count += 1

        post.save(update_fields=["rating_count", "rating_exactly", "rating"])
        return PostRating.objects.create(
            rating=rating,
            post=post,
            user=user,
        )
