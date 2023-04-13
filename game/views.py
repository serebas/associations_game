import json

from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.response import Response

from .storage import redis_db
from rest_framework.permissions import IsAuthenticated

from .models import Room

min_players = 1
max_players = 10

class CreateRoomAPIView(APIView):
    permission_classes = [IsAuthenticated,]

    def post(self, request):
        name = request.data['name']
        size = request.data['size']

        if not min_players <= int(size) <= max_players:
            return Response({'detail': f'Максимальное число игроков должно быть в предалах от {min_players} до {max_players} человек'})

        if Room.objects.filter(name=name, is_active=True).count():
            return Response({'detail': 'Комната с таким названием уже существует'})

        Room.objects.create(name=name, size=size)
        return Response({'detail': 'Комната успешно создана'})

class ListRoomAPIView(APIView):
    permission_classes = [IsAuthenticated,]

    def get(self, request):
        rooms = Room.objects.filter(is_active=True).values()

        return Response({'active_rooms': list(rooms)})

class ListWordsAPIView(APIView):
    permission_classes = [IsAuthenticated,]

    def get(self, request, *args, **kwargs):
        room_name = kwargs.get('room_name')
        room = Room.objects.get(name=room_name)
        userlist = [user.username for user in room.online.all()]
        data = {user: [json.loads(string) for string in redis_db.lrange(user, 0, -1)] for user in userlist}

        return Response({'set_words': data})

