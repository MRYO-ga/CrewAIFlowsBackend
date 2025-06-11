# 聊天数据模式定义（占位）
from pydantic import BaseModel

class ChatBase(BaseModel):
    pass

class ChatCreate(ChatBase):
    pass

class ChatUpdate(BaseModel):
    pass

class ChatResponse(ChatBase):
    pass 