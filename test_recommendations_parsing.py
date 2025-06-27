import re
from services.recommendations_service import RecommendationsService

def test_parse_text_response_with_leading_text():
    """
    Тест парсинга ответа LLM с лишним текстом в начале.
    """
    # Пример ответа с лишним текстом в начале
    text_response = """Here are some resources to help prepare for the Nuclear IT Hack (school edition):

1. Coursera - Machine Learning by Andrew Ng — https://www.coursera.org/specializations/machine-learning — курс по машинному обучению от одного из лучших специалистов в области ИИ.
2. Python for Data Science Handbook — https://jakevdp.github.io/PythonDataScienceHandbook/ — руководство по работе с данными на языке Python, которое поможет в задачах по анализу данных.
3. OpenCV Tutorial — https://docs.opencv.org/master/d9/d61/tutorial_py_kmeans_index.html — туториал по компьютерному зрению с использованием OpenCV, который может помочь в задачах по компьютерному зрению.
4. GitHub - Machine Learning Repository — https://github.com/rushter/machine-learning — репозиторий с примерами кода для задач машинного обучения.
5. Kaggle - Computer Vision Competition — https://www.kaggle.com/c/computer-vision-competition — соревнование по компьютерному зрению на платформе Kaggle, которое поможет набрать опыт в решении задач по компьютерному зрению."""

    # Создаем экземпляр сервиса
    service = RecommendationsService()
    
    # Парсим ответ
    result = service._parse_text_response(text_response)
    
    # Проверяем результат
    print("Результат парсинга:")
    print(f"Количество найденных ресурсов: {len(result['learning_resources'])}")
    
    for i, resource in enumerate(result['learning_resources'], 1):
        print(f"\n{i}. {resource['title']}")
        print(f"   URL: {resource['url']}")
        print(f"   Описание: {resource['description']}")
    
    # Проверяем, что найдено правильное количество ресурсов
    assert len(result['learning_resources']) == 5, f"Expected 5 resources, but found {len(result['learning_resources'])}"
    
    # Проверяем первый ресурс
    first_resource = result['learning_resources'][0]
    assert "Coursera" in first_resource['title']
    assert "coursera.org" in first_resource['url']
    
    print("\n✅ Тест успешно пройден!")

if __name__ == "__main__":
    test_parse_text_response_with_leading_text() 