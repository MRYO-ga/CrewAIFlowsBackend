#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空xhs_notes表脚本
"""
from sqlalchemy import create_engine, text
from database.database import DATABASE_URL

def clear_xhs_notes():
    print("⚠️ 开始清空xhs_notes表...")
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM xhs_notes"))
        conn.commit()
    print("✅ xhs_notes表已清空")

if __name__ == "__main__":
    clear_xhs_notes() 