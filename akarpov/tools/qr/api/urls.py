from rest_framework.routers import SimpleRouter

from .views import QRViewSet

router = SimpleRouter()
router.register(r"", QRViewSet, basename="")

app_name = "qr"
urlpatterns = router.urls
