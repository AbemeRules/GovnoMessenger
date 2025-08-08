from flask import Flask, request, jsonify, render_template_string, send_file
from collections import deque
from datetime import datetime
import threading
import json
import os
import socket

app = Flask(__name__)

# Конфигурация
HISTORY_FILE = "message_history2.json"
MAX_HISTORY_SIZE = 10000
ADMIN_IP = "127.0.0.1"  # IP администратора


# Загрузка истории из файла при запуске
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return deque(json.load(f), maxlen=MAX_HISTORY_SIZE)
        except Exception as e:
            print(f"Ошибка загрузки истории: {e}")
    return deque(maxlen=MAX_HISTORY_SIZE)


# Инициализация истории
message_history = load_history()
history_lock = threading.Lock()

# HTML шаблон для мессенджера
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Local Messenger</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            color: #333;
        }

        .container {
            width: 100%;
            max-width: 900px;
            height: 95vh;
            background-color: white;
            display: flex;
            flex-direction: column;
            border-radius: 20px;
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.2);
            overflow: hidden;
            position: relative;
        }

        .header {
            background: linear-gradient(to right, #4776E6, #8E54E9);
            color: white;
            padding: 20px;
            text-align: center;
            position: relative;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header-content {
            flex: 1;
        }

        h1 {
            font-size: 1.8rem;
            font-weight: 600;
            margin: 0;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        .subtitle {
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 5px;
        }

        .admin-link {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: none;
            border-radius: 20px;
            padding: 8px 15px;
            font-size: 0.9rem;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.3s ease;
            margin-left: 15px;
        }

        .admin-link:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.05);
        }

        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            background-color: #f0f4f8;
            background-image: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%239C92AC' fill-opacity='0.05' fill-rule='evenodd'/%3E%3C/svg%3E");
        }

        .message { 
            margin-bottom: 15px; 
            padding: 15px;
            border-radius: 18px;
            max-width: 80%;
            width: fit-content;
            position: relative;
            animation: fadeIn 0.3s ease-out;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }

        .message.other {
            background-color: white;
            border-bottom-left-radius: 5px;
            align-self: flex-start;
            margin-right: auto;
        }

        .message.own {
            background: linear-gradient(to right, #4776E6, #8E54E9);
            color: white;
            border-bottom-right-radius: 5px;
            align-self: flex-end;
            margin-left: auto;
        }

        .message.admin {
            background: linear-gradient(to right, #4CAF50, #8BC34A);
            color: white;
            border-bottom-right-radius: 5px;
            align-self: flex-end;
            margin-left: auto;
        }

        .sender {
            font-weight: 600;
            font-size: 0.85rem;
            margin-bottom: 5px;
            display: flex;
            align-items: center;
        }

        .message.own .sender, .message.admin .sender {
            color: rgba(255,255,255,0.9);
        }

        .content {
            font-size: 1.1rem;
            line-height: 1.4;
            word-break: break-word;
            padding: 5px 0;
        }

        .ip-display {
            font-size: 0.75rem;
            opacity: 0.7;
            margin-top: 3px;
        }

        .message-footer {
            display: flex;
            justify-content: flex-end;
            margin-top: 8px;
            font-size: 0.75rem;
            opacity: 0.8;
        }

        .datetime {
            text-align: right;
        }

        .message.other .datetime {
            color: #666;
        }

        .message.own .datetime, .message.admin .datetime {
            color: rgba(255,255,255,0.8);
        }

        .no-messages {
            text-align: center;
            color: #666;
            padding: 40px 20px;
            font-size: 1.1rem;
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }

        .input-container {
            background-color: white;
            padding: 20px;
            border-top: 1px solid #e0e4e8;
        }

        .input-area {
            display: flex;
            padding: 0;
        }

        #message-input {
            flex: 1;
            padding: 15px 20px;
            border: none;
            border-radius: 30px;
            font-size: 1.1rem;
            outline: none;
            background-color: #f0f4f8;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }

        #message-input:focus {
            background-color: #e6eef9;
            box-shadow: inset 0 2px 8px rgba(0,0,0,0.08);
        }

        #send-button {
            background: linear-gradient(to right, #4776E6, #8E54E9);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            margin-left: 15px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            box-shadow: 0 5px 15px rgba(135, 99, 232, 0.4);
            transition: all 0.3s ease;
        }

        #send-button:hover {
            transform: scale(1.05);
            box-shadow: 0 7px 20px rgba(135, 99, 232, 0.6);
        }

        #send-button:disabled {
            background: #e0e4e8;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .scroll-down {
            position: absolute;
            bottom: 10px;
            right: 20px;
            background: rgba(255,255,255,0.9);
            width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            opacity: 0;
            transform: translateY(10px);
            transition: all 0.3s ease;
            z-index: 10;
        }

        .scroll-down.visible {
            opacity: 1;
            transform: translateY(0);
        }

        @media (max-width: 768px) {
            .container {
                height: 100vh;
                border-radius: 0;
            }

            .message {
                max-width: 85%;
            }

            .header {
                padding: 15px;
                flex-direction: column;
            }

            .admin-link {
                margin-top: 10px;
                margin-left: 0;
            }

            h1 {
                font-size: 1.5rem;
            }

            .input-container {
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>Local Messenger</h1>
                <div class="subtitle">End-to-end encrypted communication</div>
            </div>
            <a href="/admin-message" class="admin-link">Последнее сообщение админа</a>
        </div>

        <div class="messages-container" id="messages-container">
            {% if history %}
                {% for msg in history %}
                    <div class="message{% if msg.is_own %} own{% elif msg.admin %} admin{% else %} other{% endif %}">
                        <div class="sender">
                            {% if msg.is_own %}Вы{% elif msg.admin %}Админ{% else %}{{ msg.ip }}{% endif %}
                        </div>
                        <div class="content">{{ msg.message }}</div>
                        <div class="message-footer">
                            <div class="datetime">
                                {{ msg.datetime }}
                            </div>
                        </div>
                    </div>
                {% endfor %}
            {% else %}
                <div class="no-messages">
                    <div>✉️</div>
                    <div style="margin-top: 15px;">Нет сообщений в истории</div>
                    <div style="font-size: 0.9rem; margin-top: 10px; opacity: 0.7;">Начните разговор!</div>
                </div>
            {% endif %}
        </div>

        <div class="input-container">
            <div class="input-area">
                <input type="text" id="message-input" placeholder="Введите ваше сообщение..." autofocus>
                <button id="send-button">➤</button>
            </div>
        </div>

        <div class="scroll-down" id="scroll-down" title="Прокрутить вниз">
            ▼
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const input = document.getElementById('message-input');
            const button = document.getElementById('send-button');
            const messagesContainer = document.getElementById('messages-container');
            const scrollDownBtn = document.getElementById('scroll-down');

            let isAtBottom = true;
            let lastMessageCount = {{ history|length if history else 0 }};
            let updateInterval;
            let currentIP = "{{ current_ip }}";  // IP текущего пользователя

            // Прокрутить вниз при загрузке
            scrollToBottom();

            // Проверка положения скролла
            messagesContainer.addEventListener('scroll', function() {
                const isBottom = messagesContainer.scrollTop + messagesContainer.clientHeight >= messagesContainer.scrollHeight - 50;
                scrollDownBtn.classList.toggle('visible', !isBottom);
                isAtBottom = isBottom;
            });

            // Кнопка прокрутки вниз
            scrollDownBtn.addEventListener('click', scrollToBottom);

            function scrollToBottom() {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                scrollDownBtn.classList.remove('visible');
                isAtBottom = true;
            }

            // Функция для отправки сообщения
            async function sendMessage() {
                const message = input.value.trim();
                if (!message) return;

                button.disabled = true;
                input.disabled = true;

                try {
                    const response = await fetch('/message', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ message })
                    });

                    const data = await response.json();

                    if (data.status === 'success') {
                        input.value = '';
                        // После отправки сразу запрашиваем обновленную историю
                        await checkForNewMessages();
                    } else {
                        console.error("Ошибка отправки:", data.message);
                    }
                } catch (error) {
                    console.error("Ошибка сети:", error);
                } finally {
                    button.disabled = false;
                    input.disabled = false;
                    input.focus();
                }
            }

            // Функция для проверки новых сообщений
            async function checkForNewMessages() {
                try {
                    const response = await fetch('/get-messages');
                    const data = await response.json();

                    if (data.history && data.history.length > lastMessageCount) {
                        // Получаем только новые сообщения
                        const newMessages = data.history.slice(lastMessageCount);

                        const noMessages = document.querySelector('.no-messages');
                        if (noMessages && newMessages.length > 0) {
                            noMessages.remove();
                        }

                        // Добавляем новые сообщения
                        for (const msg of newMessages) {
                            const messageElement = document.createElement('div');

                            // Определяем класс сообщения
                            let msgClass = 'other';
                            if (msg.is_own) msgClass = 'own';
                            else if (msg.admin) msgClass = 'admin';

                            messageElement.className = `message ${msgClass}`;

                            // Определяем отправителя
                            let sender = msg.ip;
                            if (msg.is_own) sender = 'Вы';
                            else if (msg.admin) sender = 'Админ';

                            // Формируем содержимое сообщения
                            let contentHTML = `
                                <div class="sender">${sender}</div>
                                <div class="content">${msg.message}</div>
                            `;

                            // Добавляем IP только для чужих сообщений
                            if (!msg.is_own && !msg.admin) {
                                contentHTML += `<div class="ip-display">IP: ${msg.ip}</div>`;
                            }

                            contentHTML += `
                                <div class="message-footer">
                                    <div class="datetime">${msg.datetime}</div>
                                </div>
                            `;

                            messageElement.innerHTML = contentHTML;
                            messagesContainer.appendChild(messageElement);
                        }

                        // Обновляем счетчик сообщений
                        lastMessageCount = data.history.length;

                        // Прокрутка к новому сообщению, если пользователь внизу
                        if (isAtBottom) {
                            scrollToBottom();
                        }
                    }
                } catch (error) {
                    console.error("Ошибка при проверке новых сообщений:", error);
                }
            }

            // Запускаем периодическую проверку новых сообщений
            updateInterval = setInterval(checkForNewMessages, 1000);

            // Обработчики событий
            button.addEventListener('click', sendMessage);

            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            // Автофокус на поле ввода
            input.focus();

            // Остановка интервала при закрытии страницы
            window.addEventListener('beforeunload', () => {
                clearInterval(updateInterval);
            });
        });
    </script>
