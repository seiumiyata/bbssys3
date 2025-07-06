#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PC-98時代パソコン通信BBS風アプリケーション - メインモジュール
Version: 1.3.0 - g4f最新対応・DB修正版
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
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import importlib

# g4fライブラリのインポートとエラーハンドリング
try:
    import g4f
    from g4f.client import Client
    from g4f import Provider
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
APP_VERSION = "1.3.0"

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
    """データベース管理クラス（マイグレーション対応）"""
    
    def __init__(self, db_path: str = "bbs_database.db"):
        self.db_path = db_path
        self.init_database()
        self.migrate_database()
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
                    last_post_time TIMESTAMP,
                    last_ai_post_time TIMESTAMP
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
            
            # g4fプロバイダー管理テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS g4f_providers (
                    provider_name TEXT PRIMARY KEY,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_test_time TIMESTAMP,
                    success_rate REAL DEFAULT 0.0,
                    response_time REAL DEFAULT 0.0,
                    error_count INTEGER DEFAULT 0,
                    total_requests INTEGER DEFAULT 0,
                    last_error TEXT,
                    working_model TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def migrate_database(self):
        """データベースマイグレーション"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # threadsテーブルにlast_ai_post_timeカラムが存在するかチェック
            cursor.execute("PRAGMA table_info(threads)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'last_ai_post_time' not in columns:
                try:
                    cursor.execute("ALTER TABLE threads ADD COLUMN last_ai_post_time TIMESTAMP")
                    logger.info("[DB] last_ai_post_timeカラムを追加しました")
                except Exception as e:
                    logger.error(f"[DB] マイグレーションエラー: {e}")
            
            # g4f_providersテーブルにworking_modelカラムが存在するかチェック
            cursor.execute("PRAGMA table_info(g4f_providers)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'working_model' not in columns:
                try:
                    cursor.execute("ALTER TABLE g4f_providers ADD COLUMN working_model TEXT")
                    logger.info("[DB] working_modelカラムを追加しました")
                except Exception as e:
                    logger.error(f"[DB] マイグレーションエラー: {e}")
            
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

class ProviderHealthMonitor:
    """プロバイダー健全性監視クラス"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.test_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.is_running = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """監視開始"""
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("[G4F_MONITOR] プロバイダー監視開始")
    
    def stop_monitoring(self):
        """監視停止"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("[G4F_MONITOR] プロバイダー監視停止")
    
    def _monitor_loop(self):
        """監視ループ"""
        while self.is_running:
            try:
                # 30分間隔でプロバイダーをテスト
                time.sleep(1800)  # 30分
                if self.is_running:
                    self.test_queue.put("test_all_providers")
            except Exception as e:
                logger.error(f"[G4F_MONITOR] 監視ループエラー: {e}")
                time.sleep(60)
    
    def record_provider_result(self, provider_name: str, success: bool, response_time: float, 
                              error_msg: str = "", working_model: str = ""):
        """プロバイダー結果記録"""
        try:
            # 既存レコード取得
            existing = self.db_manager.execute_query(
                "SELECT success_rate, total_requests, error_count FROM g4f_providers WHERE provider_name=?",
                (provider_name,)
            )
            
            if existing:
                success_rate, total_requests, error_count = existing[0]
                new_total = total_requests + 1
                new_errors = error_count + (0 if success else 1)
                new_success_rate = (total_requests * success_rate + (1 if success else 0)) / new_total
                
                self.db_manager.execute_insert(
                    """UPDATE g4f_providers SET 
                       is_active=?, last_test_time=CURRENT_TIMESTAMP, success_rate=?, 
                       response_time=?, error_count=?, total_requests=?, last_error=?, working_model=?
                       WHERE provider_name=?""",
                    (success, new_success_rate, response_time, new_errors, new_total, 
                     error_msg, working_model, provider_name)
                )
            else:
                # 新規レコード作成
                self.db_manager.execute_insert(
                    """INSERT INTO g4f_providers 
                       (provider_name, is_active, last_test_time, success_rate, response_time, 
                        error_count, total_requests, last_error, working_model) 
                       VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)""",
                    (provider_name, success, 1.0 if success else 0.0, response_time, 
                     0 if success else 1, 1, error_msg, working_model)
                )
                
            logger.info(f"[G4F_MONITOR] プロバイダー結果記録: {provider_name} - {'成功' if success else '失敗'}")
            
        except Exception as e:
            logger.error(f"[G4F_MONITOR] プロバイダー結果記録エラー: {e}")

