import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def run_queries(db_path: str = "test_data.db") -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== ЗАПРОС 1: Общий размер всех документов ===")
        cursor.execute("""
            SELECT COUNT(*) as total_docs, 
                   SUM(size_kb) as total_size,
                   AVG(size_kb) as avg_size
            FROM documents
        """)
        row = cursor.fetchone()
        print(f"Всего документов: {row[0]}")
        print(f"Общий размер: {row[1]} KB")
        print(f"Средний размер: {row[2]:.2f} KB")
        
        print("\n=== ЗАПРОС 2: Размер документов по категориям ===")
        cursor.execute("""
            SELECT category, 
                   COUNT(*) as doc_count,
                   SUM(size_kb) as total_size,
                   AVG(size_kb) as avg_size
            FROM documents
            GROUP BY category
            ORDER BY total_size DESC
        """)
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} док., {row[2]} KB (средний: {row[3]:.1f} KB)")
        
        print("\n=== ЗАПРОС 3: Категории с общим размером > 100 KB ===")
        cursor.execute("""
            SELECT category, 
                   COUNT(*) as doc_count,
                   SUM(size_kb) as total_size
            FROM documents
            GROUP BY category
            HAVING SUM(size_kb) > 100
            ORDER BY total_size DESC
        """)
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[2]} KB ({row[1]} документов)")
        
        print("\n=== ЗАПРОС 4: Статусы документов по отделам ===")
        cursor.execute("""
            SELECT u.department,
                   d.status,
                   COUNT(*) as count
            FROM documents d
            INNER JOIN users u ON d.user_id = u.id
            GROUP BY u.department, d.status
            ORDER BY u.department, count DESC
        """)
        for row in cursor.fetchall():
            print(f"{row[0]} | {row[1]}: {row[2]}")
            
        print("\n=== ЗАПРОС 5: Пользователи с более чем 1 документом ===")
        cursor.execute("""
            SELECT u.name,
                   COUNT(d.id) as doc_count,
                   SUM(d.size_kb) as total_size
            FROM users u
            INNER JOIN documents d ON u.id = d.user_id
            GROUP BY u.id
            HAVING COUNT(d.id) > 1
            ORDER BY doc_count DESC
        """)
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} документов ({row[2]} KB)")
            
    except sqlite3.Error as e:
        logger.error("Ошибка: %s", e)
    finally:
        conn.close()


if __name__ == "__main__":
    run_queries()