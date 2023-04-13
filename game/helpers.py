from asgiref.sync import async_to_sync
from datetime import datetime

from .storage import redis_db

def check_users_words(room, usernames_list):
    users_sets = [redis_db.lrange(redis_db.hget(f'{room}_users', user), 0, -1) for user in usernames_list]
    return all(len(sets) == len(users_sets[0]) for sets in users_sets)


def send_group_notification(consumer, type, message):
    async_to_sync(consumer.channel_layer.group_send)(
        consumer.room_group_name,
        {
            'type': type,
            'user': consumer.user.username,
            'message': message
        }
    )

def logging(room_name, message):
    redis_db.rpush(f'{room_name}_logs', f'{datetime.now().strftime("%H:%M:%S %d-%m-%Y")} - {message}')



