# app.py
import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import os
import sys
import asyncio

# Tilføj overordnet mappe til Python path for at sikre korrekt import
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from Chat.chat_logger import read_new_log_lines, filter_chat_messages, translate_message_async, get_log_path

class ChatTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CS2 Chat Translator (v1.0)")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # Flag til at kontrollere tråde
        self.running = True

        # UI-elementer
        self.create_widgets()
        
        # Queue til tråd-kommunikation
        self.queue = queue.Queue()
        
        # Start backend-tråd
        self.start_logging()
        
        # Opdater UI fra køen
        self.process_queue()
        
    def create_widgets(self):
        """Opret alle UI-elementer"""
        # Top frame til knapper
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Clear button
        self.clear_button = tk.Button(button_frame, text="Clear chat", command=self.clear_chat)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Close button
        self.close_button = tk.Button(button_frame, text="Close", command=self.close_app)
        self.close_button.pack(side=tk.RIGHT, padx=5)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=20, 
                                                     font=("Consolas", 10))
        self.chat_display.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
    
    def update_chat(self):
        """Henter chatbeskeder i en separat tråd og sender dem til UI"""
        try:
            log_path = get_log_path()
            self.queue.put(("STATUS", "Connected"))
            
            for log_line in read_new_log_lines(log_path):
                if not self.running:
                    break
                    
                chat = filter_chat_messages(log_line)
                if chat:
                    timestamp, team, username, message = chat
                    
                    # Oversæt besked og send til UI-tråd
                    translated_text = asyncio.run(translate_message_async(message))

                    # Formatér beskedfarve baseret på team
                    team_color = "gray"
                    if team == "CT":
                        team_color = "blue"
                    elif team == "T":
                        team_color = "red"
                    
                    chat_entry = {
                        "timestamp": timestamp,
                        "team": team,
                        "team_color": team_color,
                        "username": username,
                        "original": message,
                        "translated": translated_text
                    }
                    self.queue.put(("CHAT", chat_entry))
        except FileNotFoundError as e:
            self.queue.put(("ERROR", str(e)))
        except Exception as e:
            self.queue.put(("ERROR", f"Fejl: {str(e)}"))

    def process_queue(self):
        """Henter beskeder fra køen og opdaterer UI på hovedtråden"""
        try:
            while not self.queue.empty():
                msg_type, data = self.queue.get()
                
                if msg_type == "CHAT":
                    # Formatér og vis chat-besked
                    entry = data
                    timestamp = entry["timestamp"]
                    team = entry["team"]
                    team_color = entry["team_color"]
                    username = entry["username"]
                    translated = entry["translated"]
                    
                    # Indsæt formateret besked
                    self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
                    self.chat_display.insert(tk.END, f"[{team}] ", team_color)
                    self.chat_display.insert(tk.END, f"{username}: ", "username")
                    self.chat_display.insert(tk.END, f"{translated}\n", "message")
                    
                    # Scroll til bunden
                    self.chat_display.yview(tk.END)
                    
           
                    
                elif msg_type == "ERROR":
                    # Vis fejlbesked
                    self.chat_display.insert(tk.END, f"ERROR: {data}\n", "error")
                    self.chat_display.yview(tk.END)
                
        except Exception as e:
            self.chat_display.insert(tk.END, f"UI ERROR: {str(e)}\n", "error")
            
        # Konfigurer tekstfarver
        self.chat_display.tag_configure("timestamp", foreground="gray")
        self.chat_display.tag_configure("blue", foreground="blue")
        self.chat_display.tag_configure("red", foreground="red")
        self.chat_display.tag_configure("gray", foreground="gray")
        self.chat_display.tag_configure("username", foreground="black", font=("Consolas", 10, "bold"))
        self.chat_display.tag_configure("message", foreground="black")
        self.chat_display.tag_configure("small", foreground="gray", font=("Consolas", 8))
        self.chat_display.tag_configure("error", foreground="red", font=("Consolas", 10, "bold"))
        
        # Planlæg næste opdatering (hvis programmet kører)
        if self.running:
            self.root.after(100, self.process_queue)

    def start_logging(self):
        """Starter backend-logning i en separat tråd"""
        self.log_thread = threading.Thread(target=self.update_chat, daemon=True)
        self.log_thread.start()

    def clear_chat(self):
        """Ryd chatvinduet"""
        self.chat_display.delete(1.0, tk.END)
        
    def close_app(self):
        """Lukker applikationen korrekt"""
        self.running = False
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatTranslatorApp(root)
    root.mainloop()