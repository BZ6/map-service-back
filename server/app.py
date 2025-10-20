from flask import Flask, request, jsonify
from typing import Dict, Any
from mock_users import MOCK_USERS 
from flask_cors import CORS


app = Flask(__name__)

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://51.250.73.226:8000", "http://localhost:8000", "http://127.0.0.1:8000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.route('/api/example')
def example():
  return jsonify(message='Hello from Flask!')

@app.route('/api/register', methods=['POST'])
def register():
    # Получаем данные из запроса
    data: Dict[str, Any] = request.get_json()
    
    # Проверяем обязательные поля (просто для примера, в реальном приложении нужна валидация)
    required_fields = ['name', 'lastName', 'login', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # В реальном приложении здесь была бы обработка регистрации
    # (хеширование пароля, сохранение в БД и т.д.)
    
    # Возвращаем те же данные + статус успешной регистрации
    response_data = {
        'status': 'success',
        'user': {
            'name': data['name'],
            'lastName': data['lastName'],
            'login': data['login']
        }
    }
    return jsonify(response_data), 200

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    if not all(field in data for field in ['login', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    login = data['login']
    password = data['password']

    if login not in MOCK_USERS:
        return jsonify({
            'status': 'error',
            'message': 'Пользователь с таким логином не найден'
        }), 404
    
    user = MOCK_USERS[login]
    
    if password != user['password']:
        return jsonify({
            'status': 'error',
            'message': 'Неверный пароль'
        }), 401
    # В реальном приложении здесь была бы проверка учетных данных
    # (поиск пользователя, проверка пароля и т.д.)
    
    # Возвращаем те же данные + токен (в реальном приложении)
   
    return jsonify({
        'status': 'success',
        'user': {
            'name': user['name'],
            'lastName': user['lastName'],
            'login': user['login']
        },
        'token': 'dummy_token_for_example'
    }), 200

@app.route('/api/emailConfirm', methods=['POST'])
def email_confirm():
    
    data: Dict[str, Any] = request.get_json()

    required_fields = ['code']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    response_data = {
        'status': 'success',
        'code': data['code'],
    }
    return jsonify(response_data), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)