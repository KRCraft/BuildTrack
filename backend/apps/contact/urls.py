from rest_framework.routers import DefaultRouter
from .views import ContactMessageViewSet, TestimonialViewSet

router = DefaultRouter()
router.register(r'messages', ContactMessageViewSet, basename='contactmessage')
router.register(r'testimonials', TestimonialViewSet, basename='testimonial')

urlpatterns = router.urls