</body>
</html>
"""


def save_history():
    """Сохраняет текущую историю в файл"""
    with history_lock:
        history_list = list(message_history)
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history_list, f, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения истории: {e}")


@app.route('/')
def home():
    # Получаем IP текущего пользователя
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    current_ip = client_ip.split(',')[0].strip() if ',' in client_ip else client_ip
    current_ip = current_ip.split(':')[0]  # Убираем порт

    # Помечаем сообщения как "свои" для текущего пользователя
    with history_lock:
        history = []
        for msg in list(message_history):
            # Создаем копию сообщения, чтобы не изменять оригинал
            msg_copy = msg.copy()
            # Сравниваем IP без порта
            msg_ip = msg_copy['ip'].split(':')[0]  # Убираем порт
            msg_copy['is_own'] = (msg_ip == current_ip)
            history.append(msg_copy)

    return render_template_string(HTML_TEMPLATE, history=history, current_ip=current_ip)


@app.route('/message', methods=['POST'])
def handle_message():
    # Получаем IP-адрес клиента
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    clean_ip = client_ip.split(',')[0].strip() if ',' in client_ip else client_ip
    clean_ip = clean_ip.split(':')[0]  # Убираем порт

    # Извлекаем сообщение
    message = None
    json_data = request.get_json(silent=True)
    if json_data and 'message' in json_data:
        message = json_data['message']

    # Логируем сообщение
    if len(message_history) == 0:
        if 'porn' in message:
            message = 'Я тупой даун'
        is_admin = (clean_ip == ADMIN_IP)
        log_message('POST', message, clean_ip, is_admin)
    else:
        if message != message_history[-1]['message']:
            if 'porn' in message:
                message = 'Я тупой даун'
            is_admin = (clean_ip == ADMIN_IP)
            log_message('POST', message, clean_ip, is_admin)

    return jsonify({
        "status": "success",
        "message": "Сообщение получено",
        "your_message": message,
        "ip": clean_ip
    })


@app.route('/get-messages')
def get_messages():
    # Получаем IP текущего пользователя
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    current_ip = client_ip.split(',')[0].strip() if ',' in client_ip else client_ip
    current_ip = current_ip.split(':')[0]  # Убираем порт

    with history_lock:
        history = []
        for msg in list(message_history):
            # Создаем копию сообщения, чтобы не изменять оригинал
            msg_copy = msg.copy()
            # Сравниваем IP без порта
            msg_ip = msg_copy['ip'].split(':')[0]  # Убираем порт
            msg_copy['is_own'] = (msg_ip == current_ip)
            history.append(msg_copy)

    return jsonify(history=history)


@app.route('/admin-message')
def admin_message():
    """Страница с последним сообщением администратора"""
    with history_lock:
        # Ищем последнее сообщение администратора
        admin_messages = [msg for msg in reversed(message_history) if msg.get('admin')]

        if admin_messages:
            last_admin_msg = admin_messages[0]['message']
            return last_admin_msg
        else:
            return "Нет сообщений администратора"


def log_message(method, message, ip, is_admin=False):
    """Логирует сообщение в историю (добавляет в конец)"""
    # Получаем имя хоста по IP (если возможно)
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        ip_display = f"{ip} ({hostname})"
    except:
        ip_display = ip

    now = datetime.now()
    # Формат даты и времени: "дд.мм.гггг чч:мм"
    datetime_str = now.strftime("%d.%m.%Y %H:%M")

    message_data = {
        'datetime': datetime_str,
        'method': method,
        'message': message,
        'ip': ip_display,
        'admin': is_admin
    }

    with history_lock:
        # Добавляем в конец (новые сообщения будут внизу)
        message_history.append(message_data)

    # Сохраняем историю в файл
    save_history()


@app.route('/secret-file')
def download_file():
    # Укажите путь к файлу
    file_path = 'hello.txt'
    # Отправляем файл как вложение (as_attachment=True)
    return send_file(
        file_path,
        as_attachment=True,
        download_name='hello.txt',  # Имя файла при скачивании
        mimetype='text/plain'  # Тип содержимого
    )


if __name__ == '__main__':
    app.run(debug=True, port=80, host='0.0.0.0')
