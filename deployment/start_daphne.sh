#!/bin/bash
source /chat_env/bin/activate
cd /code

daphne -b 0.0.0.0 -p 8001 chatProj.asgi:application