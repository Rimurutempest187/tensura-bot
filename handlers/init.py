# handlers/__init__.py
from .quiz_handlers import quiz, quiz_button
from .admin_handlers import addadmin, listadmins, deladmin
from .broadcast_handlers import broadcast_cmd, broadcast_users_cmd
from .user_handlers import (
    start, cmd, verse, prayer, events,
    tops, daily, myid, chatid
)
