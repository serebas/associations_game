from django.urls import path

from .views import *

urlpatterns = [
    path('create-room/', CreateRoomAPIView.as_view(), name='create-room'),
    #http://127.0.0.1:8000/game/create-room/

    path('join-to-room/', ListRoomAPIView.as_view(), name='join-to-room'),
    #http://127.0.0.1:8000/game/join-to-room/

    path('get-word-set/<str:room_name>', ListWordsAPIView.as_view(), name='get-word-set'),
    #http://127.0.0.1:8000/game/get-word-set/<str:room_name>
]
