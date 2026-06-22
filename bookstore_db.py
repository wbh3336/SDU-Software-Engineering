import hashlib
from db_config import DBConnection

def hash_password(password):
    """密码加密（MD5，实验项目够用）"""
    return hashlib.md5(password.encode('utf-8')).hexdigest()

def add_user(username, password, role='member', phone=None):#注册，返回用户ID或None
    db = DBConnection()
    password_hash = hash_password(password)
    sql = """
    INSERT INTO users (username, password_hash, role, phone)
    VALUES (%s, %s, %s, %s)
    """
    rows = db.execute(sql, (username, password_hash, role, phone))
    db.close()
    return db.cursor.lastrowid if rows > 0 else None

def get_user_by_username(username):
    """根据用户名查询用户，返回用户字典或None"""
    db = DBConnection()
    sql = "SELECT * FROM users WHERE username = %s"
    user = db.query_one(sql, (username,))
    db.close()
    return user

def get_user_by_id(user_id):
    """根据用户ID查询用户"""
    db = DBConnection()
    sql = "SELECT * FROM users WHERE user_id = %s"
    user = db.query_one(sql, (user_id,))
    db.close()
    return user

def update_user_password(user_id, new_password):
    """修改用户密码，返回是否成功"""
    db = DBConnection()
    password_hash = hash_password(new_password)
    sql = "UPDATE users SET password_hash = %s WHERE user_id = %s"
    rows = db.execute(sql, (password_hash, user_id))
    db.close()
    return rows > 0

def get_all_users():
    """查询所有会员"""
    db = DBConnection()
    sql = "SELECT user_id, username, phone, create_time FROM users WHERE role = 'member'"
    users = db.query_all(sql)
    db.close()
    return users

