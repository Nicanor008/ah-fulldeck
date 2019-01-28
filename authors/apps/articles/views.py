from rest_framework.generics import (ListCreateAPIView,
                                     RetrieveUpdateDestroyAPIView,
                                     CreateAPIView,
                                     RetrieveAPIView,
                                     ListAPIView)
from rest_framework.pagination import PageNumberPagination

from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from .permissions import IsOwnerOrReadonly

from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from .models import Article, Comment, LikeDislike, ArticleRatings, Tag, FavoriteArticle
from .serializers import (ArticleSerializers,
                          CommentsSerializers,
                          LikeDislikeSerializer,
                          RatingSerializer,
                          FavoriteArticlesSerializer,
                          TagSerializer)

from .renderers import ArticleJsonRenderer, RatingJSONRenderer
from collections import Counter
from django.db.models import Avg
from rest_framework.views import APIView


def article_not_found():
    raise ValidationError(
        detail={'error': 'No article found for the slug given'})


def get_article(slug):
    try:
        article = Article.objects.get(slug=slug)
        return article
    except Exception:
        article_not_found()


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ListCreateArticle(ListCreateAPIView):
    pagination_class = StandardPagination
    queryset = Article.objects.all()
    renderer_classes = (ArticleJsonRenderer,)
    serializer_class = ArticleSerializers
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request):
        paginator = StandardPagination()
        result_page = paginator.paginate_queryset(self.queryset, request)
        serializer = ArticleSerializers(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        article = request.data.get('article', {})
        serializer = self.serializer_class(
            data=article, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RetrieveUpdateDeleteArticle(RetrieveUpdateDestroyAPIView):
    """
    This class retrieves, updates, and deletes a single article
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializers
    renderer_classes = (ArticleJsonRenderer,)
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadonly)
    lookup_field = 'slug'

    def get(self, request, slug):
        article = get_article(slug)
        if not article:
            article_not_found()
        return super().get(request, slug)

    def update(self, request, slug):
        """
        This method updates an article
        """
        try:
            article = Article.objects.get(slug=slug)
        except Exception:
            article_not_found()
            return Response(status=status.HTTP_404_NOT_FOUND)
        article_data = request.data.get('article', {})
        serializer = self.serializer_class(
            article, data=article_data, partial=True)
        if serializer.is_valid():
            self.check_object_permissions(request, article)
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slug):
        """
        Overide the default django error message after deleting an article
        """
        if not get_article(slug):
            article_not_found()
        super().delete(self, request, slug)
        return Response({"message": "Article Deleted Successfully"})


class CommentView(ListCreateAPIView):
    """
    Class for creating and listing all comments
    """
    queryset = Comment.objects.all()
    serializer_class = CommentsSerializers
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def post(self, request, slug):
        """
        Method for creating article
        """
        article = get_article(slug)

        comment = request.data.get('comment', {})
        comment['author'] = request.user.id
        comment['article'] = article.pk
        serializer = self.serializer_class(data=comment)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, slug):
        """
        Method for getting all comments
        """
        article = get_article(slug)
        comments = article.comments.filter()
        serializer = self.serializer_class(comments.all(), many=True)
        data = {
            'count': comments.count(),
            'comments': serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)


class CommentDetails(RetrieveUpdateDestroyAPIView,
                     ListCreateAPIView):
    """
    Class for retrieving, updating and deleting a comment
    """
    queryset = Comment.objects.all()
    lookup_field = 'id'
    serializer_class = CommentsSerializers
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadonly)

    def get(self, request, slug, id):
        article = get_article(slug)
        try:
            article.comments.filter(id=id).first()
            return super().get(request, id)
        except:
            raise ValidationError(
                detail={'error': 'No comment found for the ID given'})

    def create(self, request, slug, id):
        """Method for creating a child comment on parent comment."""

        article = get_article(slug)
        try:
            parent_comment = article.comments.filter(id=id).first().pk
        except:
            message = {'detail': 'Comment not found.'}
            return Response(message, status=status.HTTP_404_NOT_FOUND)
        body = request.data.get('comment', {})['body']

        data = {
            'body': body,
            'parent': parent_comment,
            'article': article.pk,
            'author': request.user.id
        }

        serializer = self.serializer_class(
            data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, slug, id):
        """
        Method for deleting a comment
        """
        article = get_article(slug)
        comment = article.comments.filter(id=id)
        if not comment:
            message = {'detail': 'Comment not found.'}
            return Response(message, status=status.HTTP_404_NOT_FOUND)
        comment[0].delete()
        message = {'detail': 'Comment Deleted Successfully'}
        return Response(message, status=status.HTTP_200_OK)

    def update(self, request, slug, id):
        """
        Method for editing a comment
        """
        article = get_article(slug)

        comment = article.comments.filter(id=id).first()
        if not comment:
            message = {'detail': 'Comment not found.'}
            return Response(message, status=status.HTTP_404_NOT_FOUND)

        new_comment = request.data.get('comment', {})['body']
        data = {
            'body': new_comment,
            'article': article.pk,
            'author': request.user.id
        }
        serializer = self.serializer_class(comment, data=data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LikeDislikeView(CreateAPIView):
    """
    this class defines the endpoint for like and dislike
    """
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = LikeDislikeSerializer
    model = None  # Data Model - Articles or Comments
    vote_type = None  # Vote type Like/Dislike

    def post(self, request, slug=None, id=None):
        """
        This view enables a user to like or dislike an article or specific
        comment
        """
        # check an article is existing
        if self.model.__name__ is 'Article':
            obj = get_object_or_404(Article, slug=slug)
        else:  # model is comment
            obj = get_object_or_404(Comment, id=id)

        try:
            # if user has ever voted
            like_dislike = LikeDislike.objects.get(
                content_type=ContentType.objects.get_for_model(obj),
                object_id=obj.id,
                user=request.user)
            # check if the user has liked or disliked the article or comment already
            if like_dislike.vote is not self.vote_type:
                like_dislike.vote = self.vote_type
                like_dislike.save(update_fields=['vote'])
                result = True
            else:
                # delete the existing record if the user is submitting a similar vote
                like_dislike.delete()
                result = False
        except LikeDislike.DoesNotExist:
            # user has never voted for the article or comment, create new record.
            obj.votes.create(user=request.user, vote=self.vote_type)
            result = True

        return Response({
            "status": result,
            "likes": obj.votes.likes().count(),
            "dislikes": obj.votes.dislikes().count(),
            "Total": obj.votes.sum_rating()
        },
            content_type="application/json",
            status=status.HTTP_201_CREATED
        )


class RatingView(CreateAPIView, RetrieveUpdateDestroyAPIView):
    serializer_class = RatingSerializer
    renderer_classes = (RatingJSONRenderer,)
    queryset = ArticleRatings.objects.all()
    permission_classes = (IsAuthenticated,)
    lookup_field = 'slug'

    def get_article(self, slug):
        article = get_article(slug=slug)

        return article

    def post(self, request, slug):
        serializer_data = request.data.get('rating', {})
        article = self.get_article(slug)

        if article is not None:
            rating = ArticleRatings.objects.filter(
                article=article, rated_by=request.user).first()
            rating_author = article.author
            rating_user = request.user
            if rating_author == rating_user:
                data = {'errors': 'You cannot rate your own article'}
                return Response(data, status=status.HTTP_403_FORBIDDEN)

            else:
                serializer = self.serializer_class(
                    rating, data=serializer_data, partial=True)
                serializer.is_valid(raise_exception=True)

                serializer.save(rated_by=request.user, article=article)
                data = serializer_data
                data['message'] = "You have rated this article successfully"
                return Response(data, status=status.HTTP_201_CREATED)


class RatingDetails(RetrieveAPIView):
    queryset = ArticleRatings.objects.all()
    serializer_class = RatingSerializer
    renderer_classes = (RatingJSONRenderer,)
    permission_classes = (IsAuthenticated,)
    lookup_field = 'slug'

    def get(self, request, slug):
        article = get_article(slug)

        if article is not None:
            avg_rating = ArticleRatings.objects.filter(article=article).aggregate(
                average_rating=Avg('rating'))['average_rating'] or 0
            avg_rating = round(avg_rating)
            total_user_rates = ArticleRatings.objects.filter(
                article=article).count()
            each_rating = Counter(ArticleRatings.objects.filter(
                article=article).values_list('rating', flat=True))

            return Response({
                'avg_rating': avg_rating,
                'total_user_rates': total_user_rates,
                'each_rating': each_rating
            }, status=status.HTTP_200_OK)


class TagsView(ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        data = self.get_queryset()
        serializer = self.serializer_class(data, many=True)
        return Response({'tags': serializer.data}, status=status.HTTP_200_OK)


class FavouriteArticleView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = FavoriteArticlesSerializer

    def put(self, request, slug):
        article = get_article(slug)

        # check if article has been favorited
        favorite_article = FavoriteArticle.objects.filter(
            user=request.user.id, article=article.id).exists()

        # if article is already a favorite, remove from favorites
        if favorite_article:
            instance = FavoriteArticle.objects.filter(
                user=request.user.id, article=article.id)

            self.perform_destroy(instance)
            return Response({'message': 'Article unfavorited'},
                            status.HTTP_200_OK)

        # if article is not a favorite, then make it favorite
        data = {"article": article.id, "user": request.user.id}
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': 'Article favorited'},
                        status.HTTP_200_OK)


class GetUserFavorites(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = FavoriteArticlesSerializer
    queryset = FavoriteArticle.objects.all()

    def get(self, request):
        fav_article = FavoriteArticle.objects.filter(user=request.user.id)
        if fav_article:
            serializer = FavoriteArticlesSerializer(fav_article, many=True)
            return Response(serializer.data, status.HTTP_200_OK)
        else:
            return Response({'message': 'No favorites available'}, status=status.HTTP_404_NOT_FOUND)
