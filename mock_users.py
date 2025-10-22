# mock_users.py
from typing import Dict

MOCK_USERS: Dict[str, Dict] = {
	"user1@example.com": {
		"name": "Иван",
		"lastName": "Иванов",
		"login": "user1@example.com",
		"password": "user"
	},
	"val.osipova@gmail.com": {
		"name": "Валерия",
		"lastName": "Осипова",
		"login": "val.osipova@gmail.com",
		"password": "1234"
	}
}