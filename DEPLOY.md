# Деплой SellShot Studio

## VPS Нидерланды (бот)

### 1. Подготовка сервера

```bash
# Подключение
ssh root@<IP>

# Создание пользователя
adduser deploy
usermod --append --groups sudo deploy
su - deploy

# Установка Python
sudo apt update
sudo apt install -y python3-venv python3-pip