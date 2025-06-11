# 聊天服务层（占位）
from sqlalchemy.orm import Session

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        
    def get_messages(self):
        return [] 