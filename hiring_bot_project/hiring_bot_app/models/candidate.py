from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime

class CustomUser(AbstractUser):
    username=models.EmailField(max_length=50, unique=True)
    password = models.CharField(max_length=100)
    is_admin = models.BooleanField(default=True)
    created_date = models.DateField(default=datetime.now)
    email = models.EmailField(max_length=50, unique=True)

    def full_name(self):
        full_name= self.first_name + " " + self.last_name
        return full_name

    class Meta:
        db_table = 'CustomUser'
        ordering = ('-created_date',)