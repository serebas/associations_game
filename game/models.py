from django.contrib.auth.models import User
from django.db import models


class Room(models.Model):
    name = models.CharField(max_length=128)#, unique=True)
    size = models.PositiveIntegerField()
    online = models.ManyToManyField(to=User, blank=True, db_table='room_user')
    is_active = models.BooleanField(default=True)

    def get_online_count(self):
        return self.online.count()

    def join(self, user):
        self.online.add(user)
        self.save()

    def leave(self, user):
        self.online.remove(user)
        self.save()

    def __str__(self):
        return f'{self.name} ({self.get_online_count()})'
