import aiohttp
import re
from loguru import logger
from typing import Optional, Dict, Any, List


class RecommendationsService:
    """
    Сервис для работы с внешним API рекомендаций ресурсов для подготовки к хакатонам.
    """
    
    def __init__(self):
        self.base_url = "http://85.198.82.236/recommendations-hackathons"
        self.timeout = aiohttp.ClientTimeout(total=10)
    
    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """
        Парсит текстовый ответ API и преобразует в структурированный формат.
        
        Args:
            text: Текстовый ответ от API
            
        Returns:
            Структурированный словарь с ресурсами
        """
        resources = {
            "learning_resources": []
        }
        
        # Находим индекс первой единицы в тексте, чтобы начать парсинг с нумерованного списка
        # Ищем паттерн "1." в начале строки или после переноса строки
        first_item_match = re.search(r'(?:^|\n)\s*1\.', text)
        if first_item_match:
            # Начинаем парсинг с позиции найденной единицы
            text_to_parse = text[first_item_match.start():].strip()
            logger.info(f"Found start of numbered list at position {first_item_match.start()}")
        else:
            # Если не нашли "1.", используем весь текст
            text_to_parse = text
            logger.warning("Could not find start of numbered list (1.), using full text")
        
        # Парсим ресурсы из текста
        # Ищем паттерн: номер. название - URL - описание
        pattern = r'(\d+)\.\s*([^-]+?)\s*;\s*(https?://[^\s]+)\s*;\s*(.+?)(?=\n\d+\.|\Z)'
        matches = re.findall(pattern, text_to_parse, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            number, title, url, description = match
            title = title.strip()
            description = description.strip()
            
            resources["learning_resources"].append({
                "title": title,
                "url": url,
                "description": description
            })
        
        return resources
    
    async def get_preparation_resources(self, hackathon_description: str) -> Optional[Dict[str, Any]]:
        """
        Получить ресурсы для подготовки к хакатону по его описанию.
        
        Args:
            hackathon_description: Описание хакатона
            
        Returns:
            Словарь с ресурсами для подготовки или None в случае ошибки
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Отправляем POST запрос с описанием хакатона в теле
                async with session.post(
                    f"{self.base_url}/recommend",
                    json={"description": hackathon_description},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        # Получаем текстовый ответ
                        text_response = await response.text()
                        logger.info(f"Successfully received text response from recommendations API")
                        
                        # Парсим текстовый ответ в структурированный формат
                        parsed_resources = self._parse_text_response(text_response)
                        return parsed_resources
                    else:
                        logger.error(f"Failed to get preparation resources. Status: {response.status}")
                        return None
                        
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error while getting preparation resources: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while getting preparation resources: {e}")
            return None 