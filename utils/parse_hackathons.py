#!/usr/bin/env python3
import re
import os
import json
import time
import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


def parse_date(date_str):
    """
    Parse date string in Russian format to datetime object
    Returns None if parsing fails
    """
    if not date_str:
        return None
        
    try:
        # Try to extract dates like "с 20 декабря 2024 по 15 января 2025"
        if "по" in date_str:
            parts = re.search(r'с\s+(\d+\s+\w+\s+\d{4})\s+по\s+(\d+\s+\w+\s+\d{4})', date_str)
            if parts:
                return parts.group(1), parts.group(2)
            
            # Another common pattern "с 10 по 15 мая 2025"
            parts = re.search(r'с\s+(\d+)\s+по\s+(\d+)\s+(\w+)\s+(\d{4})', date_str)
            if parts:
                day1, day2, month, year = parts.groups()
                return f"{day1} {month} {year}", f"{day2} {month} {year}"
        
        # Registration until date pattern "до 15 мая 2025"
        reg_until = re.search(r'(?:до|по)\s+(\d+\s+\w+\s+\d{4})', date_str)
        if reg_until:
            return None, reg_until.group(1)
        
        # Simple date
        date_match = re.search(r'(\d+\s+\w+\s+\d{4})', date_str)
        if date_match:
            return date_match.group(1), None
        
        return None, None
    except Exception:
        return None, None


def extract_money(text):
    """
    Extract prize amount from text
    """
    if not text:
        return None
        
    try:
        # Look for patterns like "1 000 000 рублей" or "500 000 ₽" or "1,5 млн рублей"
        money_match = re.search(r'(\d[\s\d]*[\d,.]+)\s*(млн|тыс)?.{0,5}(руб|₽|рубл)', text, re.IGNORECASE)
        if money_match:
            amount_str = money_match.group(1).replace(' ', '').replace(',', '.')
            multiplier = 1000000 if money_match.group(2) and 'млн' in money_match.group(2).lower() else 1000 if money_match.group(2) and 'тыс' in money_match.group(2).lower() else 1
            try:
                return float(amount_str) * multiplier
            except ValueError:
                return None
        return None
    except Exception:
        return None


def detect_hackathon_type(text):
    """
    Detect if the hackathon is online or offline based on the description
    """
    if not text:
        return None
        
    if re.search(r'\bонлайн\b|\bonline\b', text, re.IGNORECASE):
        return "online"
    elif re.search(r'\bоффлайн\b|\boffline\b|\bочн', text, re.IGNORECASE):
        return "offline"
    return None


