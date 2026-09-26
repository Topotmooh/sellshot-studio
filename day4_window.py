import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def run_queries(db_path: str = "test_data.db") -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n=== ЗАПРОС 1: Нумерация документов внутри каждой категории ===")
        cursor.execute("""
            SELECT title, category, size_kb,
                   ROW_NUMBER() OVER (PARTITION BY category ORDER BY size_kb DESC) as row_num
            FROM documents
            ORDER BY category, row_num
        """)
        for row in cursor.fetchall():
            print(f"{row[1]} | {row[0]}: {row[2]} KB (#{row[3]})")
        
        print("\n=== ЗАПРОС 2: Топ-1 документ в каждой категории ===")
        cursor.execute("""
            WITH ranked_docs AS (
                SELECT title, category, size_kb,
                       ROW_NUMBER() OVER (PARTITION BY category ORDER BY size_kb DESC) as rn
                FROM documents
            )
            SELECT title, category, size_kb
            FROM ranked_docs
            WHERE rn = 1
        """)
        for row in cursor.fetchall():
            print(f"{row[1]}: {row[0]} ({row[2]} KB)")
        
        print("\n=== ЗАПРОС 3: Ранжирование документов по размеру (общий рейтинг) ===")
        cursor.execute("""
            SELECT title, size_kb,
                   RANK() OVER (ORDER BY size_kb DESC) as rank,
                   DENSE_RANK() OVER (ORDER BY size_kb DESC) as dense_rank
            FROM documents
            ORDER BY size_kb DESC
        """)
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} KB (RANK: {row[2]}, DENSE_RANK: {row[3]})")
        
        print("\n=== ЗАПРОС 4: Дедупликация — оставляем только самый свежий документ ===")
        # Добавим дубликаты для демонстрации
        cursor.execute("""
            INSERT INTO documents (title, category, status, created_at, size_kb, user_id)
            VALUES ('Договор аренды №123 (копия)', 'contract', 'approved', '2026-09-20', 150, 1)
        """)
        conn.commit()
        
        cursor.execute("""
            WITH ranked AS (
                SELECT id, title, created_at,
                       ROW_NUMBER() OVER (PARTITION BY title ORDER BY created_at DESC) as rn
                FROM documents
            )
            SELECT id, title, created_at
            FROM ranked
            WHERE rn = 1
            ORDER BY created_at DESC
        """)
        for row in cursor.fetchall():
            print(f"ID {row[0]}: {row[1]} ({row[2]})")
        
        # Удаляем дубликаты (оставляем только rn=1)
        cursor.execute("""
            DELETE FROM documents
            WHERE id IN (
                SELECT id FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (PARTITION BY title ORDER BY created_at DESC) as rn
                    FROM documents
                ) WHERE rn > 1
            )
        """)
        conn.commit()
        logger.info("Дубликаты удалены")
            
    except sqlite3.Error as e:
        logger.error("Ошибка: %s", e)
    finally:
        conn.close()


if __name__ == "__main__":
    run_queries()