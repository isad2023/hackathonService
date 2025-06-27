#!/usr/bin/env python3
"""
Скрипт для тестирования API ендпоинта получения ресурсов подготовки к хакатону.
"""

import requests
import json
from uuid import uuid4


def test_preparation_resources_endpoint():
    """Тестирует ендпоинт получения ресурсов для подготовки к хакатону."""
    
    base_url = "http://localhost:8000"
    
    # Тестовый ID хакатона (в реальном случае нужно использовать существующий ID)
    test_hackathon_id = "550e8400-e29b-41d4-a716-446655440000"
    
    # URL ендпоинта
    url = f"{base_url}/hackathons/{test_hackathon_id}/preparation-resources"
    
    print(f"Тестируем ендпоинт: {url}")
    print("-" * 50)
    
    try:
        # Отправляем GET запрос
        response = requests.get(url, timeout=15)
        
        print(f"Статус код: {response.status_code}")
        print(f"Заголовки ответа: {dict(response.headers)}")
        print()
        
        # Парсим JSON ответ
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
            print("Ответ (JSON):")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            
            # Анализируем ответ
            if response.status_code == 200:
                if data.get("resources"):
                    print("\n✅ Успешно получены ресурсы для подготовки!")
                    resources = data["resources"]
                    
                    if "recommended_technologies" in resources:
                        print(f"Рекомендуемые технологии: {resources['recommended_technologies']}")
                    
                    if "preparation_timeline" in resources:
                        print(f"Время подготовки: {resources['preparation_timeline']}")
                        
                    if "difficulty_level" in resources:
                        print(f"Уровень сложности: {resources['difficulty_level']}")
                        
                elif data.get("error_message"):
                    print(f"\n⚠️  Ошибка получения ресурсов: {data['error_message']}")
                else:
                    print("\n❓ Неожиданный формат ответа")
                    
            elif response.status_code == 404:
                print(f"\n❌ Хакатон не найден: {data.get('detail', 'Неизвестная ошибка')}")
            else:
                print(f"\n❌ Ошибка сервера: {data.get('detail', 'Неизвестная ошибка')}")
        else:
            print("Ответ (текст):")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения. Убедитесь, что сервер запущен на localhost:8000")
    except requests.exceptions.Timeout:
        print("❌ Таймаут запроса. Сервер не отвечает.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
    except json.JSONDecodeError:
        print("❌ Ошибка парсинга JSON ответа")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")


def test_with_random_id():
    """Тестирует ендпоинт с случайным ID (должен вернуть 404)."""
    
    base_url = "http://localhost:8000"
    random_id = str(uuid4())
    url = f"{base_url}/hackathons/{random_id}/preparation-resources"
    
    print(f"\nТестируем с несуществующим ID: {random_id}")
    print("-" * 50)
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Статус код: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ Корректно возвращается 404 для несуществующего хакатона")
        else:
            print(f"⚠️  Неожиданный статус код: {response.status_code}")
            
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
            print(f"Сообщение: {data.get('detail', 'Нет сообщения')}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    print("🚀 Тестирование API ендпоинта получения ресурсов подготовки к хакатону")
    print("=" * 70)
    
    # Основной тест
    test_preparation_resources_endpoint()
    
    # Тест с несуществующим ID
    test_with_random_id()
    
    print("\n" + "=" * 70)
    print("Тестирование завершено!") 