#!/bin/bash

# 1. Оновлення та встановлення (додано gunicorn)
sudo apt update
sudo apt install -y python3-pip python3-flask python3-mysqldb mariadb-server nginx gunicorn

# 2. Налаштування бази даних
sudo mysql -e "CREATE DATABASE IF NOT EXISTS task_db;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'app_user'@'localhost' IDENTIFIED BY '1203';"
sudo mysql -e "GRANT ALL PRIVILEGES ON task_db.* TO 'app_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# 3. Створення користувачів системи згідно завданню
sudo id -u app &>/dev/null || sudo useradd -r -s /bin/false app

sudo id -u student &>/dev/null || {
    sudo useradd -m -s /bin/bash student
    echo "student:1203" | sudo chpasswd
    sudo usermod -aG sudo student
}

sudo id -u teacher &>/dev/null || {
    sudo useradd -m -s /bin/bash teacher
    echo "teacher:12345678" | sudo chpasswd
    sudo usermod -aG sudo teacher
    sudo chage -d 0 teacher
}

sudo id -u operator &>/dev/null || {
    sudo useradd -m -s /bin/bash operator
    echo "operator:12345678" | sudo chpasswd
    sudo chage -d 0 operator
    echo "operator ALL=(ALL) NOPASSWD: /usr/bin/systemctl start mywebapp, /usr/bin/systemctl stop mywebapp, /usr/bin/systemctl restart mywebapp, /usr/bin/systemctl status mywebapp, /usr/bin/systemctl reload nginx" | sudo tee /etc/sudoers.d/operator
}

# 4. Файл gradebook
echo "4" | sudo tee /home/student/gradebook
sudo chown student:student /home/student/gradebook

# 5. Копіювання коду застосунку у правильну папку для сервісу
sudo mkdir -p /opt/mywebapp
sudo cp app.py migrate.py wsgi.py requirements.txt /opt/mywebapp/
sudo chown -R app:app /opt/mywebapp

# 6. Налаштування Systemd Socket Activation
cat <<EOF | sudo tee /etc/systemd/system/mywebapp.socket
[Unit]
Description=My Web App Socket

[Socket]
ListenStream=127.0.0.1:5000

[Install]
WantedBy=sockets.target
EOF

cat <<EOF | sudo tee /etc/systemd/system/mywebapp.service
[Unit]
Description=My Web App Task Tracker
Requires=mywebapp.socket
After=network.target mariadb.service

[Service]
User=app
WorkingDirectory=/opt/mywebapp
# Міграція перед стартом
ExecStartPre=/usr/bin/python3 /opt/mywebapp/migrate.py 127.0.0.1 app_user 1203 task_db
# Запуск через gunicorn, який підхопить сокет
ExecStart=/usr/bin/gunicorn wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable mywebapp.socket
sudo systemctl start mywebapp.socket

# 7. Налаштування Nginx (обмеження доступу та логування)
cat <<EOF | sudo tee /etc/nginx/sites-available/default
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    # Запис логів запитів
    access_log /var/log/nginx/mywebapp_access.log;
    error_log /var/log/nginx/mywebapp_error.log;

    # Дозволяємо ТІЛЬКИ кореневий ендпоінт та ендпоінти бізнес-логіки
    location = / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header Accept \$http_accept;
    }

    location /tasks {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header Accept \$http_accept;
    }

    # Блокуємо доступ до /health або інших внутрішніх шляхів ззовні
    location / {
        return 403;
    }
}
EOF

sudo systemctl restart nginx

# 8. Блокування дефолтного користувача
# sudo usermod -L alex_admin

echo "Setup is 100% complete! Socket Activation and Nginx Restrictions applied."