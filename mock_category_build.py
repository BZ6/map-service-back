# TODO заменить на sql запрос: SELECT DISTINCT(category) from builds
from bd_models import Build

CATEGORIES: list[str] = [
        'cafe',
        'bar',
        'museum',
        'restaurant',
        'school',
    ]

BUILDS_BY_CATEGORY: list[dict] = [
        {'id': 1, 'name': 'Test cafe 1', 'category': 'cafe'},
        {'id': 2, 'name': 'Test cafe 2', 'category': 'cafe'},
        {'id': 3, 'name': 'Test cafe 3', 'category': 'cafe'},
        {'id': 4, 'name': 'Test cafe 4', 'category': 'cafe'},
        {'id': 5, 'name': 'Test bar 1', 'category': 'bar'},
        {'id': 6, 'name': 'Test bar 2', 'category': 'bar'},
        {'id': 7, 'name': 'Test bar 3', 'category': 'bar'},
        {'id': 8, 'name': 'Test museum 1', 'category': 'museum'},
        {'id': 9, 'name': 'Test museum 2', 'category': 'museum'},
        {'id': 10, 'name': 'Test school 1', 'category': 'school'},
]
