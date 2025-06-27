import aiohttp
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger
from pydantic import BaseModel, ValidationError, Field

from repository.hackathon_repository import HackathonRepository


class ExternalHackathonDto(BaseModel):
    """DTO для данных хакатона из внешнего API"""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None  # Изменено на description
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    tags: Optional[List[str]] = []
    event_start_date: Optional[str] = None
    event_end_date: Optional[str] = None
    registration_deadline: Optional[str] = None
    parsed_at: Optional[str] = None
    created_at: Optional[str] = None
    
    def parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Парсит строку даты в datetime объект"""
        if not date_str:
            return None
        try:
            # Попробуем разные форматы даты
            formats = [
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%d.%m.%Y",
                "%d/%m/%Y"
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            logger.warning(f"Could not parse date: {date_str}")
            return None
        except Exception as e:
            logger.warning(f"Error parsing date {date_str}: {e}")
            return None


class ApiResponse(BaseModel):
    """DTO для ответа внешнего API"""
    hackathons: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int


class HackathonParserService:
    def __init__(self):
        self.hackathon_repository = HackathonRepository()
        self.external_api_url = "http://85.198.82.236/parser-hackathons/hackathons"
        
    async def fetch_hackathons_from_external_api(self, page: int = 1, per_page: int = 100) -> Dict[str, Any]:
        """
        Получает данные хакатонов из внешнего API с пагинацией
        """
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.external_api_url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched response from external API (page {page}): {len(data.get('hackathons', []))} hackathons")
                        return data
                    else:
                        logger.error(f"Failed to fetch data from external API. Status: {response.status}")
                        return {"hackathons": [], "total": 0, "page": page, "per_page": per_page}
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error while fetching external API: {e}")
            return {"hackathons": [], "total": 0, "page": page, "per_page": per_page}
        except Exception as e:
            logger.error(f"Unexpected error while fetching external API: {e}")
            return {"hackathons": [], "total": 0, "page": page, "per_page": per_page}
    
    async def fetch_all_hackathons(self) -> List[Dict[str, Any]]:
        """
        Получает все хакатоны из внешнего API используя пагинацию
        """
        all_hackathons = []
        page = 1
        per_page = 100
        
        while True:
            response_data = await self.fetch_hackathons_from_external_api(page, per_page)
            hackathons = response_data.get("hackathons", [])
            
            if not hackathons:
                break
                
            all_hackathons.extend(hackathons)
            
            # Если получили меньше чем per_page, значит это последняя страница
            if len(hackathons) < per_page:
                break
                
            page += 1
            
        logger.info(f"Fetched total {len(all_hackathons)} hackathons from all pages")
        return all_hackathons
    
    async def parse_and_save_hackathons(self) -> int:
        """
        Получает данные из внешнего API и сохраняет их в базу данных
        Возвращает количество успешно сохраненных хакатонов
        """
        logger.info("Starting hackathon parsing and saving process")
        
        external_data = await self.fetch_all_hackathons()
        if not external_data:
            logger.warning("No data received from external API")
            return 0
        
        saved_count = 0
        
        for hackathon_data in external_data:
            try:
                # Валидируем данные через Pydantic
                hackathon_dto = ExternalHackathonDto(**hackathon_data)
                
                # Проверяем обязательные поля
                if not hackathon_dto.name:
                    logger.warning(f"Skipping hackathon without name: {hackathon_data}")
                    continue
                
                # Парсим даты
                start_of_hack = hackathon_dto.parse_datetime(hackathon_dto.event_start_date)
                end_of_registration = hackathon_dto.parse_datetime(hackathon_dto.registration_deadline)
                end_of_hack = hackathon_dto.parse_datetime(hackathon_dto.event_end_date)
                
                # Если нет даты начала хакатона, пропускаем
                if not start_of_hack:
                    logger.warning(f"Skipping hackathon without valid start date: {hackathon_dto.name}")
                    continue
                
                # Сохраняем в базу данных
                try:
                    hackathon_id = await self.hackathon_repository.upsert_hackathon(
                        name=hackathon_dto.name,
                        task_description=hackathon_dto.description,
                        end_of_registration=end_of_registration,
                        start_of_hack=start_of_hack,
                        end_of_hack=end_of_hack,
                        amount_money=None,  # Нет в API
                        type=", ".join(hackathon_dto.tags) if hackathon_dto.tags else None,
                        city=None,  # Можно извлечь из тегов если нужно
                        approved=False,  # По умолчанию одобрено
                        url=hackathon_dto.link_url,
                        url_image=hackathon_dto.image_url
                    )
                    
                    logger.info(f"Successfully saved hackathon: {hackathon_dto.name} with ID: {hackathon_id}")
                    saved_count += 1
                    
                except Exception as db_error:
                    logger.error(f"Database error saving hackathon {hackathon_dto.name}: {db_error}")
                    continue
                    
            except ValidationError as ve:
                logger.error(f"Validation error for hackathon data {hackathon_data}: {ve}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing hackathon {hackathon_data}: {e}")
                continue
        
        logger.info(f"Hackathon parsing completed. Saved {saved_count} out of {len(external_data)} hackathons")
        return saved_count 