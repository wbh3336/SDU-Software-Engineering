import pymysql

# 你的数据库配置（完全匹配你的环境）
DB_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "963196",
    "database": "online_bookstore",
    "charset": "utf8mb4"
}

# 清空数据库的SQL语句（全部用英文符号）
CLEAR_SQLS = [
    "SET FOREIGN_KEY_CHECKS = 0;",
    "TRUNCATE TABLE messages;",
    "TRUNCATE TABLE order_items;",
    "TRUNCATE TABLE orders;",
    "TRUNCATE TABLE carts;",
    "TRUNCATE TABLE books;",
    "TRUNCATE TABLE users;",
    "ALTER TABLE users AUTO_INCREMENT = 1;",
    "ALTER TABLE books AUTO_INCREMENT = 1;",
    "ALTER TABLE carts AUTO_INCREMENT = 1;",
    "ALTER TABLE orders AUTO_INCREMENT = 1;",
    "ALTER TABLE order_items AUTO_INCREMENT = 1;",
    "ALTER TABLE messages AUTO_INCREMENT = 1;",
    "SET FOREIGN_KEY_CHECKS = 1;"
]


def clear_database():
    print("开始清空数据库...")
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        for sql in CLEAR_SQLS:
            cursor.execute(sql)
            connection.commit()

        print("✅ 数据库清空完成！所有表已重置为初始状态")
        print("现在可以重新运行db_demo.py进行测试了")

    except Exception as e:
        print(f"❌ 清空失败：{e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            cursor.close()
            connection.close()


if __name__ == "__main__":
    clear_database()
    input("\n按回车键退出...")