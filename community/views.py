from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Avg, Count
from .models import DestinationReview, TripBlog, ReviewHelpful, BlogLike
from .serializers import ReviewSerializer, TripBlogSerializer


class CommunityPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([AllowAny])
def destination_reviews(request, destination_name):
    reviews = DestinationReview.objects.filter(
        destination_name__iexact=destination_name
    )
    avg = reviews.aggregate(avg=Avg('rating'))['avg']

    paginator = CommunityPagination()
    page = paginator.paginate_queryset(reviews, request)

    if page is not None:
        serializer = ReviewSerializer(page, many=True, context={'request': request})
        paginated_res = paginator.get_paginated_response(serializer.data)
        return Response({
            'success': True,
            'destination': destination_name,
            'total_reviews': reviews.count(),
            'avg_rating': round(avg, 1) if avg else None,
            'count': paginated_res.data['count'],
            'next': paginated_res.data['next'],
            'previous': paginated_res.data['previous'],
            'reviews': paginated_res.data['results']
        })

    serializer = ReviewSerializer(reviews, many=True, context={'request': request})
    return Response({
        'success': True,
        'destination': destination_name,
        'total_reviews': reviews.count(),
        'avg_rating': round(avg, 1) if avg else None,
        'reviews': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_review(request):
    existing = DestinationReview.objects.filter(
        user=request.user,
        destination_name__iexact=request.data.get('destination_name', '')
    ).first()
    if existing:
        serializer = ReviewSerializer(existing, data=request.data, partial=True, context={'request': request})
    else:
        serializer = ReviewSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response({'success': True, 'review': serializer.data}, status=status.HTTP_201_CREATED)
    return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vote_helpful(request, review_id):
    try:
        review = DestinationReview.objects.get(id=review_id)
    except DestinationReview.DoesNotExist:
        return Response({'error': 'Review not found'}, status=404)

    vote, created = ReviewHelpful.objects.get_or_create(user=request.user, review=review)
    if not created:
        vote.delete()
        review.helpful_count = max(0, review.helpful_count - 1)
        review.save()
        return Response({'success': True, 'voted': False, 'helpful_count': review.helpful_count})

    review.helpful_count += 1
    review.save()
    return Response({'success': True, 'voted': True, 'helpful_count': review.helpful_count})


@api_view(['GET'])
@permission_classes([AllowAny])
def blog_list(request):
    blogs = TripBlog.objects.filter(published=True)
    destination = request.GET.get('destination', '')
    if destination:
        blogs = blogs.filter(destination__icontains=destination)

    paginator = CommunityPagination()
    page = paginator.paginate_queryset(blogs, request)

    if page is not None:
        serializer = TripBlogSerializer(page, many=True, context={'request': request})
        paginated_res = paginator.get_paginated_response(serializer.data)
        return Response({
            'success': True,
            'count': paginated_res.data['count'],
            'next': paginated_res.data['next'],
            'previous': paginated_res.data['previous'],
            'blogs': paginated_res.data['results']
        })

    serializer = TripBlogSerializer(blogs, many=True, context={'request': request})
    return Response({'success': True, 'blogs': serializer.data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_blog(request):
    serializer = TripBlogSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        blog = serializer.save(user=request.user)
        return Response({'success': True, 'blog': TripBlogSerializer(blog, context={'request': request}).data}, status=201)
    return Response({'errors': serializer.errors}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def blog_detail(request, blog_id):
    try:
        blog = TripBlog.objects.get(id=blog_id, published=True)
        blog.views += 1
        blog.save(update_fields=['views'])
        return Response({'success': True, 'blog': TripBlogSerializer(blog, context={'request': request}).data})
    except TripBlog.DoesNotExist:
        return Response({'error': 'Blog not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_blog(request, blog_id):
    try:
        blog = TripBlog.objects.get(id=blog_id)
    except TripBlog.DoesNotExist:
        return Response({'error': 'Blog not found'}, status=404)

    like, created = BlogLike.objects.get_or_create(user=request.user, blog=blog)
    if not created:
        like.delete()
        blog.likes = max(0, blog.likes - 1)
        blog.save()
        return Response({'success': True, 'liked': False, 'likes': blog.likes})

    blog.likes += 1
    blog.save()
    return Response({'success': True, 'liked': True, 'likes': blog.likes})


@api_view(['GET'])
@permission_classes([AllowAny])
def trending_destinations(request):
    from recommendations.models import TripRecommendation
    from django.db.models import Count
    trending_qs = (
        TripRecommendation.objects
        .values('destination_name', 'country')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    paginator = CommunityPagination()
    page = paginator.paginate_queryset(trending_qs, request)

    if page is not None:
        paginated_res = paginator.get_paginated_response(list(page))
        return Response({
            'success': True,
            'count': paginated_res.data['count'],
            'next': paginated_res.data['next'],
            'previous': paginated_res.data['previous'],
            'trending': paginated_res.data['results']
        })

    return Response({'success': True, 'trending': list(trending_qs)})

