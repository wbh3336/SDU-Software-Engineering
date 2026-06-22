import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

class DBConnection:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        """创建数据库连接"""
        try:
            self.connection = pymysql.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT")),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                charset=os.getenv("DB_CHARSET"),
                cursorclass=DictCursor  # 返回字典格式结果，方便后端使用
            )
            self.cursor = self.connection.cursor()
            return True
        except Exception as e:
            print(f"数据库连接失败：{e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def execute(self, sql, params=None):
        """执行增删改操作，返回影响行数"""
        try:
            if not self.connection:
                self.connect()
            rows = self.cursor.execute(sql, params)
            self.connection.commit()
            return rows
        except Exception as e:
            self.connection.rollback()
            print(f"执行SQL失败：{e}")
            return 0

    def query_one(self, sql, params=None):
        """查询单条数据，返回字典"""
        try:
            if not self.connection:
                self.connect()
            self.cursor.execute(sql, params)
            return self.cursor.fetchone()
        except Exception as e:
            print(f"查询失败：{e}")
            return None

    def query_all(self, sql, params=None):
        """查询多条数据，返回字典列表"""
        try:
            if not self.connection:
                self.connect()
            self.cursor.execute(sql, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"查询失败：{e}")
            return []

    def begin_transaction(self):
        """开启事务"""
        if self.connection:
            self.connection.autocommit(False)

    def commit(self):
        """提交事务"""
        if self.connection:
            self.connection.commit()
            self.connection.autocommit(True)

    def rollback(self):
        """回滚事务"""
        if self.connection:
            self.connection.rollback()
            self.connection.autocommit(True)