def fetch_page_content(url):
    """
    Fetch content from a given URL
    Returns HTML content as string or None if failed
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def parse_hackathon_details(url, basic_info):
    """
    Parse detailed information from the hackathon's page
    Returns updated hackathon dictionary
    """
    hackathon = basic_info.copy()
    
    # Skip if URL is not valid or is a relative URL without domain
    if not url or not (url.startswith('http') or url.startswith('https')):
        return hackathon
    
    print(f"Fetching details for: {hackathon['name']} from {url}")
    html_content = fetch_page_content(url)
    
    if not html_content:
        return hackathon
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Common Russian month names for date pattern matching
    months = r'(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)'
    
    # Find the main content area, typically the body with header and footer excluded
    main_content_div = None
    
    # Look for elements that might contain the main content
    for div in soup.find_all('div', class_=lambda c: c and ('content' in c.lower() or 'article' in c.lower() or 'post' in c.lower())):
        if len(div.get_text(strip=True)) > 500:  # Content should be substantial
            main_content_div = div
            break
    
    # If we found a good content div, extract the description from it
    if main_content_div:
        # Try to find the real description text
        description = ""
        
        # Look for paragraphs with substantial text
        paragraphs = main_content_div.find_all(['p', 'div'], class_=lambda c: c and ('text' in str(c).lower() or 'descr' in str(c).lower()))
        if paragraphs:
            for p in paragraphs:
                p_text = p.get_text(strip=True)
                if len(p_text) > 100:  # Only include substantial paragraphs
                    description += p_text + " "
        
        # If we couldn't find good paragraphs, use the whole div but remove common navigation/footer text
        if not description and main_content_div:
            description = main_content_div.get_text(strip=True)
            
            # Remove common navigation and footer elements by pattern
            description = re.sub(r'Хакатоны\.рус.*?мир хакатонов!', '', description)
            description = re.sub(r'Регистрация открыта', '', description)
            description = re.sub(r'Подписаться|Подписывайся', '', description)
            description = re.sub(r'.*Исследования 202[0-9]', '', description)
            description = re.sub(r'АО «Инновационные интеграторы».*', '', description)
            
            # Also try to remove any text that might be date headings or categories
            description = re.sub(r'online|offline', '', description)
            
        # Limit description length and format
        if description:
            # Trim to reasonable length
            if len(description) > 1000:
                description = description[:1000] + "..."
            
            # Collapse multiple spaces
            description = re.sub(r'\s+', ' ', description).strip()
            
            # Update the hackathon description
            hackathon['task_description'] = description
    
    # PRIORITY 1: Look specifically for divs containing the exact phrases
    
    # 1. First look for "регистрация до" in divs for end_of_registration
    registration_divs = []
    for div in soup.find_all(['div', 'span', 'p', 'li']):
        div_text = div.get_text(strip=True).lower()  # Convert to lowercase for better matching
        if 'регистрация до' in div_text:
            registration_divs.append(div)
    
    # Process registration divs if found
    if registration_divs:
        for div in registration_divs:
            div_text = div.get_text(strip=True)
            # Extract the date following "регистрация до"
            match = re.search(r'регистрация\s+до\s+(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4})', div_text, re.IGNORECASE)
            if match and "Исследования" not in match.group(1) and "подпис" not in match.group(1).lower():
                hackathon['end_of_registration'] = match.group(1)
                break  # Found what we need, stop looking
            
            # Try another common format: "Регистрация до 12 апреля:" or similar
            match = re.search(r'регистрация\s+до\s+(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря))', div_text, re.IGNORECASE)
            if match and "Исследования" not in match.group(1) and "подпис" not in match.group(1).lower():
                # If year is missing, try to derive from the page or default to current year
                date_str = match.group(1)
                
                # Try to find a year in nearby text
                year_match = re.search(r'\b(202\d|203\d)\b', div_text)
                if year_match:
                    year = year_match.group(1)
                else:
                    # Check if there's a year in the hackathon name or try to infer from context
                    name_year_match = re.search(r'202\d|203\d', hackathon['name'])
                    if name_year_match:
                        year = name_year_match.group(0)
                    else:
                        # Default to current year + 1 as these are likely future events
                        current_year = datetime.datetime.now().year + 1
                        year = str(current_year)
                
                date_str += f" {year}"
                
                hackathon['end_of_registration'] = date_str
                break
    
    # 2. Look for "дата проведения" in divs for start_of_hack and end_of_hack
    event_date_divs = []
    for div in soup.find_all(['div', 'span', 'p', 'li']):
        div_text = div.get_text(strip=True).lower()  # Convert to lowercase for better matching
        if 'дата проведения' in div_text:
            event_date_divs.append(div)
    
    # Process event date divs if found
    if event_date_divs:
        for div in event_date_divs:
            div_text = div.get_text(strip=True)
            
            # Try multiple patterns for date ranges
            # Pattern 1: "дата проведения: 15-17 мая 2025"
            match = re.search(rf'дата\s+проведения[^:]*:\s*(\d{{1,2}})\s*[-—–]\s*(\d{{1,2}})\s+({months})\s+(\d{{4}})', div_text, re.IGNORECASE)
            if match:
                day1, day2, month, year = match.groups()
                hackathon['start_of_hack'] = f"{day1} {month} {year}"
                hackathon['end_of_hack'] = f"{day2} {month} {year}"
                break
                
            # Pattern 2: "дата проведения: с 15 мая по 17 мая 2025"
            match = re.search(rf'дата\s+проведения[^:]*:\s*с\s+(\d{{1,2}}\s+{months})\s+по\s+(\d{{1,2}}\s+{months}\s+\d{{4}})', div_text, re.IGNORECASE)
            if match:
                start_date = match.group(1)
                end_date = match.group(2)
                
                # Extract year from end date and add to start date
                year_match = re.search(r'(\d{4})', end_date)
                if year_match:
                    year = year_match.group(1)
                    hackathon['start_of_hack'] = f"{start_date} {year}"
                    hackathon['end_of_hack'] = end_date
                    break
            
            # Pattern 3: "дата проведения: с 15 мая 2025 по 17 июня 2025"
            match = re.search(rf'дата\s+проведения[^:]*:\s*с\s+(\d{{1,2}}\s+{months}\s+\d{{4}})\s+по\s+(\d{{1,2}}\s+{months}\s+\d{{4}})', div_text, re.IGNORECASE)
            if match:
                hackathon['start_of_hack'] = match.group(1)
                hackathon['end_of_hack'] = match.group(2)
                break
                
            # Pattern 4: "дата проведения: 15 мая 2025"
            match = re.search(rf'дата\s+проведения[^:]*:\s*(\d{{1,2}}\s+{months}\s+\d{{4}})', div_text, re.IGNORECASE)
            if match:
                hackathon['start_of_hack'] = match.group(1)
                break
                
            # Pattern 5: "дата проведения: 19 апреля, 10:00-21:00"
            match = re.search(rf'дата\s+проведения[^:]*:\s*(\d{{1,2}}\s+{months})(?:,|\s+)(?:\d{{1,2}}:\d{{2}}-\d{{1,2}}:\d{{2}})', div_text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                
                # Try to find a year in nearby text or default to current year + 1
                year_match = re.search(r'\b(202\d|203\d)\b', div_text)
                if year_match:
                    date_str += " " + year_match.group(1)
                else:
                    # Default to current year + 1 as these are likely future events
                    current_year = datetime.datetime.now().year + 1
                    date_str += f" {current_year}"
                
                hackathon['start_of_hack'] = date_str
                break
    
    # FALLBACK APPROACH: If specific divs weren't found or didn't contain dates, 
    # use the previous strategies with improved focus
    
    # Extract all text from the page for pattern matching
    all_text = soup.get_text(" ", strip=True)
    
    # 1. If we still don't have registration date, look for it in the whole text
    if not hackathon['end_of_registration']:
        # Look specifically for "регистрация до" pattern
        reg_match = re.search(rf'регистрация\s+до\s+(\d{{1,2}}\s+{months}\s+\d{{4}})', all_text, re.IGNORECASE)
        if reg_match:
            reg_date = reg_match.group(1)
            if "Исследования" not in reg_date and "подпис" not in reg_date.lower():
                # Check if the extracted year matches the expected year (from hackathon name or context)
                expected_year = None
                name_year_match = re.search(r'202\d|203\d', hackathon['name'])
                if name_year_match:
                    expected_year = name_year_match.group(0)
                
                if expected_year:
                    # Extract year from the date
                    year_in_date = re.search(r'\b(202\d|203\d)\b', reg_date)
                    if year_in_date and year_in_date.group(1) != expected_year:
                        # Replace the year with the expected year from the hackathon name
                        reg_date = re.sub(r'\b(202\d|203\d)\b', expected_year, reg_date)
                
                hackathon['end_of_registration'] = reg_date
        
        # Try other registration deadline patterns
        if not hackathon['end_of_registration']:
            reg_patterns = [
                rf'(?:заявки|заявку|заявок)\s+(?:принимаются|подавать|подать)(?:[^.]*?)до\s+(\d{{1,2}}\s+{months}\s+\d{{4}})',
                rf'(?:дедлайн|окончание)\s+(?:регистрации|подачи заявок)[^:]*?:\s*(\d{{1,2}}\s+{months}\s+\d{{4}})',
                rf'(?:окончание|завершение).*?(?:регистрац[а-я]+|заявк[а-я]+).*?(\d{{1,2}}\s+{months}\s+\d{{4}})'
            ]
            
            for pattern in reg_patterns:
                reg_match = re.search(pattern, all_text, re.IGNORECASE)
                if reg_match and "Исследования" not in reg_match.group(1) and "подпис" not in reg_match.group(1).lower():
                    hackathon['end_of_registration'] = reg_match.group(1)
                    break
    
    # 2. If we still don't have event dates, look for "дата проведения" in the whole text
    if not hackathon['start_of_hack']:
        # Look for "дата проведения" with date range
        event_match = re.search(rf'дата\s+проведения[^:]*:\s*(?:с\s+)?(\d{{1,2}}\s+{months}\s+\d{{4}})(?:\s*[-—–]\s*|\s+по\s+)(\d{{1,2}}\s+{months}\s+\d{{4}})', all_text, re.IGNORECASE)
        if event_match:
            hackathon['start_of_hack'] = event_match.group(1)
            hackathon['end_of_hack'] = event_match.group(2)
        else:
            # Look for "дата проведения" with just start date
            event_match = re.search(rf'дата\s+проведения[^:]*:\s*(\d{{1,2}}\s+{months}\s+\d{{4}})', all_text, re.IGNORECASE)
            if event_match:
                hackathon['start_of_hack'] = event_match.group(1)
    
    # 3. If still no event dates, try other common patterns
    if not hackathon['start_of_hack']:
        # Look for text indicating the event period in various formats
        date_patterns = [
            rf'(?:мероприятие|хакатон|соревнование)\s+(?:пройдет|состоится)\s+(\d{{1,2}}[-—–]\d{{1,2}}\s+{months}\s+\d{{4}})',
            rf'(?:мероприятие|хакатон|соревнование)\s+(?:пройдет|состоится)\s+(\d{{1,2}}\s+{months}\s+\d{{4}})',
            rf'(?:с|c)\s+(\d{{1,2}}\s+{months})\s+(?:по|до)\s+(\d{{1,2}}\s+{months}\s+\d{{4}})',
            rf'(\d{{1,2}})\s*[-—–]\s*(\d{{1,2}})\s+({months})\s+(\d{{4}})'  # Format like "21-23 июня 2025"
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, all_text, re.IGNORECASE)
            if date_match:
                # Validate the match is not from navigation/footer
                if "Исследования" in date_match.group(0) or "подпис" in date_match.group(0).lower():
                    continue
                
                groups = date_match.groups()
                
                # Handle the different pattern matches based on the number of captured groups
                if len(groups) == 1:
                    # Could be a range like "15-17 мая 2025" or a single date
                    if '-' in groups[0]:
                        date_parts = groups[0].split('-')
                        if len(date_parts) == 2:
                            day1 = date_parts[0].strip()
                            rest = date_parts[1].strip()
                            if re.match(rf'\d+\s+{months}\s+\d{{4}}', rest):
                                # It's a format like "15-17 мая 2025"
                                day2, month_year = rest.split(' ', 1)
                                hackathon['start_of_hack'] = f"{day1} {month_year}"
                                hackathon['end_of_hack'] = rest
                    else:
                        # Single date
                        hackathon['start_of_hack'] = groups[0]
                
                elif len(groups) == 2 and 'по' in date_match.group(0):
                    # Format with start and end dates or partial dates
                    start_date = groups[0]
                    end_date = groups[1]
                    
                    # Check if the start date has a year
                    if not re.search(r'\d{4}', start_date) and re.search(r'\d{4}', end_date):
                        # Extract year from end date to add to start date
                        year_match = re.search(r'(\d{4})', end_date)
                        if year_match:
                            year = year_match.group(1)
                            hackathon['start_of_hack'] = f"{start_date} {year}"
                            hackathon['end_of_hack'] = end_date
                    else:
                        # Both dates are complete
                        hackathon['start_of_hack'] = start_date
                        hackathon['end_of_hack'] = end_date
                
                elif len(groups) == 4:
                    # Format like "21-23 июня 2025"
                    day1, day2, month, year = groups
                    hackathon['start_of_hack'] = f"{day1} {month} {year}"
                    hackathon['end_of_hack'] = f"{day2} {month} {year}"
                
                break  # Found a valid date pattern, stop searching
    
    # Check for event dates in the description patterns like "Соревнование проходит с 21 мая по 30 июня 2025"
    # или "Хакатон пройдёт с2 по 4 мая 2025 года"
    if (not hackathon['start_of_hack'] or not hackathon['end_of_hack']) and hackathon['task_description']:
        desc_text = hackathon['task_description']
        
        # Паттерн "пройдёт с2 по 4 мая 2025 года"
        date_match = re.search(rf'пройд[её]т\s+с\s*(\d{{1,2}})\s+по\s+(\d{{1,2}})\s+({months})\s+(\d{{4}})', desc_text, re.IGNORECASE)
        if date_match:
            day1, day2, month, year = date_match.groups()
            hackathon['start_of_hack'] = f"{day1} {month} {year}"
            hackathon['end_of_hack'] = f"{day2} {month} {year}"
        else:
            # Паттерн "проходит|пройдет|состоится с 21 мая по 30 июня 2025"
            date_match = re.search(rf'(?:проходит|пройдет|состоится)\s+с\s+(\d{{1,2}}\s+{months}(?:\s+\d{{4}})?)\s+(?:по|до)\s+(\d{{1,2}}\s+{months}\s+\d{{4}})', desc_text, re.IGNORECASE)
            if date_match:
                start_date = date_match.group(1)
                end_date = date_match.group(2)
                
                # Add year to start date if missing
                if not re.search(r'\d{4}', start_date):
                    year_match = re.search(r'(\d{4})', end_date)
                    if year_match:
                        hackathon['start_of_hack'] = f"{start_date} {year_match.group(1)}"
                        hackathon['end_of_hack'] = end_date
                else:
                    hackathon['start_of_hack'] = start_date
                    hackathon['end_of_hack'] = end_date
        
        # Try pattern for date range in description
        if not hackathon['start_of_hack'] and not hackathon['end_of_hack']:
            date_match = re.search(rf'(\d{{1,2}})\s*[-—–]\s*(\d{{1,2}})\s+({months})\s+(\d{{4}})', desc_text, re.IGNORECASE)
            if date_match:
                day1, day2, month, year = date_match.groups()
                hackathon['start_of_hack'] = f"{day1} {month} {year}"
                hackathon['end_of_hack'] = f"{day2} {month} {year}"
    
    # Look for any dates as a last resort
    if not hackathon['start_of_hack'] and not hackathon['end_of_hack']:
        # Extract all dates in the format "DD Month YYYY"
        all_dates = re.findall(rf'(\d{{1,2}}\s+{months}\s+\d{{4}})', all_text)
        
        # Filter out dates that are likely from navigation or footer
        filtered_dates = [date for date in all_dates if "Исследования" not in date and "подпис" not in date.lower()]
        
        if filtered_dates:
            # Remove duplicate dates and sort chronologically
            unique_dates = sorted(set(filtered_dates))
            
            # If multiple dates are found, the first is likely the start and the last is the end
            if len(unique_dates) >= 2:
                hackathon['start_of_hack'] = unique_dates[0]
                hackathon['end_of_hack'] = unique_dates[-1]
            else:
                # If only one date, it's likely the start
                hackathon['start_of_hack'] = unique_dates[0]
    
    # FINAL VALIDATION: Ensure start_of_hack is before end_of_hack
    if hackathon['start_of_hack'] and hackathon['end_of_hack']:
        # Try to parse dates to compare
        try:
            # Simple Russian month name to number mapping
            month_to_num = {
                'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
                'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
                'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
            }
            
            def parse_ru_date(date_str):
                if not date_str or "Исследования" in date_str or "подпис" in date_str.lower():
                    return None
                    
                parts = date_str.strip().split()
                if len(parts) == 3:
                    try:
                        day, month_name, year = parts
                        month_num = month_to_num.get(month_name.lower())
                        if month_num:
                            return datetime.datetime(int(year), int(month_num), int(day))
                    except (ValueError, TypeError):
                        return None
                return None
            
            start_date = parse_ru_date(hackathon['start_of_hack'])
            end_date = parse_ru_date(hackathon['end_of_hack'])
            
            # If end date is before start date, swap them or clear end date
            if start_date and end_date and end_date < start_date:
                # For dates in same year, swap them as this is likely correct
                if start_date.year == end_date.year:
                    hackathon['start_of_hack'], hackathon['end_of_hack'] = hackathon['end_of_hack'], hackathon['start_of_hack']
                else:
                    # For different years, check if they're extremely far apart
                    if abs((end_date - start_date).days) > 365:
                        # If more than a year apart, probably one date is wrong - use only start date
                        hackathon['end_of_hack'] = None
                    else:
                        # Otherwise swap them - might be a multi-year event
                        hackathon['start_of_hack'], hackathon['end_of_hack'] = hackathon['end_of_hack'], hackathon['start_of_hack']
        except Exception:
            # If there's any error in date parsing, leave as is
            pass
    
    # Look for type (online/offline) with improved detection
    # Prioritize explicit mentions in the main content
    if main_content_div:
        main_text = main_content_div.get_text(strip=True).lower()
        
        # Check for explicit format mentions
        format_match = re.search(r'формат\s*:\s*(онлайн|оффлайн|офлайн|online|offline)', main_text, re.IGNORECASE)
        if format_match:
            format_text = format_match.group(1).lower()
            if 'онлайн' in format_text or 'online' in format_text:
                hackathon['type'] = "online"
            else:
                hackathon['type'] = "offline"
        # If no explicit format found, look for location indicators
        elif re.search(r'место\s+проведения\s*:', main_text, re.IGNORECASE):
            hackathon['type'] = "offline"
        # Or check for common location names (Russian cities)
        elif re.search(r'\b(москва|санкт-петербург|казань|новосибирск|екатеринбург)\b', main_text, re.IGNORECASE):
            hackathon['type'] = "offline"
    
    # If still no type detected, use more general patterns
    if not hackathon['type']:
        if re.search(r'\b(?:онлайн|online|виртуал|дистанц)\b', all_text, re.IGNORECASE):
            hackathon['type'] = "online"
        elif re.search(r'\b(?:оффлайн|офлайн|offline|очн|место\s+проведения)\b', all_text, re.IGNORECASE):
            hackathon['type'] = "offline"
    
    # Look for prize money with improved patterns
    prize_patterns = [
        r'(?:призовой\s+фонд|призовой|приз|награда)(?:\s+составляет)?(?:\s+в\s+размере)?[\s:]*(\d[\s\d]*[\d,.]+)\s*(млн|тыс)?\.?\s*(руб|₽|рубл)',
        r'(\d[\s\d]*[\d,.]+)\s*(млн|тыс)?\.?\s*(руб|₽|рубл).*?(?:призовой\s+фонд|приз)',
        r'(?:призов[а-я]+\s+на\s+сумму|призов[а-я]+\s+фонд[а-я]+)\s+(\d[\s\d]*[\d,.]+)\s*(млн|тыс)?',
        r'(?:1\s*место[^\d]*)(\d[\s\d]*[\d,.]+)\s*(?:руб|₽|рубл)'  # Extract from 1st place prize
    ]
    
    for pattern in prize_patterns:
        prize_match = re.search(pattern, all_text, re.IGNORECASE)
        if prize_match:
            amount_str = prize_match.group(1).replace(' ', '').replace(',', '.')
            multiplier_group = prize_match.group(2) if len(prize_match.groups()) > 1 else None
            multiplier = 1000000 if multiplier_group and 'млн' in multiplier_group.lower() else 1000 if multiplier_group and 'тыс' in multiplier_group.lower() else 1
            try:
                prize_amount = float(amount_str) * multiplier
                # If we're getting prize amount from 1st place prize, multiply appropriately
                if "1 место" in prize_match.group(0).lower() or "1-е место" in prize_match.group(0).lower():
                    # Check if there are 2nd and 3rd places mentioned
                    if re.search(r'2\s*место', all_text, re.IGNORECASE) and re.search(r'3\s*место', all_text, re.IGNORECASE):
                        prize_amount = prize_amount * 2  # Approximate total prize based on 1st place
                
                hackathon['amount_money'] = prize_amount
                break
            except ValueError:
                pass
    
    # Sleep to avoid overloading the server
    time.sleep(1)
    
    # Final Check: ensure all dates have the same expected year
    expected_year = None
    
    # 1. Попытка получить год из названия хакатона
    name_year_match = re.search(r'202\d|203\d', hackathon['name'])
    if name_year_match:
        expected_year = name_year_match.group(0)
        
    # 2. Если в названии нет года, пытаемся получить год из дат проведения хакатона
    if not expected_year and hackathon['start_of_hack']:
        hack_year_match = re.search(r'(202\d|203\d)', hackathon['start_of_hack'])
        if hack_year_match:
            expected_year = hack_year_match.group(1)
    
    if not expected_year and hackathon['end_of_hack']:
        hack_year_match = re.search(r'(202\d|203\d)', hackathon['end_of_hack'])
        if hack_year_match:
            expected_year = hack_year_match.group(1)
    
    # 3. Если не нашли год ни в названии, ни в датах, используем год + 1 от текущего
    if not expected_year:
        current_year = datetime.datetime.now().year
        next_year = current_year + 1
        expected_year = str(next_year)
    
    # Function to update year in date string
    def update_year_in_date(date_str, new_year):
        if not date_str:
            return date_str
        # Extract year from the date
        year_in_date = re.search(r'\b(202\d|203\d)\b', date_str)
        if year_in_date and year_in_date.group(1) != new_year:
            # Replace the year with the expected year
            return re.sub(r'\b(202\d|203\d)\b', new_year, date_str)
        elif not year_in_date and re.search(r'\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)', date_str):
            # If there's a date without a year, add the expected year
            return f"{date_str} {new_year}"
        return date_str
    
    # Update years in all dates
    if hackathon['end_of_registration']:
        hackathon['end_of_registration'] = update_year_in_date(hackathon['end_of_registration'], expected_year)
    if hackathon['start_of_hack']:
        hackathon['start_of_hack'] = update_year_in_date(hackathon['start_of_hack'], expected_year)
    if hackathon['end_of_hack']:
        hackathon['end_of_hack'] = update_year_in_date(hackathon['end_of_hack'], expected_year)
    
    return hackathon


def parse_hackathons_page(html_content):
    """
    Parse the hackathons page HTML content and extract hackathon data.
    Returns a list of hackathon dictionaries.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    hackathons = []
    
    # Находим все ссылки на хакатоны в relevants-item
    hackathon_links = []
    for item in soup.find_all('div', class_='t-feed__post-popup__relevants-item'):
        link = item.find('a')
        if link and link.get('href') and '/tpost/' in link.get('href'):
            url = link.get('href')
            
            # Избегаем дубликатов
            if url not in [h.get('href') for h in hackathon_links]:
                hackathon_links.append(link)
    
    # Если не нашли по новой структуре, попробуем старую
    if not hackathon_links:
        # Старый способ поиска хакатонов через js-feed-post
        feed_items = soup.find_all('li', class_='js-feed-post')
        for item in feed_items:
            title_element = item.find('div', class_='js-feed-post-title')
            if title_element and title_element.find('a'):
                link = title_element.find('a')
                if link and link.get('href') and '/tpost/' in link.get('href'):
                    hackathon_links.append(link)
    
    total_items = len(hackathon_links)
    print(f"Found {total_items} hackathon items. Starting detailed parsing...")
    
    for idx, link in enumerate(hackathon_links, 1):
        try:
            # Extract the title and URL
            url = link.get('href', '')
            
            # Find the name in different ways depending on HTML structure
            name = None
            
            # Try to find name in relevants item title
            title_div = link.find('div', class_='t-feed__post-popup__relevants-item-title')
            if title_div:
                name = title_div.get_text(strip=True)
            
            # If not found, try to find in js-feed-post-title
            if not name:
                title_element = link.find('h1', class_='js-feed-post-title')
                if title_element:
                    name = title_element.get_text(strip=True)
            
            # If still not found, try to extract from URL as a last resort
            if not name:
                # Extract name from URL: take last part after last dash and replace hyphens
                name_from_url = url.split('-')[-1]
                name = name_from_url.replace('-', ' ').capitalize()
            
            # Extract the description
            description = ""
            desc_div = link.find('div', class_='t-feed__post-popup__relevants-item-descr')
            if desc_div:
                description = desc_div.get_text(strip=True)
            
            # Create a basic hackathon object
            basic_info = {
                "name": name,
                "task_description": description,
                "start_of_registration": None,
                "end_of_registration": None,
                "start_of_hack": None,
                "end_of_hack": None,
                "amount_money": extract_money(description),
                "type": detect_hackathon_type(description),
                "url": url
            }
            
            # Get detailed information from the hackathon's page
            print(f"Processing hackathon {idx}/{total_items}: {name}")
            detailed_info = parse_hackathon_details(url, basic_info)
            
            hackathons.append(detailed_info)
            
        except Exception as e:
            print(f"Error parsing hackathon: {e}")
            continue
    
    return hackathons


def main():
    """
    Main function to run the parser
    """
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the HTML file
    html_file_path = os.path.join(script_dir, 'hackathons_page.html')
    
    try:
        # Read the HTML file
        with open(html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        # Parse the hackathons
        hackathons = parse_hackathons_page(html_content)
        
        # Print the results
        print(f"\nSuccessfully parsed {len(hackathons)} hackathons:")
        for idx, hackathon in enumerate(hackathons, 1):
            print(f"\n{idx}. {hackathon['name']}")
            print(f"   Description: {hackathon['task_description'][:100]}...")
            print(f"   URL: {hackathon['url']}")
            print(f"   Registration until: {hackathon['end_of_registration']}")
            print(f"   Event period: {hackathon['start_of_hack']} - {hackathon['end_of_hack']}")
            print(f"   Prize: {hackathon['amount_money']} руб.")
            print(f"   Type: {hackathon['type']}")
        
        # Save to a JSON file
        output_file = os.path.join(script_dir, 'parsed_hackathons.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(hackathons, f, ensure_ascii=False, indent=2)
        
        print(f"\nResults saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 