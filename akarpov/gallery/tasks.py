from celery import shared_task
from django.contrib.gis.geos import Point

from akarpov.gallery.models import Image
from akarpov.gallery.services import get_image_coordinate, load_image_meta


@shared_task()
def process_gallery_image(pk: int):
    image = Image.objects.get(pk=pk)
    data = load_image_meta(image.image.path)
    image.extra_data = data
    coordinates = get_image_coordinate(image.image.path)
    if coordinates and "lon" in coordinates and "lat" in coordinates:
        image.image_location = Point(coordinates["lon"], coordinates["lat"])
    image.save()
