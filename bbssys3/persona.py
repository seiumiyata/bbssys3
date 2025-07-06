#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PC-98時代パソコン通信BBS風アプリケーション - ペルソナモジュール完全版
Version: 3.0.0 - 詳細ペルソナ設定・特殊属性対応版
Author: AI Assistant
Created: 2025-07-06
"""

import random
import json
import datetime
import time
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

# ==============================
# 基本データクラス定義
# ==============================

class Gender(Enum):
    """性別列挙型"""
    MALE = "男性"
    FEMALE = "女性"
    NON_BINARY = "その他"

class Generation(Enum):
    """世代列挙型"""
    GENERATION_1950s = "1950s-60s世代"
    GENERATION_1970s = "1970s-80s世代"
    GENERATION_1990s = "1990s-2000s世代"
    GENERATION_2010s = "2010s-20s世代"

class PersonalityType(Enum):
    """特殊属性タイプ"""
    NORMAL = "通常"
    TROLL = "荒らし"
    WEIRD = "変人"
    OBSESSIVE = "オタク"
    PROVOCATIVE = "挑発的"
    ANTISOCIAL = "反社会的"

@dataclass
class PersonalityTraits:
    """性格特性データクラス - Big Five + 拡張"""
    # Big Five
    extroversion: float = 0.5          # 外向性
    agreeableness: float = 0.5         # 協調性
    conscientiousness: float = 0.5     # 誠実性
    neuroticism: float = 0.5           # 神経症傾向
    openness: float = 0.5              # 開放性
    
    # 拡張性格特性
    creativity: float = 0.5            # 創造性
    curiosity: float = 0.5             # 好奇心
    competitiveness: float = 0.5       # 競争心
    empathy: float = 0.5               # 共感性
    patience: float = 0.5              # 忍耐力
    humor: float = 0.5                 # ユーモア
    skepticism: float = 0.5            # 懐疑心
    optimism: float = 0.5              # 楽観性
    assertiveness: float = 0.5         # 自己主張
    sociability: float = 0.5           # 社交性
    impulsiveness: float = 0.5         # 衝動性
    stubbornness: float = 0.5          # 頑固さ
    romanticism: float = 0.5           # ロマンチシズム
    materialism: float = 0.5           # 物質主義

    def get_personality_description(self) -> str:
        """性格説明文生成"""
        traits = []
        
        if self.extroversion > 0.7:
            traits.append("非常に社交的")
        elif self.extroversion < 0.3:
            traits.append("内向的")
        
        if self.agreeableness > 0.7:
            traits.append("協調性が高い")
        elif self.agreeableness < 0.3:
            traits.append("独立心が強い")
        
        if self.conscientiousness > 0.7:
            traits.append("責任感が強い")
        elif self.conscientiousness < 0.3:
            traits.append("自由奔放")
        
        if self.neuroticism > 0.7:
            traits.append("感情的")
        elif self.neuroticism < 0.3:
            traits.append("冷静沈着")
        
        if self.openness > 0.7:
            traits.append("新しいものが好き")
        elif self.openness < 0.3:
            traits.append("伝統的")
        
        return "、".join(traits) if traits else "バランスの取れた"

@dataclass
class EmotionalState:
    """感情状態データクラス"""
    happiness: float = 0.5      # 幸福度
    anger: float = 0.1          # 怒り
    sadness: float = 0.1        # 悲しみ
    fear: float = 0.1           # 恐怖
    surprise: float = 0.3       # 驚き
    disgust: float = 0.1        # 嫌悪
    excitement: float = 0.4     # 興奮
    calmness: float = 0.6       # 平静
    confidence: float = 0.5     # 自信
    curiosity: float = 0.4      # 好奇心

    def get_emotion_description(self) -> str:
        """現在の感情状態説明"""
        dominant_emotion = max(
            [
                (self.happiness, "幸せ"),
                (self.anger, "怒っている"),
                (self.sadness, "悲しい"),
                (self.excitement, "興奮している"),
                (self.calmness, "落ち着いている"),
                (self.confidence, "自信に満ちている")
            ],
            key=lambda x: x[0]
        )
        return dominant_emotion[1]

    def update_emotion(self, emotion_type: str, delta: float):
        """感情値更新"""
        if hasattr(self, emotion_type):
            current_value = getattr(self, emotion_type)
            new_value = max(0.0, min(1.0, current_value + delta))
            setattr(self, emotion_type, new_value)

@dataclass
class TypingCharacteristics:
    """タイピング特性データクラス"""
    speed: str = "普通"           # 速度（遅い、普通、速い、非常に速い）
    accuracy: float = 0.9         # 正確性（誤字率の逆）
    sentence_style: str = "普通"   # 文体
    politeness_level: str = "普通" # 丁寧さ
    emoji_usage: float = 0.3      # 絵文字使用率
    abbreviation_usage: float = 0.2  # 略語使用率
    punctuation_style: str = "標準"  # 句読点スタイル
    
    @property
    def error_rate(self) -> float:
        """誤字率"""
        return 1.0 - self.accuracy

@dataclass
class FamilyComposition:
    """家族構成データクラス"""
    marital_status: str = "未婚"    # 婚姻状況
    spouse: Optional[str] = None    # 配偶者
    children_count: int = 0         # 子供の数
    living_situation: str = "一人暮らし"  # 居住状況
    pets: List[str] = None          # ペット
    
    def __post_init__(self):
        if self.pets is None:
            self.pets = []

@dataclass
class WorkInfo:
    """職業情報データクラス"""
    occupation: str = "無職"        # 職業
    job_title: str = ""            # 職種
    industry: str = ""             # 業種
    company_size: str = "中小企業"  # 会社規模
    work_style: str = "会社員"      # 働き方
    experience_years: int = 0       # 経験年数
    salary_level: str = "普通"      # 給与レベル

@dataclass
class SpecialAttributes:
    """特殊属性データクラス"""
    personality_type: PersonalityType = PersonalityType.NORMAL
    obsessions: List[str] = None    # こだわり・執着
    fetishes: List[str] = None      # 性癖・嗜好
    phobias: List[str] = None       # 恐怖症
    mental_traits: List[str] = None # 精神的特徴
    social_quirks: List[str] = None # 社会的な癖
    
    def __post_init__(self):
        if self.obsessions is None:
            self.obsessions = []
        if self.fetishes is None:
            self.fetishes = []
        if self.phobias is None:
            self.phobias = []
        if self.mental_traits is None:
            self.mental_traits = []
        if self.social_quirks is None:
            self.social_quirks = []

@dataclass
class LearningMemory:
    """学習記憶データクラス"""
    memories: List[Dict] = None
    topic_preferences: Dict[str, float] = None
    vocabulary_usage: Dict[str, int] = None
    interaction_history: List[Dict] = None
    learning_rate: float = 0.1
    memory_retention: float = 0.8
    
    def __post_init__(self):
        if self.memories is None:
            self.memories = []
        if self.topic_preferences is None:
            self.topic_preferences = {}
        if self.vocabulary_usage is None:
            self.vocabulary_usage = {}
        if self.interaction_history is None:
            self.interaction_history = []

# ==============================
# ペルソナクラス定義
# ==============================

class Persona:
    """個別ペルソナクラス - 完全版"""
    
    def __init__(self, name: str, age: int, gender: Gender, generation: Generation):
        self.name = name
        self.age = age
        self.gender = gender
        self.generation = generation
        self.mbti = self._generate_mbti()
        
        # 基本属性
        self.personality = PersonalityTraits()
        self.emotions = EmotionalState()
        self.typing = TypingCharacteristics()
        self.family = FamilyComposition()
        self.work = WorkInfo()
        self.special = SpecialAttributes()
        self.memory = LearningMemory()
        
        # 活動統計
        self.post_count = 0
        self.activity_level = random.uniform(0.3, 0.8)
        self.last_post_time = None
        self.created_at = datetime.datetime.now()
        self.is_active = True
        
        # 背景情報
        self.background = ""
        self.hobbies = []
        self.favorite_topics = []
        self.catchphrases = []
        
        # 初期化
        self._initialize_persona()
    
    def _generate_mbti(self) -> str:
        """MBTI生成"""
        types = [
            "INTJ", "INTP", "ENTJ", "ENTP",
            "INFJ", "INFP", "ENFJ", "ENFP",
            "ISTJ", "ISFJ", "ESTJ", "ESFJ",
            "ISTP", "ISFP", "ESTP", "ESFP"
        ]
        return random.choice(types)
    
    def _initialize_persona(self):
        """ペルソナ初期化"""
        # 年代別特性の設定
        self._set_generation_traits()
        
        # 性別特性の設定
        self._set_gender_traits()
        
        # 職業情報の設定
        self._set_work_info()
        
        # 家族構成の設定
        self._set_family_composition()
        
        # 特殊属性の設定
        self._set_special_attributes()
        
        # タイピング特性の設定
        self._set_typing_characteristics()
        
        # 背景情報の生成
        self._generate_background()
    
    def _set_generation_traits(self):
        """年代別特性設定"""
        if self.generation == Generation.GENERATION_1950s:
            # 1950s-60s世代（60-75歳）
            self.personality.conscientiousness = random.uniform(0.6, 0.9)
            self.personality.patience = random.uniform(0.7, 0.95)
            self.personality.skepticism = random.uniform(0.5, 0.8)
            self.personality.materialism = random.uniform(0.3, 0.6)
            self.typing.speed = random.choice(["遅い", "普通"])
            self.typing.politeness_level = "丁寧"
            self.typing.emoji_usage = random.uniform(0.0, 0.1)
            
        elif self.generation == Generation.GENERATION_1970s:
            # 1970s-80s世代（40-59歳）
            self.personality.competitiveness = random.uniform(0.6, 0.9)
            self.personality.assertiveness = random.uniform(0.5, 0.8)
            self.personality.materialism = random.uniform(0.5, 0.8)
            self.typing.speed = "普通"
            self.typing.politeness_level = random.choice(["普通", "丁寧"])
            self.typing.emoji_usage = random.uniform(0.1, 0.3)
            
        elif self.generation == Generation.GENERATION_1990s:
            # 1990s-2000s世代（20-39歳）
            self.personality.openness = random.uniform(0.6, 0.9)
            self.personality.curiosity = random.uniform(0.7, 0.95)
            self.personality.sociability = random.uniform(0.5, 0.8)
            self.typing.speed = random.choice(["普通", "速い"])
            self.typing.emoji_usage = random.uniform(0.2, 0.5)
            
        elif self.generation == Generation.GENERATION_2010s:
            # 2010s-20s世代（10-19歳）
            self.personality.impulsiveness = random.uniform(0.6, 0.9)
            self.personality.sociability = random.uniform(0.7, 0.95)
            self.personality.openness = random.uniform(0.8, 1.0)
            self.typing.speed = "非常に速い"
            self.typing.emoji_usage = random.uniform(0.5, 0.8)
            self.typing.abbreviation_usage = random.uniform(0.3, 0.7)
    
    def _set_gender_traits(self):
        """性別特性設定"""
        if self.gender == Gender.FEMALE:
            self.personality.empathy += random.uniform(0.1, 0.3)
            self.personality.agreeableness += random.uniform(0.05, 0.2)
            self.emotions.happiness += random.uniform(0.05, 0.15)
        elif self.gender == Gender.MALE:
            self.personality.assertiveness += random.uniform(0.1, 0.3)
            self.personality.competitiveness += random.uniform(0.05, 0.2)
            self.emotions.confidence += random.uniform(0.05, 0.15)
        
        # 値の正規化
        self._normalize_personality_values()
    
    def _set_work_info(self):
        """職業情報設定"""
        # 年代別職業設定
        if self.generation == Generation.GENERATION_1950s:
            occupations = [
                ("公務員", "事務職", "行政"),
                ("会社員", "管理職", "製造業"),
                ("自営業", "商店主", "小売業"),
                ("年金受給者", "無職", ""),
                ("農業", "農家", "農業")
            ]
        elif self.generation == Generation.GENERATION_1970s:
            occupations = [
                ("会社員", "部長", "製造業"),
                ("会社員", "課長", "金融業"),
                ("自営業", "経営者", "サービス業"),
                ("公務員", "係長", "行政"),
                ("専門職", "技術者", "IT")
            ]
        elif self.generation == Generation.GENERATION_1990s:
            occupations = [
                ("会社員", "主任", "IT"),
                ("専門職", "エンジニア", "IT"),
                ("会社員", "営業", "商社"),
                ("フリーランス", "デザイナー", "クリエイティブ"),
                ("公務員", "職員", "行政"),
                ("専業主婦", "主婦", "")
            ]
        else:  # 2010s世代
            occupations = [
                ("学生", "高校生", "教育"),
                ("学生", "大学生", "教育"),
                ("アルバイト", "店員", "小売業"),
                ("会社員", "新入社員", "IT"),
                ("フリーター", "アルバイト", "サービス業")
            ]
        
        occupation, job_title, industry = random.choice(occupations)
        self.work.occupation = occupation
        self.work.job_title = job_title
        self.work.industry = industry
        
        # 経験年数設定
        if self.age >= 22:
            self.work.experience_years = min(self.age - 22, 40)
        
        # 会社規模と給与レベル
        if occupation in ["会社員", "公務員"]:
            self.work.company_size = random.choice(["大企業", "中小企業", "ベンチャー"])
            self.work.salary_level = random.choice(["低い", "普通", "高い"])
    
    def _set_family_composition(self):
        """家族構成設定"""
        # 年代別婚姻率
        if self.age < 25:
            marriage_rate = 0.1
        elif self.age < 35:
            marriage_rate = 0.4
        elif self.age < 50:
            marriage_rate = 0.7
        else:
            marriage_rate = 0.8
        
        if random.random() < marriage_rate:
            self.family.marital_status = random.choice(["既婚", "既婚"])
            if self.gender == Gender.MALE:
                self.family.spouse = "妻"
            else:
                self.family.spouse = "夫"
            
            # 子供の設定
            if self.age > 25:
                children_probability = min(0.8, (self.age - 25) / 50)
                if random.random() < children_probability:
                    self.family.children_count = random.choices(
                        [1, 2, 3, 4], 
                        weights=[0.4, 0.4, 0.15, 0.05]
                    )[0]
        
        # 居住状況
        if self.family.marital_status == "既婚":
            self.family.living_situation = "夫婦"
            if self.family.children_count > 0:
                self.family.living_situation = "家族"
        elif self.age < 25:
            self.family.living_situation = random.choice(["実家", "一人暮らし", "寮"])
        else:
            self.family.living_situation = random.choice(["一人暮らし", "実家"])
        
        # ペット
        if random.random() < 0.3:
            pets = ["猫", "犬", "鳥", "魚", "ハムスター"]
            self.family.pets = [random.choice(pets)]
    
    def _set_special_attributes(self):
        """特殊属性設定"""
        # 5%の確率で荒らし属性
        if random.random() < 0.05:
            self.special.personality_type = PersonalityType.TROLL
            self.personality.agreeableness = random.uniform(0.0, 0.3)
            self.personality.assertiveness = random.uniform(0.7, 1.0)
            self.special.mental_traits = ["攻撃的", "挑発的", "論争好き"]
            self.special.social_quirks = ["煽り耐性低い", "マウント取りたがり"]
            
        # 10%の確率で変人属性
        elif random.random() < 0.10:
            self.special.personality_type = PersonalityType.WEIRD
            self.personality.openness = random.uniform(0.8, 1.0)
            self.personality.neuroticism = random.uniform(0.6, 0.9)
            weird_traits = [
                "独特な価値観", "変わった趣味", "マイペース", 
                "常識にとらわれない", "天然"
            ]
            self.special.mental_traits = random.sample(weird_traits, random.randint(1, 3))
            
        # 15%の確率でオタク属性
        elif random.random() < 0.15:
            self.special.personality_type = PersonalityType.OBSESSIVE
            self.personality.curiosity = random.uniform(0.8, 1.0)
            self.personality.sociability = random.uniform(0.2, 0.5)
            obsessions = [
                "アニメ", "ゲーム", "漫画", "鉄道", "アイドル", 
                "コンピューター", "映画", "音楽", "車", "料理"
            ]
            self.special.obsessions = random.sample(obsessions, random.randint(1, 3))
            
        # 特殊な嗜好や性癖（適度に設定）
        if random.random() < 0.2:
            fetishes = [
                "コレクション癖", "完璧主義", "ルーティン重視", 
                "数字へのこだわり", "清潔潔癖", "時間厳守"
            ]
            self.special.fetishes = random.sample(fetishes, random.randint(1, 2))
        
        # 恐怖症
        if random.random() < 0.1:
            phobias = [
                "高所恐怖症", "閉所恐怖症", "対人恐怖症", 
                "虫恐怖症", "暗所恐怖症"
            ]
            self.special.phobias = [random.choice(phobias)]
    
    def _set_typing_characteristics(self):
        """タイピング特性設定"""
        # 年代別調整（既に_set_generation_traitsで基本設定済み）
        
        # 性格による調整
        if self.personality.conscientiousness > 0.7:
            self.typing.accuracy = min(0.98, self.typing.accuracy + 0.1)
            self.typing.punctuation_style = "丁寧"
        
        if self.personality.impulsiveness > 0.7:
            self.typing.accuracy = max(0.7, self.typing.accuracy - 0.15)
            self.typing.abbreviation_usage += 0.2
        
        if self.special.personality_type == PersonalityType.TROLL:
            self.typing.sentence_style = "挑発的"
            self.typing.punctuation_style = "乱暴"
        
        # 文体設定
        if self.generation == Generation.GENERATION_1950s:
            self.typing.sentence_style = "丁寧語"
        elif self.special.personality_type == PersonalityType.WEIRD:
            self.typing.sentence_style = "独特"
        elif self.generation == Generation.GENERATION_2010s:
            self.typing.sentence_style = "カジュアル"
    
    def _generate_background(self):
        """背景情報生成"""
        background_parts = []
        
        # 基本情報
        background_parts.append(f"{self.age}歳の{self.gender.value}")
        background_parts.append(f"職業は{self.work.occupation}")
        
        if self.family.marital_status == "既婚":
            background_parts.append(f"{self.family.living_situation}で生活")
            if self.family.children_count > 0:
                background_parts.append(f"{self.family.children_count}人の子供がいる")
        
        # 性格特徴
        personality_desc = self.personality.get_personality_description()
        background_parts.append(f"性格は{personality_desc}")
        
        # 特殊属性
        if self.special.personality_type != PersonalityType.NORMAL:
            background_parts.append(f"{self.special.personality_type.value}的な面がある")
        
        self.background = "。".join(background_parts) + "。"
        
        # 趣味設定
        self._set_hobbies()
        
        # 好きな話題設定
        self._set_favorite_topics()
        
        # 口癖設定
        self._set_catchphrases()
    
    def _set_hobbies(self):
        """趣味設定"""
        hobby_pools = {
            Generation.GENERATION_1950s: [
                "園芸", "読書", "将棋", "囲碁", "盆栽", "書道", 
                "俳句", "茶道", "料理", "手芸"
            ],
            Generation.GENERATION_1970s: [
                "ゴルフ", "釣り", "登山", "読書", "映画鑑賞", 
                "音楽鑑賞", "料理", "旅行", "写真"
            ],
            Generation.GENERATION_1990s: [
                "映画鑑賞", "読書", "音楽", "スポーツ", "旅行", 
                "ゲーム", "アニメ", "料理", "ショッピング"
            ],
            Generation.GENERATION_2010s: [
                "ゲーム", "アニメ", "音楽", "SNS", "動画視聴", 
                "ファッション", "カラオケ", "スポーツ"
            ]
        }
        
        hobby_pool = hobby_pools.get(self.generation, [])
        if self.special.obsessions:
            hobby_pool.extend(self.special.obsessions)
        
        self.hobbies = random.sample(hobby_pool, random.randint(2, 4))
    
    def _set_favorite_topics(self):
        """好きな話題設定"""
        topic_pools = {
            "雑談": ["日常の話", "天気", "最近の出来事", "グルメ"],
            "ゲーム": ["レトロゲーム", "新作ゲーム", "RPG", "パズルゲーム"],
            "趣味": ["映画", "音楽", "読書", "スポーツ", "旅行"],
            "パソコン": ["ハードウェア", "ソフトウェア", "プログラミング"],
            "仕事": ["転職", "スキルアップ", "職場の悩み"]
        }
        
        # 世代と特殊属性に基づいて話題を選択
        favorite_categories = random.sample(list(topic_pools.keys()), random.randint(2, 4))
        
        for category in favorite_categories:
            topics = random.sample(topic_pools[category], random.randint(1, 2))
            self.favorite_topics.extend(topics)
    
    def _set_catchphrases(self):
        """口癖設定"""
        if self.special.personality_type == PersonalityType.TROLL:
            self.catchphrases = ["はぁ？", "それは違うでしょ", "何それ", "意味わからん"]
        elif self.generation == Generation.GENERATION_1950s:
            self.catchphrases = ["そうですね", "なるほど", "おっしゃる通り", "確かに"]
        elif self.generation == Generation.GENERATION_2010s:
            self.catchphrases = ["やばい", "まじで", "すごい", "えー", "うける"]
        else:
            self.catchphrases = ["そうですね", "なるほど", "確かに", "面白いですね"]
    
    def _normalize_personality_values(self):
        """性格値の正規化"""
        for field_name in PersonalityTraits.__dataclass_fields__:
            value = getattr(self.personality, field_name)
            setattr(self.personality, field_name, max(0.0, min(1.0, value)))
    
    def update_activity(self, post_content: str):
        """活動更新"""
        self.post_count += 1
        self.last_post_time = datetime.datetime.now()
        
        # 感情の更新
        if any(positive in post_content for positive in ["良い", "嬉しい", "楽しい", "最高"]):
            self.emotions.update_emotion("happiness", 0.1)
        if any(negative in post_content for negative in ["悪い", "嫌", "最悪", "ムカつく"]):
            self.emotions.update_emotion("anger", 0.1)
        
        # 学習データに記録
        self.memory.interaction_history.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "content": post_content,
            "emotion_state": asdict(self.emotions)
        })
        
        # メモリ制限
        if len(self.memory.interaction_history) > 100:
            self.memory.interaction_history = self.memory.interaction_history[-100:]
    
    def generate_response_context(self) -> str:
        """応答生成用コンテキスト作成"""
        context_parts = [
            f"あなたは{self.name}です。",
            f"基本情報: {self.background}",
            f"MBTI: {self.mbti}",
            f"現在の感情: {self.emotions.get_emotion_description()}",
            f"趣味: {', '.join(self.hobbies)}",
        ]
        
        if self.special.personality_type != PersonalityType.NORMAL:
            context_parts.append(f"特徴: {self.special.personality_type.value}的な性格")
        
        if self.special.obsessions:
            context_parts.append(f"こだわり: {', '.join(self.special.obsessions)}")
        
        # タイピング特性
        typing_info = f"文体: {self.typing.sentence_style}"
        if self.typing.emoji_usage > 0.5:
            typing_info += "、絵文字をよく使う"
        context_parts.append(typing_info)
        
        return "\n".join(context_parts)
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            "name": self.name,
            "age": self.age,
            "gender": self.gender.value,
            "generation": self.generation.value,
            "mbti": self.mbti,
            "personality": asdict(self.personality),
            "emotions": asdict(self.emotions),
            "typing": asdict(self.typing),
            "family": asdict(self.family),
            "work": asdict(self.work),
            "special": asdict(self.special),
            "memory": asdict(self.memory),
            "post_count": self.post_count,
            "activity_level": self.activity_level,
            "background": self.background,
            "hobbies": self.hobbies,
            "favorite_topics": self.favorite_topics,
            "catchphrases": self.catchphrases,
            "is_active": self.is_active
        }

# ==============================
# ペルソナマネージャークラス
# ==============================

class PersonaManager:
    """ペルソナ管理クラス - 完全版"""
    
    def __init__(self, db_manager, ai_manager):
        self.db_manager = db_manager
        self.ai_manager = ai_manager
        self.personas: Dict[str, Persona] = {}
        
        # 名前データベース
        self.name_database = self._load_name_database()
        
        # ペルソナ生成
        self.generate_all_personas()
        
        # データベースに保存
        self.save_all_personas()
        
        logger.info(f"[PERSONA] {len(self.personas)}体のペルソナを生成しました")
    
    def _load_name_database(self) -> Dict[str, List[str]]:
        """名前データベース読み込み"""
        return {
            "male_1950s": [
                "太郎", "次郎", "三郎", "正雄", "和夫", "昭夫", "茂", "修", "清", "博",
                "勝", "進", "実", "稔", "豊", "誠", "明", "光雄", "英雄", "忠雄"
            ],
            "female_1950s": [
                "花子", "美代子", "和子", "洋子", "節子", "幸子", "千代子", "春子", "雪子", "静子",
                "光子", "信子", "久子", "恵子", "良子", "百合子", "道子", "文子", "智子", "君子"
            ],
            "male_1970s": [
                "健一", "直樹", "雅史", "浩", "学", "隆", "哲也", "亮", "徹", "聡",
                "智", "拓也", "克彦", "善行", "義明", "晃", "淳", "誠二", "正志", "宏"
            ],
            "female_1970s": [
                "恵美", "由美", "真理", "純子", "美奈子", "典子", "久美子", "智子", "順子", "裕子",
                "陽子", "直子", "康子", "佳子", "美穂", "亜紀", "真由美", "敦子", "里美", "法子"
            ],
            "male_1990s": [
                "大輔", "健太", "翔", "拓海", "亮太", "駿", "航", "颯太", "陸", "蓮",
                "大和", "悠人", "優斗", "雄大", "佑介", "直人", "雅人", "智也", "祐介", "昌也"
            ],
            "female_1990s": [
                "美咲", "愛", "彩", "優", "美穂", "絵美", "沙織", "麻衣", "瞳", "舞",
                "真美", "恵理", "梓", "香織", "奈美", "由香", "亜美", "千春", "理恵", "加奈"
            ],
            "male_2010s": [
                "蓮", "陽翔", "樹", "大翔", "颯", "朝陽", "悠人", "湊", "健太郎", "翔太",
                "陽太", "優斗", "伊織", "瑛太", "陸斗", "航", "悠斗", "廉", "心", "奏"
            ],
            "female_2010s": [
                "陽菜", "凛", "結愛", "美咲", "莉子", "心春", "愛梨", "優奈", "美羽", "咲良",
                "愛莉", "美桜", "結菜", "柚希", "彩花", "琴音", "詩織", "千尋", "美月", "花音"
            ]
        }
    
    def generate_all_personas(self):
        """全ペルソナ生成"""
        logger.info("[PERSONA] ペルソナ生成開始")
        
        # 各世代25名ずつ生成
        generation_configs = [
            (Generation.GENERATION_1950s, "1950s", 25, (60, 75)),
            (Generation.GENERATION_1970s, "1970s", 25, (40, 59)),
            (Generation.GENERATION_1990s, "1990s", 25, (20, 39)),
            (Generation.GENERATION_2010s, "2010s", 25, (10, 19))
        ]
        
        for generation, gen_key, count, age_range in generation_configs:
            logger.info(f"[PERSONA] {generation.value}のペルソナ生成中...")
            self._generate_generation_personas(generation, gen_key, count, age_range)
        
        logger.info(f"[PERSONA] 総ペルソナ数: {len(self.personas)}体")
    
    def _generate_generation_personas(self, generation: Generation, gen_key: str, count: int, age_range: Tuple[int, int]):
        """世代別ペルソナ生成"""
        for i in range(count):
            # 性別決定（男女比をある程度調整）
            gender = Gender.MALE if i % 2 == 0 else Gender.FEMALE
            
            # 年齢決定
            age = random.randint(age_range[0], age_range[1])
            
            # 名前決定
            name_key = f"{'male' if gender == Gender.MALE else 'female'}_{gen_key}"
            available_names = self.name_database.get(name_key, [f"ペルソナ{i}"])
            name = random.choice(available_names)
            
            # 既存チェック
            if name in self.personas:
                name = f"{name}{i}"
            
            # ペルソナ生成
            persona = Persona(name, age, gender, generation)
            self.personas[name] = persona
            
            logger.debug(f"[PERSONA] 生成: {name} ({age}歳, {gender.value}, {generation.value})")
    
    def get_persona_stats(self) -> Dict:
        """ペルソナ統計取得"""
        stats = {
            "total_personas": len(self.personas),
            "active_personas": sum(1 for p in self.personas.values() if p.is_active),
            "troll_personas": sum(1 for p in self.personas.values() 
                                if p.special.personality_type == PersonalityType.TROLL),
            "total_posts": sum(p.post_count for p in self.personas.values()),
            "average_activity": sum(p.activity_level for p in self.personas.values()) / len(self.personas),
            "generation_stats": {}
        }
        
        # 世代別統計
        for generation in Generation:
            gen_personas = [p for p in self.personas.values() if p.generation == generation]
            if gen_personas:
                stats["generation_stats"][generation.value] = {
                    "count": len(gen_personas),
                    "total_posts": sum(p.post_count for p in gen_personas),
                    "average_activity": sum(p.activity_level for p in gen_personas) / len(gen_personas)
                }
        
        return stats
    
    def select_posting_persona(self, thread_id: int) -> Optional[Persona]:
        """投稿ペルソナ選択"""
        try:
            # アクティブなペルソナをフィルタ
            active_personas = [p for p in self.personas.values() if p.is_active]
            
            if not active_personas:
                return None
            
            # 活動レベルに基づく重み付き選択
            weights = [p.activity_level for p in active_personas]
            selected_persona = random.choices(active_personas, weights=weights)[0]
            
            return selected_persona
            
        except Exception as e:
            logger.error(f"[PERSONA] ペルソナ選択エラー: {e}")
            return None
    
    def generate_auto_post(self, thread_id: int) -> bool:
        """自動投稿生成"""
        try:
            # ペルソナ選択
            persona = self.select_posting_persona(thread_id)
            if not persona:
                logger.warning(f"[PERSONA] 投稿ペルソナが選択できませんでした")
                return False
            
            # スレッド情報取得
            thread_info = self._get_thread_info(thread_id)
            if not thread_info:
                logger.warning(f"[PERSONA] スレッド情報取得失敗: {thread_id}")
                return False
            
            # 投稿内容生成
            post_content = self._generate_post_content(persona, thread_info)
            if not post_content:
                logger.warning(f"[PERSONA] 投稿内容生成失敗: {persona.name}")
                return False
            
            # 投稿実行
            success = self._execute_post(thread_id, persona, post_content)
            
            if success:
                # ペルソナ活動更新
                persona.update_activity(post_content)
                logger.info(f"[PERSONA] 自動投稿成功: {persona.name} -> Thread {thread_id}")
                return True
            else:
                logger.warning(f"[PERSONA] 投稿実行失敗: {persona.name}")
                return False
                
        except Exception as e:
            logger.error(f"[PERSONA] 自動投稿エラー: {e}")
            return False
    
    def _get_thread_info(self, thread_id: int) -> Optional[Dict]:
        """スレッド情報取得"""
        try:
            # データベースからスレッド情報を取得
            thread_data = self.db_manager.execute_query(
                """SELECT t.title, t.description, m.category_name, s.sub_category_name
                   FROM threads t
                   JOIN main_categories m ON t.main_category_id = m.category_id
                   JOIN sub_categories s ON t.sub_category_id = s.sub_category_id
                   WHERE t.thread_id = ?""",
                (thread_id,)
            )
            
            if not thread_data:
                return None
            
            title, description, main_category, sub_category = thread_data[0]
            
            # 最近の投稿を取得
            recent_posts = self.db_manager.execute_query(
                """SELECT persona_name, content, posted_at
                   FROM posts 
                   WHERE thread_id = ? AND is_deleted = 0
                   ORDER BY posted_at DESC LIMIT 5""",
                (thread_id,)
            )
            
            return {
                "thread_id": thread_id,
                "title": title,
                "description": description,
                "main_category": main_category,
                "sub_category": sub_category,
                "recent_posts": recent_posts
            }
            
        except Exception as e:
            logger.error(f"[PERSONA] スレッド情報取得エラー: {e}")
            return None
    
    def _generate_post_content(self, persona: Persona, thread_info: Dict) -> Optional[str]:
        """投稿内容生成"""
        try:
            # ペルソナコンテキスト構築
            persona_context = persona.generate_response_context()
            
            # プロンプト構築
            prompt = self._build_post_prompt(persona, thread_info)
            
            # AI応答生成
            response = self.ai_manager.generate_response(prompt, persona_context)
            
            if response:
                # ペルソナ特性に基づく後処理
                processed_response = self._post_process_content(response, persona)
                return processed_response
            
            return None
            
        except Exception as e:
            logger.error(f"[PERSONA] 投稿内容生成エラー: {e}")
            return None
    
    def _build_post_prompt(self, persona: Persona, thread_info: Dict) -> str:
        """投稿プロンプト構築"""
        prompt_parts = [
            f"スレッド「{thread_info['title']}」に投稿してください。",
            f"カテゴリ: {thread_info['main_category']} > {thread_info['sub_category']}",
        ]
        
        if thread_info['description']:
            prompt_parts.append(f"スレッドの説明: {thread_info['description']}")
        
        # 最近の投稿があれば文脈として追加
        if thread_info['recent_posts']:
            prompt_parts.append("\n最近の投稿:")
            for i, (name, content, _) in enumerate(thread_info['recent_posts'][:3]):
                prompt_parts.append(f"{name}: {content[:100]}...")
        
        prompt_parts.extend([
            f"\nあなた（{persona.name}）らしい投稿をしてください。",
            "投稿内容は自然で、スレッドの話題に関連している必要があります。",
            "150文字以内で簡潔にまとめてください。"
        ])
        
        # 特殊属性による調整
        if persona.special.personality_type == PersonalityType.TROLL:
            prompt_parts.append("少し挑発的で議論を呼びそうな内容にしてください。")
        elif persona.special.personality_type == PersonalityType.WEIRD:
            prompt_parts.append("独特な視点や変わった意見を含めてください。")
        elif persona.special.obsessions:
            obsession = random.choice(persona.special.obsessions)
            prompt_parts.append(f"できれば{obsession}に関連付けて投稿してください。")
        
        return "\n".join(prompt_parts)
    
    def _post_process_content(self, content: str, persona: Persona) -> str:
        """投稿内容の後処理"""
        processed = content
        
        # 口癖の追加
        if persona.catchphrases and random.random() < 0.3:
            catchphrase = random.choice(persona.catchphrases)
            if random.random() < 0.5:
                processed = f"{catchphrase}、{processed}"
            else:
                processed = f"{processed}{catchphrase}。"
        
        # 絵文字の追加
        if persona.typing.emoji_usage > random.random():
            emojis = ["😊", "😄", "🤔", "😅", "👍", "✨", "💦", "😰", "😤", "🎵"]
            if persona.generation == Generation.GENERATION_2010s:
                emojis.extend(["✨", "💕", "🎉", "👏", "😍", "🔥"])
            
            if random.random() < 0.7:
                processed += random.choice(emojis)
        
        # タイピングエラーの追加
        if persona.typing.accuracy < random.random():
            processed = self._add_typing_errors(processed)
        
        # 特殊属性による調整
        if persona.special.personality_type == PersonalityType.TROLL:
            # より攻撃的な表現に調整
            processed = processed.replace("思います", "思うんですけど")
            processed = processed.replace("です", "っす")
        
        return processed
    
    def _add_typing_errors(self, content: str) -> str:
        """タイピングエラー追加"""
        # 簡単な誤字パターン
        error_patterns = [
            ("です", "でず"),
            ("ます", "まず"),
            ("こと", "こと"),
            ("して", "shて"),
            ("でしょう", "でしょお"),
        ]
        
        for original, error in error_patterns:
            if original in content and random.random() < 0.1:
                content = content.replace(original, error, 1)
                break
        
        return content
    
    def _execute_post(self, thread_id: int, persona: Persona, content: str) -> bool:
        """投稿実行"""
        try:
            # データベースに投稿を追加
            post_id = self.db_manager.execute_insert(
                """INSERT INTO posts (thread_id, persona_name, content, is_user_post)
                   VALUES (?, ?, ?, ?)""",
                (thread_id, persona.name, content, False)
            )
            
            if post_id > 0:
                # スレッドの統計更新
                self.db_manager.execute_insert(
                    """UPDATE threads SET
                       post_count = (SELECT COUNT(*) FROM posts WHERE thread_id = ? AND is_deleted=0),
                       last_post_time = CURRENT_TIMESTAMP,
                       last_ai_post_time = CURRENT_TIMESTAMP,
                       updated_at = CURRENT_TIMESTAMP
                       WHERE thread_id = ?""",
                    (thread_id, thread_id)
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"[PERSONA] 投稿実行エラー: {e}")
            return False
    
    def record_user_interaction(self, thread_id: int, content: str):
        """ユーザー交流記録"""
        try:
            # メンション検出
            mentions = re.findall(r'@([^\s]+)', content)
            
            for mention in mentions:
                if mention in self.personas:
                    persona = self.personas[mention]
                    # 学習データに記録
                    persona.memory.interaction_history.append({
                        "timestamp": datetime.datetime.now().isoformat(),
                        "type": "user_mention",
                        "content": content,
                        "thread_id": thread_id
                    })
                    
                    # 感情更新（ポジティブな呼びかけと仮定）
                    persona.emotions.update_emotion("happiness", 0.05)
                    
        except Exception as e:
            logger.error(f"[PERSONA] ユーザー交流記録エラー: {e}")
    
    def save_all_personas(self):
        """全ペルソナ保存"""
        try:
            for persona in self.personas.values():
                self._save_persona_to_db(persona)
            logger.info(f"[PERSONA] {len(self.personas)}体のペルソナを保存しました")
            
        except Exception as e:
            logger.error(f"[PERSONA] ペルソナ保存エラー: {e}")
    
    def _save_persona_to_db(self, persona: Persona):
        """個別ペルソナのDB保存"""
        try:
            # 既存チェック
            existing = self.db_manager.execute_query(
                "SELECT persona_id FROM personas WHERE name = ?",
                (persona.name,)
            )
            
            persona_data = (
                persona.name,
                persona.age,
                persona.work.occupation,
                persona.background,
                persona.generation.value,
                persona.mbti,
                persona.personality.extroversion,
                persona.personality.agreeableness,
                persona.personality.conscientiousness,
                persona.personality.neuroticism,
                persona.personality.openness,
                json.dumps(persona.to_dict(), ensure_ascii=False),
                json.dumps(asdict(persona.emotions), ensure_ascii=False),
                json.dumps(asdict(persona.memory), ensure_ascii=False),
                persona.activity_level,
                persona.post_count,
                persona.special.personality_type == PersonalityType.TROLL,
                persona.is_active
            )
            
            if existing:
                # 更新
                self.db_manager.execute_insert(
                    """UPDATE personas SET
                       age=?, occupation=?, background=?, generation=?, mbti=?,
                       extroversion=?, agreeableness=?, conscientiousness=?, neuroticism=?, openness=?,
                       additional_params=?, emotion_state=?, learning_data=?,
                       activity_level=?, post_count=?, is_troll=?, is_active=?
                       WHERE name=?""",
                    persona_data[1:] + (persona.name,)
                )
            else:
                # 新規挿入
                self.db_manager.execute_insert(
                    """INSERT INTO personas 
                       (name, age, occupation, background, generation, mbti,
                        extroversion, agreeableness, conscientiousness, neuroticism, openness,
                        additional_params, emotion_state, learning_data,
                        activity_level, post_count, is_troll, is_active)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    persona_data
                )
                
        except Exception as e:
            logger.error(f"[PERSONA] ペルソナDB保存エラー ({persona.name}): {e}")
    
    def load_personas_from_db(self):
        """データベースからペルソナ読み込み"""
        try:
            personas_data = self.db_manager.execute_query(
                """SELECT name, age, occupation, background, generation, mbti,
                          extroversion, agreeableness, conscientiousness, neuroticism, openness,
                          additional_params, emotion_state, learning_data,
                          activity_level, post_count, is_troll, is_active
                   FROM personas WHERE is_active = 1"""
            )
            
            loaded_count = 0
            for data in personas_data:
                try:
                    # 基本情報から復元
                    name, age, occupation, background, generation_str, mbti = data[:6]
                    
                    # 列挙型変換
                    generation = Generation(generation_str)
                    
                    # ペルソナオブジェクト作成（簡略版）
                    # 実際のプロダクションでは、より詳細な復元処理が必要
                    gender = Gender.MALE  # デフォルト値（実際は保存が必要）
                    persona = Persona(name, age, gender, generation)
                    
                    # 保存されたデータで上書き
                    persona.mbti = mbti
                    persona.work.occupation = occupation
                    persona.background = background
                    
                    # 性格データ復元
                    personality_data = data[6:11]
                    persona.personality.extroversion = personality_data[0]
                    persona.personality.agreeableness = personality_data[1]
                    persona.personality.conscientiousness = personality_data[2]
                    persona.personality.neuroticism = personality_data[3]
                    persona.personality.openness = personality_data[4]
                    
                    # JSONデータ復元
                    if data[11]:  # additional_params
                        additional_data = json.loads(data[11])
                        # 必要に応じて復元処理
                    
                    if data[12]:  # emotion_state
                        emotion_data = json.loads(data[12])
                        for key, value in emotion_data.items():
                            if hasattr(persona.emotions, key):
                                setattr(persona.emotions, key, value)
                    
                    if data[13]:  # learning_data
                        learning_data = json.loads(data[13])
                        for key, value in learning_data.items():
                            if hasattr(persona.memory, key):
                                setattr(persona.memory, key, value)
                    
                    # 統計データ
                    persona.activity_level = data[14]
                    persona.post_count = data[15]
                    
                    if data[16]:  # is_troll
                        persona.special.personality_type = PersonalityType.TROLL
                    
                    persona.is_active = bool(data[17])
                    
                    self.personas[name] = persona
                    loaded_count += 1
                    
                except Exception as e:
                    logger.error(f"[PERSONA] 個別ペルソナ読み込みエラー ({data[0]}): {e}")
                    continue
            
            logger.info(f"[PERSONA] データベースから{loaded_count}体のペルソナを読み込みました")
            
            # 不足分があれば新規生成
            if len(self.personas) < 100:
                missing_count = 100 - len(self.personas)
                logger.info(f"[PERSONA] {missing_count}体のペルソナを新規生成します")
                # 不足分の生成処理
                
        except Exception as e:
            logger.error(f"[PERSONA] ペルソナ読み込みエラー: {e}")
            # エラー時は新規生成
            self.generate_all_personas()
    
    def update_all_personas(self):
        """全ペルソナ状態更新"""
        try:
            current_time = datetime.datetime.now()
            
            for persona in self.personas.values():
                # 感情の自然減衰
                if persona.emotions.anger > 0.1:
                    persona.emotions.update_emotion("anger", -0.01)
                if persona.emotions.sadness > 0.1:
                    persona.emotions.update_emotion("sadness", -0.01)
                
                # 活動レベルの調整
                if persona.last_post_time:
                    hours_since_last_post = (current_time - persona.last_post_time).total_seconds() / 3600
                    if hours_since_last_post > 24:
                        persona.activity_level = max(0.1, persona.activity_level - 0.01)
                
        except Exception as e:
            logger.error(f"[PERSONA] ペルソナ状態更新エラー: {e}")

# ==============================
# エクスポート用関数
# ==============================

def create_test_persona() -> Persona:
    """テスト用ペルソナ作成"""
    return Persona(
        name="テスト太郎",
        age=25,
        gender=Gender.MALE,
        generation=Generation.GENERATION_1990s
    )

if __name__ == "__main__":
    # テスト実行
    print("ペルソナモジュールテスト開始")
    
    test_persona = create_test_persona()
    print(f"テストペルソナ: {test_persona.name}")
    print(f"背景: {test_persona.background}")
    print(f"性格: {test_persona.personality.get_personality_description()}")
    print(f"感情: {test_persona.emotions.get_emotion_description()}")
    print(f"MBTI: {test_persona.mbti}")
    
    print("ペルソナモジュールテスト完了")
