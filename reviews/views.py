from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.http import JsonResponse
from product.models import Product
from orders.models import OrderItem
import logging
from .models import ProductReview


logger = logging.getLogger(__name__)

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def submit_rating(request):
    product_id = request.POST.get('productId')
    rating = request.POST.get('rating')
    title = request.POST.get('title')
    comment = request.POST.get('comment')
    try:
        product = Product.objects.get(id=product_id)
        existing_review = ProductReview.objects.filter(user=request.user, product=product).first()
        
        if existing_review:
            existing_review.rating = rating
            existing_review.title = title
            existing_review.comment = comment
            existing_review.save()
            message = 'Review updated successfully'
        else:
            is_verified_purchase = OrderItem.objects.filter(
                order__user=request.user,
                product_variant__product=product,
                status='Delivered'
            ).exists()
            ProductReview.objects.create(
                user=request.user,
                product=product,
                rating=rating,
                title=title,
                comment=comment,
                is_verified_purchase=is_verified_purchase
            )
            message = 'Review submitted successfully'

        return JsonResponse({'success': True, 'message': message})
    except Product.DoesNotExist:
        logger.error(f"Product with id {product_id} not found")
        return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
    except Exception as e:
        logger.error(f"Error occurred while submitting review: {e}")
        return JsonResponse({'success': False, 'message': 'An error occurred while submitting the review. Please try again later.'}, status=500)


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def get_user_review(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        review = ProductReview.objects.filter(user=request.user, product=product).first()
        
        if review:
            return JsonResponse({
                'exists': True,
                'rating': review.rating,
                'title': review.title,
                'comment': review.comment
            })
        else:
            return JsonResponse({'exists': False})
    
    except Product.DoesNotExist:
        logger.error(f"Product with id {product_id} not found")
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        logger.error(f"Error occurred while fetching user review: {e}")
        return JsonResponse({'error': 'An error occurred while fetching the review. Please try again later.'}, status=500)