def add_book(title, author, price, stock, category, description=None):
    """添加图书，返回图书ID或None"""
    db = DBConnection()
    sql = """
    INSERT INTO books (title, author, price, stock, category, description)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    rows = db.execute(sql, (title, author, price, stock, category, description))
    db.close()
    return db.cursor.lastrowid if rows > 0 else None

def get_book_by_id(book_id):
    """根据ID查询图书"""
    db = DBConnection()
    sql = "SELECT * FROM books WHERE book_id = %s"
    book = db.query_one(sql, (book_id,))
    db.close()
    return book

def get_books_by_category(category=None):
    """按分类查询图书"""
    db = DBConnection()
    if category:
        sql = "SELECT * FROM books WHERE category = %s"
        books = db.query_all(sql, (category,))
    else:
        sql = "SELECT * FROM books"
        books = db.query_all(sql)
    db.close()
    return books

def update_book(book_id, **kwargs):
    """更新图书信息，返回是否成功"""
    db = DBConnection()
    allowed_fields = ['title', 'author', 'price', 'stock', 'category', 'description']
    update_fields = [f"{k} = %s" for k in kwargs.keys() if k in allowed_fields]
    if not update_fields:
        db.close()
        return False
    sql = f"UPDATE books SET {', '.join(update_fields)} WHERE book_id = %s"
    params = list(kwargs.values()) + [book_id]
    rows = db.execute(sql, params)
    db.close()
    return rows > 0

def delete_book(book_id):
    """删除图书"""
    db = DBConnection()
    sql = "DELETE FROM books WHERE book_id = %s"
    rows = db.execute(sql, (book_id,))
    db.close()
    return rows > 0

def update_book_stock(book_id, quantity, db=None):
    """更新图书库存，quantity为正表示增加，负表示减少"""
    if not db:
        db = DBConnection()
        need_close = True
    else:
        need_close = False
    sql = "UPDATE books SET stock = stock + %s WHERE book_id = %s AND stock + %s >= 0"
    rows = db.execute(sql, (quantity, book_id, quantity))
    if need_close:
        db.close()
    return rows > 0

# ------------------------------ 购物车操作 ------------------------------
def add_to_cart(user_id, book_id, quantity=1):
    """添加商品到购物车，若存在则更新数量"""
    db = DBConnection()
    # 先检查是否已存在
    sql = "SELECT cart_id, quantity FROM carts WHERE user_id = %s AND book_id = %s"
    existing = db.query_one(sql, (user_id, book_id))
    if existing:
        # 更新数量
        new_quantity = existing['quantity'] + quantity
        sql = "UPDATE carts SET quantity = %s WHERE cart_id = %s"
        rows = db.execute(sql, (new_quantity, existing['cart_id']))
    else:
        # 新增记录
        sql = "INSERT INTO carts (user_id, book_id, quantity) VALUES (%s, %s, %s)"
        rows = db.execute(sql, (user_id, book_id, quantity))
    db.close()
    return rows > 0

def get_user_cart(user_id):
    """查询用户购物车，返回带图书信息的列表"""
    db = DBConnection()
    sql = """
    SELECT c.cart_id, c.book_id, b.title, b.author, b.price, c.quantity, (b.price * c.quantity) AS subtotal
    FROM carts c
    JOIN books b ON c.book_id = b.book_id
    WHERE c.user_id = %s
    """
    cart_items = db.query_all(sql, (user_id,))
    db.close()
    return cart_items

def update_cart_item(cart_id, quantity):
    """更新购物车商品数量"""
    db = DBConnection()
    sql = "UPDATE carts SET quantity = %s WHERE cart_id = %s"
    rows = db.execute(sql, (quantity, cart_id))
    db.close()
    return rows > 0

def delete_cart_item(cart_id):
    """删除购物车商品"""
    db = DBConnection()
    sql = "DELETE FROM carts WHERE cart_id = %s"
    rows = db.execute(sql, (cart_id,))
    db.close()
    return rows > 0

def clear_user_cart(user_id, db=None):
    """清空用户购物车（下单后调用，支持事务）"""
    if not db:
        db = DBConnection()
        need_close = True
    else:
        need_close = False
    sql = "DELETE FROM carts WHERE user_id = %s"
    rows = db.execute(sql, (user_id,))
    if need_close:
        db.close()
    return rows > 0

# ------------------------------ 订单操作 ------------------------------
def create_order(user_id, cart_items):
    """
    创建订单（事务处理：扣减库存+创建订单+创建订单明细+清空购物车）
    cart_items格式：[{"book_id":1, "quantity":2, "price":39.9}, ...]
    返回订单ID或None
    """
    db = DBConnection()
    if not db.connect():
        return None
    
    try:
        # 开启事务
        db.begin_transaction()
        
        # 1. 计算总金额
        total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
        
        # 2. 创建订单主表
        order_sql = "INSERT INTO orders (user_id, total_amount) VALUES (%s, %s)"
        db.execute(order_sql, (user_id, total_amount))
        order_id = db.cursor.lastrowid
        
        # 3. 创建订单明细
        item_sql = """
        INSERT INTO order_items (order_id, book_id, quantity, unit_price)
        VALUES (%s, %s, %s, %s)
        """
        for item in cart_items:
            db.execute(item_sql, (order_id, item['book_id'], item['quantity'], item['price']))
            
            # 4. 扣减库存
            if not update_book_stock(item['book_id'], -item['quantity'], db):
                raise Exception(f"图书{int(item['book_id'])}库存不足")
        
        # 5. 清空购物车
        clear_user_cart(user_id, db)
        
        # 提交事务
        db.commit()
        return order_id
    
    except Exception as e:
        # 回滚事务
        db.rollback()
        print(f"创建订单失败：{e}")
        return None
    finally:
        db.close()

def get_order_by_id(order_id):
    """查询订单详情（含明细）"""
    db = DBConnection()
    # 查询订单主表
    order_sql = "SELECT * FROM orders WHERE order_id = %s"
    order = db.query_one(order_sql, (order_id,))
    if not order:
        db.close()
        return None
    
    # 查询订单明细
    item_sql = """
    SELECT oi.book_id, b.title, oi.quantity, oi.unit_price, (oi.quantity * oi.unit_price) AS subtotal
    FROM order_items oi
    JOIN books b ON oi.book_id = b.book_id
    WHERE oi.order_id = %s
    """
    order['items'] = db.query_all(item_sql, (order_id,))
    db.close()
    return order

def get_user_orders(user_id):
    """查询用户的所有订单"""
    db = DBConnection()
    sql = "SELECT * FROM orders WHERE user_id = %s ORDER BY create_time DESC"
    orders = db.query_all(sql, (user_id,))
    db.close()
    return orders

def get_all_orders(status=None):
    """店主查询所有订单，可按状态筛选"""
    db = DBConnection()
    if status:
        sql = "SELECT * FROM orders WHERE status = %s ORDER BY create_time DESC"
        orders = db.query_all(sql, (status,))
    else:
        sql = "SELECT * FROM orders ORDER BY create_time DESC"
        orders = db.query_all(sql)
    db.close()
    return orders

def update_order_status(order_id, new_status):
    """更新订单状态"""
    db = DBConnection()
    sql = "UPDATE orders SET status = %s WHERE order_id = %s"
    rows = db.execute(sql, (new_status, order_id))
    db.close()
    return rows > 0

# ------------------------------ 留言操作 ------------------------------
def add_message(user_id, content):
    """用户添加留言"""
    db = DBConnection()
    sql = "INSERT INTO messages (user_id, content) VALUES (%s, %s)"
    rows = db.execute(sql, (user_id, content))
    db.close()
    return db.cursor.lastrowid if rows > 0 else None

def get_all_messages():
    """店主查询所有留言（带用户名）"""
    db = DBConnection()
    sql = """
    SELECT m.message_id, m.user_id, u.username, m.content, m.reply, m.create_time, m.reply_time
    FROM messages m
    JOIN users u ON m.user_id = u.user_id
    ORDER BY m.create_time DESC
    """
    messages = db.query_all(sql)
    db.close()
    return messages

def reply_message(message_id, reply_content):
    """店主回复留言"""
    db = DBConnection()
    sql = """
    UPDATE messages 
    SET reply = %s, reply_time = CURRENT_TIMESTAMP 
    WHERE message_id = %s
    """
    rows = db.execute(sql, (reply_content, message_id))
    db.close()
    return rows > 0