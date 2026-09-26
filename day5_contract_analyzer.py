import sqlite3
import logging
from datetime import datetime, timedelta
import random

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def setup_database(db_path: str = "contracts.db") -> None:
    """Создаёт базу данных с реалистичными тестовыми данными."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Создаём таблицы
    cursor.executescript("""
        DROP TABLE IF EXISTS contracts;
        DROP TABLE IF EXISTS lawyers;
        
        CREATE TABLE lawyers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            hire_date TEXT NOT NULL
        );
        
        CREATE TABLE contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            contract_type TEXT NOT NULL,
            status TEXT NOT NULL,
            value_rub INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            lawyer_id INTEGER,
            FOREIGN KEY (lawyer_id) REFERENCES lawyers(id)
        );
    """)
    
    # Добавляем юристов
    lawyers = [
        ("Иванов И.И.", "корпоративное право", "2020-01-15"),
        ("Петрова А.С.", "трудовое право", "2021-06-01"),
        ("Сидоров П.М.", "корпоративное право", "2019-03-20"),
        ("Козлова Е.В.", "налоговое право", "2022-09-10"),
        ("Новиков Д.А.", "трудовое право", "2023-02-01"),
    ]
    cursor.executemany(
        "INSERT INTO lawyers (name, specialization, hire_date) VALUES (?, ?, ?)",
        lawyers
    )
    
    # Генерируем 20 договоров
    contract_types = ["аренда", "поставка", "услуги", "трудовой", "NDA"]
    statuses = ["approved", "pending", "rejected", "draft"]
    
    contracts = []
    base_date = datetime(2026, 8, 1)
    
    for i in range(20):
        title = f"Договор {contract_types[i % 5]} №{1000 + i}"
        contract_type = contract_types[i % 5]
        status = random.choice(statuses)
        value = random.randint(50000, 500000)
        created_at = (base_date + timedelta(days=random.randint(0, 50))).strftime("%Y-%m-%d")
        lawyer_id = random.randint(1, 5)
        contracts.append((title, contract_type, status, value, created_at, lawyer_id))
    
    # Добавляем 2 дубликата для демонстрации дедупликации
    contracts.append(("Договор аренда №1000", "аренда", "approved", 150000, "2026-09-20", 1))
    contracts.append(("Договор аренда №1000", "аренда", "approved", 150000, "2026-09-22", 1))
    
    cursor.executemany(
        """INSERT INTO contracts 
           (title, contract_type, status, value_rub, created_at, lawyer_id) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        contracts
    )
    
    conn.commit()
    logger.info("База создана: %d юристов, %d договоров", len(lawyers), len(contracts))
    conn.close()


def run_analytics(db_path: str = "contracts.db") -> None:
    """Запускает серию аналитических запросов."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print(" АНАЛИТИКА ДОГОВОРОВ")
    print("="*60)
    
    # 1. Общая статистика
    print("\n📌 1. ОБЩАЯ СТАТИСТИКА")
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(value_rub) as total_value,
            AVG(value_rub) as avg_value,
            MAX(value_rub) as max_value
        FROM contracts
    """)
    row = cursor.fetchone()
    print(f"   Всего договоров: {row[0]}")
    print(f"   Общая сумма: {row[1]:,} руб.")
    print(f"   Средняя сумма: {row[2]:,.0f} руб.")
    print(f"   Максимальная сумма: {row[3]:,} руб.")
    
    # 2. Статистика по типам
    print("\n📌 2. ДОГОВОРЫ ПО ТИПАМ")
    cursor.execute("""
        SELECT contract_type,
               COUNT(*) as count,
               SUM(value_rub) as total_value,
               AVG(value_rub) as avg_value
        FROM contracts
        GROUP BY contract_type
        ORDER BY total_value DESC
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]:15} | {row[1]} дог. | {row[2]:>10,} руб. | средн: {row[3]:,.0f}")
    
    # 3. Активность юристов (JOIN + GROUP BY)
    print("\n📌 3. АКТИВНОСТЬ ЮРИСТОВ")
    cursor.execute("""
        SELECT l.name, l.specialization,
               COUNT(c.id) as contracts_count,
               SUM(c.value_rub) as total_value
        FROM lawyers l
        LEFT JOIN contracts c ON l.id = c.lawyer_id
        GROUP BY l.id
        ORDER BY contracts_count DESC
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]:20} | {row[1]:25} | {row[2]} дог. | {row[3]:>10,} руб.")
    
    # 4. Топ-3 самых дорогих договора (оконная функция)
    print("\n 4. ТОП-3 ДОРОГИХ ДОГОВОРА")
    cursor.execute("""
        WITH ranked AS (
            SELECT title, value_rub, created_at,
                   ROW_NUMBER() OVER (ORDER BY value_rub DESC) as rn
            FROM contracts
        )
        SELECT title, value_rub, created_at
        FROM ranked
        WHERE rn <= 3
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]:,} руб. ({row[2]})")
    
    # 5. Дедупликация: находим дубликаты
    print("\n📌 5. ДУБЛИКАТЫ (по названию)")
    cursor.execute("""
        WITH duplicates AS (
            SELECT title, COUNT(*) as cnt,
                   GROUP_CONCAT(id) as ids
            FROM contracts
            GROUP BY title
            HAVING COUNT(*) > 1
        )
        SELECT title, cnt, ids FROM duplicates
    """)
    for row in cursor.fetchall():
        print(f"   ⚠️  '{row[0]}' — {row[1]} копий (ID: {row[2]})")
    
    # 6. Статусы договоров по специализации юристов
    print("\n📌 6. СТАТУСЫ ПО СПЕЦИАЛИЗАЦИИ")
    cursor.execute("""
        SELECT l.specialization, c.status, COUNT(*) as count
        FROM contracts c
        INNER JOIN lawyers l ON c.lawyer_id = l.id
        GROUP BY l.specialization, c.status
        ORDER BY l.specialization, count DESC
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]:25} | {row[1]:10} | {row[2]}")
    
    # 7. Свежие документы (последние 5)
    print("\n📌 7. ПОСЛЕДНИЕ 5 ДОГОВОРОВ")
    cursor.execute("""
        SELECT title, created_at, value_rub
        FROM contracts
        ORDER BY created_at DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   {row[0]} | {row[1]} | {row[2]:,} руб.")
    
    conn.close()


if __name__ == "__main__":
    setup_database()
    run_analytics()