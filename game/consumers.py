import json

from datetime import datetime

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from .helpers import check_users_words, send_group_notification, logging
from .models import Room
from .storage import redis_db


class GameConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name = None
        self.room_group_name = None
        self.room = None
        self.user = None  # new

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'room_{self.room_name}'
        self.room = Room.objects.get(name=self.room_name, is_active=True)
        self.user = self.scope['user']

        # if the number of online players is less than room size, then connection is accepted
        if self.room.get_online_count() < self.room.size:
            self.accept()

        redis_db.hset(
            name=f'{self.room_name}_users',
            key=self.user.username,
            value=self.channel_name
        )

        # join the room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name,
        )

        # join to online users of current room
        self.room.online.add(self.user)

        # send list of players to all players
        self.send(json.dumps({
            'type': 'user_list',
            'users': [user.username for user in self.room.online.all()],
        }))

        # send all players message about joining a new player
        group_message = f'{self.user.username} присоединился к игре'
        send_group_notification(
            consumer=self,
            type='user_join',
            message=group_message,
        )
        logging(
            room_name=self.room_name,
            message=group_message
        )


    def disconnect(self, close_code):
        #delete player channel from room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name,
        )

        # send the leave event to the room
        group_message = f'{self.user.username} покинул игру'
        send_group_notification(
            consumer=self,
            type='user_leave',
            message=group_message,
        )
        logging(
            room_name=self.room_name,
            message=group_message
        )

        # send list of players to all players
        self.send(json.dumps({
            'type': 'user_list',
            'users': [user.username for user in self.room.online.all()],
        }))

        #remove user from online list
        self.room.online.remove(self.user)

        #delete word set of current user
        redis_db.delete(self.channel_name)

        #delete username and user channel from room
        redis_db.hdel(f'{self.room_name}_users', self.user.username)

        #deactivate room and flush redis when the last player leave the room
        if self.room.get_online_count() < 1:
            self.room.is_active = False
            self.room.save()
            redis_db.delete(f'{self.room_name}_users')
            redis_db.delete(f'{self.room_name}_logs')



    def receive(self, text_data=None, bytes_data=None):                                          #вместо имен пользователей используются их каналы
        text_data_json = json.loads(text_data)                                                   #распарсим пришедшее сообщение
        me = self.channel_name                                                                   #канал текущего потребителя
        round = text_data_json['round']                                                          #номер текущего раунда
        from_user = redis_db.hget(name=f'{self.room_name}_users', key=text_data_json['user'])    #канал игрока, от которого пришло сообщение
        message = text_data_json['message']                                                      #его сообщение (слово)
        user_set = json.dumps({'from_user': self.user.username, 'message': message})             #набор для записи в бд

        if round == '1':
            redis_db.rpush(me, user_set)                                                         #записываем этот набор на собственное имя, т.к. в 1 раунде игроки пишут свои слова
        else:
            redis_db.rpush(from_user, user_set)                                                  #в последубщих раундах набор записываем на того, на чье имя писали ассоциацию

        group_message = f'{self.user.username} написал свое слово'                               #отправляем уведомление а том что игрок написал свое слово
        send_group_notification(
            consumer=self,
            type='wrote',
            message=group_message,
        )                                                                                        #далее логируем это слово
        logging(
            room_name=self.room_name,
            message=group_message
        )

        usernames_list = [user.username for user in self.room.online.all()]                     #формируем список всех никнеймов в текущей комнате

        if check_users_words(self.room_name, usernames_list):                                   #если в текущем раунде слова написали все

            group_message = f'{self.user.username} завершил {round}-й раунд'                    #тогда уведомляем всех что раунд окончен, и кем
            send_group_notification(
                consumer=self,
                type='end_round',
                message=group_message,
            )                                                                                   #логируем это уведомление
            logging(
                room_name=self.room_name,
                message=group_message
            )

            total_round = self.room.get_online_count()                                         #считаем максимальное количество раундов
            if int(round) != total_round:                                                      #если раунд не последний
                userchannels_list = redis_db.hvals(name=f'{self.room_name}_users')[::-1]       #формируем список всех каналов игроков в комнате
                for i, user_channel in enumerate(userchannels_list):                           #проходимся по каждому каналу
                    user_set = redis_db.lrange(user_channel, 0, -1)                            #извлекаем по каналу набор наборов слов
                    to_channel = userchannels_list[(i + len(user_set)) % total_round]          #определяем кому будет отправлено слово в следующем раунде
                    message = json.loads(user_set[-1])['message']                              #из последнего набора наборов извлекаем слово
                                                                                               #и отправляем его определенному каналу в следующий раунд
                    async_to_sync(self.channel_layer.send)(
                        to_channel,
                        {
                            'type': 'message_to_user',
                            'from_user': usernames_list[i],
                            'message': message
                        }
                    )
            else:                                                                             #если раунд последний, то рассылаем всем итоговый набор слов
                #sending result to each user if round is last
                data = {usernames_list[i]: [json.loads(string) for string in redis_db.lrange(redis_db.hget(f'{self.room_name}_users', usernames_list[i]), 0, -1)] for i in range(total_round)}
                self.send(json.dumps({
                    'set_word': data,
                }))



    def message_to_user(self, event):
        self.send(text_data=json.dumps(event))

    def user_join(self, event):
        self.send(text_data=json.dumps(event))

    def wrote(self, event):
        self.send(text_data=json.dumps(event))

    def end_round(self, event):
        self.send(text_data=json.dumps(event))

    def user_leave(self, event):
        self.send(text_data=json.dumps(event))

    def set_word(self,event):
        self.send(text_data=json.dumps(event))
