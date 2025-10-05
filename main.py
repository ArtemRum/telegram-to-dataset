import os
import json
from datetime import datetime

def process_telegram_exports():
    """Основная функция для обработки Telegram экспортов"""
    
    # Файлы для результатов
    known_people_file = "known_people.txt"
    training_dialogs_file = "training_dialogs.txt"
    
    # Создаем файлы если их нет
    if not os.path.exists(known_people_file):
        open(known_people_file, 'w', encoding='utf-8').close()
    
    if not os.path.exists(training_dialogs_file):
        open(training_dialogs_file, 'w', encoding='utf-8').close()
    
    # Загружаем уже известных людей (кроме Артёма)
    known_people = set()
    if os.path.exists(known_people_file):
        with open(known_people_file, 'r', encoding='utf-8') as f:
            for line in f:
                person = line.strip()
                if person and person != "Артём":
                    known_people.add(person)
    
    # Ищем все папки в текущей директории
    folders_processed = 0
    total_messages = 0
    
    for item in os.listdir('.'):
        if os.path.isdir(item):
            result_json_path = os.path.join(item, "result.json")
            
            if os.path.exists(result_json_path):
                try:
                    # Обрабатываем файл
                    messages_found = process_json_file(
                        result_json_path, 
                        known_people, 
                        training_dialogs_file
                    )
                    total_messages += messages_found
                    folders_processed += 1
                    print(f"✓ Обработана папка: {item} ({messages_found} сообщений)")
                    
                except Exception as e:
                    print(f"✗ Ошибка в папке {item}: {e}")
            else:
                print(f"✗ Не найден файл {result_json_path}")
    
    # Сохраняем обновленный список известных людей
    save_known_people(known_people, known_people_file)
    
    print(f"\n📊 Итоги обработки:")
    print(f"   Обработано папок: {folders_processed}")
    print(f"   Найдено сообщений: {total_messages}")
    print(f"   Уникальных авторов: {len(known_people)}")
    print(f"   Файл known_people.txt обновлен")
    print(f"   Файл training_dialogs.txt дополнен")

def process_json_file(file_path, known_people, output_file):
    """Обрабатывает один JSON файл и возвращает количество сообщений"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    messages_processed = 0
    
    # Открываем файл для дозаписи
    with open(output_file, 'a', encoding='utf-8') as dialogs_file:
        
        for message in data.get('messages', []):
            # Извлекаем текст сообщения
            text = extract_message_text(message.get('text', ''))
            if not text or len(text.strip()) < 2:
                continue
            
            # Извлекаем автора
            author = extract_author(message)
            if not author:
                continue
            
            # Добавляем автора в known_people (кроме Артёма)
            if author != "Артём" and author not in known_people:
                known_people.add(author)
            
            # Извлекаем и форматируем время
            time_str = format_message_time(message.get('date', ''))
            
            # Форматируем строку для training_dialogs.txt
            formatted_message = f"({time_str}) [{author}] {text}"
            
            # Записываем в файл
            dialogs_file.write(formatted_message + '\n')
            messages_processed += 1
    
    return messages_processed

def extract_message_text(text_data):
    """Извлекает текст сообщения из разных форматов Telegram"""
    
    if isinstance(text_data, str):
        return text_data.strip()
    
    elif isinstance(text_data, list):
        text_parts = []
        for part in text_data:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict):
                # Обрабатываем разные типы контента
                if 'text' in part:
                    text_parts.append(part['text'])
                elif 'type' in part and part['type'] == 'link':
                    text_parts.append(part.get('text', part.get('href', '')))
        return ' '.join(text_parts).strip()
    
    return ""

def extract_author(message):
    """Извлекает имя автора из сообщения"""
    
    author = message.get('from', '')
    
    # Если автор не найден, пробуем другие поля
    if not author:
        author = message.get('from_id', '')
        author = message.get('actor', author)
        author = message.get('actor_id', author)
    
    # Очищаем имя автора
    if isinstance(author, str):
        author = author.strip()
        # Убираем префиксы типа "channel#", "user#"
        if '#' in author:
            author = author.split('#')[-1]
    
    return author if author else "Неизвестно"

def format_message_time(date_str):
    """Форматирует время сообщения в нужный формат"""
    
    if not date_str:
        return "00:00"
    
    try:
        # Пробуем разные форматы дат из Telegram
        if 'T' in date_str:
            if 'Z' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(date_str)
        else:
            # Старый формат даты
            dt = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
        
        return dt.strftime("%H:%M")
        
    except (ValueError, AttributeError):
        return "00:00"

def save_known_people(known_people, output_file):
    """Сохраняет список известных людей в файл"""
    
    # Сортируем для удобства (кроме "Неизвестно")
    sorted_people = sorted([p for p in known_people if p != "Неизвестно"])
    
    # "Неизвестно" добавляем в конец если есть
    if "Неизвестно" in known_people:
        sorted_people.append("Неизвестно")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for person in sorted_people:
            f.write(person + '\n')

def show_statistics():
    """Показывает статистику по обработанным файлам"""
    
    if os.path.exists("known_people.txt"):
        with open("known_people.txt", 'r', encoding='utf-8') as f:
            people = [line.strip() for line in f if line.strip()]
        print(f"\n📋 Известные авторы ({len(people)}):")
        for person in people[:10]:  # Показываем первые 10
            print(f"   • {person}")
        if len(people) > 10:
            print(f"   ... и еще {len(people) - 10}")
    
    if os.path.exists("training_dialogs.txt"):
        with open("training_dialogs.txt", 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"\n📝 Сообщений для обучения: {len(lines)}")

if __name__ == "__main__":
    print("🔍 Поиск и обработка Telegram экспортов...")
    print("   Ищу папки с файлами result.json\n")
    
    process_telegram_exports()
    show_statistics()
    
    print("\n✅ Обработка завершена!")
