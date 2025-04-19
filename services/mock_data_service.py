from datetime import datetime, timedelta
from uuid import uuid4
from loguru import logger
from typing import Optional, List, Dict
from random import choice, randint, sample

from services.hacker_service import HackerService
from services.role_service import RoleService
from services.team_service import TeamService
from services.hackathon_service import HackathonService
from services.winner_solution_service import WinnerSolutionService
from persistent.db.role import RoleEnum


class MockDataService:
    def __init__(self):
        self.role_service = RoleService()
        self.hacker_service = HackerService()
        self.team_service = TeamService()
        self.hackathon_service = HackathonService()
        self.winner_solution_service = WinnerSolutionService()

    async def initialize_mock_data(self):
        """
        Инициализирует тестовые данные в базе данных.
        """
        # Проверяем, нужно ли инициализировать данные
        roles = await self.role_service.get_all_roles()
        if len(roles) > 0:
            logger.info("Mock data already initialized, skipping...")
            return

        logger.info("Initializing mock data...")
        
        # Инициализация ролей
        logger.info("Initializing roles...")
        await self.role_service.init_roles()
        roles = await self.role_service.get_all_roles()
        if not roles:
            logger.error("Failed to initialize roles")
            return
        logger.info(f"Roles initialized: {len(roles)} roles created")
        
        # Логируем созданные роли
        for role in roles:
            logger.info(f"Role: {role.name}")

        # Создаем множество хакеров с разными ролями
        hackers = []
        hacker_names = [
            "John Doe", "Jane Smith", "Alex Johnson", "Maria Garcia", 
            "Wei Chen", "Aisha Patel", "Carlos Rodriguez", "Olga Ivanova",
            "Hiroshi Tanaka", "Fatima Ahmed", "Dmitry Petrov", "Sarah Wilson",
            "Mohammed Ali", "Emma Brown", "Raj Kumar", "Sophia Martinez",
            "Yuki Yamamoto", "Kwame Osei", "Natasha Romanov", "Miguel Hernandez"
        ]
        
        logger.info("Creating multiple hackers with various roles...")
        for name in hacker_names:
            user_id = uuid4()
            hacker_id = await self.hacker_service.upsert_hacker(user_id, name)
            if hacker_id:
                hackers.append(hacker_id)
                logger.info(f"Hacker created: {name} with ID: {hacker_id}")
                
                # Назначаем случайные роли каждому хакеру
                role_count = randint(1, 3)  # От 1 до 3 ролей на хакера
                role_names = sample([r.name for r in roles], role_count)
                role_ids = [role.id for role in roles if role.name in role_names]
                
                if role_ids:
                    success = await self.hacker_service.update_hacker_roles(hacker_id, role_ids)
                    if success:
                        logger.info(f"Added roles to {name}: {role_names}")
                    else:
                        logger.error(f"Failed to add roles to {name}")
            else:
                logger.error(f"Failed to create hacker: {name}")
        
        if not hackers:
            logger.error("Failed to create any hackers, aborting mock data initialization")
            return
        
        # Создаем несколько команд с разными участниками
        teams = []
        team_names = [
            "Elite Hackers", "Code Wizards", "Binary Bandits", "Syntax Savants",
            "Algorithm Aces", "Data Dynamos", "Quantum Coders", "Pixel Pirates",
            "Neural Ninjas", "Cloud Crusaders"
        ]
        
        logger.info("Creating multiple teams...")
        for team_name in team_names:
            # Выбираем случайного владельца команды
            owner_id = choice(hackers)
            max_size = randint(3, 7)
            
            try:
                team_id, status = await self.team_service.create_team(
                    owner_id=owner_id, 
                    name=team_name, 
                    max_size=max_size
                )
                
                if status > 0:
                    teams.append(team_id)
                    logger.info(f"Team '{team_name}' created with ID: {team_id}, owner: {owner_id}")
                    
                    # Добавляем случайных участников в команду
                    team_size = randint(2, max_size)
                    potential_members = [h for h in hackers if h != owner_id]
                    if potential_members and team_size > 1:
                        members_to_add = sample(potential_members, min(team_size-1, len(potential_members)))
                        for member_id in members_to_add:
                            result, code = await self.team_service.add_hacker_to_team(team_id, member_id)
                            if code > 0:
                                logger.info(f"Added hacker {member_id} to team {team_name}")
                            else:
                                logger.warning(f"Failed to add hacker {member_id} to team {team_name}, code: {code}")
                else:
                    logger.error(f"Error creating team '{team_name}', status: {status}")
            except Exception as e:
                logger.error(f"Error creating team '{team_name}': {str(e)}")
        
        if not teams:
            logger.error("Failed to create any teams, continuing with limited mock data")
        
        # Создаем несколько хакатонов с разными параметрами
        hackathons = []
        hackathon_data = [
            {
                "name": "Global Hackathon 2024",
                "task_description": "Solve real-world problems with innovative solutions.",
                "start_date": "2024-01-01",
                "duration_days": 21,
                "amount_money": 10000.0,
                "type": "offline",
                "city": "Moscow",
                "approved": True,
            },
            {
                "name": "AI Revolution Challenge",
                "task_description": "Create AI solutions for healthcare challenges.",
                "start_date": "2024-02-15",
                "duration_days": 14,
                "amount_money": 15000.0,
                "type": "online",
                "city": "Novosibirsk",
                "approved": False,
            },
            {
                "name": "Sustainable Tech Hackathon",
                "task_description": "Develop technologies to address climate change.",
                "start_date": "2024-03-10",
                "duration_days": 30,
                "amount_money": 20000.0,
                "type": "hybrid",
                "city": "",
                "approved": True,
            },
            {
                "name": "Fintech Innovation Cup",
                "task_description": "Revolutionize financial services with cutting-edge technology.",
                "start_date": "2024-04-05",
                "duration_days": 10,
                "amount_money": 12500.0,
                "type": "online",
                "city": "Moscow",
                "approved": False,
            },
            {
                "name": "Smart Cities Hackathon",
                "task_description": "Build solutions for the cities of tomorrow.",
                "start_date": "2024-05-20",
                "duration_days": 15,
                "amount_money": 18000.0,
                "type": "offline",
                "city": "New-York",
                "approved": True,
            }
        ]

        logger.info("Creating multiple hackathons...")
        for hack_data in hackathon_data:
            start_date = datetime.strptime(hack_data["start_date"], "%Y-%m-%d")
            duration = hack_data["duration_days"]
            
            # Расчет дат для хакатона
            start_of_registration = start_date
            end_of_registration = start_date + timedelta(days=duration//3)
            start_of_hack = end_of_registration + timedelta(days=2)
            end_of_hack = start_of_hack + timedelta(days=duration//2)
            
            try:
                hackathon_id = await self.hackathon_service.upsert_hackathon(
                    name=hack_data["name"],
                    task_description=hack_data["task_description"],
                    start_of_registration=start_of_registration,
                    end_of_registration=end_of_registration,
                    start_of_hack=start_of_hack,
                    end_of_hack=end_of_hack,
                    amount_money=hack_data["amount_money"],
                    type=hack_data["type"],
                    city=hack_data["city"],
                    approved=hack_data["approved"],
                )
                
                if hackathon_id:
                    hackathons.append(hackathon_id)
                    logger.info(f"Hackathon '{hack_data['name']}' created with ID: {hackathon_id}")
                else:
                    logger.error(f"Failed to create hackathon '{hack_data['name']}'")
            except Exception as e:
                logger.error(f"Error creating hackathon '{hack_data['name']}': {str(e)}")
        
        if not hackathons:
            logger.error("Failed to create any hackathons, skipping winner solution creation")
            return
        
        # Создаем решения хакатонов для разных команд
        logger.info("Creating winner solutions for teams in hackathons...")
        for i, hackathon_id in enumerate(hackathons):
            # Выбираем случайные команды-победители для каждого хакатона
            if teams:
                winners_count = min(3, len(teams))  # До 3 победителей на хакатон
                winning_teams = sample(teams, winners_count)
                
                for place, team_id in enumerate(winning_teams, 1):
                    link_to_solution = f"https://github.com/team{team_id}/solution{hackathon_id}"
                    link_to_presentation = f"https://slides.com/team{team_id}/presentation{hackathon_id}"
                    win_money = float(hackathon_data[i % len(hackathon_data)]["amount_money"]) / place  # Призовые уменьшаются с местом
                    can_share = place == 1  # Только первое место может делиться решением
                    
                    try:
                        solution_id, success = await self.winner_solution_service.create_winner_solution(
                            hackathon_id=hackathon_id,
                            team_id=team_id,
                            win_money=win_money,
                            link_to_solution=link_to_solution,
                            link_to_presentation=link_to_presentation,
                            can_share=can_share,
                        )
                        
                        if success and solution_id:
                            logger.info(f"Winner solution created for team {team_id} in hackathon {hackathon_id}, place: {place}")
                        else:
                            logger.error(f"Failed to create winner solution for team {team_id} in hackathon {hackathon_id}")
                    except Exception as e:
                        logger.error(f"Error creating winner solution: {str(e)}")
        
        logger.info("Mock data initialization completed with multiple entities and relationships!")