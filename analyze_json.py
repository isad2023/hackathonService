import json
import re

# Открываем JSON-файл
with open('parsed_hackathons.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Количество хакатонов: {len(data)}')

for i, hack in enumerate(data):
    name = hack['name']
    desc = hack['task_description']
    
    # Анализируем структуру описания
    newlines = desc.count('\n')
    blocks = desc.split('\n')
    
    # Ищем списки
    ul_items = re.findall(r'^- .+', desc, re.MULTILINE)
    ol_items = re.findall(r'^\d+\. .+', desc, re.MULTILINE)
    
    print(f"\n{i+1}. {name}")
    print(f"   URL: {hack['url']}")
    print(f"   Длина описания: {len(desc)} символов")
    print(f"   Количество блоков: {len(blocks)}")
    print(f"   Количество переносов строк: {newlines}")
    print(f"   Элементы маркированного списка: {len(ul_items)}")
    print(f"   Элементы нумерованного списка: {len(ol_items)}")
    
    # Показываем первые 3 блока описания
    print("\n   Начало описания:")
    for j, block in enumerate(blocks[:3]):
        if block.strip():
            print(f"   > [{j+1}] {block}")
    
    # Показываем примеры элементов списков
    if ul_items:
        print("\n   Примеры элементов маркированного списка:")
        for item in ul_items[:2]:
            print(f"   > {item}")
    
    if ol_items:
        print("\n   Примеры элементов нумерованного списка:")
        for item in ol_items[:2]:
            print(f"   > {item}")
            
print("\nДетальный анализ переносов строк:")
for hack in data:
    desc = hack['task_description']
    
    # Количество блоков с минимальной длиной строки
    blocks = desc.split('\n')
    substantive_blocks = len([b for b in blocks if len(b.strip()) > 20])
    
    # Проверка наличия последовательных блоков разделенных переносами
    consecutive_blocks = re.findall(r'[^\n]{20,}\n[^\n]{20,}', desc)
    
    print(f"\n{hack['name']}:")
    print(f"  - Общее количество блоков: {len(blocks)}")
    print(f"  - Значимых блоков (>20 символов): {substantive_blocks}")
    print(f"  - Последовательных блоков с переносами: {len(consecutive_blocks)}")
    
    # Показываем первый последовательный блок
    if consecutive_blocks:
        sample = consecutive_blocks[0]
        parts = sample.split('\n')
        print(f"\n  Пример последовательных блоков:")
        for i, part in enumerate(parts):
            print(f"  Блок {i+1}: {part[:50]}..." if len(part) > 50 else f"  Блок {i+1}: {part}") 