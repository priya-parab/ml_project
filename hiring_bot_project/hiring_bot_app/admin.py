from django.contrib import admin

# Register your models here.
from .models.candidate import CustomUser

admin.site.register(CustomUser)