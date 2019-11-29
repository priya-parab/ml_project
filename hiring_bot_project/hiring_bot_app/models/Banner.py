from django.db import models


class Banners(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    banner_title = models.CharField(max_length=50, blank=True, null=True)
    banner_path = models.ImageField(max_length=255,upload_to='pictures', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ('name',)