class G4FManager:
    """g4fライブラリ管理クラス（最新対応版）"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.client = None
        self.available_providers = []
        self.current_provider = None
        self.current_model = None
        self.provider_stats = {}
        self.health_monitor = ProviderHealthMonitor(db_manager)
        self.last_provider_test = 0
        self.provider_test_interval = 300  # 5分間隔
        self.max_retries = 3
        self.timeout = 30
        self.lock = threading.Lock()
        
        # 2025年対応プロバイダー・モデル組み合わせ
        self.provider_model_map = self._get_current_provider_models()
        
        self.init_g4f()
        self.health_monitor.start_monitoring()
    
    def _get_current_provider_models(self) -> Dict:
        """2025年現在の有効なプロバイダー・モデル組み合わせ"""
        return {
            # 高成功率プロバイダー
            'Liaobots': ['claude-3-sonnet', 'gpt-4', 'gemini-pro'],
            'DDG': ['gpt-4o-mini', 'claude-3-haiku', 'llama-3-8b'],
            'Bing': ['gpt-4', 'copilot'],
            'You': ['gpt-4o', 'claude-3-sonnet', 'llama-3-70b'],
            'Blackbox': ['blackbox', 'gpt-4o'],
            
            # 中成功率プロバイダー
            'ChatGpt': ['gpt-4o-mini', 'gpt-4'],
            'Phind': ['phind-codellama', 'gpt-4'],
            'FreeChatgpt': ['gpt-3.5-turbo', 'gpt-4'],
            'GPTalk': ['gpt-3.5-turbo'],
            'AiMathGPT': ['gpt-4o-mini'],
            
            # 試験的プロバイダー
            'OpenaiChat': ['gpt-4o', 'gpt-4o-mini'],
            'ChatBase': ['gpt-3.5-turbo'],
            'FreeGpt': ['gpt-3.5-turbo'],
            'Yqcloud': ['gpt-4'],
            'HuggingChat': ['llama-3-70b', 'mistral-7b'],
        }
    
    def init_g4f(self):
        """g4f初期化（2025年対応版）"""
        if not G4F_AVAILABLE:
            logger.warning("[G4F] g4fライブラリが利用できません")
            return
        
        try:
            self.client = Client()
            self.find_available_providers()
            logger.info(f"[G4F] 初期化完了。利用可能プロバイダー: {len(self.available_providers)}個")
            
        except Exception as e:
            logger.error(f"[G4F] 初期化エラー: {e}")
            # 初期化失敗時は再試行
            threading.Timer(30.0, self.init_g4f).start()
    
    def find_available_providers(self):
        """利用可能プロバイダー検索（2025年対応版）"""
        logger.info(f"[G4F] プロバイダーテスト開始: {len(self.provider_model_map)}個")
        
        working_providers = []
        
        # 各プロバイダーを順次テスト（並列処理は不安定なため順次実行）
        for provider_name, models in self.provider_model_map.items():
            try:
                if not hasattr(Provider, provider_name):
                    continue
                
                provider_class = getattr(Provider, provider_name)
                is_working, response_time, error_msg, working_model = self._test_provider_with_models(
                    provider_class, models
                )
                
                # 結果を記録
                self.health_monitor.record_provider_result(
                    provider_name, is_working, response_time, error_msg, working_model
                )
                
                if is_working:
                    working_providers.append({
                        'provider': provider_class,
                        'model': working_model,
                        'response_time': response_time
                    })
                    logger.info(f"[G4F] プロバイダー利用可能: {provider_name} + {working_model} ({response_time:.2f}s)")
                else:
                    logger.warning(f"[G4F] プロバイダー利用不可: {provider_name} - {error_msg}")
                    
            except Exception as e:
                logger.error(f"[G4F] プロバイダーテストエラー: {provider_name} - {e}")
        
        with self.lock:
            self.available_providers = working_providers
            if self.available_providers:
                # 応答時間でソートして最も高速なものを選択
                self.available_providers.sort(key=lambda x: x['response_time'])
                self.current_provider = self.available_providers[0]['provider']
                self.current_model = self.available_providers[0]['model']
                logger.info(f"[G4F] 利用可能プロバイダー: {len(self.available_providers)}個")
                logger.info(f"[G4F] 現在の設定: {self.current_provider.__name__} + {self.current_model}")
            else:
                logger.error("[G4F] 利用可能なプロバイダーがありません")
        
        self.last_provider_test = time.time()
    
    def _test_provider_with_models(self, provider_class, models: List[str]) -> Tuple[bool, float, str, str]:
        """プロバイダーとモデルの組み合わせテスト"""
        for model in models:
            try:
                start_time = time.time()
                
                # 日本語テストメッセージ
                test_message = "こんにちは"
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": test_message}],
                    provider=provider_class,
                    timeout=15  # 短いタイムアウト
                )
                
                response_time = time.time() - start_time
                
                if response and isinstance(response, str) and len(response.strip()) > 0:
                    if self._is_valid_japanese_response(response):
                        return True, response_time, "", model
                
            except Exception as e:
                error_msg = str(e)
                logger.debug(f"[G4F] モデル {model} テスト失敗: {error_msg}")
                continue
        
        return False, 0.0, "全モデルで失敗", ""
    
    def _is_valid_japanese_response(self, response: str) -> bool:
        """日本語応答の妥当性チェック"""
        if not response or len(response.strip()) < 1:
            return False
        
        # 基本的な応答チェック（日本語でなくても有効なレスポンスは受け入れる）
        invalid_patterns = [
            r'^Error:.*', r'^Sorry.*', r'^I apologize.*', 
            r'.*error occurred.*', r'.*something went wrong.*',
            r'.*errors.*', r'.*failed.*', r'.*unavailable.*'
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return False
        
        return True
    
    def get_best_provider(self):
        """最適なプロバイダーを選択"""
        if not self.available_providers:
            return None, None
        
        # 成功率の高いプロバイダーを優先
        best_provider = self.available_providers[0]
        return best_provider['provider'], best_provider['model']
    
    def generate_response(self, prompt: str, persona_context: str = "") -> str:
        """AI応答生成（2025年対応版）"""
        if not self.client:
            logger.warning("[G4F] クライアントが利用できません")
            return None
        
        # 定期的なプロバイダーテスト
        if time.time() - self.last_provider_test > self.provider_test_interval:
            threading.Thread(target=self.find_available_providers, daemon=True).start()
        
        if not self.available_providers:
            logger.warning("[G4F] 利用可能なプロバイダーがありません")
            return None
        
        # フルプロンプト構築
        full_prompt = f"{persona_context}\n\n{prompt}" if persona_context else prompt
        
        # リトライ処理
        for attempt in range(self.max_retries):
            provider, model = self.get_best_provider()
            if not provider or not model:
                break
            
            try:
                start_time = time.time()
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": full_prompt}],
                    provider=provider,
                    timeout=self.timeout
                )
                
                response_time = time.time() - start_time
                
                if response and isinstance(response, str):
                    cleaned_response = self.clean_response(response)
                    if cleaned_response:
                        # 成功を記録
                        self.health_monitor.record_provider_result(
                            provider.__name__, True, response_time, "", model
                        )
                        logger.info(f"[G4F] 応答生成成功: {provider.__name__} + {model}")
                        return cleaned_response
                
                # 失敗を記録
                self.health_monitor.record_provider_result(
                    provider.__name__, False, response_time, "無効な応答", model
                )
                
            except Exception as e:
                response_time = time.time() - start_time if 'start_time' in locals() else 0
                error_msg = str(e)
                
                # エラーを記録
                self.health_monitor.record_provider_result(
                    provider.__name__, False, response_time, error_msg, model or ""
                )
                
                logger.warning(f"[G4F] プロバイダーエラー: {provider.__name__} - {error_msg}")
                
                # プロバイダーを一時的に除外
                with self.lock:
                    self.available_providers = [p for p in self.available_providers if p['provider'] != provider]
        
        # 全て失敗した場合
        logger.error("[G4F] 全プロバイダーで応答生成に失敗しました")
        return None
    
    def clean_response(self, response: str) -> str:
        """応答のクリーニング（強化版）"""
        if not response:
            return ""
        
        # 強化されたエラーパターン
        error_patterns = [
            # 英語エラーパターン
            r'^Error:.*', r'^Sorry.*', r'^I apologize.*', r'^Unable to.*',
            r'^Cannot.*', r'.*error occurred.*', r'.*something went wrong.*',
            r'^I\'m sorry.*', r'^I can\'t.*', r'.*not available.*',
            r'.*system error.*', r'.*service unavailable.*',
            
            # 中国語エラーパターン
            r'.*错误.*', r'.*失败.*', r'.*异常.*', r'.*系统.*错误.*',
            r'.*抱歉.*', r'.*无法.*', r'.*不能.*',
            
            # 日本語エラーパターン
            r'.*エラー.*', r'.*失敗.*', r'.*利用.*できません.*',
            r'.*申し訳.*', r'.*すみません.*システム.*',
            r'.*AI.*利用.*', r'.*システム.*エラー.*',
            r'.*現在.*利用.*できません.*', r'.*サービス.*利用.*できません.*',
            r'.*接続.*エラー.*', r'.*応答.*生成.*できません.*'
        ]
        
        # エラーパターンチェック
        for pattern in error_patterns:
            if re.search(pattern, response.strip(), re.IGNORECASE):
                return ""
        
        # AI関連の文言を自然に修正
        response = re.sub(r'AI.*として.*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'人工知能.*です.*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'アシスタント.*', '', response, flags=re.IGNORECASE)
        
        return response.strip()
    
    def get_provider_statistics(self) -> Dict:
        """プロバイダー統計取得"""
        stats = self.db_manager.execute_query(
            """SELECT provider_name, is_active, success_rate, response_time, 
               error_count, total_requests, last_error, working_model
               FROM g4f_providers ORDER BY success_rate DESC"""
        )
        
        return {
            'total_providers': len(self.provider_model_map),
            'available_providers': len(self.available_providers),
            'current_provider': self.current_provider.__name__ if self.current_provider else None,
            'current_model': self.current_model,
            'provider_details': [
                {
                    'name': s[0],
                    'active': bool(s[1]),
                    'success_rate': s[2],
                    'response_time': s[3],
                    'error_count': s[4],
                    'total_requests': s[5],
                    'last_error': s[6],
                    'working_model': s[7]
                }
                for s in stats
            ]
        }
    
    def force_provider_refresh(self):
        """プロバイダー強制更新"""
        logger.info("[G4F] プロバイダー強制更新開始")
        threading.Thread(target=self.find_available_providers, daemon=True).start()

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
    
    def get_all_threads(self) -> List[Dict]:
        """全スレッド取得"""
        threads = self.db_manager.execute_query(
            """SELECT thread_id, category_main, category_sub, title, post_count, 
               last_post_time, last_ai_post_time FROM threads WHERE status='active'"""
        )
        
        return [
            {
                "thread_id": t[0],
                "category_main": t[1],
                "category_sub": t[2],
                "title": t[3],
                "post_count": t[4] or 0,
                "last_post_time": t[5],
                "last_ai_post_time": t[6]
            }
            for t in threads
        ]
    
    def get_thread_posts(self, thread_id: int, limit: int = 50) -> List[Dict]:
        """スレッド投稿取得"""
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
            for p in reversed(posts)
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
            if is_user_post:
                self.db_manager.execute_insert(
                    """UPDATE threads SET 
                       post_count = (SELECT COUNT(*) FROM posts WHERE thread_id = ?),
                       last_post_time = CURRENT_TIMESTAMP 
                       WHERE thread_id = ?""",
                    (thread_id, thread_id)
                )
            else:
                self.db_manager.execute_insert(
                    """UPDATE threads SET 
                       post_count = (SELECT COUNT(*) FROM posts WHERE thread_id = ?),
                       last_post_time = CURRENT_TIMESTAMP,
                       last_ai_post_time = CURRENT_TIMESTAMP
                       WHERE thread_id = ?""",
                    (thread_id, thread_id)
                )
            
            logger.info(f"[THREAD] 投稿追加: {persona_name} -> Thread {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"[THREAD] 投稿追加エラー: {e}")
            return False
    
    def get_seconds_since_last_ai_post(self, thread_id: int) -> float:
        """最後のAI投稿からの経過秒数を取得"""
        try:
            result = self.db_manager.execute_query(
                "SELECT last_ai_post_time FROM threads WHERE thread_id=?",
                (thread_id,)
            )
            
            if result and result[0][0]:
                last_time = datetime.datetime.fromisoformat(result[0][0])
                now = datetime.datetime.now()
                return (now - last_time).total_seconds()
            else:
                return 999999  # 投稿がない場合は十分大きな値
                
        except Exception as e:
            logger.error(f"[THREAD] 最終AI投稿時間取得エラー: {e}")
            return 999999

class BBSApplication:
    """メインアプリケーションクラス"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        
        # コンポーネント初期化
        self.db_manager = DatabaseManager()
        self.g4f_manager = G4FManager(self.db_manager)
        self.thread_manager = ThreadManager(self.db_manager)
        self.persona_manager = PersonaManager(self.db_manager, self.g4f_manager)
        
        # UI状態
        self.current_category = "雑談"
        self.current_thread_id = None
        self.admin_mode = False
        self.ai_activity_enabled = True
        self.auto_post_interval = 45
        
        # メッセージキュー
        self.message_queue = queue.Queue()
        
        # GUI構築
        self.create_widgets()
        self.setup_keybindings()
        
        # 人間らしい自動投稿システム開始
        self.start_human_like_posting()
        
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
        admin_window.title("管理パネル - g4f最新対応版")
        admin_window.geometry("700x700")
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
        
        # g4f管理
        g4f_frame = ttk.Frame(admin_window, style='BBS.TFrame')
        g4f_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(g4f_frame, text="g4f管理 (2025年対応版):", style='BBS.TLabel').pack(anchor=tk.W)
        
        g4f_button_frame = ttk.Frame(g4f_frame, style='BBS.TFrame')
        g4f_button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            g4f_button_frame,
            text="プロバイダー再検索",
            command=self.g4f_manager.force_provider_refresh,
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # 現在の接続状況表示
        connection_frame = ttk.Frame(admin_window, style='BBS.TFrame')
        connection_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(connection_frame, text="現在の接続状況:", style='BBS.TLabel').pack(anchor=tk.W)
        
        connection_text = tk.Text(
            connection_frame,
            bg="#000080",
            fg="#FFFFFF",
            font=('MS Gothic', 9),
            height=3,
            state=tk.DISABLED
        )
        connection_text.pack(fill=tk.X, pady=5)
        
        def update_connection_status():
            connection_text.config(state=tk.NORMAL)
            connection_text.delete(1.0, tk.END)
            
            if self.g4f_manager.current_provider and self.g4f_manager.current_model:
                connection_text.insert(tk.END, f"✓ 接続中: {self.g4f_manager.current_provider.__name__}\n")
                connection_text.insert(tk.END, f"  使用モデル: {self.g4f_manager.current_model}\n")
                connection_text.insert(tk.END, f"  利用可能プロバイダー: {len(self.g4f_manager.available_providers)}個")
            else:
                connection_text.insert(tk.END, "✗ 接続なし\n")
                connection_text.insert(tk.END, "利用可能なプロバイダーがありません")
            
            connection_text.config(state=tk.DISABLED)
        
        update_connection_status()
        
        ttk.Button(
            connection_frame,
            text="接続状況更新",
            command=update_connection_status,
            style='BBS.TButton'
        ).pack(pady=2)
        
        # g4f統計表示
        stats_frame = ttk.Frame(admin_window, style='BBS.TFrame')
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(stats_frame, text="g4fプロバイダー統計 (2025年最新):", style='BBS.TLabel').pack(anchor=tk.W)
        
        stats_text = scrolledtext.ScrolledText(
            stats_frame,
            bg="#000000",
            fg="#00FF00",
            font=('MS Gothic', 8),
            height=20,
            state=tk.DISABLED
        )
        stats_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        def update_all_stats():
            try:
                stats = self.g4f_manager.get_provider_statistics()
                
                stats_text.config(state=tk.NORMAL)
                stats_text.delete(1.0, tk.END)
                
                stats_text.insert(tk.END, f"■ g4fシステム統計 (Version {APP_VERSION}) ■\n")
                stats_text.insert(tk.END, f"総プロバイダー数: {stats['total_providers']}\n")
                stats_text.insert(tk.END, f"利用可能: {stats['available_providers']}\n")
                stats_text.insert(tk.END, f"現在使用中: {stats['current_provider'] or 'なし'}\n")
                stats_text.insert(tk.END, f"現在のモデル: {stats['current_model'] or 'なし'}\n\n")
                
                stats_text.insert(tk.END, "■ プロバイダー詳細 ■\n")
                for provider in stats['provider_details']:
                    status = "✓" if provider['active'] else "✗"
                    stats_text.insert(tk.END, f"{status} {provider['name']}\n")
                    stats_text.insert(tk.END, f"   動作モデル: {provider['working_model'] or 'なし'}\n")
                    stats_text.insert(tk.END, f"   成功率: {provider['success_rate']:.1%}\n")
                    stats_text.insert(tk.END, f"   応答時間: {provider['response_time']:.2f}s\n")
                    stats_text.insert(tk.END, f"   エラー: {provider['error_count']}/{provider['total_requests']}\n")
                    if provider['last_error']:
                        stats_text.insert(tk.END, f"   最終エラー: {provider['last_error'][:50]}...\n")
                    stats_text.insert(tk.END, "\n")
                
                stats_text.config(state=tk.DISABLED)
                
            except Exception as e:
                logger.error(f"[ADMIN] 統計更新エラー: {e}")
        
        update_all_stats()
        
        ttk.Button(
            stats_frame,
            text="統計更新",
            command=update_all_stats,
            style='BBS.TButton'
        ).pack(pady=5)
        
        # バージョン情報
        version_frame = ttk.Frame(admin_window, style='BBS.TFrame')
        version_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(version_frame, text="バージョン情報:", style='BBS.TLabel').pack(anchor=tk.W)
        ttk.Label(
            version_frame, 
            text=f"草の根BBS v{APP_VERSION}\ng4f最新対応・DB修正版\n開発日: 2025年7月\n対応プロバイダー: Liaobots, DDG, Bing, You, Blackbox等",
            style='BBS.TLabel'
        ).pack(anchor=tk.W, pady=5)
    
    def set_ai_activity(self, enabled: bool):
        """AI活動設定"""
        self.ai_activity_enabled = enabled
        self.update_status()
        logger.info(f"[ADMIN] AI活動: {'有効' if enabled else '無効'}")
    
    def update_status(self):
        """ステータス更新"""
        provider_status = ""
        if self.g4f_manager.current_provider and self.g4f_manager.current_model:
            provider_status = f" | {self.g4f_manager.current_provider.__name__}+{self.g4f_manager.current_model}"
        
        status_text = f"Version: {APP_VERSION} | AI活動: {'ON' if self.ai_activity_enabled else 'OFF'} | 管理モード: {'ON' if self.admin_mode else 'OFF'}{provider_status}"
        self.status_label.config(text=status_text)
    
    def start_human_like_posting(self):
        """人間らしい自動投稿システム開始"""
        def human_like_post_worker():
            """人間らしい投稿ワーカー"""
            while True:
                try:
                    if not self.ai_activity_enabled:
                        time.sleep(10)
                        continue
                    
                    # 全スレッドを取得
                    all_threads = self.thread_manager.get_all_threads()
                    if not all_threads:
                        time.sleep(30)
                        continue
                    
                    # 投稿候補スレッドを選出
                    candidate_threads = []
                    for thread in all_threads:
                        thread_id = thread['thread_id']
                        seconds_since_last_ai_post = self.thread_manager.get_seconds_since_last_ai_post(thread_id)
                        
                        if seconds_since_last_ai_post >= 30:
                            probability = min(0.95, 0.5 + (seconds_since_last_ai_post - 30) * 0.01)
                            
                            if random.random() < probability:
                                candidate_threads.append({
                                    'thread': thread,
                                    'seconds_since': seconds_since_last_ai_post,
                                    'priority': seconds_since_last_ai_post + random.uniform(0, 10)
                                })
                    
                    # 優先度順でソート
                    candidate_threads.sort(key=lambda x: x['priority'], reverse=True)
                    
                    # 上位1-3スレッドに投稿
                    post_count = min(len(candidate_threads), random.choice([1, 1, 1, 2, 2, 3]))
                    
                    for i in range(post_count):
                        if i < len(candidate_threads):
                            thread_data = candidate_threads[i]['thread']
                            thread_id = thread_data['thread_id']
                            
                            logger.info(f"[HUMAN_POST] 投稿対象選択: Thread {thread_id}")
                            
                            # ペルソナによる投稿生成
                            success = self.persona_manager.generate_auto_post(thread_id)
                            
                            if success:
                                # UI更新をメインスレッドに依頼
                                self.message_queue.put(('update_display', None))
                                logger.info(f"[HUMAN_POST] 投稿成功: Thread {thread_id}")
                            
                            # 投稿間隔
                            post_interval = random.uniform(2, 8)
                            time.sleep(post_interval)
                    
                    # 次のチェックまでの待機時間
                    check_interval = random.uniform(5, 15)
                    time.sleep(check_interval)
                    
                except Exception as e:
                    logger.error(f"[HUMAN_POST] エラー: {e}")
                    time.sleep(30)
        
        human_post_thread = threading.Thread(target=human_like_post_worker, daemon=True)
        human_post_thread.start()
        logger.info("[APP] 人間らしい自動投稿システム開始")
    
    def process_messages(self):
        """メッセージキュー処理"""
        try:
            while True:
                message_type, data = self.message_queue.get_nowait()
                
                if message_type == 'update_display':
                    self.update_post_display()
                    self.update_thread_list()
                    self.update_status()
                elif message_type == 'show_notification':
                    messagebox.showinfo("通知", data)
                
        except queue.Empty:
            pass
        
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
            self.g4f_manager.health_monitor.stop_monitoring()
            logger.info("[APP] アプリケーション終了")

def main():
    """メイン関数"""
    print("=" * 60)
    print("  草の根BBS - PC-98時代パソコン通信の再現")
    print(f"  Version: {APP_VERSION} (g4f最新対応・DB修正版)")
    print("=" * 60)
    print("[SYSTEM] アプリケーション初期化中...")
    
    try:
        app = BBSApplication()
        print("[SYSTEM] 初期化完了。アプリケーションを開始します。")
        print("[INFO] 主な改善点:")
        print("  ✓ データベースマイグレーション対応")
        print("  ✓ 2025年最新g4fプロバイダー・モデル対応")
        print("  ✓ プロバイダー個別テスト実装")
        print("  ✓ エラー完全除外システム")
        print("[INFO] キーボード操作:")
        print("  Ctrl+Enter: 投稿")
        print("  F5: 更新")
        print("  F12: 管理モード（接続状況・統計表示）")
        print("  Ctrl+Q: 終了")
        app.run()
    except Exception as e:
        print(f"[ERROR] アプリケーション開始エラー: {e}")
        logger.error(f"アプリケーション開始エラー: {e}")

if __name__ == "__main__":
    main()
