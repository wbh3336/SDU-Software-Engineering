import pymysql
from pymysql.err import OperationalError, ProgrammingError

# 数据库配置（已修改为你的实际设置）
DB_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "963196",
    "charset": "utf8mb4"
}
DB_NAME = "online_bookstore"

# 修复后的SQL创建脚本（去掉不兼容的IF NOT EXISTS索引语法）
CREATE_SQLS = [
    # 1. 创建数据库
    f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
    # 2. 使用数据库
    f"USE {DB_NAME};",
    # 3. 用户表（会员+店主）
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户唯一ID',
        username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名（唯一）',
        password_hash VARCHAR(64) NOT NULL COMMENT '加密后的密码',
        role ENUM('member', 'admin') NOT NULL DEFAULT 'member' COMMENT '角色：member会员/admin店主',
        phone VARCHAR(20) COMMENT '联系电话',
        create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间'
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    # 4. 图书表
    """
    CREATE TABLE IF NOT EXISTS books (
        book_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '图书唯一ID',
        title VARCHAR(100) NOT NULL COMMENT '书名',
        author VARCHAR(50) NOT NULL COMMENT '作者',
        price DECIMAL(10,2) NOT NULL COMMENT '图书价格',
        stock INT NOT NULL DEFAULT 0 COMMENT '库存数量',
        category VARCHAR(30) NOT NULL COMMENT '图书分类（如：计算机、文学）',
        description TEXT COMMENT '图书简介',
        create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上架时间'
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    # 5. 购物车表
    """
    CREATE TABLE IF NOT EXISTS carts (
        cart_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '购物车项ID',
        user_id INT NOT NULL COMMENT '用户ID',
        book_id INT NOT NULL COMMENT '图书ID',
        quantity INT NOT NULL DEFAULT 1 COMMENT '购买数量',
        create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '添加时间',
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
        UNIQUE KEY (user_id, book_id) COMMENT '同一用户同一图书只能有一条购物车记录'
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    # 6. 订单主表
    """
    CREATE TABLE IF NOT EXISTS orders (
        order_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '订单唯一ID',
        user_id INT NOT NULL COMMENT '下单用户ID',
        total_amount DECIMAL(10,2) NOT NULL COMMENT '订单总金额',
        status ENUM('pending', 'shipped', 'completed', 'cancelled') NOT NULL DEFAULT 'pending' COMMENT '订单状态：待发货/已发货/已完成/已取消',
        create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '下单时间',
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    # 7. 订单明细表
    """
    CREATE TABLE IF NOT EXISTS order_items (
        item_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '明细ID',
        order_id INT NOT NULL COMMENT '订单ID',
        book_id INT NOT NULL COMMENT '图书ID',
        quantity INT NOT NULL COMMENT '购买数量',
        unit_price DECIMAL(10,2) NOT NULL COMMENT '下单时的单价',
        FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
        FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    # 8. 留言表
    """
    CREATE TABLE IF NOT EXISTS messages (
        message_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '留言ID',
        user_id INT NOT NULL COMMENT '留言用户ID',
        content TEXT NOT NULL COMMENT '留言内容',
        reply TEXT COMMENT '店主回复内容',
        create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '留言时间',
        reply_time DATETIME COMMENT '回复时间',
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    # 9. 添加索引（修复：去掉IF NOT EXISTS，第一次创建不会冲突）
    "CREATE INDEX idx_books_category ON books(category);",
    "CREATE INDEX idx_orders_user_id ON orders(user_id);",
    "CREATE INDEX idx_orders_status ON orders(status);"
]

def create_database_and_tables():
    print("=== 开始创建网上书店数据库 ===")
    connection = None
    try:
        # 1. 连接MySQL服务器（不指定数据库）
        print("正在连接MySQL服务器...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("MySQL连接成功！")

        # 2. 逐条执行SQL语句
        for i, sql in enumerate(CREATE_SQLS):
            try:
                cursor.execute(sql)
                connection.commit()
                print(f"执行步骤 {i+1}/{len(CREATE_SQLS)} 成功")
            except Exception as e:
                # 如果是索引已存在的错误，忽略继续执行
                if "Duplicate key name" in str(e):
                    print(f"步骤 {i+1} 索引已存在，跳过")
                    continue
                print(f"执行步骤 {i+1} 失败：{e}")
                connection.rollback()
                raise

        print("\n✅ 所有数据库和表创建完成！")
        print(f"数据库名称：{DB_NAME}")
        print("包含表：users, books, carts, orders, order_items, messages")

        # 3. 验证创建结果
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("\n已创建的表：")
        for table in tables:
            print(f"  - {table[0]}")

        # 4. 验证索引
        cursor.execute("SHOW INDEX FROM books;")
        indexes = cursor.fetchall()
        print("\n已创建的索引：")
        for idx in indexes:
            print(f"  - {idx[2]}")

    except OperationalError as e:
        print(f"\n❌ MySQL连接失败！")
        print(f"错误原因：{e}")
        print("请检查：")
        print("1. MySQL服务是否已启动")
        print("2. root密码是否为963196")
        print("3. MySQL端口是否为3307")
    except Exception as e:
        print(f"\n❌ 创建失败：{e}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("\n数据库连接已关闭")

if __name__ == "__main__":
    create_database_and_tables()
    input("\n按回车键退出...")