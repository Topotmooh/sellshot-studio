import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def setup_database(db_path: str = "test_data.db") -> None:
    """Создаёт таблицы и заполняет тестовыми данными (идемпотентно)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # === Создаём таблицу users ===
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                department TEXT NOT NULL
            )
        """)
        
        # Используем INSERT OR IGNORE, чтобы не создавать дубликаты
        users_data = [
            ("Иванов Иван", "ivanov@company.ru", "legal"),
            ("Петрова Мария", "petrova@company.ru", "hr"),
            ("Сидоров Алексей", "sidorov@company.ru", "legal"),
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO users (name, email, department)
            VALUES (?, ?, ?)
        """, users_data)
        logger.info("Таблица users готова")
        
        # === Добавляем колонку user_id в documents (если её нет) ===
        # Проверяем, существует ли колонка
        cursor.execute("PRAGMA table_info(documents)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "user_id" not in columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN user_id INTEGER")
            logger.info("Колонка user_id добавлена в documents")
        else:
            logger.info("Колонка user_id уже существует")
        
        # === Привязываем документы к пользователям ===
        updates = [
            (1, 1), (2, 2), (3, 1), (4, 3), (5, 2), (6, 1)
        ]
        
        cursor.executemany("""
            UPDATE documents SET user_id = ? WHERE id = ?
        """, [(user_id, doc_id) for doc_id, user_id in updates])
        logger.info("Документы привязаны к пользователям")
        
        conn.commit()
        
    except sqlite3.Error as e:
        logger.error("Ошибка при настройке базы данных: %s", e)
        conn.rollback()
        raise
    finally:
        conn.close()


def run_queries(db_path: str = "test_data.db") -> None:
    """Выполняет демонстрационные запросы с JOIN."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== ЗАПРОС 1: Все документы с именами авторов ===")
        cursor.execute("""
            SELECT d.title, u.name as author_name
            FROM documents d
            INNER JOIN users u ON d.user_id = u.id
        """)
        for row in cursor.fetchall():
            print(row)
        
        print("\n=== ЗАПРОС 2: Документы отдела Legal ===")
        cursor.execute("""
            SELECT d.title, u.name, u.department
            FROM documents d
            INNER JOIN users u ON d.user_id = u.id
            WHERE u.department = 'legal'
        """)
        for row in cursor.fetchall():
            print(row)
        
        print("\n=== ЗАПРОС 3: Сколько документов создал каждый пользователь ===")
        cursor.execute("""
            SELECT u.name, COUNT(d.id) as doc_count
            FROM users u
            LEFT JOIN documents d ON u.id = d.user_id
            GROUP BY u.id
            ORDER BY doc_count DESC
        """)
        for row in cursor.fetchall():
            print(row)
            
    except sqlite3.Error as e:
        logger.error("Ошибка при выполнении запросов: %s", e)
    finally:
        conn.close()


if __name__ == "__main__":
    setup_database()
    run_queries()