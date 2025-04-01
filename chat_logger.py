import os
import re
import time
from deep_translator import GoogleTranslator
import asyncio

def get_log_path():
    path = os.path.expandvars(r"%PROGRAMFILES(X86)%\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\console.log")
    if not os.path.exists(path):
        raise FileNotFoundError("Console.log was not found. Start game with -condebug")
    return path

def read_new_log_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line.strip()

def filter_chat_messages(line):
    match = re.search(r"(\d{2}/\d{2} \d{2}:\d{2}:\d{2})  \[(ALL|CT|T)\] ([^:]+?): (.+)", line)
    return match.groups() if match else None

async def translate_message_async(message):
    """Asynkron oversættelse med deep-translator"""
    try:
               
        # Brug deep-translator til at oversætte beskeden
        translated = await asyncio.to_thread(GoogleTranslator(source='auto', target='en').translate, message)
        return translated  
    except Exception as e:
        print(f"Oversættelsesfejl: {e}")
        return "unknown", message

async def monitor_chat(callback):
    """Asynkron chat monitor der kalder callback for hver besked"""
    try:
        path = get_log_path()
        for line in read_new_log_lines(path):
            if chat := filter_chat_messages(line):
                timestamp, team, username, message = chat
                lang, translated = await translate_message_async(message)
                await callback({
                    'type': 'message',
                    'timestamp': timestamp,
                    'team': team,
                    'username': username,
                    'text': translated,
                    'lang': lang
                })
    except Exception as e:
        await callback({'type': 'error', 'text': str(e)})