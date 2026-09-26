import sqlite3

# Создаём подключение к базе данных (файл создастся автоматически)
conn = sqlite3.connect("test_data.db")
cursor = conn.cursor()

# Создаём таблицу "documents" (документы)
cursor.execute("""
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    size_kb INTEGER
)
""")

# Вставляем тестовые данные
test_data = [
    ("Договор аренды №123", "contract", "approved", "2026-09-01", 150),
    ("Исковое заявление", "lawsuit", "pending", "2026-09-05", 80),
    ("Акт выполненных работ", "act", "approved", "2026-09-10", 45),
    ("Договор поставки №456", "contract", "rejected", "2026-09-12", 200),
    ("Претензия", "claim", "pending", "2026-09-15", 60),
    ("Договор аренды №789", "contract", "approved", "2026-09-18", 175),
]

cursor.executemany("""
INSERT INTO documents (title, category, status, created_at, size_kb)
VALUES (?, ?, ?, ?, ?)
""", test_data)

conn.commit()
print("✅ База данных создана и заполнена!")

# Закрываем подключение
conn.close()