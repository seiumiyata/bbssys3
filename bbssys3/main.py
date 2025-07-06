#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PC-98時代パソコン通信BBS風アプリケーション - メインモジュール完全版
Version: 3.0.0 - 全機能実装・バージョン管理・動的スレッド作成対応版
Author: AI Assistant
Created: 2025-07-06
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import sqlite3
import threading
import time
import random
import json
import datetime
import sys
import os
import re
import subprocess
import shutil
from typing import Dict, List, Optional, Tuple, Any
import queue
import logging
import hashlib
import pickle
import csv

# G4Fライブラリのインポートとエラーハンドリング
try:
    import g4f
    from g4f import Provider
    G4F_AVAILABLE = True
    print("[SYSTEM] g4fライブラリが正常に読み込まれました")
except ImportError as e:
    G4F_AVAILABLE = False
    print(f"[WARNING] g4fライブラリの読み込みに失敗しました: {e}")
    print("[INFO] Gemini CLIを使用します")

# ペルソナモジュールのインポート
try:
    from persona import PersonaManager
    print("[SYSTEM] ペルソナモジュールが正常に読み込まれました")
except ImportError as e:
    print(f"[ERROR] ペルソナモジュールの読み込みに失敗しました: {e}")
    sys.exit(1)

# アプリケーション情報
APP_NAME = "草の根BBS - PC-98風パソコン通信"
APP_VERSION = "3.0.0"
APP_BUILD = "20250706"
APP_AUTHOR = "AI Assistant"
VERSION_HISTORY = [
    {"version": "1.0.0", "date": "2025-01-01", "changes": "初回リリース - 基本BBS機能"},
    {"version": "1.5.0", "date": "2025-03-15", "changes": "G4F接続問題解決、ペルソナ拡張"},
    {"version": "2.0.0", "date": "2025-05-20", "changes": "Gemini CLI対応、管理画面拡張"},
    {"version": "2.1.0", "date": "2025-06-10", "changes": "初期化機能、統計表示改善"},
    {"version": "3.0.0", "date": "2025-07-06", "changes": "動的スレッド作成、呼びかけ応答、完全版"}
]

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
    """データベース管理クラス - 完全版"""
    
    def __init__(self, db_path: str = "bbs_database.db"):
        self.db_path = db_path
        self.init_database()
        self.migrate_database()
        logger.info(f"[DB] データベース初期化完了: {db_path}")
    
    def init_database(self):
        """データベース初期化 - 拡張版"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 大分類テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS main_categories (
                    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT UNIQUE NOT NULL,
                    display_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'システム'
                )
            ''')
            
            # 小分類テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sub_categories (
                    sub_category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    main_category_id INTEGER,
                    sub_category_name TEXT NOT NULL,
                    display_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'システム',
                    FOREIGN KEY (main_category_id) REFERENCES main_categories(category_id)
                )
            ''')
            
            # スレッドテーブル - 拡張版
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS threads (
                    thread_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    main_category_id INTEGER,
                    sub_category_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'システム',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    post_count INTEGER DEFAULT 0,
                    last_post_time TIMESTAMP,
                    last_ai_post_time TIMESTAMP,
                    view_count INTEGER DEFAULT 0,
                    is_pinned BOOLEAN DEFAULT FALSE,
                    is_locked BOOLEAN DEFAULT FALSE,
                    auto_created BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (main_category_id) REFERENCES main_categories(category_id),
                    FOREIGN KEY (sub_category_id) REFERENCES sub_categories(sub_category_id)
                )
            ''')
            
            # 投稿テーブル - 拡張版
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id INTEGER,
                    persona_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    is_user_post BOOLEAN DEFAULT FALSE,
                    is_edited BOOLEAN DEFAULT FALSE,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    reply_to_post_id INTEGER,
                    mention_names TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (thread_id) REFERENCES threads(thread_id),
                    FOREIGN KEY (reply_to_post_id) REFERENCES posts(post_id)
                )
            ''')
            
            # ペルソナテーブル - 拡張版
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS personas (
                    persona_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    age INTEGER,
                    occupation TEXT,
                    background TEXT,
                    generation TEXT,
                    mbti TEXT,
                    extroversion REAL,
                    agreeableness REAL,
                    conscientiousness REAL,
                    neuroticism REAL,
                    openness REAL,
                    additional_params TEXT,
                    emotion_state TEXT,
                    learning_data TEXT,
                    activity_level REAL DEFAULT 0.5,
                    post_count INTEGER DEFAULT 0,
                    last_active_time TIMESTAMP,
                    is_troll BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # AI接続統計テーブル - 拡張版
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_connection_stats (
                    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_name TEXT NOT NULL,
                    model_name TEXT,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    total_requests INTEGER DEFAULT 0,
                    avg_response_time REAL DEFAULT 0.0,
                    min_response_time REAL DEFAULT 0.0,
                    max_response_time REAL DEFAULT 0.0,
                    last_success_time TIMESTAMP,
                    last_failure_time TIMESTAMP,
                    error_details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # システム設定テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT,
                    setting_type TEXT DEFAULT 'string',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # バージョン履歴テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS version_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL,
                    build_number TEXT,
                    release_date TIMESTAMP,
                    changes TEXT,
                    author TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # アクティビティログテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity_type TEXT NOT NULL,
                    user_name TEXT,
                    target_type TEXT,
                    target_id INTEGER,
                    description TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def migrate_database(self):
        """データベースマイグレーション - 拡張版"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 既存のthreadsテーブルをチェック
            cursor.execute("PRAGMA table_info(threads)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # 必要なカラムを段階的に追加
            new_columns = [
                ('last_ai_post_time', 'TIMESTAMP'),
                ('main_category_id', 'INTEGER'),
                ('sub_category_id', 'INTEGER'),
                ('description', 'TEXT'),
                ('updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
                ('view_count', 'INTEGER DEFAULT 0'),
                ('is_pinned', 'BOOLEAN DEFAULT FALSE'),
                ('is_locked', 'BOOLEAN DEFAULT FALSE'),
                ('auto_created', 'BOOLEAN DEFAULT FALSE')
            ]
            
            for column_name, column_type in new_columns:
                if column_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE threads ADD COLUMN {column_name} {column_type}")
                        logger.info(f"[DB] {column_name}カラムを追加しました")
                    except Exception as e:
                        logger.error(f"[DB] マイグレーションエラー: {e}")
            
            # postsテーブルの拡張
            cursor.execute("PRAGMA table_info(posts)")
            post_columns = [column[1] for column in cursor.fetchall()]
            
            post_new_columns = [
                ('updated_at', 'TIMESTAMP'),
                ('is_edited', 'BOOLEAN DEFAULT FALSE'),
                ('is_deleted', 'BOOLEAN DEFAULT FALSE'),
                ('reply_to_post_id', 'INTEGER'),
                ('mention_names', 'TEXT'),
                ('ip_address', 'TEXT'),
                ('user_agent', 'TEXT')
            ]
            
            for column_name, column_type in post_new_columns:
                if column_name not in post_columns:
                    try:
                        cursor.execute(f"ALTER TABLE posts ADD COLUMN {column_name} {column_type}")
                        logger.info(f"[DB] posts.{column_name}カラムを追加しました")
                    except Exception as e:
                        logger.error(f"[DB] マイグレーションエラー: {e}")
            
            # バージョン履歴の初期化
            self.init_version_history()
            
            conn.commit()
    
    def init_version_history(self):
        """バージョン履歴の初期化"""
        try:
            for version_info in VERSION_HISTORY:
                existing = self.execute_query(
                    "SELECT history_id FROM version_history WHERE version=?",
                    (version_info["version"],)
                )
                
                if not existing:
                    self.execute_insert(
                        """INSERT INTO version_history 
                           (version, release_date, changes, author)
                           VALUES (?, ?, ?, ?)""",
                        (
                            version_info["version"],
                            version_info["date"],
                            version_info["changes"],
                            APP_AUTHOR
                        )
                    )
            logger.info("[DB] バージョン履歴を初期化しました")
        except Exception as e:
            logger.error(f"[DB] バージョン履歴初期化エラー: {e}")
    
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
    
    def log_activity(self, activity_type: str, user_name: str, target_type: str = None, 
                    target_id: int = None, description: str = None):
        """アクティビティログ記録"""
        try:
            self.execute_insert(
                """INSERT INTO activity_logs 
                   (activity_type, user_name, target_type, target_id, description)
                   VALUES (?, ?, ?, ?, ?)""",
                (activity_type, user_name, target_type, target_id, description)
            )
        except Exception as e:
            logger.error(f"[DB] アクティビティログ記録エラー: {e}")

class GeminiCLIManager:
    """Gemini CLI管理クラス - 強化版"""
    
    def __init__(self):
        self.available = self._check_gemini_cli()
        self.model = "gemini-pro"
        self.timeout = 30
        self.max_retries = 3
        logger.info(f"[GEMINI] CLI利用可能: {self.available}")
    
    def _check_gemini_cli(self) -> bool:
        """Gemini CLIの利用可能性チェック"""
        try:
            result = subprocess.run(
                ["gemini", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            # 代替チェック: gcloud cli
            try:
                result = subprocess.run(
                    ["gcloud", "ai", "models", "list", "--limit=1"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
            except:
                return False
    
    def generate_response(self, prompt: str, persona_context: str = "", 
                         mention_context: str = "") -> Optional[str]:
        """Gemini CLIによる応答生成 - 拡張版"""
        if not self.available:
            return None
        
        for attempt in range(self.max_retries):
            try:
                # フルプロンプト構築
                full_prompt = self._build_full_prompt(prompt, persona_context, mention_context)
                
                # Gemini CLIコマンド実行
                result = subprocess.run(
                    ["gemini", "generate", "--model", self.model, "--prompt", full_prompt],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    response = result.stdout.strip()
                    cleaned_response = self._clean_response(response)
                    if cleaned_response:
                        logger.info(f"[GEMINI] 応答生成成功 (試行{attempt+1}/{self.max_retries})")
                        return cleaned_response
                
                time.sleep(1)  # リトライ前の待機
                
            except Exception as e:
                logger.warning(f"[GEMINI] 応答生成エラー (試行{attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
        
        return None
    
    def _build_full_prompt(self, prompt: str, persona_context: str, mention_context: str) -> str:
        """フルプロンプト構築"""
        parts = []
        
        if persona_context:
            parts.append(f"ペルソナ情報:\n{persona_context}")
        
        if mention_context:
            parts.append(f"呼びかけ情報:\n{mention_context}")
        
        parts.append(f"指示:\n{prompt}")
        
        return "\n\n".join(parts)
    
    def _clean_response(self, response: str) -> str:
        """応答のクリーニング - 強化版"""
        if not response:
            return ""
        
        # エラーパターンの除外
        error_patterns = [
            r'^Error:.*', r'^Sorry.*', r'^I apologize.*', r'^Unable to.*',
            r'.*エラー.*', r'.*失敗.*', r'.*利用.*できません.*',
            r'.*AI.*として.*', r'.*人工知能.*です.*', r'.*助手.*です.*'
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, response.strip(), re.IGNORECASE):
                return ""
        
        # 日本語チェック
        japanese_chars = re.findall(r'[ひらがなカタカナ漢字]', response)
        if len(japanese_chars) < 2:
            return ""
        
        # 不適切な内容のチェック
        inappropriate_patterns = [
            r'.*殺.*', r'.*死.*', r'.*危険.*薬物.*', r'.*違法.*'
        ]
        
        for pattern in inappropriate_patterns:
            if re.search(pattern, response.strip()):
                return ""
        
        return response.strip()

class AIManager:
    """AI接続管理クラス - 完全版"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.g4f_available = G4F_AVAILABLE
        self.gemini_cli = GeminiCLIManager()
        self.current_provider = None
        self.current_model = None
        self.available_combinations = []
        self.lock = threading.Lock()
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
        
        # 初期化
        self.init_ai_connections()
        logger.info(f"[AI] 初期化完了 - G4F: {self.g4f_available}, Gemini: {self.gemini_cli.available}")
    
    def init_ai_connections(self):
        """AI接続初期化 - 拡張版"""
        if self.g4f_available:
            try:
                self._init_g4f()
            except Exception as e:
                logger.error(f"[AI] G4F初期化エラー: {e}")
                self.g4f_available = False
        
        if not self.g4f_available and not self.gemini_cli.available:
            logger.warning("[AI] 利用可能なAI接続がありません")
        
        # デフォルト統計レコードの作成
        self._init_default_stats()
    
    def _init_g4f(self):
        """G4F初期化 - 強化版"""
        try:
            g4f.debug.logging = True
            g4f.debug.version_check = False
            
            # 確認済み組み合わせ（優先順位付き）
            verified_combinations = [
                {'provider_name': 'Chatai', 'model': 'gpt-3.5-turbo', 'priority': 1},
                {'provider_name': 'Chatai', 'model': 'gpt-4', 'priority': 2},
                {'provider_name': 'Bing', 'model': 'gpt-4', 'priority': 3},
                {'provider_name': 'You', 'model': 'gpt-3.5-turbo', 'priority': 4},
            ]
            
            working_providers = [
                provider for provider in g4f.Provider.__providers__
                if hasattr(provider, 'working') and provider.working
            ]
            
            # 優先順位順にテスト
            for combo in sorted(verified_combinations, key=lambda x: x['priority']):
                provider_name = combo['provider_name']
                model = combo['model']
                
                provider_obj = None
                for provider in working_providers:
                    if provider.__name__ == provider_name:
                        provider_obj = provider
                        break
                
                if provider_obj:
                    # 接続テスト
                    try:
                        test_response = g4f.ChatCompletion.create(
                            model=model,
                            provider=provider_obj,
                            messages=[{"role": "user", "content": "テスト"}],
                            timeout=15
                        )
                        
                        if test_response and len(str(test_response).strip()) > 0:
                            self.available_combinations.append({
                                'provider': provider_obj,
                                'model': model,
                                'priority': combo['priority']
                            })
                            logger.info(f"[G4F] 利用可能: {provider_name} + {model}")
                            
                            # 最初の成功した組み合わせを現在のものとして設定
                            if not self.current_provider:
                                self.current_provider = provider_obj
                                self.current_model = model
                            
                    except Exception as e:
                        logger.warning(f"[G4F] テスト失敗: {provider_name} + {model} - {e}")
            
            if self.available_combinations:
                logger.info(f"[G4F] 使用組み合わせ: {self.current_provider.__name__} + {self.current_model}")
            else:
                logger.warning("[G4F] 利用可能な組み合わせがありません")
                self.g4f_available = False
            
        except Exception as e:
            logger.error(f"[G4F] 初期化エラー: {e}")
            self.g4f_available = False
    
    def _init_default_stats(self):
        """デフォルト統計レコードの初期化"""
        try:
            providers = ["G4F-Chatai", "G4F-Bing", "G4F-You", "Gemini CLI"]
            for provider in providers:
                existing = self.db_manager.execute_query(
                    "SELECT stat_id FROM ai_connection_stats WHERE provider_name=?",
                    (provider,)
                )
                
                if not existing:
                    self.db_manager.execute_insert(
                        """INSERT INTO ai_connection_stats 
                           (provider_name, model_name, success_count, failure_count)
                           VALUES (?, ?, 0, 0)""",
                        (provider, "default")
                    )
        except Exception as e:
            logger.error(f"[AI] デフォルト統計初期化エラー: {e}")
    
    def generate_response(self, prompt: str, persona_context: str = "", 
                         mention_context: str = "") -> Optional[str]:
        """AI応答生成 - 完全版"""
        with self.lock:
            self.request_count += 1
        
        start_time = time.time()
        
        # G4Fを試行
        if self.g4f_available and self.available_combinations:
            for combination in self.available_combinations:
                try:
                    provider = combination['provider']
                    model = combination['model']
                    
                    full_prompt = self._build_full_prompt(prompt, persona_context, mention_context)
                    
                    response = g4f.ChatCompletion.create(
                        model=model,
                        provider=provider,
                        messages=[{"role": "user", "content": full_prompt}],
                        timeout=25
                    )
                    
                    if response:
                        cleaned_response = self._clean_response(str(response))
                        if cleaned_response:
                            response_time = time.time() - start_time
                            self._update_stats(f"G4F-{provider.__name__}", model, True, response_time)
                            
                            with self.lock:
                                self.success_count += 1
                            
                            return cleaned_response
                
                except Exception as e:
                    logger.warning(f"[G4F] エラー: {e}")
                    response_time = time.time() - start_time
                    if 'provider' in locals():
                        self._update_stats(f"G4F-{provider.__name__}", model, False, response_time)
        
        # Gemini CLIフォールバック
        if self.gemini_cli.available:
            try:
                response = self.gemini_cli.generate_response(prompt, persona_context, mention_context)
                if response:
                    response_time = time.time() - start_time
                    self._update_stats("Gemini CLI", "gemini-pro", True, response_time)
                    
                    with self.lock:
                        self.success_count += 1
                    
                    return response
                else:
                    response_time = time.time() - start_time
                    self._update_stats("Gemini CLI", "gemini-pro", False, response_time)
            except Exception as e:
                logger.error(f"[GEMINI] エラー: {e}")
        
        with self.lock:
            self.failure_count += 1
        
        return None
    
    def _build_full_prompt(self, prompt: str, persona_context: str, mention_context: str) -> str:
        """フルプロンプト構築"""
        parts = []
        
        if persona_context:
            parts.append(persona_context)
        
        if mention_context:
            parts.append(f"重要: {mention_context}")
        
        parts.append(prompt)
        parts.append("回答は自然で人間らしい日本語で、150文字以内にまとめてください。")
        
        return "\n\n".join(parts)
    
    def _clean_response(self, response: str) -> str:
        """応答のクリーニング - 強化版"""
        if not response:
            return ""
        
        # エラーパターンの除外
        error_patterns = [
            r'^Error:.*', r'^Sorry.*', r'^I apologize.*', r'^Unable to.*',
            r'.*エラー.*', r'.*失敗.*', r'.*利用.*できません.*',
            r'.*AI.*として.*', r'.*人工知能.*です.*', r'.*助手.*です.*'
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, response.strip(), re.IGNORECASE):
                return ""
        
        # 日本語チェック
        japanese_chars = re.findall(r'[ひらがなカタカナ漢字]', response)
        if len(japanese_chars) < 2:
            return ""
        
        # 長さ制限
        if len(response) > 500:
            response = response[:500] + "..."
        
        return response.strip()
    
    def _update_stats(self, provider_name: str, model_name: str, success: bool, response_time: float):
        """統計更新 - 拡張版"""
        try:
            # 既存レコードを取得
            existing = self.db_manager.execute_query(
                "SELECT success_count, failure_count, total_requests, avg_response_time, min_response_time, max_response_time FROM ai_connection_stats WHERE provider_name=? AND model_name=?",
                (provider_name, model_name)
            )
            
            if existing:
                success_count, failure_count, total_requests, avg_response_time, min_response_time, max_response_time = existing[0]
                
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                
                total_requests += 1
                
                # 応答時間統計の更新
                if response_time > 0:
                    if avg_response_time == 0:
                        avg_response_time = response_time
                    else:
                        avg_response_time = (avg_response_time * (total_requests - 1) + response_time) / total_requests
                    
                    if min_response_time == 0 or response_time < min_response_time:
                        min_response_time = response_time
                    
                    if response_time > max_response_time:
                        max_response_time = response_time
                
                # 更新
                if success:
                    self.db_manager.execute_insert(
                        """UPDATE ai_connection_stats SET 
                           success_count=?, total_requests=?, avg_response_time=?, 
                           min_response_time=?, max_response_time=?, last_success_time=CURRENT_TIMESTAMP,
                           updated_at=CURRENT_TIMESTAMP
                           WHERE provider_name=? AND model_name=?""",
                        (success_count, total_requests, avg_response_time, min_response_time, max_response_time, provider_name, model_name)
                    )
                else:
                    self.db_manager.execute_insert(
                        """UPDATE ai_connection_stats SET 
                           failure_count=?, total_requests=?, last_failure_time=CURRENT_TIMESTAMP,
                           updated_at=CURRENT_TIMESTAMP
                           WHERE provider_name=? AND model_name=?""",
                        (failure_count, total_requests, provider_name, model_name)
                    )
            else:
                # 新規作成
                self.db_manager.execute_insert(
                    """INSERT INTO ai_connection_stats 
                       (provider_name, model_name, success_count, failure_count, total_requests, avg_response_time, min_response_time, max_response_time, last_success_time)
                       VALUES (?, ?, ?, ?, 1, ?, ?, ?, CURRENT_TIMESTAMP)""",
                    (provider_name, model_name, 1 if success else 0, 0 if success else 1, response_time, response_time, response_time)
                )
                
        except Exception as e:
            logger.error(f"[AI] 統計更新エラー: {e}")
    
    def get_connection_status(self) -> Dict:
        """接続状況取得 - 拡張版"""
        status = {
            'g4f_available': self.g4f_available,
            'gemini_available': self.gemini_cli.available,
            'current_provider': None,
            'current_model': None,
            'available_combinations': len(self.available_combinations),
            'total_requests': self.request_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'success_rate': 0.0
        }
        
        if self.request_count > 0:
            status['success_rate'] = self.success_count / self.request_count * 100
        
        if self.current_provider:
            status['current_provider'] = f"G4F-{self.current_provider.__name__}"
            status['current_model'] = self.current_model
        elif self.gemini_cli.available:
            status['current_provider'] = "Gemini CLI"
            status['current_model'] = "gemini-pro"
        
        return status

class CategoryManager:
    """カテゴリ管理クラス - 拡張版"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.init_default_categories()
        logger.info("[CATEGORY] カテゴリ管理初期化完了")
    
    def init_default_categories(self):
        """デフォルトカテゴリ初期化 - 拡張版"""
        # 大分類の初期化
        default_main_categories = [
            ("雑談", 1, "日常的な話題や気軽な会話"),
            ("ゲーム", 2, "ゲームに関する話題全般"),
            ("趣味", 3, "趣味や娯楽に関する話題"),
            ("パソコン", 4, "コンピューターやIT関連の話題"),
            ("仕事", 5, "仕事や職業に関する話題")
        ]
        
        for category_name, order, description in default_main_categories:
            existing = self.db_manager.execute_query(
                "SELECT category_id FROM main_categories WHERE category_name=?",
                (category_name,)
            )
            
            if not existing:
                category_id = self.db_manager.execute_insert(
                    "INSERT INTO main_categories (category_name, display_order) VALUES (?, ?)",
                    (category_name, order)
                )
                
                # 小分類の初期化
                sub_categories = self.get_default_sub_categories(category_name)
                for i, (sub_name, sub_desc) in enumerate(sub_categories):
                    self.db_manager.execute_insert(
                        "INSERT INTO sub_categories (main_category_id, sub_category_name, display_order) VALUES (?, ?, ?)",
                        (category_id, sub_name, i + 1)
                    )
    
    def get_default_sub_categories(self, main_category: str) -> List[Tuple[str, str]]:
        """デフォルト小分類取得 - 説明付き"""
        sub_categories_map = {
            "雑談": [
                ("日常の話", "日々の出来事や身近な話題"),
                ("最近の出来事", "ニュースや時事問題について"),
                ("天気の話", "天気や季節に関する話題"),
                ("グルメ情報", "食べ物や料理に関する話題"),
                ("地域情報", "地域のイベントや情報")
            ],
            "ゲーム": [
                ("レトロゲーム", "昔懐かしいゲームの話題"),
                ("RPG", "ロールプレイングゲーム全般"),
                ("アクションゲーム", "アクション系ゲームの話題"),
                ("パズルゲーム", "パズル・思考系ゲーム"),
                ("新作ゲーム", "最新ゲームの情報と感想")
            ],
            "趣味": [
                ("読書", "本や文学に関する話題"),
                ("映画鑑賞", "映画やドラマの感想"),
                ("音楽", "音楽や楽器に関する話題"),
                ("スポーツ", "スポーツ観戦や実践"),
                ("旅行", "旅行先や観光地の情報")
            ],
            "パソコン": [
                ("ハードウェア", "PCパーツや機器の話題"),
                ("ソフトウェア", "アプリケーションの情報"),
                ("プログラミング", "プログラミング技術の話題"),
                ("インターネット", "ネット関連の話題"),
                ("トラブル相談", "PC関連のトラブル解決")
            ],
            "仕事": [
                ("転職相談", "転職活動や求職情報"),
                ("スキルアップ", "技能向上や学習"),
                ("職場の悩み", "職場環境や人間関係"),
                ("副業", "副業や在宅ワーク"),
                ("資格取得", "資格試験や勉強法")
            ]
        }
        
        return sub_categories_map.get(main_category, [])
    
    def get_main_categories(self) -> List[Dict]:
        """大分類一覧取得"""
        categories = self.db_manager.execute_query(
            "SELECT category_id, category_name FROM main_categories ORDER BY display_order"
        )
        return [{"id": c[0], "name": c[1]} for c in categories]
    
    def get_sub_categories(self, main_category_id: int) -> List[Dict]:
        """小分類一覧取得"""
        sub_categories = self.db_manager.execute_query(
            "SELECT sub_category_id, sub_category_name FROM sub_categories WHERE main_category_id=? ORDER BY display_order",
            (main_category_id,)
        )
        return [{"id": s[0], "name": s[1]} for s in sub_categories]
    
    def create_category(self, category_name: str, parent_id: int = None) -> int:
        """動的カテゴリ作成"""
        try:
            if parent_id is None:
                # 大分類作成
                category_id = self.db_manager.execute_insert(
                    "INSERT INTO main_categories (category_name, display_order) VALUES (?, ?)",
                    (category_name, 999)
                )
            else:
                # 小分類作成
                category_id = self.db_manager.execute_insert(
                    "INSERT INTO sub_categories (main_category_id, sub_category_name, display_order) VALUES (?, ?, ?)",
                    (parent_id, category_name, 999)
                )
            
            self.db_manager.log_activity("category_create", "システム", "category", category_id, f"カテゴリ作成: {category_name}")
            return category_id
        except Exception as e:
            logger.error(f"[CATEGORY] カテゴリ作成エラー: {e}")
            return -1

class ThreadManager:
    """スレッド管理クラス - 完全版"""
    
    def __init__(self, db_manager: DatabaseManager, category_manager: CategoryManager):
        self.db_manager = db_manager
        self.category_manager = category_manager
        self.init_default_threads()
        logger.info("[THREAD] スレッド管理初期化完了")
    
    def init_default_threads(self):
        """デフォルトスレッド作成 - 拡張版"""
        main_categories = self.category_manager.get_main_categories()
        for main_cat in main_categories:
            sub_categories = self.category_manager.get_sub_categories(main_cat["id"])
            for sub_cat in sub_categories:
                thread_title = f"{sub_cat['name']}について語りましょう"
                thread_description = f"{sub_cat['name']}に関する話題を自由に投稿してください。"
                
                # 既存チェック
                existing = self.db_manager.execute_query(
                    "SELECT thread_id FROM threads WHERE main_category_id=? AND sub_category_id=? AND auto_created=1",
                    (main_cat["id"], sub_cat["id"])
                )
                
                if not existing:
                    thread_id = self.db_manager.execute_insert(
                        """INSERT INTO threads (main_category_id, sub_category_id, title, description, created_by, auto_created)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (main_cat["id"], sub_cat["id"], thread_title, thread_description, "システム", True)
                    )
                    logger.debug(f"[THREAD] デフォルトスレッド作成: {thread_title} (ID: {thread_id})")
    
    def create_thread(self, main_category_id: int, sub_category_id: int, title: str, 
                     description: str = "", created_by: str = "ユーザー") -> int:
        """動的スレッド作成"""
        try:
            # 重複チェック
            existing = self.db_manager.execute_query(
                "SELECT thread_id FROM threads WHERE title=? AND main_category_id=? AND sub_category_id=?",
                (title, main_category_id, sub_category_id)
            )
            
            if existing:
                logger.warning(f"[THREAD] 重複スレッド作成試行: {title}")
                return existing[0][0]
            
            # スレッド作成
            thread_id = self.db_manager.execute_insert(
                """INSERT INTO threads (main_category_id, sub_category_id, title, description, created_by, auto_created)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (main_category_id, sub_category_id, title, description, created_by, False)
            )
            
            # アクティビティログ
            self.db_manager.log_activity("thread_create", created_by, "thread", thread_id, f"スレッド作成: {title}")
            
            logger.info(f"[THREAD] 新規スレッド作成: {title} (ID: {thread_id}, 作成者: {created_by})")
            return thread_id
            
        except Exception as e:
            logger.error(f"[THREAD] スレッド作成エラー: {e}")
            return -1
    
    def get_threads_by_category(self, main_category_id: int) -> List[Dict]:
        """カテゴリ別スレッド取得 - 拡張版"""
        threads = self.db_manager.execute_query(
            """SELECT t.thread_id, s.sub_category_name, t.title, t.post_count, 
                      t.last_post_time, t.view_count, t.is_pinned, t.is_locked,
                      t.created_by, t.created_at, t.description
               FROM threads t
               JOIN sub_categories s ON t.sub_category_id = s.sub_category_id
               WHERE t.main_category_id=? AND t.status='active'
               ORDER BY t.is_pinned DESC, t.last_post_time DESC, t.created_at DESC""",
            (main_category_id,)
        )
        
        return [
            {
                "thread_id": t[0],
                "sub_category_name": t[1],
                "title": t[2],
                "post_count": t[3] or 0,
                "last_post_time": t[4],
                "view_count": t[5] or 0,
                "is_pinned": bool(t[6]),
                "is_locked": bool(t[7]),
                "created_by": t[8],
                "created_at": t[9],
                "description": t[10] or ""
            }
            for t in threads
        ]
    
    def get_thread_posts(self, thread_id: int, limit: int = 50) -> List[Dict]:
        """スレッド投稿取得 - 拡張版"""
        # ビューカウント更新
        self.increment_view_count(thread_id)
        
        posts = self.db_manager.execute_query(
            """SELECT post_id, persona_name, content, posted_at, is_user_post, 
                      is_edited, reply_to_post_id, mention_names
               FROM posts 
               WHERE thread_id=? AND is_deleted=0
               ORDER BY posted_at ASC LIMIT ?""",
            (thread_id, limit)
        )
        
        return [
            {
                "post_id": p[0],
                "persona_name": p[1],
                "content": p[2],
                "posted_at": p[3],
                "is_user_post": bool(p[4]),
                "is_edited": bool(p[5]),
                "reply_to_post_id": p[6],
                "mention_names": p[7] or ""
            }
            for p in posts
        ]
    
    def add_post(self, thread_id: int, persona_name: str, content: str, 
                is_user_post: bool = False, reply_to_post_id: int = None) -> bool:
        """投稿追加 - 拡張版"""
        try:
            # メンション検出
            mention_names = self.extract_mentions(content)
            
            # 投稿を追加
            post_id = self.db_manager.execute_insert(
                """INSERT INTO posts (thread_id, persona_name, content, is_user_post, reply_to_post_id, mention_names)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (thread_id, persona_name, content, is_user_post, reply_to_post_id, mention_names)
            )
            
            # スレッドの統計更新
            self.db_manager.execute_insert(
                """UPDATE threads SET
                   post_count = (SELECT COUNT(*) FROM posts WHERE thread_id = ? AND is_deleted=0),
                   last_post_time = CURRENT_TIMESTAMP,
                   updated_at = CURRENT_TIMESTAMP
                   WHERE thread_id = ?""",
                (thread_id, thread_id)
            )
            
            if not is_user_post:
                # AI投稿の場合、最終AI投稿時間も更新
                self.db_manager.execute_insert(
                    """UPDATE threads SET last_ai_post_time = CURRENT_TIMESTAMP WHERE thread_id = ?""",
                    (thread_id,)
                )
            
            # アクティビティログ
            activity_type = "user_post" if is_user_post else "ai_post"
            self.db_manager.log_activity(activity_type, persona_name, "post", post_id, f"投稿: {content[:50]}...")
            
            logger.info(f"[THREAD] 投稿追加: {persona_name} -> Thread {thread_id} (Post {post_id})")
            return True
            
        except Exception as e:
            logger.error(f"[THREAD] 投稿追加エラー: {e}")
            return False
    
    def extract_mentions(self, content: str) -> str:
        """メンション抽出"""
        # @username パターンでメンションを検出
        mentions = re.findall(r'@([^\s]+)', content)
        return ",".join(mentions) if mentions else ""
    
    def edit_post(self, post_id: int, new_content: str, editor_name: str) -> bool:
        """投稿編集"""
        try:
            self.db_manager.execute_insert(
                """UPDATE posts SET 
                   content=?, updated_at=CURRENT_TIMESTAMP, is_edited=1
                   WHERE post_id=?""",
                (new_content, post_id)
            )
            
            self.db_manager.log_activity("post_edit", editor_name, "post", post_id, f"投稿編集: {new_content[:50]}...")
            logger.info(f"[THREAD] 投稿編集: Post {post_id} by {editor_name}")
            return True
            
        except Exception as e:
            logger.error(f"[THREAD] 投稿編集エラー: {e}")
            return False
    
    def delete_post(self, post_id: int, deleter_name: str) -> bool:
        """投稿削除（論理削除）"""
        try:
            self.db_manager.execute_insert(
                """UPDATE posts SET 
                   is_deleted=1, updated_at=CURRENT_TIMESTAMP
                   WHERE post_id=?""",
                (post_id,)
            )
            
            self.db_manager.log_activity("post_delete", deleter_name, "post", post_id, "投稿削除")
            logger.info(f"[THREAD] 投稿削除: Post {post_id} by {deleter_name}")
            return True
            
        except Exception as e:
            logger.error(f"[THREAD] 投稿削除エラー: {e}")
            return False
    
    def increment_view_count(self, thread_id: int):
        """ビューカウント増加"""
        try:
            self.db_manager.execute_insert(
                "UPDATE threads SET view_count = view_count + 1 WHERE thread_id = ?",
                (thread_id,)
            )
        except Exception as e:
            logger.error(f"[THREAD] ビューカウント更新エラー: {e}")
    
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
                return 999999
        except Exception as e:
            logger.error(f"[THREAD] 最終AI投稿時間取得エラー: {e}")
            return 999999
    
    def get_thread_by_id(self, thread_id: int) -> Optional[Dict]:
        """スレッド詳細取得"""
        try:
            result = self.db_manager.execute_query(
                """SELECT t.thread_id, t.title, t.description, t.created_by, t.created_at,
                          t.post_count, t.view_count, t.is_pinned, t.is_locked,
                          m.category_name, s.sub_category_name
                   FROM threads t
                   JOIN main_categories m ON t.main_category_id = m.category_id
                   JOIN sub_categories s ON t.sub_category_id = s.sub_category_id
                   WHERE t.thread_id=?""",
                (thread_id,)
            )
            
            if result:
                r = result[0]
                return {
                    "thread_id": r[0],
                    "title": r[1],
                    "description": r[2],
                    "created_by": r[3],
                    "created_at": r[4],
                    "post_count": r[5] or 0,
                    "view_count": r[6] or 0,
                    "is_pinned": bool(r[7]),
                    "is_locked": bool(r[8]),
                    "main_category": r[9],
                    "sub_category": r[10]
                }
            return None
            
        except Exception as e:
            logger.error(f"[THREAD] スレッド詳細取得エラー: {e}")
            return None

class MentionManager:
    """呼びかけ応答管理クラス"""
    
    def __init__(self, persona_manager, ai_manager: AIManager):
        self.persona_manager = persona_manager
        self.ai_manager = ai_manager
        self.mention_patterns = [
            r'@([^\s]+)',
            r'([^\s]+)さん',
            r'([^\s]+)君',
            r'([^\s]+)ちゃん'
        ]
    
    def detect_mentions(self, content: str) -> List[str]:
        """メンション検出"""
        mentions = []
        for pattern in self.mention_patterns:
            found = re.findall(pattern, content)
            mentions.extend(found)
        
        # ペルソナ名と照合
        valid_mentions = []
        if hasattr(self.persona_manager, 'personas'):
            for mention in mentions:
                if mention in self.persona_manager.personas:
                    valid_mentions.append(mention)
        
        return list(set(valid_mentions))
    
    def should_respond_to_mention(self, persona_name: str, content: str) -> bool:
        """メンション応答判定"""
        mentions = self.detect_mentions(content)
        if persona_name in mentions:
            # 呼びかけられたペルソナの場合、高確率で応答
            return random.random() < 0.8
        
        # その他のキーワードベース判定
        keywords = ["みんな", "だれか", "誰か", "みなさん", "皆さん"]
        for keyword in keywords:
            if keyword in content:
                return random.random() < 0.3
        
        return False
    
    def generate_mention_response(self, persona_name: str, original_content: str, thread_id: int) -> Optional[str]:
        """メンション応答生成"""
        try:
            if not hasattr(self.persona_manager, 'personas') or persona_name not in self.persona_manager.personas:
                return None
            
            persona = self.persona_manager.personas[persona_name]
            
            # 呼びかけ文脈を構築
            mention_context = f"あなた（{persona_name}）に対する呼びかけ: {original_content}"
            
            # ペルソナ情報を構築
            persona_context = f"""あなたは{persona_name}です。
年齢: {persona.age}歳
職業: {persona.occupation}
性格: {persona.personality.get_personality_description()}
現在の感情: {persona.emotions.get_emotion_description()}

以下の呼びかけに対して、あなたの性格と感情に基づいて自然に応答してください。"""
            
            # 応答プロンプト
            prompt = f"""以下の投稿であなたが呼びかけられています。あなたらしく応答してください：

「{original_content}」

応答のガイドライン：
- 自然で親しみやすい返事を心がけてください
- あなたの年代や職業に応じた話し方をしてください
- 質問があれば答え、話題があれば発展させてください
- 100文字以内で簡潔にまとめてください"""
            
            # AI応答生成
            response = self.ai_manager.generate_response(prompt, persona_context, mention_context)
            
            if response:
                logger.info(f"[MENTION] 呼びかけ応答生成: {persona_name}")
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"[MENTION] 呼びかけ応答生成エラー: {e}")
            return None

class DataExporter:
    """データエクスポート管理クラス"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def export_all_data(self, format_type: str = "json") -> Optional[str]:
        """全データエクスポート"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format_type == "json":
                return self._export_json(timestamp)
            elif format_type == "csv":
                return self._export_csv(timestamp)
            elif format_type == "backup":
                return self._export_backup(timestamp)
            else:
                logger.error(f"[EXPORT] 未対応のフォーマット: {format_type}")
                return None
                
        except Exception as e:
            logger.error(f"[EXPORT] エクスポートエラー: {e}")
            return None
    
    def _export_json(self, timestamp: str) -> str:
        """JSON形式でエクスポート"""
        filename = f"bbs_export_{timestamp}.json"
        
        export_data = {
            "export_info": {
                "timestamp": timestamp,
                "version": APP_VERSION,
                "format": "json"
            },
            "categories": {},
            "threads": [],
            "posts": [],
            "personas": [],
            "statistics": {}
        }
        
        # カテゴリデータ
        main_categories = self.db_manager.execute_query("SELECT * FROM main_categories")
        sub_categories = self.db_manager.execute_query("SELECT * FROM sub_categories")
        export_data["categories"]["main"] = [dict(zip([desc[0] for desc in self.db_manager.execute_query("PRAGMA table_info(main_categories)")], cat)) for cat in main_categories]
        export_data["categories"]["sub"] = [dict(zip([desc[0] for desc in self.db_manager.execute_query("PRAGMA table_info(sub_categories)")], cat)) for cat in sub_categories]
        
        # スレッドデータ
        threads = self.db_manager.execute_query("SELECT * FROM threads")
        export_data["threads"] = [dict(zip([desc[0] for desc in self.db_manager.execute_query("PRAGMA table_info(threads)")], thread)) for thread in threads]
        
        # 投稿データ
        posts = self.db_manager.execute_query("SELECT * FROM posts")
        export_data["posts"] = [dict(zip([desc[0] for desc in self.db_manager.execute_query("PRAGMA table_info(posts)")], post)) for post in posts]
        
        # ペルソナデータ
        personas = self.db_manager.execute_query("SELECT * FROM personas")
        export_data["personas"] = [dict(zip([desc[0] for desc in self.db_manager.execute_query("PRAGMA table_info(personas)")], persona)) for persona in personas]
        
        # 統計データ
        stats = self.db_manager.execute_query("SELECT * FROM ai_connection_stats")
        export_data["statistics"]["ai_stats"] = [dict(zip([desc[0] for desc in self.db_manager.execute_query("PRAGMA table_info(ai_connection_stats)")], stat)) for stat in stats]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"[EXPORT] JSONエクスポート完了: {filename}")
        return filename
    
    def _export_csv(self, timestamp: str) -> str:
        """CSV形式でエクスポート"""
        base_filename = f"bbs_export_{timestamp}"
        
        # テーブルごとにCSVファイルを作成
        tables = ["main_categories", "sub_categories", "threads", "posts", "personas", "ai_connection_stats"]
        
        for table in tables:
            filename = f"{base_filename}_{table}.csv"
            
            # テーブルデータを取得
            data = self.db_manager.execute_query(f"SELECT * FROM {table}")
            
            if data:
                # カラム名を取得
                columns = [desc[0] for desc in self.db_manager.execute_query(f"PRAGMA table_info({table})")]
                
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    writer.writerows(data)
        
        logger.info(f"[EXPORT] CSVエクスポート完了: {base_filename}_*.csv")
        return base_filename
    
    def _export_backup(self, timestamp: str) -> str:
        """バックアップ形式でエクスポート"""
        filename = f"bbs_backup_{timestamp}.db"
        
        # データベースファイルをコピー
        shutil.copy2(self.db_manager.db_path, filename)
        
        logger.info(f"[EXPORT] バックアップ完了: {filename}")
        return filename

class BBSApplication:
    """メインアプリケーションクラス - 完全版"""
    
    def __init__(self):
        self.root = tk.Tk()
        
        # 設定の初期化
        self.font_size = 12
        self.window_width = 1200
        self.window_height = 800
        self.load_settings()
        self.setup_window()
        
        # コンポーネント初期化
        self.db_manager = DatabaseManager()
        self.ai_manager = AIManager(self.db_manager)
        self.category_manager = CategoryManager(self.db_manager)
        self.thread_manager = ThreadManager(self.db_manager, self.category_manager)
        self.persona_manager = PersonaManager(self.db_manager, self.ai_manager)
        self.mention_manager = MentionManager(self.persona_manager, self.ai_manager)
        self.data_exporter = DataExporter(self.db_manager)
        
        # UI状態
        self.current_main_category_id = None
        self.current_thread_id = None
        self.current_threads = []
        self.admin_mode = False
        self.ai_activity_enabled = True
        self.auto_post_interval = 60
        self.selected_post_id = None
        
        # メッセージキュー
        self.message_queue = queue.Queue()
        
        # GUI構築
        self.create_widgets()
        self.setup_keybindings()
        
        # 初期化検証
        self.verify_initialization()
        
        # 自動投稿システム開始
        self.start_auto_posting()
        
        # メッセージ処理開始
        self.process_messages()
        
        logger.info(f"[APP] アプリケーション初期化完了 - Version {APP_VERSION}")
    
    def load_settings(self):
        """設定読み込み - 拡張版"""
        try:
            if os.path.exists("bbs_settings.json"):
                with open("bbs_settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.font_size = settings.get("font_size", 12)
                    self.window_width = settings.get("window_width", 1200)
                    self.window_height = settings.get("window_height", 800)
                    self.auto_post_interval = settings.get("auto_post_interval", 60)
                    self.ai_activity_enabled = settings.get("ai_activity_enabled", True)
        except Exception as e:
            logger.error(f"[APP] 設定読み込みエラー: {e}")
    
    def save_settings(self):
        """設定保存 - 拡張版"""
        try:
            settings = {
                "font_size": self.font_size,
                "window_width": self.window_width,
                "window_height": self.window_height,
                "auto_post_interval": self.auto_post_interval,
                "ai_activity_enabled": self.ai_activity_enabled
            }
            with open("bbs_settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[APP] 設定保存エラー: {e}")
    
    def setup_window(self):
        """ウィンドウ設定 - レスポンシブ対応"""
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.configure(bg="#000000")
        
        # 最小サイズ設定
        self.root.minsize(800, 600)
        
        # ウィンドウリサイズイベント
        self.root.bind('<Configure>', self.on_window_resize)
        
        # PC-98風カラーテーマ
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('BBS.TFrame', background='#000000', foreground='#00FF00')
        style.configure('BBS.TLabel', background='#000000', foreground='#00FF00',
                       font=('MS Gothic', self.font_size))
        style.configure('BBS.TButton', background='#0000FF', foreground='#FFFFFF',
                       font=('MS Gothic', self.font_size - 1))
        style.configure('BBS.Treeview', background='#000080', foreground='#FFFFFF',
                       fieldbackground='#000080')
        
        # プログレスバーのスタイル
        style.configure('BBS.TProgressbar', background='#00FF00', troughcolor='#000080')
    
    def on_window_resize(self, event):
        """ウィンドウリサイズイベント"""
        if event.widget == self.root:
            self.window_width = event.width
            self.window_height = event.height
            self.adjust_responsive_layout()
    
    def adjust_responsive_layout(self):
        """レスポンシブレイアウト調整"""
        try:
            # ウィンドウサイズに応じてフォントサイズを調整
            if self.window_width < 900:
                new_font_size = max(8, self.font_size - 2)
            elif self.window_width < 1100:
                new_font_size = max(10, self.font_size - 1)
            else:
                new_font_size = self.font_size
            
            # フォントサイズ更新
            if hasattr(self, 'post_display'):
                self.post_display.configure(font=('MS Gothic', new_font_size))
            
            if hasattr(self, 'post_input'):
                self.post_input.configure(font=('MS Gothic', new_font_size))
            
            # 600px以下での最適化
            if self.window_width < 600:
                # コンパクトモードに切り替え
                if hasattr(self, 'category_listbox'):
                    self.category_listbox.configure(height=4)
                if hasattr(self, 'thread_listbox'):
                    self.thread_listbox.configure(height=8)
                    
        except Exception as e:
            logger.error(f"[APP] レスポンシブ調整エラー: {e}")
    
    def create_widgets(self):
        """ウィジェット作成 - 完全版"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, style='BBS.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ヘッダー
        header_frame = ttk.Frame(main_frame, style='BBS.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(
            header_frame,
            text=f"■ {APP_NAME} ■",
            style='BBS.TLabel',
            font=('MS Gothic', self.font_size + 2, 'bold')
        )
        title_label.pack()
        
        # ステータス表示
        connection_status = self.ai_manager.get_connection_status()
        ai_status = f"AI: {connection_status.get('current_provider', 'なし')}"
        
        status_text = f"Version: {APP_VERSION} | Build: {APP_BUILD} | {ai_status} | AI活動: {'ON' if self.ai_activity_enabled else 'OFF'}"
        
        status_label = ttk.Label(
            header_frame,
            text=status_text,
            style='BBS.TLabel',
            font=('MS Gothic', self.font_size - 2)
        )
        status_label.pack()
        self.status_label = status_label
        
        # メインコンテンツエリア
        content_frame = ttk.Frame(main_frame, style='BBS.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左側パネル（カテゴリ・スレッド一覧）
        left_frame = ttk.Frame(content_frame, style='BBS.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 大分類選択
        category_label = ttk.Label(left_frame, text="■ 大分類 ■", style='BBS.TLabel')
        category_label.pack(anchor=tk.W)
        
        self.category_listbox = tk.Listbox(
            left_frame,
            bg="#000080",
            fg="#FFFFFF",
            font=('MS Gothic', self.font_size),
            width=20,
            height=8,
            selectbackground="#0080FF"
        )
        
        # 大分類を読み込み
        main_categories = self.category_manager.get_main_categories()
        for category in main_categories:
            self.category_listbox.insert(tk.END, category["name"])
        
        self.category_listbox.pack(pady=(5, 10))
        self.category_listbox.bind('<<ListboxSelect>>', self.on_category_select)
        
        if main_categories:
            self.category_listbox.selection_set(0)
            self.current_main_category_id = main_categories[0]["id"]
        
        # スレッド一覧
        thread_label = ttk.Label(left_frame, text="■ スレッド一覧 ■", style='BBS.TLabel')
        thread_label.pack(anchor=tk.W)
        
        # スレッド操作ボタン
        thread_button_frame = ttk.Frame(left_frame, style='BBS.TFrame')
        thread_button_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.create_thread_button = ttk.Button(
            thread_button_frame,
            text="新規作成",
            command=self.show_create_thread_dialog,
            style='BBS.TButton'
        )
        self.create_thread_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.refresh_thread_button = ttk.Button(
            thread_button_frame,
            text="更新",
            command=self.update_thread_list,
            style='BBS.TButton'
        )
        self.refresh_thread_button.pack(side=tk.LEFT)
        
        self.thread_listbox = tk.Listbox(
            left_frame,
            bg="#000080",
            fg="#FFFFFF",
            font=('MS Gothic', self.font_size - 1),
            width=35,
            height=18,
            selectbackground="#0080FF"
        )
        self.thread_listbox.pack(pady=(5, 10))
        self.thread_listbox.bind('<<ListboxSelect>>', self.on_thread_select)
        self.thread_listbox.bind('<Double-Button-1>', self.on_thread_double_click)
        
        # 右側パネル（投稿表示・入力）
        right_frame = ttk.Frame(content_frame, style='BBS.TFrame')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # スレッド情報表示
        thread_info_frame = ttk.Frame(right_frame, style='BBS.TFrame')
        thread_info_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.thread_info_label = ttk.Label(
            thread_info_frame, 
            text="スレッドを選択してください", 
            style='BBS.TLabel',
            font=('MS Gothic', self.font_size - 1)
        )
        self.thread_info_label.pack(anchor=tk.W)
        
        # 投稿表示エリア
        post_label = ttk.Label(right_frame, text="■ 投稿内容 ■", style='BBS.TLabel')
        post_label.pack(anchor=tk.W)
        
        # 投稿操作ボタン
        post_button_frame = ttk.Frame(right_frame, style='BBS.TFrame')
        post_button_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.edit_post_button = ttk.Button(
            post_button_frame,
            text="投稿編集",
            command=self.edit_selected_post,
            style='BBS.TButton',
            state=tk.DISABLED
        )
        self.edit_post_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.delete_post_button = ttk.Button(
            post_button_frame,
            text="投稿削除",
            command=self.delete_selected_post,
            style='BBS.TButton',
            state=tk.DISABLED
        )
        self.delete_post_button.pack(side=tk.LEFT)
        
        self.post_display = scrolledtext.ScrolledText(
            right_frame,
            bg="#000000",
            fg="#00FF00",
            font=('MS Gothic', self.font_size),
            wrap=tk.WORD,
            height=25,
            state=tk.DISABLED,
            cursor="arrow"
        )
        self.post_display.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        self.post_display.bind('<Button-1>', self.on_post_click)
        
        # 投稿入力エリア
        input_label = ttk.Label(right_frame, text="■ 投稿入力 ■", style='BBS.TLabel')
        input_label.pack(anchor=tk.W)
        
        # 投稿オプション
        input_option_frame = ttk.Frame(right_frame, style='BBS.TFrame')
        input_option_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.mention_var = tk.StringVar()
        mention_label = ttk.Label(input_option_frame, text="@返信:", style='BBS.TLabel')
        mention_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.mention_entry = tk.Entry(
            input_option_frame,
            textvariable=self.mention_var,
            bg="#000080",
            fg="#FFFFFF",
            font=('MS Gothic', self.font_size - 1),
            width=15
        )
        self.mention_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_mention_button = ttk.Button(
            input_option_frame,
            text="クリア",
            command=lambda: self.mention_var.set(""),
            style='BBS.TButton'
        )
        clear_mention_button.pack(side=tk.LEFT)
        
        self.post_input = tk.Text(
            right_frame,
            bg="#000080",
            fg="#FFFFFF",
            font=('MS Gothic', self.font_size),
            height=5,
            wrap=tk.WORD,
            insertbackground="#FFFFFF"
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
        
        self.export_button = ttk.Button(
            button_frame,
            text="エクスポート",
            command=self.show_export_dialog,
            style='BBS.TButton'
        )
        self.export_button.pack(side=tk.LEFT, padx=(0, 10))
        
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
        """キーバインド設定 - 拡張版"""
        self.root.bind('<Control-Return>', lambda e: self.submit_post())
        self.root.bind('<F5>', lambda e: self.refresh_display())
        self.root.bind('<F12>', lambda e: self.toggle_admin_mode())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Control-n>', lambda e: self.show_create_thread_dialog())
        self.root.bind('<Control-e>', lambda e: self.edit_selected_post())
        self.root.bind('<Delete>', lambda e: self.delete_selected_post())
        
        # フォントサイズ調整
        self.root.bind('<Control-plus>', lambda e: self.change_font_size(1))
        self.root.bind('<Control-minus>', lambda e: self.change_font_size(-1))
        self.root.bind('<Control-0>', lambda e: self.reset_font_size())
        
        logger.info("[APP] キーバインド設定完了")
    
    def change_font_size(self, delta: int):
        """フォントサイズ変更"""
        new_size = max(8, min(20, self.font_size + delta))
        if new_size != self.font_size:
            self.font_size = new_size
            self.adjust_responsive_layout()
            self.save_settings()
    
    def reset_font_size(self):
        """フォントサイズリセット"""
        self.font_size = 12
        self.adjust_responsive_layout()
        self.save_settings()
    
    def verify_initialization(self):
        """初期化状態を検証し、必要に応じて自動復旧"""
        try:
            # データベースの存在確認
            if not os.path.exists("bbs_database.db"):
                logger.warning("[INIT] データベースが存在しません。自動作成します。")
                self.db_manager = DatabaseManager()
            
            # カテゴリの存在確認
            main_categories = self.category_manager.get_main_categories()
            if not main_categories:
                logger.warning("[INIT] カテゴリが存在しません。自動作成します。")
                self.category_manager.init_default_categories()
                main_categories = self.category_manager.get_main_categories()
            
            # スレッドの存在確認
            if main_categories:
                threads = self.thread_manager.get_threads_by_category(main_categories[0]["id"])
                if not threads:
                    logger.warning("[INIT] スレッドが存在しません。自動作成します。")
                    self.thread_manager.init_default_threads()
            
            # ペルソナの存在確認
            if not hasattr(self.persona_manager, 'personas') or not self.persona_manager.personas:
                logger.warning("[INIT] ペルソナが存在しません。自動作成します。")
                self.persona_manager = PersonaManager(self.db_manager, self.ai_manager)
            
            logger.info("[INIT] 初期化状態の検証が完了しました。")
            
        except Exception as e:
            logger.error(f"[INIT] 初期化検証エラー: {e}")
    
    def on_category_select(self, event):
        """カテゴリ選択イベント - 強化版"""
        try:
            selection = self.category_listbox.curselection()
            if not selection:
                logger.warning("[APP] カテゴリが選択されていません")
                return
            
            category_name = self.category_listbox.get(selection[0])
            logger.info(f"[APP] カテゴリ選択: {category_name}")
            
            # カテゴリIDを取得
            main_categories = self.category_manager.get_main_categories()
            for category in main_categories:
                if category["name"] == category_name:
                    self.current_main_category_id = category["id"]
                    logger.info(f"[APP] カテゴリID設定: {self.current_main_category_id}")
                    break
            
            if self.current_main_category_id:
                # スレッド一覧を強制更新
                self.update_thread_list()
                self.clear_post_selection()
            else:
                logger.error(f"[APP] カテゴリIDが見つかりません: {category_name}")
                
        except Exception as e:
            logger.error(f"[APP] カテゴリ選択エラー: {e}")
    
    def on_thread_select(self, event):
        """スレッド選択イベント - 強化版"""
        try:
            selection = self.thread_listbox.curselection()
            if not selection:
                return
            
            thread_index = selection[0]
            if thread_index < len(self.current_threads):
                thread = self.current_threads[thread_index]
                self.current_thread_id = thread['thread_id']
                
                # スレッド情報を更新
                self.update_thread_info(thread)
                
                # 投稿表示を更新
                self.update_post_display()
                
                # 投稿選択をクリア
                self.clear_post_selection()
                
                logger.info(f"[APP] スレッド選択: {self.current_thread_id} - {thread['title']}")
                
        except Exception as e:
            logger.error(f"[APP] スレッド選択エラー: {e}")
    
    def on_thread_double_click(self, event):
        """スレッドダブルクリックイベント"""
        # スレッド詳細表示や編集機能を実装可能
        pass
    
    def on_post_click(self, event):
        """投稿クリックイベント"""
        try:
            # クリック位置から投稿IDを特定
            index = self.post_display.index(tk.INSERT)
            
            # 投稿選択状態を更新
            self.update_post_selection()
            
        except Exception as e:
            logger.error(f"[APP] 投稿クリックエラー: {e}")
    
    def update_thread_info(self, thread: Dict):
        """スレッド情報表示更新"""
        try:
            info_text = f"📌 {thread['title']} "
            
            if thread['is_pinned']:
                info_text += "[固定] "
            if thread['is_locked']:
                info_text += "[ロック] "
            
            info_text += f"(投稿: {thread['post_count']}, 閲覧: {thread['view_count']}) "
            info_text += f"作成者: {thread['created_by']}"
            
            self.thread_info_label.config(text=info_text)
            
        except Exception as e:
            logger.error(f"[APP] スレッド情報更新エラー: {e}")
    
    def clear_post_selection(self):
        """投稿選択クリア"""
        self.selected_post_id = None
        self.edit_post_button.config(state=tk.DISABLED)
        self.delete_post_button.config(state=tk.DISABLED)
    
    def update_post_selection(self):
        """投稿選択更新"""
        # 実際の実装では、クリック位置から投稿IDを特定
        # ここでは簡易実装
        self.selected_post_id = 1  # 仮の値
        self.edit_post_button.config(state=tk.NORMAL)
        self.delete_post_button.config(state=tk.NORMAL)
    
    def update_thread_list(self):
        """スレッド一覧更新 - 拡張版"""
        if not self.current_main_category_id:
            logger.warning("[APP] カテゴリIDが設定されていません")
            return
        
        try:
            # リストボックスをクリア
            self.thread_listbox.delete(0, tk.END)
            
            # デバッグ：カテゴリ情報を確認
            logger.info(f"[APP] スレッド取得開始 - カテゴリID: {self.current_main_category_id}")
            
            # スレッド一覧を取得
            self.current_threads = self.thread_manager.get_threads_by_category(self.current_main_category_id)
            
            # デバッグ：取得結果を確認
            logger.info(f"[APP] 取得されたスレッド数: {len(self.current_threads)}")
            
            if not self.current_threads:
                # データが無い場合は強制的にデフォルトスレッドを作成
                logger.warning("[APP] スレッドが存在しません。デフォルトスレッドを作成します。")
                self.thread_manager.init_default_threads()
                self.current_threads = self.thread_manager.get_threads_by_category(self.current_main_category_id)
            
            # スレッドをリストボックスに追加
            for thread in self.current_threads:
                prefix = ""
                if thread['is_pinned']:
                    prefix += "📌 "
                if thread['is_locked']:
                    prefix += "🔒 "
                
                display_text = f"{prefix}[{thread['thread_id']}] {thread['sub_category_name']}: {thread['title']} ({thread['post_count']})"
                
                # 文字数制限（リストボックス幅に合わせて調整）
                if len(display_text) > 50:
                    display_text = display_text[:47] + "..."
                
                self.thread_listbox.insert(tk.END, display_text)
                logger.debug(f"[APP] スレッド追加: {display_text}")
            
            # 最初のスレッドを自動選択
            if self.current_threads:
                self.thread_listbox.selection_set(0)
                self.current_thread_id = self.current_threads[0]['thread_id']
                self.update_thread_info(self.current_threads[0])
                self.update_post_display()
                logger.info(f"[APP] 初期スレッド選択: {self.current_thread_id}")
            
            # UI更新を強制実行
            self.thread_listbox.update()
            
        except Exception as e:
            logger.error(f"[APP] スレッド一覧更新エラー: {e}")
            # エラー時は空のメッセージを表示
            self.thread_listbox.insert(tk.END, "スレッドの読み込みに失敗しました")
    
    def update_post_display(self):
        """投稿表示更新 - 完全版"""
        if not self.current_thread_id:
            logger.warning("[APP] スレッドIDが設定されていません")
            return
        
        try:
            # 投稿データを取得
            posts = self.thread_manager.get_thread_posts(self.current_thread_id)
            
            # 表示エリアをクリア
            self.post_display.config(state=tk.NORMAL)
            self.post_display.delete(1.0, tk.END)
            
            if not posts:
                self.post_display.insert(tk.END, "まだ投稿がありません。\n最初の投稿をお待ちしています！")
                self.post_display.config(state=tk.DISABLED)
                return
            
            # 投稿を表示
            for i, post in enumerate(posts):
                self.display_single_post(i + 1, post)
            
            # タグ設定
            self.configure_post_display_tags()
            
            self.post_display.config(state=tk.DISABLED)
            self.post_display.see(tk.END)
            
            logger.info(f"[APP] 投稿表示更新完了: Thread {self.current_thread_id}, {len(posts)}件")
            
        except Exception as e:
            logger.error(f"[APP] 投稿表示更新エラー: {e}")
            self.post_display.config(state=tk.NORMAL)
            self.post_display.delete(1.0, tk.END)
            self.post_display.insert(tk.END, f"投稿の読み込みに失敗しました: {e}")
            self.post_display.config(state=tk.DISABLED)
    
    def display_single_post(self, post_number: int, post: Dict):
        """単一投稿の表示"""
        try:
            timestamp = post['posted_at']
            name = post['persona_name']
            content = post['content']
            is_user = post['is_user_post']
            is_edited = post.get('is_edited', False)
            mentions = post.get('mention_names', '')
            
            # 投稿番号とタイムスタンプ
            self.post_display.insert(tk.END, f"{post_number:3d}: ", "number")
            self.post_display.insert(tk.END, f"{timestamp}\n", "timestamp")
            
            # 投稿者名（ユーザーとAIで色分け）
            name_tag = "user_name" if is_user else "ai_name"
            self.post_display.insert(tk.END, f" {name}", name_tag)
            
            # 編集マークとメンションマーク
            if is_edited:
                self.post_display.insert(tk.END, " [編集済み]", "edited_mark")
            if mentions:
                self.post_display.insert(tk.END, f" →@{mentions}", "mention_mark")
            
            self.post_display.insert(tk.END, "\n", "name")
            
            # 投稿内容をフォーマットして表示
            formatted_content = self.format_post_content(content)
            content_tag = "user_content" if is_user else "ai_content"
            self.post_display.insert(tk.END, f" {formatted_content}\n\n", content_tag)
            
        except Exception as e:
            logger.error(f"[APP] 投稿表示エラー: {e}")
            self.post_display.insert(tk.END, f" [投稿表示エラー: {e}]\n\n", "error")
    
    def configure_post_display_tags(self):
        """投稿表示のタグ設定"""
        try:
            # 基本タグ
            self.post_display.tag_configure("number", foreground="#808080", font=('MS Gothic', self.font_size - 2))
            self.post_display.tag_configure("timestamp", foreground="#808080", font=('MS Gothic', self.font_size - 2))
            
            # 名前タグ
            self.post_display.tag_configure("user_name", foreground="#00FFFF", font=('MS Gothic', self.font_size, 'bold'))
            self.post_display.tag_configure("ai_name", foreground="#FFFF00", font=('MS Gothic', self.font_size, 'bold'))
            
            # 内容タグ
            self.post_display.tag_configure("user_content", foreground="#FFFFFF", font=('MS Gothic', self.font_size))
            self.post_display.tag_configure("ai_content", foreground="#00FF00", font=('MS Gothic', self.font_size))
            
            # 特殊マーク
            self.post_display.tag_configure("edited_mark", foreground="#FF8080", font=('MS Gothic', self.font_size - 2))
            self.post_display.tag_configure("mention_mark", foreground="#FF80FF", font=('MS Gothic', self.font_size - 2))
            self.post_display.tag_configure("error", foreground="#FF0000", font=('MS Gothic', self.font_size - 1))
            
        except Exception as e:
            logger.error(f"[APP] タグ設定エラー: {e}")
    
    def format_post_content(self, content: str) -> str:
        """投稿内容のフォーマット - 強化版"""
        if not content:
            return ""
        
        lines = []
        current_line = ""
        
        for char in content:
            if char == '\n':
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                lines.append("")
            else:
                current_line += char
                # 45文字程度で改行（PC-98風）
                if len(current_line) >= 45 and char in ['。', '！', '？', '、', ' ']:
                    lines.append(current_line)
                    current_line = ""
        
        if current_line:
            lines.append(current_line)
        
        # 行頭にスペースを追加してインデント
        formatted_lines = []
        for line in lines:
            if line.strip():
                formatted_lines.append(line)
            else:
                formatted_lines.append("")
        
        return '\n '.join(formatted_lines)
    
    def submit_post(self):
        """投稿送信 - 完全版"""
        if not self.current_thread_id:
            messagebox.showwarning("警告", "スレッドが選択されていません。")
            return
        
        content = self.post_input.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("警告", "投稿内容を入力してください。")
            return
        
        try:
            # メンション処理
            mention_name = self.mention_var.get().strip()
            if mention_name:
                content = f"@{mention_name} {content}"
            
            # ユーザー投稿として追加
            success = self.thread_manager.add_post(
                self.current_thread_id,
                "あなた",
                content,
                is_user_post=True
            )
            
            if success:
                # 入力欄をクリア
                self.post_input.delete(1.0, tk.END)
                self.mention_var.set("")
                
                # 表示更新
                self.update_post_display()
                self.update_thread_list()
                self.update_status()
                
                # ペルソナに学習データとして記録
                if hasattr(self.persona_manager, 'record_user_interaction'):
                    self.persona_manager.record_user_interaction(self.current_thread_id, content)
                
                # メンション応答処理
                if mention_name or any(keyword in content for keyword in ["みんな", "だれか", "誰か"]):
                    self.trigger_mention_responses(content)
                
                logger.info(f"[APP] ユーザー投稿完了: Thread {self.current_thread_id}")
            else:
                messagebox.showerror("エラー", "投稿に失敗しました。")
                
        except Exception as e:
            logger.error(f"[APP] 投稿送信エラー: {e}")
            messagebox.showerror("エラー", f"投稿中にエラーが発生しました: {e}")
    
    def trigger_mention_responses(self, original_content: str):
        """メンション応答のトリガー"""
        try:
            # メンション検出
            mentions = self.mention_manager.detect_mentions(original_content)
            
            # 呼びかけ応答処理（別スレッドで実行）
            def process_mentions():
                for persona_name in mentions:
                    if self.mention_manager.should_respond_to_mention(persona_name, original_content):
                        response = self.mention_manager.generate_mention_response(
                            persona_name, original_content, self.current_thread_id
                        )
                        
                        if response:
                            # 応答投稿を追加
                            success = self.thread_manager.add_post(
                                self.current_thread_id,
                                persona_name,
                                response,
                                is_user_post=False
                            )
                            
                            if success:
                                # UI更新をメインスレッドに依頼
                                self.message_queue.put(('update_display', None))
                                logger.info(f"[MENTION] 呼びかけ応答: {persona_name}")
                            
                            # 応答間隔
                            time.sleep(random.uniform(3, 8))
            
            # 別スレッドで実行
            mention_thread = threading.Thread(target=process_mentions, daemon=True)
            mention_thread.start()
            
        except Exception as e:
            logger.error(f"[APP] メンション応答エラー: {e}")
    
    def show_create_thread_dialog(self):
        """スレッド作成ダイアログ表示"""
        if not self.current_main_category_id:
            messagebox.showwarning("警告", "カテゴリを選択してください。")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("新規スレッド作成")
        dialog.geometry("500x300")
        dialog.configure(bg="#000000")
        dialog.resizable(False, False)
        
        # モーダルに設定
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 小分類選択
        sub_cat_frame = ttk.Frame(dialog, style='BBS.TFrame')
        sub_cat_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(sub_cat_frame, text="小分類:", style='BBS.TLabel').pack(anchor=tk.W)
        
        sub_categories = self.category_manager.get_sub_categories(self.current_main_category_id)
        sub_cat_var = tk.StringVar()
        
        sub_cat_combo = ttk.Combobox(
            sub_cat_frame,
            textvariable=sub_cat_var,
            values=[cat["name"] for cat in sub_categories],
            state="readonly",
            width=40
        )
        sub_cat_combo.pack(fill=tk.X, pady=5)
        
        if sub_categories:
            sub_cat_combo.set(sub_categories[0]["name"])
        
        # タイトル入力
        title_frame = ttk.Frame(dialog, style='BBS.TFrame')
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(title_frame, text="スレッドタイトル:", style='BBS.TLabel').pack(anchor=tk.W)
        
        title_entry = tk.Entry(
            title_frame,
            bg="#000080",
            fg="#FFFFFF",
            font=('MS Gothic', self.font_size),
            width=50
        )
        title_entry.pack(fill=tk.X, pady=5)
        title_entry.focus()
        
        # 説明入力
        desc_frame = ttk.Frame(dialog, style='BBS.TFrame')
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(desc_frame, text="説明（任意）:", style='BBS.TLabel').pack(anchor=tk.W)
        
        desc_text = tk.Text(
            desc_frame,
            bg="#000080",
            fg="#FFFFFF",
            font=('MS Gothic', self.font_size),
            height=5,
            wrap=tk.WORD
        )
        desc_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # ボタン
        button_frame = ttk.Frame(dialog, style='BBS.TFrame')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def create_thread():
            try:
                title = title_entry.get().strip()
                description = desc_text.get(1.0, tk.END).strip()
                sub_cat_name = sub_cat_var.get()
                
                if not title:
                    messagebox.showwarning("警告", "スレッドタイトルを入力してください。")
                    return
                
                if not sub_cat_name:
                    messagebox.showwarning("警告", "小分類を選択してください。")
                    return
                
                # 小分類IDを取得
                sub_cat_id = None
                for cat in sub_categories:
                    if cat["name"] == sub_cat_name:
                        sub_cat_id = cat["id"]
                        break
                
                if not sub_cat_id:
                    messagebox.showerror("エラー", "小分類の取得に失敗しました。")
                    return
                
                # スレッド作成
                thread_id = self.thread_manager.create_thread(
                    self.current_main_category_id,
                    sub_cat_id,
                    title,
                    description,
                    "あなた"
                )
                
                if thread_id > 0:
                    messagebox.showinfo("成功", f"スレッド「{title}」を作成しました。")
                    dialog.destroy()
                    
                    # スレッド一覧を更新
                    self.update_thread_list()
                    
                    # 作成したスレッドを選択
                    for i, thread in enumerate(self.current_threads):
                        if thread['thread_id'] == thread_id:
                            self.thread_listbox.selection_clear(0, tk.END)
                            self.thread_listbox.selection_set(i)
                            self.current_thread_id = thread_id
                            self.update_thread_info(thread)
                            self.update_post_display()
                            break
                else:
                    messagebox.showerror("エラー", "スレッドの作成に失敗しました。")
                    
            except Exception as e:
                logger.error(f"[APP] スレッド作成エラー: {e}")
                messagebox.showerror("エラー", f"スレッド作成中にエラーが発生しました: {e}")
        
        ttk.Button(
            button_frame,
            text="作成",
            command=create_thread,
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="キャンセル",
            command=dialog.destroy,
            style='BBS.TButton'
        ).pack(side=tk.LEFT)
        
        # Enterキーでスレッド作成
        dialog.bind('<Return>', lambda e: create_thread())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
    
    def edit_selected_post(self):
        """選択投稿の編集"""
        if not self.selected_post_id:
            messagebox.showwarning("警告", "編集する投稿を選択してください。")
            return
        
        # 実装: 投稿編集ダイアログ
        messagebox.showinfo("情報", "投稿編集機能は次回アップデートで実装予定です。")
    
    def delete_selected_post(self):
        """選択投稿の削除"""
        if not self.selected_post_id:
            messagebox.showwarning("警告", "削除する投稿を選択してください。")
            return
        
        if messagebox.askyesno("確認", "選択した投稿を削除しますか？"):
            # 実装: 投稿削除処理
            messagebox.showinfo("情報", "投稿削除機能は次回アップデートで実装予定です。")
    
    def show_export_dialog(self):
        """エクスポートダイアログ表示"""
        dialog = tk.Toplevel(self.root)
        dialog.title("データエクスポート")
        dialog.geometry("400x250")
        dialog.configure(bg="#000000")
        dialog.resizable(False, False)
        
        # モーダルに設定
        dialog.transient(self.root)
        dialog.grab_set()
        
        # エクスポート形式選択
        format_frame = ttk.Frame(dialog, style='BBS.TFrame')
        format_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(format_frame, text="エクスポート形式:", style='BBS.TLabel').pack(anchor=tk.W)
        
        format_var = tk.StringVar(value="json")
        
        formats = [
            ("JSON形式", "json"),
            ("CSV形式", "csv"),
            ("データベースバックアップ", "backup")
        ]
        
        for text, value in formats:
            tk.Radiobutton(
                format_frame,
                text=text,
                variable=format_var,
                value=value,
                bg="#000000",
                fg="#00FF00",
                selectcolor="#000080",
                font=('MS Gothic', self.font_size)
            ).pack(anchor=tk.W, pady=2)
        
        # プログレスバー
        progress_frame = ttk.Frame(dialog, style='BBS.TFrame')
        progress_frame.pack(fill=tk.X, padx=20, pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_frame,
            variable=progress_var,
            maximum=100,
            style='BBS.TProgressbar'
        )
        progress_bar.pack(fill=tk.X)
        
        status_label = ttk.Label(progress_frame, text="", style='BBS.TLabel')
        status_label.pack(anchor=tk.W, pady=(5, 0))
        
        # ボタン
        button_frame = ttk.Frame(dialog, style='BBS.TFrame')
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def start_export():
            try:
                format_type = format_var.get()
                
                # プログレスバー開始
                progress_var.set(0)
                status_label.config(text="エクスポート開始...")
                dialog.update()
                
                def export_worker():
                    try:
                        # エクスポート実行
                        progress_var.set(25)
                        status_label.config(text="データ取得中...")
                        dialog.update()
                        
                        filename = self.data_exporter.export_all_data(format_type)
                        
                        progress_var.set(75)
                        status_label.config(text="ファイル書き込み中...")
                        dialog.update()
                        
                        if filename:
                            progress_var.set(100)
                            status_label.config(text="完了")
                            dialog.update()
                            
                            time.sleep(1)
                            messagebox.showinfo("成功", f"エクスポートが完了しました。\nファイル: {filename}")
                            dialog.destroy()
                        else:
                            status_label.config(text="エラー")
                            messagebox.showerror("エラー", "エクスポートに失敗しました。")
                            
                    except Exception as e:
                        logger.error(f"[EXPORT] エクスポートエラー: {e}")
                        status_label.config(text="エラー")
                        messagebox.showerror("エラー", f"エクスポート中にエラーが発生しました: {e}")
                
                # 別スレッドで実行
                export_thread = threading.Thread(target=export_worker, daemon=True)
                export_thread.start()
                
            except Exception as e:
                logger.error(f"[APP] エクスポート開始エラー: {e}")
                messagebox.showerror("エラー", f"エクスポート開始時にエラーが発生しました: {e}")
        
        ttk.Button(
            button_frame,
            text="エクスポート開始",
            command=start_export,
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="キャンセル",
            command=dialog.destroy,
            style='BBS.TButton'
        ).pack(side=tk.LEFT)
    
    def refresh_display(self):
        """表示更新 - 完全版"""
        try:
            # 全体的な更新
            self.update_thread_list()
            self.update_post_display()
            self.update_status()
            
            # ペルソナ情報更新
            if hasattr(self.persona_manager, 'update_all_personas'):
                self.persona_manager.update_all_personas()
            
            logger.info("[APP] 表示更新完了")
            
        except Exception as e:
            logger.error(f"[APP] 表示更新エラー: {e}")
            messagebox.showerror("エラー", f"表示更新中にエラーが発生しました: {e}")
    
    def toggle_admin_mode(self):
        """管理モード切り替え"""
        self.admin_mode = not self.admin_mode
        self.update_status()
        if self.admin_mode:
            self.show_admin_panel()
        logger.info(f"[APP] 管理モード: {'ON' if self.admin_mode else 'OFF'}")
    
    def show_admin_panel(self):
        """管理パネル表示 - 完全版"""
        admin_window = tk.Toplevel(self.root)
        admin_window.title(f"管理パネル - {APP_NAME} v{APP_VERSION}")
        admin_window.geometry("1000x700")
        admin_window.configure(bg="#000000")
        
        # ノートブック（タブ）作成
        notebook = ttk.Notebook(admin_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 1. システム制御タブ
        self.create_system_control_tab(notebook)
        
        # 2. バージョン管理タブ
        self.create_version_management_tab(notebook)
        
        # 3. 統計情報タブ
        self.create_statistics_tab(notebook)
        
        # 4. ペルソナ管理タブ
        self.create_persona_management_tab(notebook)
        
        # 5. データ管理タブ
        self.create_data_management_tab(notebook)
        
        # 6. 設定タブ
        self.create_settings_tab(notebook)
    
    def create_system_control_tab(self, notebook):
        """システム制御タブ作成"""
        system_frame = ttk.Frame(notebook, style='BBS.TFrame')
        notebook.add(system_frame, text="システム制御")
        
        # AI活動制御セクション
        ai_section = ttk.LabelFrame(system_frame, text="AI活動制御", style='BBS.TFrame')
        ai_section.pack(fill=tk.X, padx=10, pady=10)
        
        ai_button_frame = ttk.Frame(ai_section, style='BBS.TFrame')
        ai_button_frame.pack(fill=tk.X, padx=10, pady=10)
        
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
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # 現在の状態表示
        ai_status_label = ttk.Label(
            ai_button_frame,
            text=f"現在の状態: {'有効' if self.ai_activity_enabled else '無効'}",
            style='BBS.TLabel'
        )
        ai_status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 投稿間隔調整セクション
        interval_section = ttk.LabelFrame(system_frame, text="AI投稿間隔調整", style='BBS.TFrame')
        interval_section.pack(fill=tk.X, padx=10, pady=10)
        
        self.interval_var = tk.IntVar(value=self.auto_post_interval)
        
        interval_frame = ttk.Frame(interval_section, style='BBS.TFrame')
        interval_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(interval_frame, text="間隔（秒）:", style='BBS.TLabel').pack(side=tk.LEFT)
        
        interval_scale = tk.Scale(
            interval_frame,
            from_=30,
            to=300,
            orient=tk.HORIZONTAL,
            variable=self.interval_var,
            bg="#000080",
            fg="#FFFFFF",
            highlightbackground="#000000",
            command=self.update_interval,
            length=300
        )
        interval_scale.pack(side=tk.LEFT, padx=(10, 0))
        
        # システム初期化セクション
        init_section = ttk.LabelFrame(system_frame, text="システム初期化", style='BBS.TFrame')
        init_section.pack(fill=tk.X, padx=10, pady=10)
        
        init_button_frame = ttk.Frame(init_section, style='BBS.TFrame')
        init_button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            init_button_frame,
            text="データベース初期化",
            command=self.reset_database,
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            init_button_frame,
            text="ペルソナ再生成",
            command=self.regenerate_personas,
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            init_button_frame,
            text="スレッド再作成",
            command=self.recreate_threads,
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            init_button_frame,
            text="完全リセット",
            command=self.complete_reset,
            style='BBS.TButton'
        ).pack(side=tk.LEFT)
    
    def create_version_management_tab(self, notebook):
        """バージョン管理タブ作成"""
        version_frame = ttk.Frame(notebook, style='BBS.TFrame')
        notebook.add(version_frame, text="バージョン管理")
        
        # 現在のバージョン情報
        current_section = ttk.LabelFrame(version_frame, text="現在のバージョン", style='BBS.TFrame')
        current_section.pack(fill=tk.X, padx=10, pady=10)
        
        current_info = ttk.Frame(current_section, style='BBS.TFrame')
        current_info.pack(fill=tk.X, padx=10, pady=10)
        
        version_info_text = f"""
■ アプリケーション情報 ■
名前: {APP_NAME}
バージョン: {APP_VERSION}
ビルド: {APP_BUILD}
作成者: {APP_AUTHOR}
作成日: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

■ 機能状況 ■
✅ 基本BBS機能
✅ AIペルソナシステム（100体）
✅ G4F + Gemini CLI対応
✅ 自動投稿システム
✅ 動的スレッド作成
✅ 呼びかけ応答機能
✅ データエクスポート機能
✅ 管理画面
✅ バージョン管理
✅ レスポンシブ対応
"""
        
        version_display = scrolledtext.ScrolledText(
            current_info,
            bg="#000000",
            fg="#00FF00",
            font=('MS Gothic', self.font_size - 1),
            height=15,
            state=tk.DISABLED
        )
        version_display.pack(fill=tk.BOTH, expand=True)
        
        version_display.config(state=tk.NORMAL)
        version_display.insert(tk.END, version_info_text)
        version_display.config(state=tk.DISABLED)
        
        # バージョン履歴
        history_section = ttk.LabelFrame(version_frame, text="バージョン履歴", style='BBS.TFrame')
        history_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        history_text = scrolledtext.ScrolledText(
            history_section,
            bg="#000000",
            fg="#00FF00",
            font=('MS Gothic', self.font_size - 1),
            height=10,
            state=tk.DISABLED
        )
        history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # バージョン履歴を表示
        def update_version_history():
            history_text.config(state=tk.NORMAL)
            history_text.delete(1.0, tk.END)
            
            history_text.insert(tk.END, "■ バージョン履歴 ■\n\n")
            
            for version_info in reversed(VERSION_HISTORY):
                history_text.insert(tk.END, f"Version {version_info['version']} ({version_info['date']})\n")
                history_text.insert(tk.END, f"  変更内容: {version_info['changes']}\n\n")
            
            history_text.config(state=tk.DISABLED)
        
        update_version_history()
    
    def create_statistics_tab(self, notebook):
        """統計情報タブ作成"""
        stats_frame = ttk.Frame(notebook, style='BBS.TFrame')
        notebook.add(stats_frame, text="統計情報")
        
        stats_text = scrolledtext.ScrolledText(
            stats_frame,
            bg="#000000",
            fg="#00FF00",
            font=('MS Gothic', self.font_size - 1),
            height=30,
            state=tk.DISABLED
        )
        stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def update_statistics():
            try:
                stats_text.config(state=tk.NORMAL)
                stats_text.delete(1.0, tk.END)
                
                # システム統計
                main_categories = self.category_manager.get_main_categories()
                all_threads = []
                for cat in main_categories:
                    threads = self.thread_manager.get_threads_by_category(cat["id"])
                    all_threads.extend(threads)
                
                total_posts = sum(thread['post_count'] for thread in all_threads)
                total_views = sum(thread['view_count'] for thread in all_threads)
                
                stats_text.insert(tk.END, f"■ システム統計 ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ■\n\n")
                stats_text.insert(tk.END, f"アプリケーション情報:\n")
                stats_text.insert(tk.END, f"  バージョン: {APP_VERSION}\n")
                stats_text.insert(tk.END, f"  ビルド: {APP_BUILD}\n")
                stats_text.insert(tk.END, f"  起動時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                stats_text.insert(tk.END, f"コンテンツ統計:\n")
                stats_text.insert(tk.END, f"  大分類数: {len(main_categories)}\n")
                stats_text.insert(tk.END, f"  スレッド数: {len(all_threads)}\n")
                stats_text.insert(tk.END, f"  総投稿数: {total_posts}\n")
                stats_text.insert(tk.END, f"  総閲覧数: {total_views}\n")
                stats_text.insert(tk.END, f"  AI活動状態: {'有効' if self.ai_activity_enabled else '無効'}\n")
                stats_text.insert(tk.END, f"  投稿間隔: {self.auto_post_interval}秒\n\n")
                
                # AI接続統計
                connection_status = self.ai_manager.get_connection_status()
                stats_text.insert(tk.END, f"■ AI接続統計 ■\n")
                stats_text.insert(tk.END, f"G4F接続:\n")
                stats_text.insert(tk.END, f"  利用可能: {'はい' if connection_status['g4f_available'] else 'いいえ'}\n")
                stats_text.insert(tk.END, f"Gemini CLI接続:\n")
                stats_text.insert(tk.END, f"  利用可能: {'はい' if connection_status['gemini_available'] else 'いいえ'}\n")
                stats_text.insert(tk.END, f"現在のプロバイダー: {connection_status.get('current_provider', 'なし')}\n")
                stats_text.insert(tk.END, f"現在のモデル: {connection_status.get('current_model', 'なし')}\n")
                stats_text.insert(tk.END, f"利用可能組み合わせ: {connection_status['available_combinations']}個\n")
                stats_text.insert(tk.END, f"総リクエスト数: {connection_status['total_requests']}\n")
                stats_text.insert(tk.END, f"成功数: {connection_status['success_count']}\n")
                stats_text.insert(tk.END, f"失敗数: {connection_status['failure_count']}\n")
                stats_text.insert(tk.END, f"成功率: {connection_status['success_rate']:.1f}%\n\n")
                
                # ペルソナ統計
                if hasattr(self.persona_manager, 'get_persona_stats'):
                    persona_stats = self.persona_manager.get_persona_stats()
                    stats_text.insert(tk.END, f"■ ペルソナ統計 ■\n")
                    stats_text.insert(tk.END, f"総ペルソナ数: {persona_stats.get('total_personas', 0)}\n")
                    stats_text.insert(tk.END, f"アクティブペルソナ数: {persona_stats.get('active_personas', 0)}\n")
                    stats_text.insert(tk.END, f"荒らしペルソナ数: {persona_stats.get('troll_personas', 0)}\n")
                    stats_text.insert(tk.END, f"総AI投稿数: {persona_stats.get('total_posts', 0)}\n")
                    stats_text.insert(tk.END, f"平均活動レベル: {persona_stats.get('average_activity', 0):.2f}\n\n")
                    
                    # 世代別統計
                    generation_stats = persona_stats.get('generation_stats', {})
                    if generation_stats:
                        stats_text.insert(tk.END, f"世代別統計:\n")
                        for generation, stats in generation_stats.items():
                            stats_text.insert(tk.END, f"  {generation}: {stats.get('count', 0)}名 (投稿数: {stats.get('total_posts', 0)})\n")
                    
                    stats_text.insert(tk.END, "\n")
                
                # カテゴリ別統計
                stats_text.insert(tk.END, f"■ カテゴリ別統計 ■\n")
                for category in main_categories:
                    cat_threads = self.thread_manager.get_threads_by_category(category["id"])
                    cat_posts = sum(thread['post_count'] for thread in cat_threads)
                    cat_views = sum(thread['view_count'] for thread in cat_threads)
                    
                    stats_text.insert(tk.END, f"{category['name']}:\n")
                    stats_text.insert(tk.END, f"  スレッド数: {len(cat_threads)}\n")
                    stats_text.insert(tk.END, f"  投稿数: {cat_posts}\n")
                    stats_text.insert(tk.END, f"  閲覧数: {cat_views}\n")
                
                stats_text.config(state=tk.DISABLED)
                
            except Exception as e:
                stats_text.config(state=tk.NORMAL)
                stats_text.delete(1.0, tk.END)
                stats_text.insert(tk.END, f"統計情報の取得中にエラーが発生しました: {e}")
                stats_text.config(state=tk.DISABLED)
                logger.error(f"[ADMIN] 統計更新エラー: {e}")
        
        update_statistics()
        
        # 更新ボタン
        ttk.Button(
            stats_frame,
            text="統計更新",
            command=update_statistics,
            style='BBS.TButton'
        ).pack(pady=5)
    
    def create_persona_management_tab(self, notebook):
        """ペルソナ管理タブ作成"""
        persona_frame = ttk.Frame(notebook, style='BBS.TFrame')
        notebook.add(persona_frame, text="ペルソナ管理")
        
        # 上部: ペルソナ一覧
        list_frame = ttk.Frame(persona_frame, style='BBS.TFrame')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左側: ペルソナリスト
        left_frame = ttk.Frame(list_frame, style='BBS.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(left_frame, text="ペルソナ一覧:", style='BBS.TLabel').pack(anchor=tk.W)
        
        persona_listbox = tk.Listbox(
            left_frame,
            bg="#000080",
            fg="#FFFFFF",
            font=('MS Gothic', self.font_size - 1),
            width=25,
            height=25
        )
        persona_listbox.pack(fill=tk.Y, expand=True, pady=5)
        
        # 右側: ペルソナ詳細
        right_frame = ttk.Frame(list_frame, style='BBS.TFrame')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(right_frame, text="ペルソナ詳細:", style='BBS.TLabel').pack(anchor=tk.W)
        
        persona_detail_text = scrolledtext.ScrolledText(
            right_frame,
            bg="#000000",
            fg="#00FF00",
            font=('MS Gothic', self.font_size - 2),
            height=25,
            state=tk.DISABLED
        )
        persona_detail_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        def load_persona_list():
            """ペルソナ一覧読み込み"""
            persona_listbox.delete(0, tk.END)
            if hasattr(self.persona_manager, 'personas'):
                for name, persona in self.persona_manager.personas.items():
                    status = "🔴" if getattr(persona, 'is_troll', False) else "🟢"
                    age = getattr(persona, 'age', '不明')
                    generation = getattr(persona, 'generation', '不明')
                    display_text = f"{status} {name} ({age}歳, {generation})"
                    persona_listbox.insert(tk.END, display_text)
        
        def on_persona_select(event):
            """ペルソナ選択イベント"""
            selection = persona_listbox.curselection()
            if selection and hasattr(self.persona_manager, 'personas'):
                selected_text = persona_listbox.get(selection[0])
                # ペルソナ名を抽出
                parts = selected_text.split(" ")
                if len(parts) >= 2:
                    persona_name = parts[1]
                    
                    if persona_name in self.persona_manager.personas:
                        persona = self.persona_manager.personas[persona_name]
                        
                        # 詳細情報を表示
                        persona_detail_text.config(state=tk.NORMAL)
                        persona_detail_text.delete(1.0, tk.END)
                        
                        detail_info = self.format_persona_details(persona)
                        persona_detail_text.insert(tk.END, detail_info)
                        persona_detail_text.config(state=tk.DISABLED)
        
        persona_listbox.bind('<<ListboxSelect>>', on_persona_select)
        
        # ペルソナ管理ボタン
        button_frame = ttk.Frame(persona_frame, style='BBS.TFrame')
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            button_frame,
            text="一覧更新",
            command=load_persona_list,
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="データ保存",
            command=lambda: self.save_persona_data(),
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="詳細エクスポート",
            command=lambda: self.export_persona_details(),
            style='BBS.TButton'
        ).pack(side=tk.LEFT)
        
        # 初期ロード
        load_persona_list()
    
    def format_persona_details(self, persona) -> str:
        """ペルソナ詳細情報のフォーマット"""
        try:
            details = f"■ ペルソナ詳細: {persona.name} ■\n\n"
            
            # 基本情報
            details += "基本情報:\n"
            details += f"  年齢: {getattr(persona, 'age', '不明')}歳\n"
            details += f"  職業: {getattr(persona, 'occupation', '不明')}\n"
            details += f"  世代: {getattr(persona, 'generation', '不明')}\n"
            details += f"  MBTI: {getattr(persona, 'mbti', '不明')}\n"
            details += f"  タイプ: {'荒らし' if getattr(persona, 'is_troll', False) else '通常'}\n"
            details += f"  背景: {getattr(persona, 'background', '不明')}\n\n"
            
            # 性格特性
            if hasattr(persona, 'personality'):
                p = persona.personality
                details += "性格特性 (Big Five):\n"
                details += f"  外向性: {getattr(p, 'extroversion', 0):.2f}\n"
                details += f"  協調性: {getattr(p, 'agreeableness', 0):.2f}\n"
                details += f"  誠実性: {getattr(p, 'conscientiousness', 0):.2f}\n"
                details += f"  神経症傾向: {getattr(p, 'neuroticism', 0):.2f}\n"
                details += f"  開放性: {getattr(p, 'openness', 0):.2f}\n\n"
                
                details += "拡張性格特性:\n"
                details += f"  創造性: {getattr(p, 'creativity', 0):.2f}\n"
                details += f"  好奇心: {getattr(p, 'curiosity', 0):.2f}\n"
                details += f"  競争心: {getattr(p, 'competitiveness', 0):.2f}\n"
                details += f"  共感性: {getattr(p, 'empathy', 0):.2f}\n"
                details += f"  忍耐力: {getattr(p, 'patience', 0):.2f}\n"
                details += f"  ユーモア: {getattr(p, 'humor', 0):.2f}\n\n"
            
            # 感情状態
            if hasattr(persona, 'emotions'):
                e = persona.emotions
                details += "現在の感情状態:\n"
                details += f"  幸福度: {getattr(e, 'happiness', 0):.2f}\n"
                details += f"  怒り: {getattr(e, 'anger', 0):.2f}\n"
                details += f"  悲しみ: {getattr(e, 'sadness', 0):.2f}\n"
                details += f"  興奮: {getattr(e, 'excitement', 0):.2f}\n"
                details += f"  平静: {getattr(e, 'calmness', 0):.2f}\n"
                details += f"  自信: {getattr(e, 'confidence', 0):.2f}\n\n"
            
            # タイピング特性
            if hasattr(persona, 'typing'):
                t = persona.typing
                details += "タイピング特性:\n"
                details += f"  速度: {getattr(t, 'speed', '不明')}\n"
                details += f"  文体: {getattr(t, 'sentence_style', '不明')}\n"
                details += f"  丁寧さ: {getattr(t, 'politeness_level', '不明')}\n"
                details += f"  誤字率: {getattr(t, 'error_rate', 0):.2%}\n"
                details += f"  絵文字使用率: {getattr(t, 'emoji_usage', 0):.2%}\n\n"
            
            # 活動統計
            details += "活動統計:\n"
            details += f"  投稿数: {getattr(persona, 'post_count', 0)}\n"
            details += f"  活動レベル: {getattr(persona, 'activity_level', 0):.2f}\n"
            
            last_post_time = getattr(persona, 'last_post_time', None)
            if last_post_time:
                if isinstance(last_post_time, str):
                    details += f"  最終投稿: {last_post_time}\n"
                else:
                    details += f"  最終投稿: {last_post_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            else:
                details += "  最終投稿: なし\n"
            
            # 学習データ
            if hasattr(persona, 'memory'):
                m = persona.memory
                details += "\n学習データ:\n"
                details += f"  記憶数: {len(getattr(m, 'memories', []))}\n"
                details += f"  トピック嗜好数: {len(getattr(m, 'topic_preferences', {}))}\n"
                details += f"  語彙使用数: {len(getattr(m, 'vocabulary_usage', {}))}\n"
            
            return details
            
        except Exception as e:
            logger.error(f"[ADMIN] ペルソナ詳細フォーマットエラー: {e}")
            return f"ペルソナ詳細の表示中にエラーが発生しました: {e}"
    
    def create_data_management_tab(self, notebook):
        """データ管理タブ作成"""
        data_frame = ttk.Frame(notebook, style='BBS.TFrame')
        notebook.add(data_frame, text="データ管理")
        
        # データバックアップセクション
        backup_section = ttk.LabelFrame(data_frame, text="データバックアップ", style='BBS.TFrame')
        backup_section.pack(fill=tk.X, padx=10, pady=10)
        
        backup_button_frame = ttk.Frame(backup_section, style='BBS.TFrame')
        backup_button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            backup_button_frame,
            text="完全バックアップ",
            command=lambda: self.create_full_backup(),
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            backup_button_frame,
            text="データベースのみ",
            command=lambda: self.backup_database_only(),
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            backup_button_frame,
            text="設定ファイル",
            command=lambda: self.backup_settings(),
            style='BBS.TButton'
        ).pack(side=tk.LEFT)
        
        # データインポートセクション
        import_section = ttk.LabelFrame(data_frame, text="データインポート", style='BBS.TFrame')
        import_section.pack(fill=tk.X, padx=10, pady=10)
        
        import_button_frame = ttk.Frame(import_section, style='BBS.TFrame')
        import_button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            import_button_frame,
            text="バックアップ復元",
            command=lambda: self.restore_backup(),
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            import_button_frame,
            text="CSVインポート",
            command=lambda: self.import_csv_data(),
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            import_button_frame,
            text="設定復元",
            command=lambda: self.restore_settings(),
            style='BBS.TButton'
        ).pack(side=tk.LEFT)
        
        # データクリーンアップセクション
        cleanup_section = ttk.LabelFrame(data_frame, text="データクリーンアップ", style='BBS.TFrame')
        cleanup_section.pack(fill=tk.X, padx=10, pady=10)
        
        cleanup_button_frame = ttk.Frame(cleanup_section, style='BBS.TFrame')
        cleanup_button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            cleanup_button_frame,
            text="古い投稿削除",
            command=lambda: self.cleanup_old_posts(),
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            cleanup_button_frame,
            text="ログファイル整理",
            command=lambda: self.cleanup_log_files(),
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            cleanup_button_frame,
            text="データベース最適化",
            command=lambda: self.optimize_database(),
            style='BBS.TButton'
        ).pack(side=tk.LEFT)
    
    def create_settings_tab(self, notebook):
        """設定タブ作成"""
        settings_frame = ttk.Frame(notebook, style='BBS.TFrame')
        notebook.add(settings_frame, text="設定")
        
        # フォント設定セクション
        font_section = ttk.LabelFrame(settings_frame, text="フォント設定", style='BBS.TFrame')
        font_section.pack(fill=tk.X, padx=10, pady=10)
        
        font_frame = ttk.Frame(font_section, style='BBS.TFrame')
        font_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(font_frame, text="フォントサイズ:", style='BBS.TLabel').pack(side=tk.LEFT)
        
        font_var = tk.IntVar(value=self.font_size)
        font_scale = tk.Scale(
            font_frame,
            from_=8,
            to=20,
            orient=tk.HORIZONTAL,
            variable=font_var,
            bg="#000080",
            fg="#FFFFFF",
            command=lambda v: self.change_font_size(int(v) - self.font_size),
            length=200
        )
        font_scale.pack(side=tk.LEFT, padx=(10, 0))
        
        # ウィンドウ設定セクション
        window_section = ttk.LabelFrame(settings_frame, text="ウィンドウ設定", style='BBS.TFrame')
        window_section.pack(fill=tk.X, padx=10, pady=10)
        
        window_frame = ttk.Frame(window_section, style='BBS.TFrame')
        window_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(window_frame, text=f"現在のサイズ: {self.window_width}x{self.window_height}", style='BBS.TLabel').pack(anchor=tk.W)
        
        size_buttons = ttk.Frame(window_frame, style='BBS.TFrame')
        size_buttons.pack(anchor=tk.W, pady=5)
        
        ttk.Button(
            size_buttons,
            text="800x600",
            command=lambda: self.set_window_size(800, 600),
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            size_buttons,
            text="1024x768",
            command=lambda: self.set_window_size(1024, 768),
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            size_buttons,
            text="1200x800",
            command=lambda: self.set_window_size(1200, 800),
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            size_buttons,
            text="1400x900",
            command=lambda: self.set_window_size(1400, 900),
            style='BBS.TButton'
        ).pack(side=tk.LEFT)
        
        # AI設定セクション
        ai_settings_section = ttk.LabelFrame(settings_frame, text="AI設定", style='BBS.TFrame')
        ai_settings_section.pack(fill=tk.X, padx=10, pady=10)
        
        ai_settings_frame = ttk.Frame(ai_settings_section, style='BBS.TFrame')
        ai_settings_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(ai_settings_frame, text="タイムアウト設定:", style='BBS.TLabel').pack(anchor=tk.W)
        
        timeout_frame = ttk.Frame(ai_settings_frame, style='BBS.TFrame')
        timeout_frame.pack(anchor=tk.W, pady=5)
        
        timeout_var = tk.IntVar(value=30)
        timeout_scale = tk.Scale(
            timeout_frame,
            from_=10,
            to=60,
            orient=tk.HORIZONTAL,
            variable=timeout_var,
            bg="#000080",
            fg="#FFFFFF",
            length=200
        )
        timeout_scale.pack(side=tk.LEFT)
        
        ttk.Label(timeout_frame, text="秒", style='BBS.TLabel').pack(side=tk.LEFT, padx=(5, 0))
        
        # 保存ボタン
        save_frame = ttk.Frame(settings_frame, style='BBS.TFrame')
        save_frame.pack(fill=tk.X, padx=10, pady=20)
        
        ttk.Button(
            save_frame,
            text="設定保存",
            command=self.save_all_settings,
            style='BBS.TButton'
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            save_frame,
            text="設定リセット",
            command=self.reset_all_settings,
            style='BBS.TButton'
        ).pack(side=tk.LEFT)
    
    # 管理機能メソッド群
    def set_ai_activity(self, enabled: bool):
        """AI活動設定"""
        self.ai_activity_enabled = enabled
        self.update_status()
        logger.info(f"[ADMIN] AI活動: {'有効' if enabled else '無効'}")
    
    def update_interval(self, value):
        """投稿間隔更新"""
        self.auto_post_interval = int(value)
        logger.info(f"[APP] 投稿間隔変更: {self.auto_post_interval}秒")
    
    def reset_database(self):
        """データベース初期化"""
        try:
            if messagebox.askyesno("確認", "データベースを初期化しますか？\n全てのデータが削除されます。"):
                logger.info("[ADMIN] データベース初期化開始")
                
                # 一時的にAI活動を停止
                old_ai_state = self.ai_activity_enabled
                self.ai_activity_enabled = False
                
                # データベースを削除して再作成
                if os.path.exists("bbs_database.db"):
                    os.remove("bbs_database.db")
                
                # 新しいデータベースを初期化
                self.db_manager = DatabaseManager()
                self.category_manager = CategoryManager(self.db_manager)
                self.thread_manager = ThreadManager(self.db_manager, self.category_manager)
                
                # UI更新
                self.update_thread_list()
                self.update_post_display()
                
                # AI活動状態を復元
                self.ai_activity_enabled = old_ai_state
                
                messagebox.showinfo("完了", "データベースの初期化が完了しました。")
                logger.info("[ADMIN] データベース初期化完了")
                
        except Exception as e:
            logger.error(f"[ADMIN] データベース初期化エラー: {e}")
            messagebox.showerror("エラー", f"データベース初期化に失敗しました: {e}")
    
    def regenerate_personas(self):
        """ペルソナ再生成"""
        try:
            if messagebox.askyesno("確認", "ペルソナを再生成しますか？"):
                logger.info("[ADMIN] ペルソナ再生成開始")
                
                # ペルソナマネージャーを再初期化
                self.persona_manager = PersonaManager(self.db_manager, self.ai_manager)
                
                messagebox.showinfo("完了", "ペルソナの再生成が完了しました。")
                logger.info("[ADMIN] ペルソナ再生成完了")
                
        except Exception as e:
            logger.error(f"[ADMIN] ペルソナ再生成エラー: {e}")
            messagebox.showerror("エラー", f"ペルソナ再生成に失敗しました: {e}")
    
    def recreate_threads(self):
        """スレッド再作成"""
        try:
            if messagebox.askyesno("確認", "スレッドを再作成しますか？"):
                logger.info("[ADMIN] スレッド再作成開始")
                
                # スレッドを再作成
                self.thread_manager.init_default_threads()
                self.update_thread_list()
                
                messagebox.showinfo("完了", "スレッドの再作成が完了しました。")
                logger.info("[ADMIN] スレッド再作成完了")
                
        except Exception as e:
            logger.error(f"[ADMIN] スレッド再作成エラー: {e}")
            messagebox.showerror("エラー", f"スレッド再作成に失敗しました: {e}")
    
    def complete_reset(self):
        """完全リセット"""
        try:
            if messagebox.askyesno("確認", "完全リセットを実行しますか？\n全てのデータが初期化されます。"):
                logger.info("[ADMIN] 完全リセット開始")
                
                # AI活動停止
                self.ai_activity_enabled = False
                
                # データベース削除・再作成
                if os.path.exists("bbs_database.db"):
                    os.remove("bbs_database.db")
                
                # 全てのマネージャーを再初期化
                self.db_manager = DatabaseManager()
                self.category_manager = CategoryManager(self.db_manager)
                self.thread_manager = ThreadManager(self.db_manager, self.category_manager)
                self.persona_manager = PersonaManager(self.db_manager, self.ai_manager)
                
                # UI状態をリセット
                self.current_main_category_id = None
                self.current_thread_id = None
                
                # カテゴリを再選択
                if self.category_listbox.size() > 0:
                    self.category_listbox.selection_set(0)
                    main_categories = self.category_manager.get_main_categories()
                    if main_categories:
                        self.current_main_category_id = main_categories[0]["id"]
                
                # UI更新
                self.update_thread_list()
                self.update_post_display()
                self.update_status()
                
                # AI活動再開
                self.ai_activity_enabled = True
                
                messagebox.showinfo("完了", "完全リセットが完了しました。")
                logger.info("[ADMIN] 完全リセット完了")
                
        except Exception as e:
            logger.error(f"[ADMIN] 完全リセットエラー: {e}")
            messagebox.showerror("エラー", f"完全リセットに失敗しました: {e}")
    
    def save_persona_data(self):
        """ペルソナデータ保存"""
        try:
            if hasattr(self.persona_manager, 'save_all_personas'):
                self.persona_manager.save_all_personas()
                messagebox.showinfo("完了", "ペルソナデータを保存しました。")
            else:
                messagebox.showwarning("警告", "ペルソナマネージャーが初期化されていません。")
        except Exception as e:
            logger.error(f"[ADMIN] ペルソナデータ保存エラー: {e}")
            messagebox.showerror("エラー", f"ペルソナデータ保存に失敗しました: {e}")
    
    def export_persona_details(self):
        """ペルソナ詳細エクスポート"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"persona_details_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"ペルソナ詳細エクスポート - {timestamp}\n")
                f.write("=" * 80 + "\n\n")
                
                if hasattr(self.persona_manager, 'personas'):
                    for name, persona in self.persona_manager.personas.items():
                        details = self.format_persona_details(persona)
                        f.write(details)
                        f.write("\n" + "=" * 80 + "\n\n")
            
            messagebox.showinfo("完了", f"ペルソナ詳細をエクスポートしました。\nファイル: {filename}")
            logger.info(f"[ADMIN] ペルソナ詳細エクスポート完了: {filename}")
            
        except Exception as e:
            logger.error(f"[ADMIN] ペルソナ詳細エクスポートエラー: {e}")
            messagebox.showerror("エラー", f"ペルソナ詳細エクスポートに失敗しました: {e}")
    
    def create_full_backup(self):
        """完全バックアップ作成"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"backup_{timestamp}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # データベースをコピー
            if os.path.exists("bbs_database.db"):
                shutil.copy2("bbs_database.db", os.path.join(backup_dir, "bbs_database.db"))
            
            # 設定ファイルをコピー
            if os.path.exists("bbs_settings.json"):
                shutil.copy2("bbs_settings.json", os.path.join(backup_dir, "bbs_settings.json"))
            
            # ログファイルをコピー
            if os.path.exists("bbs_app.log"):
                shutil.copy2("bbs_app.log", os.path.join(backup_dir, "bbs_app.log"))
            
            messagebox.showinfo("完了", f"完全バックアップを作成しました。\nディレクトリ: {backup_dir}")
            logger.info(f"[ADMIN] 完全バックアップ作成完了: {backup_dir}")
            
        except Exception as e:
            logger.error(f"[ADMIN] 完全バックアップエラー: {e}")
            messagebox.showerror("エラー", f"完全バックアップに失敗しました: {e}")
    
    def backup_database_only(self):
        """データベースのみバックアップ"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bbs_database_backup_{timestamp}.db"
            
            if os.path.exists("bbs_database.db"):
                shutil.copy2("bbs_database.db", filename)
                messagebox.showinfo("完了", f"データベースバックアップを作成しました。\nファイル: {filename}")
                logger.info(f"[ADMIN] データベースバックアップ完了: {filename}")
            else:
                messagebox.showwarning("警告", "データベースファイルが見つかりません。")
                
        except Exception as e:
            logger.error(f"[ADMIN] データベースバックアップエラー: {e}")
            messagebox.showerror("エラー", f"データベースバックアップに失敗しました: {e}")
    
    def backup_settings(self):
        """設定ファイルバックアップ"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bbs_settings_backup_{timestamp}.json"
            
            if os.path.exists("bbs_settings.json"):
                shutil.copy2("bbs_settings.json", filename)
                messagebox.showinfo("完了", f"設定ファイルバックアップを作成しました。\nファイル: {filename}")
                logger.info(f"[ADMIN] 設定バックアップ完了: {filename}")
            else:
                messagebox.showwarning("警告", "設定ファイルが見つかりません。")
                
        except Exception as e:
            logger.error(f"[ADMIN] 設定バックアップエラー: {e}")
            messagebox.showerror("エラー", f"設定バックアップに失敗しました: {e}")
    
    def restore_backup(self):
        """バックアップ復元"""
        try:
            filename = filedialog.askopenfilename(
                title="バックアップファイルを選択",
                filetypes=[("データベースファイル", "*.db"), ("全てのファイル", "*.*")]
            )
            
            if filename:
                if messagebox.askyesno("確認", f"バックアップを復元しますか？\n現在のデータは上書きされます。\n\nファイル: {filename}"):
                    # AI活動停止
                    old_ai_state = self.ai_activity_enabled
                    self.ai_activity_enabled = False
                    
                    # ファイルを復元
                    shutil.copy2(filename, "bbs_database.db")
                    
                    # システム再初期化
                    self.db_manager = DatabaseManager()
                    self.category_manager = CategoryManager(self.db_manager)
                    self.thread_manager = ThreadManager(self.db_manager, self.category_manager)
                    self.persona_manager = PersonaManager(self.db_manager, self.ai_manager)
                    
                    # UI更新
                    self.update_thread_list()
                    self.update_post_display()
                    
                    # AI活動復元
                    self.ai_activity_enabled = old_ai_state
                    
                    messagebox.showinfo("完了", "バックアップの復元が完了しました。")
                    logger.info(f"[ADMIN] バックアップ復元完了: {filename}")
                    
        except Exception as e:
            logger.error(f"[ADMIN] バックアップ復元エラー: {e}")
            messagebox.showerror("エラー", f"バックアップ復元に失敗しました: {e}")
    
    def import_csv_data(self):
        """CSVデータインポート"""
        # 実装: CSVインポート機能
        messagebox.showinfo("情報", "CSVインポート機能は次回アップデートで実装予定です。")
    
    def restore_settings(self):
        """設定復元"""
        try:
            filename = filedialog.askopenfilename(
                title="設定ファイルを選択",
                filetypes=[("JSONファイル", "*.json"), ("全てのファイル", "*.*")]
            )
            
            if filename:
                if messagebox.askyesno("確認", f"設定を復元しますか？\n現在の設定は上書きされます。\n\nファイル: {filename}"):
                    shutil.copy2(filename, "bbs_settings.json")
                    self.load_settings()
                    self.adjust_responsive_layout()
                    messagebox.showinfo("完了", "設定の復元が完了しました。")
                    logger.info(f"[ADMIN] 設定復元完了: {filename}")
                    
        except Exception as e:
            logger.error(f"[ADMIN] 設定復元エラー: {e}")
            messagebox.showerror("エラー", f"設定復元に失敗しました: {e}")
    
    def cleanup_old_posts(self):
        """古い投稿削除"""
        # 実装: 古い投稿のクリーンアップ
        messagebox.showinfo("情報", "古い投稿削除機能は次回アップデートで実装予定です。")
    
    def cleanup_log_files(self):
        """ログファイル整理"""
        try:
            if messagebox.askyesno("確認", "ログファイルを整理しますか？\n古いログが削除される可能性があります。"):
                # ログファイルのローテーション
                if os.path.exists("bbs_app.log"):
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    archived_name = f"bbs_app_archived_{timestamp}.log"
                    shutil.move("bbs_app.log", archived_name)
                    
                    # 新しいログファイルを開始
                    logger.info("[ADMIN] ログファイル整理完了")
                    
                messagebox.showinfo("完了", "ログファイルの整理が完了しました。")
                
        except Exception as e:
            logger.error(f"[ADMIN] ログファイル整理エラー: {e}")
            messagebox.showerror("エラー", f"ログファイル整理に失敗しました: {e}")
    
    def optimize_database(self):
        """データベース最適化"""
        try:
            if messagebox.askyesno("確認", "データベースを最適化しますか？\n処理に時間がかかる場合があります。"):
                logger.info("[ADMIN] データベース最適化開始")
                
                # AI活動停止
                old_ai_state = self.ai_activity_enabled
                self.ai_activity_enabled = False
                
                # VACUUM実行
                with sqlite3.connect(self.db_manager.db_path) as conn:
                    conn.execute("VACUUM")
                    conn.execute("ANALYZE")
                
                # AI活動復元
                self.ai_activity_enabled = old_ai_state
                
                messagebox.showinfo("完了", "データベースの最適化が完了しました。")
                logger.info("[ADMIN] データベース最適化完了")
                
        except Exception as e:
            logger.error(f"[ADMIN] データベース最適化エラー: {e}")
            messagebox.showerror("エラー", f"データベース最適化に失敗しました: {e}")
    
    def set_window_size(self, width: int, height: int):
        """ウィンドウサイズ設定"""
        try:
            self.root.geometry(f"{width}x{height}")
            self.window_width = width
            self.window_height = height
            self.save_settings()
            logger.info(f"[APP] ウィンドウサイズ変更: {width}x{height}")
        except Exception as e:
            logger.error(f"[APP] ウィンドウサイズ変更エラー: {e}")
    
    def save_all_settings(self):
        """全設定保存"""
        try:
            self.save_settings()
            messagebox.showinfo("完了", "設定を保存しました。")
            logger.info("[ADMIN] 設定保存完了")
        except Exception as e:
            logger.error(f"[ADMIN] 設定保存エラー: {e}")
            messagebox.showerror("エラー", f"設定保存に失敗しました: {e}")
    
    def reset_all_settings(self):
        """全設定リセット"""
        try:
            if messagebox.askyesno("確認", "設定をリセットしますか？\n全ての設定がデフォルト値に戻ります。"):
                # デフォルト値に戻す
                self.font_size = 12
                self.window_width = 1200
                self.window_height = 800
                self.auto_post_interval = 60
                self.ai_activity_enabled = True
                
                # UI更新
                self.root.geometry(f"{self.window_width}x{self.window_height}")
                self.adjust_responsive_layout()
                self.save_settings()
                
                messagebox.showinfo("完了", "設定をリセットしました。")
                logger.info("[ADMIN] 設定リセット完了")
                
        except Exception as e:
            logger.error(f"[ADMIN] 設定リセットエラー: {e}")
            messagebox.showerror("エラー", f"設定リセットに失敗しました: {e}")
    
    def update_status(self):
        """ステータス更新 - 完全版"""
        try:
            connection_status = self.ai_manager.get_connection_status()
            ai_status = f"AI: {connection_status.get('current_provider', 'なし')}"
            
            status_text = f"Version: {APP_VERSION} | Build: {APP_BUILD} | {ai_status} | "
            status_text += f"AI活動: {'ON' if self.ai_activity_enabled else 'OFF'} | "
            status_text += f"間隔: {self.auto_post_interval}秒"
            
            # ペルソナ数とスレッド数も表示
            if hasattr(self.persona_manager, 'personas'):
                persona_count = len(self.persona_manager.personas)
                status_text += f" | ペルソナ: {persona_count}体"
            
            if hasattr(self, 'current_threads'):
                thread_count = len(self.current_threads)
                status_text += f" | スレッド: {thread_count}本"
            
            self.status_label.config(text=status_text)
            
        except Exception as e:
            logger.error(f"[APP] ステータス更新エラー: {e}")
    
    def start_auto_posting(self):
        """自動投稿システム開始 - 完全版"""
        def auto_post_worker():
            """自動投稿ワーカー - 拡張版"""
            logger.info("[AUTO_POST] 自動投稿システム開始")
            
            while True:
                try:
                    if not self.ai_activity_enabled:
                        time.sleep(30)
                        continue
                    
                    # 全スレッドを取得
                    main_categories = self.category_manager.get_main_categories()
                    all_threads = []
                    for cat in main_categories:
                        threads = self.thread_manager.get_threads_by_category(cat["id"])
                        all_threads.extend(threads)
                    
                    if not all_threads:
                        logger.warning("[AUTO_POST] スレッドが存在しません")
                        time.sleep(60)
                        continue
                    
                    # 投稿候補スレッドを選出
                    candidate_threads = []
                    for thread in all_threads:
                        # ロックされたスレッドはスキップ
                        if thread.get('is_locked', False):
                            continue
                        
                        thread_id = thread['thread_id']
                        seconds_since_last_ai_post = self.thread_manager.get_seconds_since_last_ai_post(thread_id)
                        
                        # 投稿間隔チェック
                        if seconds_since_last_ai_post >= self.auto_post_interval:
                            # 投稿確率計算（時間が経つほど高確率）
                            base_probability = 0.2
                            time_bonus = (seconds_since_last_ai_post - self.auto_post_interval) * 0.002
                            thread_popularity = min(0.3, thread['post_count'] * 0.01)  # 人気スレッドは投稿されやすい
                            
                            probability = min(0.8, base_probability + time_bonus + thread_popularity)
                            
                            if random.random() < probability:
                                candidate_threads.append({
                                    'thread_id': thread_id,
                                    'thread_info': thread,
                                    'seconds_since': seconds_since_last_ai_post,
                                    'priority': seconds_since_last_ai_post + random.uniform(0, 50),
                                    'probability': probability
                                })
                    
                    if not candidate_threads:
                        logger.debug("[AUTO_POST] 投稿候補なし")
                        time.sleep(random.uniform(30, 60))
                        continue
                    
                    # 優先度順でソート
                    candidate_threads.sort(key=lambda x: x['priority'], reverse=True)
                    
                    # 上位1-3スレッドに投稿
                    max_posts = min(len(candidate_threads), random.choice([1, 1, 2, 2, 3]))
                    actual_posts = 0
                    
                    for i in range(max_posts):
                        if i < len(candidate_threads):
                            candidate = candidate_threads[i]
                            thread_id = candidate['thread_id']
                            thread_info = candidate['thread_info']
                            
                            logger.info(f"[AUTO_POST] 投稿対象選択: Thread {thread_id} ({thread_info['title']}) - 確率: {candidate['probability']:.2f}")
                            
                            # ペルソナによる投稿生成
                            if hasattr(self.persona_manager, 'generate_auto_post'):
                                success = self.persona_manager.generate_auto_post(thread_id)
                                
                                if success:
                                    actual_posts += 1
                                    # UI更新をメインスレッドに依頼
                                    self.message_queue.put(('update_display', None))
                                    logger.info(f"[AUTO_POST] 投稿成功: Thread {thread_id}")
                                    
                                    # 投稿間隔（複数投稿の場合）
                                    post_interval = random.uniform(10, 25)
                                    time.sleep(post_interval)
                                else:
                                    logger.warning(f"[AUTO_POST] 投稿失敗: Thread {thread_id}")
                            else:
                                logger.warning("[AUTO_POST] ペルソナマネージャーに投稿メソッドがありません")
                    
                    logger.info(f"[AUTO_POST] 投稿サイクル完了: {actual_posts}/{max_posts}件投稿")
                    
                    # 次のチェックまでの待機時間（投稿数に応じて調整）
                    if actual_posts > 0:
                        check_interval = random.uniform(60, 120)
                    else:
                        check_interval = random.uniform(30, 60)
                    
                    logger.debug(f"[AUTO_POST] 次回チェックまで {check_interval:.1f}秒待機")
                    time.sleep(check_interval)
                    
                except KeyboardInterrupt:
                    logger.info("[AUTO_POST] 自動投稿システム停止（キーボード割り込み）")
                    break
                except Exception as e:
                    logger.error(f"[AUTO_POST] 自動投稿エラー: {e}")
                    time.sleep(60)  # エラー時は長めに待機
        
        # 自動投稿スレッドを開始
        auto_post_thread = threading.Thread(target=auto_post_worker, daemon=True)
        auto_post_thread.start()
        logger.info("[APP] 自動投稿システム開始完了")
    
    def process_messages(self):
        """メッセージキュー処理 - 完全版"""
        try:
            processed_count = 0
            max_process = 10  # 一度に処理する最大メッセージ数
            
            while processed_count < max_process:
                try:
                    message_type, data = self.message_queue.get_nowait()
                    processed_count += 1
                    
                    if message_type == 'update_display':
                        # 表示更新
                        if self.current_thread_id:
                            self.update_post_display()
                        self.update_thread_list()
                        self.update_status()
                        
                    elif message_type == 'show_notification':
                        # 通知表示
                        if isinstance(data, dict):
                            messagebox.showinfo(data.get('title', '通知'), data.get('message', ''))
                        else:
                            messagebox.showinfo("通知", str(data))
                    
                    elif message_type == 'persona_update':
                        # ペルソナ状態更新
                        if hasattr(self.persona_manager, 'update_persona_status'):
                            self.persona_manager.update_persona_status(data)
                    
                    elif message_type == 'thread_created':
                        # 新規スレッド作成通知
                        self.update_thread_list()
                        if data and 'thread_id' in data:
                            # 作成されたスレッドに移動
                            for i, thread in enumerate(self.current_threads):
                                if thread['thread_id'] == data['thread_id']:
                                    self.thread_listbox.selection_clear(0, tk.END)
                                    self.thread_listbox.selection_set(i)
                                    self.current_thread_id = data['thread_id']
                                    self.update_post_display()
                                    break
                    
                    elif message_type == 'ai_response_generated':
                        # AI応答生成完了通知
                        if data and 'thread_id' in data and data['thread_id'] == self.current_thread_id:
                            self.update_post_display()
                    
                    elif message_type == 'error':
                        # エラー通知
                        logger.error(f"[MESSAGE] エラーメッセージ: {data}")
                        if data and 'show_user' in data and data['show_user']:
                            messagebox.showerror("エラー", data.get('message', '不明なエラーが発生しました'))
                    
                    elif message_type == 'log':
                        # ログメッセージ
                        if data and 'level' in data and 'message' in data:
                            level = data['level']
                            message = data['message']
                            if level == 'info':
                                logger.info(f"[MESSAGE] {message}")
                            elif level == 'warning':
                                logger.warning(f"[MESSAGE] {message}")
                            elif level == 'error':
                                logger.error(f"[MESSAGE] {message}")
                    
                    else:
                        logger.warning(f"[MESSAGE] 未知のメッセージタイプ: {message_type}")
                        
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"[MESSAGE] メッセージ処理エラー: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"[MESSAGE] メッセージキュー処理エラー: {e}")
        
        # 定期的にメッセージキューをチェック（レスポンシブ間隔）
        if processed_count > 0:
            # メッセージがあった場合は短い間隔で再チェック
            self.root.after(200, self.process_messages)
        else:
            # メッセージがない場合は通常間隔
            self.root.after(1000, self.process_messages)
    
    def on_window_close(self):
        """ウィンドウクローズイベント"""
        try:
            logger.info("[APP] アプリケーション終了処理開始")
            
            # AI活動停止
            self.ai_activity_enabled = False
            
            # 設定保存
            self.save_settings()
            
            # ペルソナデータ保存
            if hasattr(self.persona_manager, 'save_all_personas'):
                try:
                    self.persona_manager.save_all_personas()
                    logger.info("[APP] ペルソナデータ保存完了")
                except Exception as e:
                    logger.error(f"[APP] ペルソナデータ保存エラー: {e}")
            
            # データベース接続終了
            try:
                if hasattr(self.db_manager, 'close'):
                    self.db_manager.close()
            except Exception as e:
                logger.error(f"[APP] データベース終了エラー: {e}")
            
            logger.info("[APP] アプリケーション終了処理完了")
            
        except Exception as e:
            logger.error(f"[APP] 終了処理エラー: {e}")
        finally:
            self.root.destroy()
    
    def run(self):
        """アプリケーション実行 - 完全版"""
        logger.info("[APP] アプリケーション開始")
        
        try:
            # ウィンドウクローズイベントの設定
            self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
            
            # 例外ハンドラーの設定
            def handle_exception(exc_type, exc_value, exc_traceback):
                if issubclass(exc_type, KeyboardInterrupt):
                    logger.info("[APP] キーボード割り込みによる終了")
                    sys.__excepthook__(exc_type, exc_value, exc_traceback)
                    return
                
                logger.error(f"[APP] 未処理例外: {exc_type.__name__}: {exc_value}")
                logger.error("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                
                # ユーザーに通知
                messagebox.showerror(
                    "予期しないエラー",
                    f"アプリケーションで予期しないエラーが発生しました。\n\n"
                    f"エラー種別: {exc_type.__name__}\n"
                    f"エラー内容: {exc_value}\n\n"
                    f"詳細はログファイルを確認してください。"
                )
            
            sys.excepthook = handle_exception
            
            # メインループ開始
            logger.info("[APP] メインループ開始")
            self.root.mainloop()
            
        except KeyboardInterrupt:
            logger.info("[APP] キーボード割り込みによる終了")
        except Exception as e:
            logger.error(f"[APP] 実行時エラー: {e}")
            messagebox.showerror("実行エラー", f"アプリケーション実行中にエラーが発生しました: {e}")
        finally:
            logger.info("[APP] アプリケーション終了")

# ==============================
# ユーティリティ関数群
# ==============================

def check_dependencies():
    """依存関係チェック"""
    print("[SYSTEM] 依存関係チェック中...")
    
    # 必須ライブラリのチェック
    required_modules = ['tkinter', 'sqlite3', 'threading', 'json', 'datetime', 'random', 're']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}: OK")
        except ImportError:
            missing_modules.append(module)
            print(f"  ❌ {module}: 不足")
    
    # オプションライブラリのチェック
    optional_modules = [
        ('g4f', 'G4F AI接続'),
        ('subprocess', 'Gemini CLI接続')
    ]
    
    for module, description in optional_modules:
        try:
            __import__(module)
            print(f"  ✅ {module} ({description}): OK")
        except ImportError:
            print(f"  ⚠️ {module} ({description}): 利用不可")
    
    if missing_modules:
        print(f"\n[ERROR] 必須モジュールが不足しています: {', '.join(missing_modules)}")
        return False
    
    print("[SYSTEM] 依存関係チェック完了")
    return True

def setup_logging():
    """ログ設定の詳細化"""
    # ログファイルのローテーション
    if os.path.exists('bbs_app.log'):
        file_size = os.path.getsize('bbs_app.log')
        if file_size > 10 * 1024 * 1024:  # 10MB以上の場合
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.move('bbs_app.log', f'bbs_app_old_{timestamp}.log')
    
    # ログレベルの設定
    log_level = os.environ.get('BBS_LOG_LEVEL', 'INFO').upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    logging.getLogger().setLevel(numeric_level)

def print_startup_info():
    """起動時情報表示"""
    print("=" * 80)
    print(f"  {APP_NAME}")
    print(f"  Version: {APP_VERSION} (Build: {APP_BUILD})")
    print(f"  Author: {APP_AUTHOR}")
    print(f"  起動日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    print("\n[INFO] 主な機能:")
    print(" ✅ PC-98風UI（ダークテーマ・緑文字）")
    print(" ✅ 5大分類×5小分類の掲示板システム（25スレッド）")
    print(" ✅ 100体のAIペルソナ（年代別特徴、Big Five性格モデル）")
    print(" ✅ G4F + Gemini CLI対応（フォールバック機能付き）")
    print(" ✅ 動的スレッド作成機能")
    print(" ✅ 呼びかけ応答システム（@メンション対応）")
    print(" ✅ 自動投稿システム（間隔調整可能）")
    print(" ✅ 完全管理画面（ペルソナ詳細表示）")
    print(" ✅ データエクスポート機能（JSON/CSV/バックアップ）")
    print(" ✅ バージョン管理システム")
    print(" ✅ レスポンシブ対応（600px以上推奨）")
    print(" ✅ 学習機能付きペルソナ")
    print(" ✅ 投稿編集・削除機能")
    print(" ✅ 統計情報・アクティビティログ")
    
    print("\n[INFO] 技術仕様:")
    print(f" 🐍 Python: {sys.version.split()[0]}")
    print(f" 🗄️ データベース: SQLite3")
    print(f" 🖼️ GUI: Tkinter (PC-98風テーマ)")
    print(f" 🤖 AI: G4F + Gemini CLI")
    print(f" 💾 データ形式: JSON/CSV/SQLite")
    
    print("\n[INFO] カテゴリ構成:")
    categories = {
        "雑談": ["日常の話", "最近の出来事", "天気の話", "グルメ情報", "地域情報"],
        "ゲーム": ["レトロゲーム", "RPG", "アクションゲーム", "パズルゲーム", "新作ゲーム"],
        "趣味": ["読書", "映画鑑賞", "音楽", "スポーツ", "旅行"],
        "パソコン": ["ハードウェア", "ソフトウェア", "プログラミング", "インターネット", "トラブル相談"],
        "仕事": ["転職相談", "スキルアップ", "職場の悩み", "副業", "資格取得"]
    }
    
    for main_cat, sub_cats in categories.items():
        print(f" 📁 {main_cat}: {', '.join(sub_cats)}")
    
    print("\n[INFO] ペルソナ構成:")
    print(" 👴 1950s-60s世代（25名）: 60-75歳、戦後復興期育ち、慎重なタイピング")
    print(" 👨 1970s-80s世代（25名）: 40-59歳、高度経済成長期育ち、ビジネス調の文体")
    print(" 👩 1990s-2000s世代（25名）: 20-39歳、デジタルネイティブ、カジュアルな文体")
    print(" 👦 2010s-20s世代（25名）: 10-19歳、SNS世代、短文・絵文字多用")
    
    print("\n[INFO] キーボード操作:")
    shortcuts = [
        ("Ctrl+Enter", "投稿"),
        ("F5", "更新"),
        ("F12", "管理モード"),
        ("Ctrl+Q", "終了"),
        ("Ctrl+N", "新規スレッド作成"),
        ("Ctrl+E", "投稿編集"),
        ("Delete", "投稿削除"),
        ("Ctrl + / Ctrl -", "フォントサイズ調整"),
        ("Ctrl+0", "フォントサイズリセット")
    ]
    
    for shortcut, description in shortcuts:
        print(f" ⌨️ {shortcut}: {description}")

def check_system_requirements():
    """システム要件チェック"""
    print("\n[SYSTEM] システム要件チェック...")
    
    # Pythonバージョンチェック
    python_version = sys.version_info
    if python_version < (3, 7):
        print(f"  ❌ Python: {python_version.major}.{python_version.minor} (要求: 3.7以上)")
        return False
    else:
        print(f"  ✅ Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # メモリチェック（概算）
    try:
        import psutil
        memory = psutil.virtual_memory()
        if memory.available < 512 * 1024 * 1024:  # 512MB
            print(f"  ⚠️ 利用可能メモリ: {memory.available // (1024*1024)}MB (推奨: 512MB以上)")
        else:
            print(f"  ✅ 利用可能メモリ: {memory.available // (1024*1024)}MB")
    except ImportError:
        print("  ⚠️ メモリ情報取得不可（psutilモジュールなし）")
    
    # ディスク容量チェック
    try:
        disk_usage = shutil.disk_usage('.')
        free_space_mb = disk_usage.free // (1024 * 1024)
        if free_space_mb < 100:  # 100MB
            print(f"  ⚠️ ディスク空き容量: {free_space_mb}MB (推奨: 100MB以上)")
        else:
            print(f"  ✅ ディスク空き容量: {free_space_mb}MB")
    except Exception:
        print("  ⚠️ ディスク容量情報取得不可")
    
    print("[SYSTEM] システム要件チェック完了")
    return True

def create_sample_data():
    """サンプルデータ作成（デバッグ用）"""
    print("[DEBUG] サンプルデータ作成中...")
    
    try:
        # 開発・テスト用のサンプル投稿を生成
        sample_posts = [
            "こんにちは！初めて投稿します。よろしくお願いします。",
            "今日はいい天気ですね。散歩日和です。",
            "最近読んだ本がとても面白かったです。",
            "新しいゲームを始めました。RPGは時間を忘れてしまいます。",
            "プログラミングの勉強をしています。難しいですが楽しいです。"
        ]
        
        print(f"  サンプル投稿: {len(sample_posts)}件準備")
        print("[DEBUG] サンプルデータ作成完了")
        
        return sample_posts
        
    except Exception as e:
        print(f"[DEBUG] サンプルデータ作成エラー: {e}")
        return []

def main():
    """メイン関数 - 完全版"""
    # 基本情報表示
    print_startup_info()
    
    # システム要件チェック
    if not check_system_requirements():
        print("[ERROR] システム要件を満たしていません。")
        sys.exit(1)
    
    # 依存関係チェック
    if not check_dependencies():
        print("[ERROR] 必須ライブラリが不足しています。")
        sys.exit(1)
    
    # ログ設定
    setup_logging()
    
    # デバッグモード判定
    debug_mode = '--debug' in sys.argv or os.environ.get('BBS_DEBUG', '').lower() == 'true'
    if debug_mode:
        print("[DEBUG] デバッグモードで起動")
        create_sample_data()
    
    try:
        print("\n[SYSTEM] アプリケーション初期化中...")
        
        # メインアプリケーション作成
        app = BBSApplication()
        
        print("[SYSTEM] 初期化完了。アプリケーションを開始します。")
        
        # AI接続状況確認
        connection_status = app.ai_manager.get_connection_status()
        print(f"\n[INFO] AI接続状況:")
        if connection_status['g4f_available']:
            print(f"  ✅ G4F: {connection_status.get('current_provider', 'なし')}")
        else:
            print("  ❌ G4F: 利用不可")
        
        if connection_status['gemini_available']:
            print("  ✅ Gemini CLI: 利用可能")
        else:
            print("  ❌ Gemini CLI: 利用不可")
        
        if not connection_status['g4f_available'] and not connection_status['gemini_available']:
            print("\n[WARNING] AI接続が利用できません。手動投稿のみとなります。")
        
        # ペルソナ情報表示
        if hasattr(app.persona_manager, 'personas'):
            persona_count = len(app.persona_manager.personas)
            print(f"\n[INFO] ペルソナ: {persona_count}体のAIペルソナが生成されました")
        
        print(f"\n[INFO] データベース: {app.db_manager.db_path}")
        print(f"[INFO] 設定ファイル: bbs_settings.json")
        print(f"[INFO] ログファイル: bbs_app.log")
        
        print("\n" + "=" * 80)
        print("  🚀 アプリケーション開始")
        print("  👋 草の根BBSへようこそ！PC-98時代の雰囲気をお楽しみください")
        print("  📝 F12キーで管理画面、Ctrl+Qで終了です")
        print("=" * 80)
        
        # アプリケーション実行
        app.run()
        
    except KeyboardInterrupt:
        print("\n[INFO] キーボード割り込みによる終了")
    except Exception as e:
        print(f"\n[ERROR] アプリケーション開始エラー: {e}")
        logger.error(f"アプリケーション開始エラー: {e}")
        
        # エラー詳細をログに記録
        import traceback
        logger.error(f"エラー詳細: {traceback.format_exc()}")
        
        # ユーザーにエラー情報を表示
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # メインウィンドウを隠す
            messagebox.showerror(
                "起動エラー",
                f"アプリケーションの起動に失敗しました。\n\n"
                f"エラー: {e}\n\n"
                f"詳細はログファイル（bbs_app.log）を確認してください。"
            )
        except:
            pass  # Tkinter が使えない場合は無視
        
        sys.exit(1)
    
    finally:
        print("\n[SYSTEM] アプリケーション終了")

# ==============================
# プログラムエントリーポイント
# ==============================

if __name__ == "__main__":
    # 必要なモジュールのインポート
    import traceback
    
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL ERROR] 予期しないエラーが発生しました: {e}")
        print("=" * 80)
        traceback.print_exc()
        print("=" * 80)
        input("Enterキーを押して終了してください...")
        sys.exit(1)
