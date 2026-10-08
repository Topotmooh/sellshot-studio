import os
import requests
from PIL import Image

def handle_user_photo(user_id, photo_url, bot):
    # Скачиваем фото
    response = requests.get(photo_url)
    if response.status_code == 200:
        filename = f"temp_{user_id}.jpg"
        with open(filename, "wb") as f:
            f.write(response.content)
        
        # Обрабатываем фото (добавляем вотермарку)
        img = Image.open(filename)
        img = img.resize((800, 800))
        img.save(filename)
        
        # Отправляем обратно в телеграм
        with open(filename, "rb") as f:
            bot.send_photo(user_id, f, caption="Готово!")
            
        # Удаляем временный файл
        os.remove(filename)
        return True
    else:
        return False