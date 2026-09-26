import sqlite3

conn = sqlite3.connect("test_data.db")
cursor = conn.cursor()

print("=== ЗАПРОС 1: Все документы ===")
cursor.execute("SELECT * FROM documents")
rows = cursor.fetchall()
for row in rows:
    print(row)

print("\n=== ЗАПРОС 2: Только одобренные документы ===")
cursor.execute("SELECT title, status FROM documents WHERE status = 'approved'")
rows = cursor.fetchall()
for row in rows:
    print(row)

print("\n=== ЗАПРОС 3: Документы категории 'contract', отсортированные по дате ===")
cursor.execute("""
    SELECT title, created_at 
    FROM documents 
    WHERE category = 'contract' 
    ORDER BY created_at DESC
""")
rows = cursor.fetchall()
for row in rows:
    print(row)

print("\n=== ЗАПРОС 4: Документы больше 100 KB ===")
cursor.execute("SELECT title, size_kb FROM documents WHERE size_kb > 100")
rows = cursor.fetchall()
for row in rows:
    print(row)

    print("\n=== ЗАПРОС 5: Pending документы по размеру ===")
cursor.execute("""
    SELECT title, size_kb 
    FROM documents 
    WHERE status = 'pending'
    ORDER BY size_kb DESC
""")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()