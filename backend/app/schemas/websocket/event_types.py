from enum import Enum


class WebSocketEventType(str, Enum):
    MESSAGE_SEND = "message_send"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_EDIT = "message_edit"
    MESSAGE_REACTION = "message_reaction"
    MESSAGE_ACK = "message_ack"
    MESSAGE_READ = "message_read"
    TYPING = "typing"
    PRESENCE = "presence"
    ERROR = "error"
