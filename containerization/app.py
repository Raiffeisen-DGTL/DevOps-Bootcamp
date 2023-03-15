from flask import Flask, render_template, request, jsonify
import os
import redis
import requests

app = Flask(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def process_request():
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        r.incr("count")
    except redis.exceptions.ConnectionError:
        return jsonify({"error": "Не удалось подключиться к Redis."}), 500

    container_env = os.getenv("CONTAINERENV")
    if container_env is None or container_env.lower() != "true":
        return jsonify({"error": "Переменная CONTAINERENV не задана или имеет неправильное значение."}), 500

    mail_filename = "mail.txt"
    name_filename = "name.txt"

    try:
        with open(mail_filename, "r") as mail_file:
            mail_content = mail_file.read().strip()

        with open(name_filename, "r") as name_file:
            name_content = name_file.read().strip()

        if not mail_content or not name_content:
            raise Exception("Пустой файл")

    except Exception as e:
        return jsonify({"error": f"Ошибка при чтении файлов: {str(e)}"}), 500
    json_data = {"email": mail_content, "name": name_content}

    try:
        response = requests.post("https://functions.yandexcloud.net/d4e7uq330vnrmbdqgtek", json=json_data)
        if response.status_code != 200:
            return jsonify({"error": f"Ошибка при отправке данных на сервер. Код ответа: {response.status_code}"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Ошибка при отправке данных на сервер: {str(e)}"}), 500

    return jsonify({"success": "Данные успешно обработаны и отправлены на сервер."})


app.run(host="0.0.0.0", port=5000)
