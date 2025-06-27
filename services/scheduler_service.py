import asyncio
from aiocron import crontab
from loguru import logger

from services.hackathon_parser_service import HackathonParserService


class SchedulerService:
    def __init__(self):
        self.hackathon_parser_service = HackathonParserService()
        self.is_running = False
        
    async def start_scheduler(self):
        """
        Запускает планировщик задач
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
            
        self.is_running = True
        logger.info("Starting scheduler service")
        
        # Запускаем задачу каждые 30 минут (*/30 * * * *)
        @crontab('*/30 * * * *', start=True)
        async def scheduled_hackathon_parsing():
            logger.info("Starting scheduled hackathon parsing")
            try:
                saved_count = await self.hackathon_parser_service.parse_and_save_hackathons()
                logger.info(f"Scheduled hackathon parsing completed. Saved {saved_count} hackathons")
            except Exception as e:
                logger.error(f"Error during scheduled hackathon parsing: {e}")
        
        logger.info("Scheduler started successfully. Hackathon parsing will run every 30 minutes")
        
        # Запускаем первый раз сразу при старте
        try:
            logger.info("Running initial hackathon parsing")
            saved_count = await self.hackathon_parser_service.parse_and_save_hackathons()
            logger.info(f"Initial hackathon parsing completed. Saved {saved_count} hackathons")
        except Exception as e:
            logger.error(f"Error during initial hackathon parsing: {e}")
    
    async def stop_scheduler(self):
        """
        Останавливает планировщик задач
        """
        self.is_running = False
        logger.info("Scheduler service stopped")
    
    async def manual_parse_hackathons(self) -> int:
        """
        Ручной запуск парсинга хакатонов
        """
        logger.info("Manual hackathon parsing requested")
        try:
            saved_count = await self.hackathon_parser_service.parse_and_save_hackathons()
            logger.info(f"Manual hackathon parsing completed. Saved {saved_count} hackathons")
            return saved_count
        except Exception as e:
            logger.error(f"Error during manual hackathon parsing: {e}")
            raise 