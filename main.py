#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PC-98時代パソコン通信BBS風アプリケーション - メインモジュール
Version: 1.0.0
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import threading
import time
import random
import json
import datetime
import sys
import os
import re
from typing import Dict, List, Optional, Tuple
import queue
import logging

# g4fライブラリのインポートとエラーハンドリング
try:
    import g4f
    from g4f.client import Client
    G4F_AVAILABLE = True
    print("[SYSTEM] g4fライブラリが正常に読み込まれました")
except ImportError as e:
    G4F_AVAILABLE = False
    print(f"[ERROR] g4fライブラリの読み込みに失敗しました: {e}")

# ペルソナモジュールのインポート
try:
    from persona import PersonaManager
    print("[SYSTEM] ペルソナモジュールが正常に読み込まれました")
except ImportError as e:
    print(f"[ERROR] ペルソナモジュールの読み込みに失敗しました: {e}")
    sys.exit(1)

# アプリケーションバージョン
APP_VERSION = "1.0.0"

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bbs_app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, db_path: str = "bbs_database.db"):
        self.db_path = db_path
        self.init_database()
        logger.info(f"[DB] データベース初期化完了: {db_path}")
    
    def init_database(self):
        """データベース初期化"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # スレッドテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS threads (
                    thread_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_main TEXT NOT NULL,
                    category_sub TEXT,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    status TEXT DEFAULT 'active',
                    post_count INTEGER DEFAULT 0,
                    last_post_time TIMESTAMP
                )
            ''')
            
            # 投稿テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id INTEGER,
                    persona_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_user_post BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (thread_id) REFERENCES threads(thread_id)
                )
            ''')
            
            # ペルソナテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS personas (
                    persona_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    age INTEGER,
                    occupation TEXT,
                    background TEXT,
                    extroversion REAL,
                    agreeableness REAL,
                    conscientiousness REAL,
                    neuroticism REAL,
                    openness REAL,
                    additional_params TEXT,
                    emotion_state TEXT,
                    learning_data TEXT,
                    is_troll BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 学習履歴テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    persona_id INTEGER,
                    interaction_context TEXT,
                    response_pattern TEXT,
                    learning_weight REAL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (persona_id) REFERENCES personas(persona_id)
                )
            ''')
            
            # アプリケーション設定テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """クエリ実行"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"[DB] クエリ実行エラー: {e}")
            return []
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """INSERT実行"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"[DB] INSERT実行エラー: {e}")
            return -1

class G4FManager:
    """g4fライブラリ管理クラス"""
    
    def __init__(self):
        self.client = None
        self.available_providers = []
        self.current_provider = None
        self.init_g4f()
    
    def init_g4f(self):
        """g4f初期化"""
        if not G4F_AVAILABLE:
            logger.warning("[G4F] g4fライブラリが利用できません")
            return
        
        try:
            self.client = Client()
            self.find_available_providers()
            logger.info(f"[G4F] 初期化完了。利用可能プロバイダー: {len(self.available_providers)}個")
        except Exception as e:
            logger.error(f"[G4F] 初期化エラー: {e}")
    
    def find_available_providers(self):
        """利用可能プロバイダー検索"""
        try:
            # プロバイダーリストを取得
            providers = [
                g4f.Provider.Bing,
                g4f.Provider.ChatBase,
                g4f.Provider.FreeGpt,
                g4f.Provider.GPTalk,
                g4f.Provider.Liaobots,
                g4f.Provider.OpenaiChat,
                g4f.Provider.You,
                g4f.Provider.Yqcloud,
            ]
            
            for provider in providers:
                try:
                    # 簡単なテストメッセージで確認
                    test_response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "test"}],
                        provider=provider,
                        timeout=10
                    )
                    if test_response:
                        self.available_providers.append(provider)
                        logger.info(f"[G4F] プロバイダー利用可能: {provider.__name__}")
                except:
                    continue
            
            if self.available_providers:
                self.current_provider = self.available_providers[0]
                
        except Exception as e:
            logger.error(f"[G4F] プロバイダー検索エラー: {e}")
    
    def generate_response(self, prompt: str, persona_context: str = "") -> str:
        """AI応答生成"""
        if not self.client or not self.available_providers:
            return "AIシステムが利用できません。"
        
        try:
            # プロバイダーをローテーション
            if len(self.available_providers) > 1:
                self.current_provider = random.choice(self.available_providers)
            
            # プロンプト構築
            full_prompt = f"{persona_context}\n\n{prompt}"
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": full_prompt}],
                provider=self.current_provider,
                timeout=30
            )
            
            # 英語・中国語エラーメッセージを除外
            if isinstance(response, str):
                cleaned_response = self.clean_response(response)
                if cleaned_response:
                    logger.info(f"[G4F] 応答生成成功: {self.current_provider.__name__}")
                    return cleaned_response
            
            return "応答の生成に失敗しました。"
            
        except Exception as e:
            logger.error(f"[G4F] 応答生成エラー: {e}")
            # プロバイダーを変更して再試行
            if len(self.available_providers) > 1:
                self.available_providers.remove(self.current_provider)
                return self.generate_response(prompt, persona_context)
            return "AIシステムエラーが発生しました。"
    
    def clean_response(self, response: str) -> str:
        """応答のクリーニング（英語・中国語エラーメッセージ除外）"""
        # 英語エラーパターン
        english_patterns = [
            r'^Error:.*',
            r'^Sorry.*',
            r'^I apologize.*',
            r'^Unable to.*',
            r'^Cannot.*',
            r'.*error occurred.*',
            r'.*something went wrong.*'
        ]
        
        # 中国語エラーパターン
        chinese_patterns = [
            r'.*错误.*',
            r'.*失败.*',
            r'.*异常.*',
            r'.*系统.*错误.*'
        ]
        
        # パターンチェック
        for pattern in english_patterns + chinese_patterns:
            if re.match(pattern, response, re.IGNORECASE):
                return ""
        
        # 日本語が含まれているかチェック
        japanese_chars = re.findall(r'[ひらがなカタカナ漢字]', response)
        if len(japanese_chars) < 5:  # 日本語文字が5文字未満の場合は除外
            return ""
        
        return response.strip()

class ThreadManager:
    """スレッド管理クラス"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.categories = {
            "雑談": ["日常の話", "趣味の話", "最近の出来事", "天気の話", "グルメ情報"],
            "ゲーム": ["RPGの話", "アクションゲーム", "パズルゲーム", "レトロゲーム", "新作ゲーム"],
            "趣味": ["読書", "映画鑑賞", "音楽", "スポーツ", "旅行"],
            "パソコン": ["ハードウェア", "ソフトウェア", "プログラミング", "インターネット", "トラブル相談"],
            "仕事": ["転職相談", "スキルアップ", "職場の悩み", "副業", "資格取得"]
        }
        self.init_default_threads()
        logger.info("[THREAD] スレッド管理初期化完了")
    
    def init_default_threads(self):
        """デフォルトスレッド作成"""
        for main_category, sub_categories in self.categories.items():
            for sub_category in sub_categories:
                thread_title = f"{sub_category}について語りましょう"
                
                # 既存チェック
                existing = self.db_manager.execute_query(
                    "SELECT thread_id FROM threads WHERE category_main=? AND category_sub=?",
                    (main_category, sub_category)
                )
                
                if not existing:
                    self.db_manager.execute_insert(
                        """INSERT INTO threads (category_main, category_sub, title, created_by) 
                           VALUES (?, ?, ?, ?)""",
                        (main_category, sub_category, thread_title, "システム")
                    )
    
    def get_threads_by_category(self, main_category: str) -> List[Dict]:
        """カテゴリ別スレッド取得"""
        threads = self.db_manager.execute_query(
            """SELECT thread_id, category_sub, title, post_count, last_post_time 
               FROM threads WHERE category_main=? AND status='active' 
               ORDER BY last_post_time DESC""",
            (main_category,)
        )
        
        return [
            {
                "thread_id": t[0],
                "category_sub": t[1],
                "title": t[2],
                "post_count": t[3] or 0,
                "last_post_time": t[4]
            }
            for t in threads
        ]
    
    def get_thread_posts(self, thread_id: int, limit: int = 50) -> List[Dict]:
        """スレッド投稿取得（近い時間ほど重視）"""
        posts = self.db_manager.execute_query(
            """SELECT persona_name, content, posted_at, is_user_post 
               FROM posts WHERE thread_id=? 
               ORDER BY posted_at DESC LIMIT ?""",
            (thread_id, limit)
        )
        
        return [
            {
                "persona_name": p[0],
                "content": p[1],
                "posted_at": p[2],
                "is_user_post": bool(p[3])
            }
            for p in reversed(posts)  # 時系列順にする
        ]
    
    def add_post(self, thread_id: int, persona_name: str, content: str, is_user_post: bool = False) -> bool:
        """投稿追加"""
        try:
            self.db_manager.execute_insert(
                """INSERT INTO posts (thread_id, persona_name, content, is_user_post) 
                   VALUES (?, ?, ?, ?)""",
                (thread_id, persona_name, content, is_user_post)
            )
            
            # スレッドの投稿数と最終投稿時間を更新
            self.db_manager.execute_insert(
                """UPDATE threads SET 
                   post_count = (SELECT COUNT(*) FROM posts WHERE thread_id = ?),
                   last_post_time = CURRENT_TIMESTAMP 
                   WHERE thread_id = ?""",
                (thread_id, thread_id)
            )
            
            logger.info(f"[THREAD] 投稿追加: {persona_name} -> Thread {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"[THREAD] 投稿追加エラー: {e}")
            return False

class BBSApplication:
    """メインアプリケーションクラス"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        
        # コンポーネント初期化
        self.db_manager = DatabaseManager()
        self.g4f_manager = G4FManager()
        self.thread_manager = ThreadManager(self.db_manager)
        self.persona_manager = PersonaManager(self.db_manager, self.g4f_manager)
        
        # UI状態
        self.current_category = "雑談"
        self.current_thread_id = None
        self.admin_mode = False
        self.ai_activity_enabled = True
        self.auto_post_interval = 45  # 秒
        
        # メッセージキュー
        self.message_queue = queue.Queue()
        
        # GUI構築
        self.create_widgets()
        self.setup_keybindings()
        
        # 自動投稿スレッド開始
        self.start_auto_posting()
        
        # メッセージ処理開始
        self.process_messages()
        
        logger.info(f"[APP] アプリケーション初期化完了 - Version {APP_VERSION}")
    
    def setup_window(self):
        """ウィンドウ設定"""
        self.root.title(f"草の根BBS - PC-98風パソコン通信 v{APP_VERSION}")
        self.root.geometry("1024x768")
        self.root.configure(bg="#000000")
        
        # PC-98風カラーテーマ
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('BBS.TFrame', background='#000000', foreground='#00FF00')
        style.configure('BBS.TLabel', background='#000000', foreground='#00FF00', font=('MS Gothic', 10))
        style.configure('BBS.TButton', background='#0000FF', foreground='#FFFFFF', font=('MS Gothic', 9))
        style.configure('BBS.Treeview', background='#000080', foreground='#FFFFFF', fieldbackground='#000080')
        
        # アイコン設定（存在する場合）
        try:
            self.root.iconbitmap('bbs_icon.ico')
        except:
            pass
    
    def create_widgets(self):
        """ウィジェット作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, style='BBS.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ヘッダー
        header_frame = ttk.Frame(main_frame, style='BBS.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(
            header_frame, 
            text="■ 草の根BBS ■ PC-98時代パソコン通信の再現 ■",
            style='BBS.TLabel',
            font=('MS Gothic', 12, 'bold')
        )
        title_label.pack()
        
        status_label = ttk.Label(
            header_frame,
            text=f"Version: {APP_VERSION} | AI活動: {'ON' if self.ai_activity_enabled else 'OFF'} | 管理モード: {'ON' if self.admin_mode else 'OFF'}",
            style='BBS.TLabel',
            font=('MS Gothic', 8)
        )
        status_label.pack()
        self.status_label = status_label
        
        # 左側パネル（カテゴリ・スレッド一覧）
        left_frame = ttk.Frame(main_frame, style='BBS.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # カテゴリ選択
        category_label = ttk.Label(left_frame, text="■ カテゴリ ■", style='BBS.TLabel')
        category_label.pack(anchor=tk.W)
        
        self.category_listbox = tk.Listbox(
            left_frame, 
            bg="#000080", 
            fg="#FFFFFF", 
            font=('MS Gothic', 10),
            width=20,
            height=8
        )
        for category in self.thread_manager.categories.keys():
            self.category_listbox.insert(tk.END, category)
        self.category_listbox.pack(pady=(5, 10))
        self.category_listbox.bind('<<ListboxSelect>>', self.on_category_select)
        self.category_listbox.selection_set(0)
        
        # スレッド一覧
        thread_label = ttk.Label(left_frame, text="■ スレッド一覧 ■", style='BBS.TLabel')
        thread_label.pack(anchor=tk.W)
        
        self.thread_listbox = tk.Listbox(
            left_frame,
            bg="#000080",
            fg="#FFFFFF",
            font=('MS Gothic', 9),
            width=25,
            height=15
        )
        self.thread_listbox.pack(pady=(5, 10))
        self.thread_listbox.bind('<<ListboxSelect>>', self.on_thread_select)
        
        # 右側パネル（投稿表示・入力）
        right_frame = ttk.Frame(main_frame, style='BBS.TFrame')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 投稿表示エリア
        post_label = ttk.Label(right_frame, text="■ 投稿内容 ■", style='BBS.TLabel')
        post_label.pack(anchor=tk.W)
        
        self.post_display = scrolledtext.ScrolledText(
            right_frame,
            bg="#000000",
            fg="#00FF00",
            font=('MS Gothic', 9),
            wrap=tk.WORD,
            height=25,
            state=tk.DISABLED
        )
        self.post_display.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # 投稿入力エリア
        input_label = ttk.Label(right_frame, text="■ 投稿入力 ■", style='BBS.TLabel')
        input_label.pack(anchor=tk.W)
        
        self.post_input = tk.Text(
            right_frame,
            bg="#000080",
            fg="#FFFFFF",
            font=('MS Gothic', 9),
            height=4,
            wrap=tk.WORD
        )
        self.post_input.pack(fill=tk.X, pady=(5, 5))
        
        # ボタンエリア
        button_frame = ttk.Frame(right_frame, style='BBS.TFrame')
        button_frame.pack(fill=tk.X)
        
        self.post_button = ttk.Button(
            button_frame,
            text="投稿 (Ctrl+Enter)",
            command=self.submit_post,
            style='BBS.TButton'
        )
        self.post_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.refresh_button = ttk.Button(
            button_frame,
            text="更新 (F5)",
            command=self.refresh_display,
            style='BBS.TButton'
        )
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.admin_button = ttk.Button(
            button_frame,
            text="管理 (F12)",
            command=self.toggle_admin_mode,
            style='BBS.TButton'
        )
        self.admin_button.pack(side=tk.RIGHT)
        
        # 初期表示
        self.update_thread_list()
        self.update_status()
    
    def setup_keybindings(self):
        """キーバインド設定"""
        self.root.bind('<Control-Return>', lambda e: self.submit_post())
        self.root.bind('<F5>', lambda e: self.refresh_display())
        self.root.bind('<F12>', lambda e: self.toggle_admin_mode())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Escape>', lambda e: self.post_input.focus_set())
        
        # フォーカス移動
        self.root.bind('<Tab>', self.focus_next_widget)
        self.root.bind('<Shift-Tab>', self.focus_prev_widget)
        
        # カテゴリ・スレッド選択
        self.root.bind('<Up>', self.navigate_up)
        self.root.bind('<Down>', self.navigate_down)
        self.root.bind('<Left>', self.navigate_left)
        self.root.bind('<Right>', self.navigate_right)
        
        logger.info("[APP] キーバインド設定完了")
    
    def focus_next_widget(self, event):
        """次のウィジェットにフォーカス"""
        event.widget.tk_focusNext().focus()
        return "break"
    
    def focus_prev_widget(self, event):
        """前のウィジェットにフォーカス"""
        event.widget.tk_focusPrev().focus()
        return "break"
    
    def navigate_up(self, event):
        """上方向ナビゲーション"""
        if event.widget == self.category_listbox:
            current = self.category_listbox.curselection()
            if current and current[0] > 0:
                self.category_listbox.selection_clear(0, tk.END)
                self.category_listbox.selection_set(current[0] - 1)
                self.on_category_select(None)
        elif event.widget == self.thread_listbox:
            current = self.thread_listbox.curselection()
            if current and current[0] > 0:
                self.thread_listbox.selection_clear(0, tk.END)
                self.thread_listbox.selection_set(current[0] - 1)
                self.on_thread_select(None)
    
    def navigate_down(self, event):
        """下方向ナビゲーション"""
        if event.widget == self.category_listbox:
            current = self.category_listbox.curselection()
            if current and current[0] < self.category_listbox.size() - 1:
                self.category_listbox.selection_clear(0, tk.END)
                self.category_listbox.selection_set(current[0] + 1)
                self.on_category_select(None)
        elif event.widget == self.thread_listbox:
            current = self.thread_listbox.curselection()
            if current and current[0] < self.thread_listbox.size() - 1:
                self.thread_listbox.selection_clear(0, tk.END)
                self.thread_listbox.selection_set(current[0] + 1)
                self.on_thread_select(None)
    
    def navigate_left(self, event):
        """左方向ナビゲーション"""
        self.category_listbox.focus_set()
    
    def navigate_right(self, event):
        """右方向ナビゲーション"""
        self.thread_listbox.focus_set()
    
    def on_category_select(self, event):
        """カテゴリ選択イベント"""
        selection = self.category_listbox.curselection()
        if selection:
            self.current_category = self.category_listbox.get(selection[0])
            self.update_thread_list()
            logger.info(f"[APP] カテゴリ変更: {self.current_category}")
    
    def on_thread_select(self, event):
        """スレッド選択イベント"""
        selection = self.thread_listbox.curselection()
        if selection:
            thread_info = self.thread_listbox.get(selection[0])
            # スレッドIDを抽出
            for thread in self.current_threads:
                if f"[{thread['thread_id']}]" in thread_info:
                    self.current_thread_id = thread['thread_id']
                    self.update_post_display()
                    logger.info(f"[APP] スレッド選択: {self.current_thread_id}")
                    break
    
    def update_thread_list(self):
        """スレッド一覧更新"""
        self.thread_listbox.delete(0, tk.END)
        self.current_threads = self.thread_manager.get_threads_by_category(self.current_category)
        
        for thread in self.current_threads:
            display_text = f"[{thread['thread_id']}] {thread['category_sub']} ({thread['post_count']})"
            self.thread_listbox.insert(tk.END, display_text)
        
        if self.current_threads:
            self.thread_listbox.selection_set(0)
            self.current_thread_id = self.current_threads[0]['thread_id']
            self.update_post_display()
    
    def update_post_display(self):
        """投稿表示更新"""
        if not self.current_thread_id:
            return
        
        posts = self.thread_manager.get_thread_posts(self.current_thread_id)
        
        self.post_display.config(state=tk.NORMAL)
        self.post_display.delete(1.0, tk.END)
        
        for i, post in enumerate(posts):
            timestamp = post['posted_at']
            name = post['persona_name']
            content = post['content']
            is_user = post['is_user_post']
            
            # ユーザー投稿とAI投稿で色分け
            if is_user:
                name_color = "#FFFF00"  # 黄色
            else:
                name_color = "#00FFFF"  # シアン
            
            # 投稿表示
            self.post_display.insert(tk.END, f"{i+1:3d}: ", "number")
            self.post_display.insert(tk.END, f"{timestamp} ", "timestamp")
            self.post_display.insert(tk.END, f"{name}\n", "name")
            self.post_display.insert(tk.END, f"     {content}\n\n", "content")
        
        # タグ設定
        self.post_display.tag_configure("number", foreground="#808080")
        self.post_display.tag_configure("timestamp", foreground="#808080")
        self.post_display.tag_configure("name", foreground="#00FFFF", font=('MS Gothic', 9, 'bold'))
        self.post_display.tag_configure("content", foreground="#00FF00")
        
        self.post_display.config(state=tk.DISABLED)
        self.post_display.see(tk.END)
    
    def submit_post(self):
        """投稿送信"""
        if not self.current_thread_id:
            messagebox.showwarning("警告", "スレッドが選択されていません。")
            return
        
        content = self.post_input.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("警告", "投稿内容を入力してください。")
            return
        
        # ユーザー投稿として追加
        success = self.thread_manager.add_post(
            self.current_thread_id, 
            "あなた", 
            content, 
            is_user_post=True
        )
        
        if success:
            self.post_input.delete(1.0, tk.END)
            self.update_post_display()
            self.update_thread_list()
            
            # ペルソナに学習データとして記録
            self.persona_manager.record_user_interaction(self.current_thread_id, content)
            
            logger.info(f"[APP] ユーザー投稿完了: Thread {self.current_thread_id}")
        else:
            messagebox.showerror("エラー", "投稿に失敗しました。")
    
    def refresh_display(self):
        """表示更新"""
        self.update_thread_list()
        self.update_post_display()
        self.update_status()
        logger.info("[APP] 表示更新完了")
    
    def toggle_admin_mode(self):
        """管理モード切り替え"""
        self.admin_mode = not self.admin_mode
        self.update_status()
        
        if self.admin_mode:
            self.show_admin_panel()
        
        logger.info(f"[APP] 管理モード: {'ON' if self.admin_mode else 'OFF'}")
    
    def show_admin_panel(self):
        """管理パネル表示"""
        admin_window = tk.Toplevel(self.root)
        admin_window.title("管理パネル")
        admin_window.geometry("400x300")
        admin_window.configure(bg="#000000")
        
        # AI活動制御
        ai_frame = ttk.Frame(admin_window, style='BBS.TFrame')
        ai_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(ai_frame, text="AI活動制御:", style='BBS.TLabel').pack(anchor=tk.W)
        
        ai_button_frame = ttk.Frame(ai_frame, style='BBS.TFrame')
        ai_button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            ai_button_frame,
            text="AI活動 ON",
            command=lambda: self.set_ai_activity(True),
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            ai_button_frame,
            text="AI活動 OFF", 
            command=lambda: self.set_ai_activity(False),
            style='BBS.TButton'
        ).pack(side=tk.LEFT)
        
        # 投稿間隔調整
        interval_frame = ttk.Frame(admin_window, style='BBS.TFrame')
        interval_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(interval_frame, text="投稿間隔調整:", style='BBS.TLabel').pack(anchor=tk.W)
        
        self.interval_var = tk.IntVar(value=self.auto_post_interval)
        interval_scale = tk.Scale(
            interval_frame,
            from_=30,
            to=120,
            orient=tk.HORIZONTAL,
            variable=self.interval_var,
            bg="#000080",
            fg="#FFFFFF",
            command=self.update_interval
        )
        interval_scale.pack(fill=tk.X, pady=5)
        
        # バージョン情報
        version_frame = ttk.Frame(admin_window, style='BBS.TFrame')
        version_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(version_frame, text="バージョン情報:", style='BBS.TLabel').pack(anchor=tk.W)
        ttk.Label(
            version_frame, 
            text=f"草の根BBS v{APP_VERSION}\n開発日: 2025年7月\nPython版PC-98風BBS",
            style='BBS.TLabel'
        ).pack(anchor=tk.W, pady=5)
        
        # ペルソナ統計
        stats_frame = ttk.Frame(admin_window, style='BBS.TFrame')
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(stats_frame, text="システム統計:", style='BBS.TLabel').pack(anchor=tk.W)
        
        persona_count = len(self.persona_manager.personas)
        active_personas = sum(1 for p in self.persona_manager.personas.values() if p.is_active)
        
        ttk.Label(
            stats_frame,
            text=f"ペルソナ数: {persona_count}\n活動中: {active_personas}\nスレッド数: {len(self.current_threads)}",
            style='BBS.TLabel'
        ).pack(anchor=tk.W, pady=5)
    
    def set_ai_activity(self, enabled: bool):
        """AI活動設定"""
        self.ai_activity_enabled = enabled
        self.update_status()
        logger.info(f"[ADMIN] AI活動: {'有効' if enabled else '無効'}")
    
    def update_interval(self, value):
        """投稿間隔更新"""
        self.auto_post_interval = int(value)
        logger.info(f"[ADMIN] 投稿間隔変更: {self.auto_post_interval}秒")
    
    def update_status(self):
        """ステータス更新"""
        status_text = f"Version: {APP_VERSION} | AI活動: {'ON' if self.ai_activity_enabled else 'OFF'} | 管理モード: {'ON' if self.admin_mode else 'OFF'}"
        self.status_label.config(text=status_text)
    
    def start_auto_posting(self):
        """自動投稿スレッド開始"""
        def auto_post_worker():
            while True:
                try:
                    if self.ai_activity_enabled and self.current_threads:
                        # ランダムなスレッドを選択
                        thread = random.choice(self.current_threads)
                        thread_id = thread['thread_id']
                        
                        # ペルソナによる投稿生成
                        success = self.persona_manager.generate_auto_post(thread_id)
                        
                        if success:
                            # UI更新をメインスレッドに依頼
                            self.message_queue.put(('update_display', None))
                    
                    # インターバル待機（ランダム要素追加）
                    wait_time = self.auto_post_interval + random.randint(-10, 10)
                    time.sleep(max(30, wait_time))
                    
                except Exception as e:
                    logger.error(f"[AUTO_POST] エラー: {e}")
                    time.sleep(60)  # エラー時は1分待機
        
        auto_thread = threading.Thread(target=auto_post_worker, daemon=True)
        auto_thread.start()
        logger.info("[APP] 自動投稿スレッド開始")
    
    def process_messages(self):
        """メッセージキュー処理"""
        try:
            while True:
                message_type, data = self.message_queue.get_nowait()
                
                if message_type == 'update_display':
                    self.update_post_display()
                    self.update_thread_list()
                elif message_type == 'show_notification':
                    messagebox.showinfo("通知", data)
                
        except queue.Empty:
            pass
        
        # 100ms後に再実行
        self.root.after(100, self.process_messages)
    
    def run(self):
        """アプリケーション実行"""
        logger.info("[APP] アプリケーション開始")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("[APP] キーボード割り込みによる終了")
        except Exception as e:
            logger.error(f"[APP] 実行時エラー: {e}")
        finally:
            logger.info("[APP] アプリケーション終了")

def main():
    """メイン関数"""
    print("=" * 60)
    print("  草の根BBS - PC-98時代パソコン通信の再現")
    print(f"  Version: {APP_VERSION}")
    print("=" * 60)
    print("[SYSTEM] アプリケーション初期化中...")
    
    try:
        app = BBSApplication()
        print("[SYSTEM] 初期化完了。アプリケーションを開始します。")
        print("[INFO] キーボード操作:")
        print("  Ctrl+Enter: 投稿")
        print("  F5: 更新")
        print("  F12: 管理モード")
        print("  Ctrl+Q: 終了")
        print("  Tab/Shift+Tab: フォーカス移動")
        print("  矢印キー: ナビゲーション")
        app.run()
    except Exception as e:
        print(f"[ERROR] アプリケーション開始エラー: {e}")
        logger.error(f"アプリケーション開始エラー: {e}")

if __name__ == "__main__":
    main()
