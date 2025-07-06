#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PC-98時代パソコン通信BBS風アプリケーション - ペルソナ管理モジュール
AIペルソナの性格システム、感情システム、学習機能を管理
"""

import json
import random
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)

@dataclass
class PersonalityTraits:
    """ビッグファイブ + 拡張性格特性"""
    # ビッグファイブ
    extroversion: float = 0.5      # 外向性
    agreeableness: float = 0.5     # 協調性  
    conscientiousness: float = 0.5 # 誠実性
    neuroticism: float = 0.5       # 神経症傾向
    openness: float = 0.5          # 開放性
    
    # 拡張性格パラメータ（14種）
    creativity: float = 0.5        # 創造性
    curiosity: float = 0.5         # 好奇心
    competitiveness: float = 0.5   # 競争心
    empathy: float = 0.5           # 共感性
    patience: float = 0.5          # 忍耐力
    humor: float = 0.5             # ユーモア
    skepticism: float = 0.5        # 懐疑心
    optimism: float = 0.5          # 楽観性
    independence: float = 0.5      # 独立性
    leadership: float = 0.5        # リーダーシップ
    adaptability: float = 0.5      # 適応性
    risk_taking: float = 0.5       # リスク志向
    perfectionism: float = 0.5     # 完璧主義
    sociability: float = 0.5       # 社交性

@dataclass
class EmotionalState:
    """感情状態（10種）"""
    happiness: float = 0.5         # 幸福
    sadness: float = 0.0           # 悲しみ
    anger: float = 0.0             # 怒り
    fear: float = 0.0              # 恐怖
    surprise: float = 0.0          # 驚き
    excitement: float = 0.3        # 興奮
    calmness: float = 0.7          # 平静
    curiosity_emotion: float = 0.4 # 好奇心（感情）
    confidence: float = 0.5        # 自信
    frustration: float = 0.0       # イライラ

class LearningMemory:
    """学習記憶システム"""
    
    def __init__(self):
        self.memories: List[Dict] = []
        self.topic_preferences: Dict[str, float] = {}
        self.response_patterns: Dict[str, List[str]] = {}
        self.interaction_history: List[Dict] = []
        self.learning_weights: Dict[str, float] = {}
    
    def add_memory(self, context: str, response: str, feedback_score: float = 0.5):
        """記憶追加"""
        memory = {
            'context': context,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'feedback_score': feedback_score,
            'usage_count': 0
        }
        self.memories.append(memory)
        
        # 古い記憶を削除（最大1000件）
        if len(self.memories) > 1000:
            self.memories = self.memories[-1000:]
    
    def get_relevant_memories(self, context: str, limit: int = 5) -> List[Dict]:
        """関連記憶取得"""
        relevant = []
        context_words = set(context.lower().split())
        
        for memory in self.memories:
            memory_words = set(memory['context'].lower().split())
            similarity = len(context_words & memory_words) / max(len(context_words), 1)
            
            if similarity > 0.2:  # 20%以上の単語一致
                memory['similarity'] = similarity
                relevant.append(memory)
        
        # 類似度と使用回数でソート
        relevant.sort(key=lambda x: (x['similarity'], x['usage_count']), reverse=True)
        return relevant[:limit]
    
    def update_topic_preference(self, topic: str, sentiment: float):
        """トピック嗜好更新"""
        if topic not in self.topic_preferences:
            self.topic_preferences[topic] = 0.5
        
        # 現在の嗜好と新しい感情を組み合わせ
        current = self.topic_preferences[topic]
        self.topic_preferences[topic] = (current * 0.8) + (sentiment * 0.2)
        
        # 0-1の範囲に制限
        self.topic_preferences[topic] = max(0.0, min(1.0, self.topic_preferences[topic]))

class Persona:
    """AIペルソナクラス"""
    
    def __init__(self, name: str, age: int, occupation: str, background: str, is_troll: bool = False):
        self.name = name
        self.age = age
        self.occupation = occupation
        self.background = background
        self.is_troll = is_troll
        self.is_active = True
        
        # 性格特性初期化
        self.personality = self._generate_personality()
        
        # 感情状態初期化
        self.emotions = EmotionalState()
        if is_troll:
            self.emotions.anger = random.uniform(0.3, 0.7)
            self.emotions.frustration = random.uniform(0.4, 0.8)
        
        # 学習記憶初期化
        self.memory = LearningMemory()
        
        # 活動統計
        self.post_count = 0
        self.last_post_time = None
        self.activity_level = random.uniform(0.3, 0.9)
        
        logger.info(f"[PERSONA] 作成完了: {name} ({'荒らし' if is_troll else '通常'})")
    
    def _generate_personality(self) -> PersonalityTraits:
        """性格特性生成"""
        traits = PersonalityTraits()
        
        if self.is_troll:
            # 荒らしキャラクターの性格調整
            traits.agreeableness = random.uniform(0.1, 0.3)
            traits.neuroticism = random.uniform(0.6, 0.9)
            traits.competitiveness = random.uniform(0.7, 1.0)
            traits.skepticism = random.uniform(0.6, 0.9)
            traits.risk_taking = random.uniform(0.7, 1.0)
        else:
            # 通常キャラクターはランダム生成
            for field in traits.__dataclass_fields__:
                # 年齢や職業による調整
                base_value = random.uniform(0.2, 0.8)
                
                # 年齢調整
                if self.age < 25:
                    if field in ['openness', 'curiosity', 'risk_taking']:
                        base_value += 0.2
                elif self.age > 50:
                    if field in ['conscientiousness', 'patience']:
                        base_value += 0.2
                
                # 職業調整
                if 'エンジニア' in self.occupation or 'プログラマ' in self.occupation:
                    if field in ['conscientiousness', 'perfectionism']:
                        base_value += 0.2
                elif '営業' in self.occupation or '接客' in self.occupation:
                    if field in ['extroversion', 'sociability']:
                        base_value += 0.2
                
                setattr(traits, field, max(0.0, min(1.0, base_value)))
        
        return traits
    
    def update_emotions(self, stimulus: str, context: str = ""):
        """感情状態更新"""
        # 刺激の分析
        positive_words = ['嬉しい', '楽しい', '面白い', '素晴らしい', '良い', 'いい']
        negative_words = ['悲しい', '辛い', '嫌', 'むかつく', '最悪', 'ダメ']
        surprising_words = ['驚き', 'びっくり', '意外', '予想外']
        
        # 感情変化量計算
        emotion_change = 0.1
        if self.personality.neuroticism > 0.7:
            emotion_change *= 1.5  # 神経質な人は感情変動が大きい
        
        # ポジティブ刺激
        for word in positive_words:
            if word in stimulus:
                self.emotions.happiness = min(1.0, self.emotions.happiness + emotion_change)
                self.emotions.sadness = max(0.0, self.emotions.sadness - emotion_change * 0.5)
                break
        
        # ネガティブ刺激
        for word in negative_words:
            if word in stimulus:
                if self.is_troll:
                    self.emotions.anger = min(1.0, self.emotions.anger + emotion_change * 1.5)
                    self.emotions.frustration = min(1.0, self.emotions.frustration + emotion_change)
                else:
                    self.emotions.sadness = min(1.0, self.emotions.sadness + emotion_change)
                    self.emotions.happiness = max(0.0, self.emotions.happiness - emotion_change * 0.5)
                break
        
        # 驚き刺激
        for word in surprising_words:
            if word in stimulus:
                self.emotions.surprise = min(1.0, self.emotions.surprise + emotion_change * 2)
                self.emotions.curiosity_emotion = min(1.0, self.emotions.curiosity_emotion + emotion_change)
                break
        
        # 感情の自然減衰
        self._decay_emotions()
    
    def _decay_emotions(self):
        """感情の自然減衰"""
        decay_rate = 0.05
        
        self.emotions.anger = max(0.0, self.emotions.anger - decay_rate)
        self.emotions.sadness = max(0.0, self.emotions.sadness - decay_rate)
        self.emotions.fear = max(0.0, self.emotions.fear - decay_rate)
        self.emotions.surprise = max(0.0, self.emotions.surprise - decay_rate)
        self.emotions.frustration = max(0.0, self.emotions.frustration - decay_rate)
        
        # ポジティブ感情は基本レベルに戻る
        self.emotions.happiness = self.emotions.happiness * 0.95 + 0.5 * 0.05
        self.emotions.calmness = self.emotions.calmness * 0.95 + 0.7 * 0.05
        self.emotions.confidence = self.emotions.confidence * 0.95 + 0.5 * 0.05
    
    def generate_response_context(self, thread_context: str, recent_posts: List[str]) -> str:
        """応答コンテキスト生成"""
        # 基本的な性格設定
        personality_desc = f"""
あなたは{self.name}、{self.age}歳の{self.occupation}です。
背景: {self.background}

性格特性:
- 外向性: {self.personality.extroversion:.1f} ({'外向的' if self.personality.extroversion > 0.5 else '内向的'})
- 協調性: {self.personality.agreeableness:.1f} ({'協調的' if self.personality.agreeableness > 0.5 else '独立的'})
- 誠実性: {self.personality.conscientiousness:.1f} ({'真面目' if self.personality.conscientiousness > 0.5 else '自由'})
- 感情安定性: {1.0 - self.personality.neuroticism:.1f} ({'安定' if self.personality.neuroticism < 0.5 else '敏感'})
- 開放性: {self.personality.openness:.1f} ({'新しいもの好き' if self.personality.openness > 0.5 else '保守的'})

現在の感情:
- 幸福度: {self.emotions.happiness:.1f}
- 怒り: {self.emotions.anger:.1f}
- 興奮: {self.emotions.excitement:.1f}
- 平静: {self.emotions.calmness:.1f}
"""
        
        # 荒らしキャラクターの特別設定
        if self.is_troll:
            personality_desc += """
注意: あなたは時々挑発的で議論好きな性格です。適度に批判的または皮肉な発言をしますが、極端に攻撃的にはならないでください。
"""
        
        # 最近の投稿を考慮
        if recent_posts:
            recent_context = "最近の投稿:\n" + "\n".join(recent_posts[-3:])
            personality_desc += f"\n{recent_context}\n"
        
        # 学習記憶からの関連情報
        relevant_memories = self.memory.get_relevant_memories(thread_context, 2)
        if relevant_memories:
            memory_context = "関連する過去の記憶:\n"
            for memory in relevant_memories:
                memory_context += f"- {memory['context']}: {memory['response']}\n"
            personality_desc += f"\n{memory_context}"
        
        personality_desc += f"""
指示:
1. {self.name}として、上記の性格と現在の感情状態に基づいて自然に応答してください
2. 日本語で2-3文程度の短い投稿をしてください
3. BBSの雰囲気に合わせて、親しみやすい口調で書いてください
4. 同じような内容の繰り返しは避けてください
5. トピック: {thread_context}
"""
        
        return personality_desc
    
    def learn_from_interaction(self, context: str, response: str, feedback: float = 0.5):
        """インタラクションから学習"""
        # 記憶に追加
        self.memory.add_memory(context, response, feedback)
        
        # トピック嗜好更新
        topic_keywords = context.lower().split()
        for keyword in topic_keywords:
            if len(keyword) > 2:  # 2文字以上のキーワード
                sentiment = feedback
                self.memory.update_topic_preference(keyword, sentiment)
        
        # 性格の微調整（長期的な学習効果）
        if len(self.memory.memories) > 50:
            self._adjust_personality_from_learning()
    
    def _adjust_personality_from_learning(self):
        """学習から性格微調整"""
        recent_memories = self.memory.memories[-20:]  # 最近の20件
        
        positive_interactions = sum(1 for m in recent_memories if m['feedback_score'] > 0.6)
        negative_interactions = sum(1 for m in recent_memories if m['feedback_score'] < 0.4)
        
        adjustment = 0.01  # 小さな調整値
        
        if positive_interactions > negative_interactions:
            # ポジティブな経験が多い場合
            self.personality.agreeableness = min(1.0, self.personality.agreeableness + adjustment)
            self.personality.extroversion = min(1.0, self.personality.extroversion + adjustment * 0.5)
        elif negative_interactions > positive_interactions:
            # ネガティブな経験が多い場合
            self.personality.neuroticism = min(1.0, self.personality.neuroticism + adjustment)
            self.personality.skepticism = min(1.0, self.personality.skepticism + adjustment * 0.5)
    
    def should_post_now(self, thread_activity: int, time_since_last_post: int) -> bool:
        """投稿判定"""
        # 基本的な活動レベル
        base_probability = self.activity_level
        
        # 性格による調整
        if self.personality.extroversion > 0.7:
            base_probability *= 1.3
        elif self.personality.extroversion < 0.3:
            base_probability *= 0.7
        
        # スレッド活動度による調整
        if thread_activity > 10:  # 活発なスレッド
            base_probability *= 1.2
        elif thread_activity < 3:  # 静かなスレッド
            base_probability *= 0.8
        
        # 最後の投稿からの時間による調整
        if time_since_last_post > 300:  # 5分以上
            base_probability *= 1.1
        elif time_since_last_post < 60:  # 1分未満
            base_probability *= 0.5
        
        # 感情状態による調整
        if self.emotions.excitement > 0.7:
            base_probability *= 1.4
        elif self.emotions.anger > 0.5 and self.is_troll:
            base_probability *= 1.5
        elif self.emotions.sadness > 0.6:
            base_probability *= 0.6
        
        return random.random() < base_probability
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            'name': self.name,
            'age': self.age,
            'occupation': self.occupation,
            'background': self.background,
            'is_troll': self.is_troll,
            'personality': asdict(self.personality),
            'emotions': asdict(self.emotions),
            'memory': {
                'memories': self.memory.memories[-50:],  # 最新50件のみ
                'topic_preferences': self.memory.topic_preferences,
                'response_patterns': self.memory.response_patterns
            },
            'stats': {
                'post_count': self.post_count,
                'last_post_time': self.last_post_time.isoformat() if self.last_post_time else None,
                'activity_level': self.activity_level
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Persona':
        """辞書から復元"""
        persona = cls(
            data['name'],
            data['age'], 
            data['occupation'],
            data['background'],
            data['is_troll']
        )
        
        # 性格特性復元
        for key, value in data['personality'].items():
            setattr(persona.personality, key, value)
        
        # 感情状態復元
        for key, value in data['emotions'].items():
            setattr(persona.emotions, key, value)
        
        # 記憶復元
        if 'memory' in data:
            persona.memory.memories = data['memory'].get('memories', [])
            persona.memory.topic_preferences = data['memory'].get('topic_preferences', {})
            persona.memory.response_patterns = data['memory'].get('response_patterns', {})
        
        # 統計復元
        if 'stats' in data:
            persona.post_count = data['stats'].get('post_count', 0)
            persona.activity_level = data['stats'].get('activity_level', 0.5)
            if data['stats'].get('last_post_time'):
                persona.last_post_time = datetime.fromisoformat(data['stats']['last_post_time'])
        
        return persona

class PersonaManager:
    """ペルソナ管理クラス"""
    
    def __init__(self, db_manager, g4f_manager):
        self.db_manager = db_manager
        self.g4f_manager = g4f_manager
        self.personas: Dict[str, Persona] = {}
        
        self.persona_templates = self._create_persona_templates()
        self.initialize_personas()
        
        logger.info(f"[PERSONA_MGR] 初期化完了: {len(self.personas)}体のペルソナ")
    
    def _create_persona_templates(self) -> List[Dict]:
        """ペルソナテンプレート作成"""
        templates = [
            # 通常ペルソナ
            {"name": "田中太郎", "age": 28, "occupation": "システムエンジニア", "background": "東京在住、プログラミング歴5年。ゲームとアニメが好き。"},
            {"name": "佐藤花子", "age": 24, "occupation": "デザイナー", "background": "美術大学卒、イラストと写真が趣味。猫を2匹飼っている。"},
            {"name": "鈴木一郎", "age": 35, "occupation": "営業マン", "background": "大阪出身、野球観戦が趣味。家族は妻と子供2人。"},
            {"name": "高橋美咲", "age": 31, "occupation": "看護師", "background": "医療従事者、読書と料理が好き。ボランティア活動にも参加。"},
            {"name": "伊藤健太", "age": 26, "occupation": "教師", "background": "中学校教師、歴史が専門。旅行で史跡巡りをするのが趣味。"},
            {"name": "渡辺久美", "age": 29, "occupation": "事務員", "background": "経理事務、手芸と園芸が趣味。休日は映画鑑賞を楽しむ。"},
            {"name": "山田俊介", "age": 33, "occupation": "フリーランサー", "background": "Webデザイナー、在宅ワーク。音楽制作が趣味。"},
            {"name": "中村あゆみ", "age": 27, "occupation": "販売員", "background": "アパレル店勤務、ファッションとコスメに詳しい。"},
            {"name": "小林浩二", "age": 41, "occupation": "管理職", "background": "製造業の課長、釣りとゴルフが趣味。部下の指導に熱心。"},
            {"name": "加藤理恵", "age": 23, "occupation": "学生", "background": "大学院生、心理学専攻。カフェ巡りが好き。"},
            
            # 荒らしペルソナ（2-3名）
            {"name": "匿名の批評家", "age": 30, "occupation": "フリーター", "background": "様々な仕事を転々とする。批判的で議論好き。", "is_troll": True},
            {"name": "炎上マニア", "age": 25, "occupation": "ニート", "background": "ネット掲示板の常連。挑発的な発言を好む。", "is_troll": True},
        ]
        
        # 追加ペルソナを生成（100名まで）
        additional_names = [
            "松本", "木村", "林", "清水", "森", "池田", "橋本", "山口", "石川", "前田",
            "藤田", "石井", "小川", "後藤", "岡田", "長谷川", "村上", "近藤", "石田", "上田",
            "青木", "森田", "原田", "武田", "宮田", "酒井", "工藤", "横山", "井上", "西村"
        ]
        
        occupations = [
            "プログラマー", "公務員", "研究者", "医師", "弁護士", "会計士", "建築士", "薬剤師",
            "美容師", "調理師", "運転手", "警備員", "清掃員", "配達員", "店長", "アルバイト",
            "主婦", "退職者", "芸術家", "作家", "翻訳者", "コンサルタント", "起業家"
        ]
        
        for i, surname in enumerate(additional_names):
            if len(templates) >= 100:
                break
            
            first_names = ["太郎", "次郎", "三郎", "花子", "美子", "正子", "裕子", "恵子", "健一", "雅子"]
            name = f"{surname}{random.choice(first_names)}"
            age = random.randint(18, 65)
            occupation = random.choice(occupations)
            
            backgrounds = [
                f"{random.choice(['東京', '大阪', '名古屋', '福岡', '札幌'])}在住。",
                f"{random.choice(['映画', '読書', '音楽', 'スポーツ', '旅行', '料理', 'ゲーム'])}が趣味。",
                f"{random.choice(['犬', '猫', '金魚'])}を飼っている。",
                f"{random.choice(['英語', '中国語', 'プログラミング', '資格取得'])}を勉強中。"
            ]
            background = "".join(random.sample(backgrounds, 2))
            
            templates.append({
                "name": name,
                "age": age,
                "occupation": occupation,
                "background": background,
                "is_troll": False
            })
        
        return templates
    
    def initialize_personas(self):
        """ペルソナ初期化"""
        # データベースから既存ペルソナを読み込み
        existing_personas = self.db_manager.execute_query(
            "SELECT name, age, occupation, background, extroversion, agreeableness, conscientiousness, neuroticism, openness, additional_params, emotion_state, learning_data, is_troll FROM personas"
        )
        
        if existing_personas:
            # 既存ペルソナを復元
            for persona_data in existing_personas:
                name, age, occupation, background, extroversion, agreeableness, conscientiousness, neuroticism, openness, additional_params, emotion_state, learning_data, is_troll = persona_data
                
                persona = Persona(name, age, occupation, background, bool(is_troll))
                
                # 性格特性復元
                persona.personality.extroversion = extroversion
                persona.personality.agreeableness = agreeableness
                persona.personality.conscientiousness = conscientiousness
                persona.personality.neuroticism = neuroticism
                persona.personality.openness = openness
                
                # 拡張パラメータ復元
                if additional_params:
                    try:
                        additional_data = json.loads(additional_params)
                        for key, value in additional_data.items():
                            if hasattr(persona.personality, key):
                                setattr(persona.personality, key, value)
                    except:
                        pass
                
                # 感情状態復元
                if emotion_state:
                    try:
                        emotion_data = json.loads(emotion_state)
                        for key, value in emotion_data.items():
                            if hasattr(persona.emotions, key):
                                setattr(persona.emotions, key, value)
                    except:
                        pass
                
                # 学習データ復元
                if learning_data:
                    try:
                        learning_dict = json.loads(learning_data)
                        persona.memory.memories = learning_dict.get('memories', [])
                        persona.memory.topic_preferences = learning_dict.get('topic_preferences', {})
                        persona.memory.response_patterns = learning_dict.get('response_patterns', {})
                    except:
                        pass
                
                self.personas[name] = persona
                
            logger.info(f"[PERSONA_MGR] 既存ペルソナ復元: {len(existing_personas)}体")
        else:
            # 新規ペルソナ作成
            for template in self.persona_templates:
                persona = Persona(
                    template["name"],
                    template["age"],
                    template["occupation"],
                    template["background"],
                    template.get("is_troll", False)
                )
                self.personas[template["name"]] = persona
                self.save_persona(persona)
            
            logger.info(f"[PERSONA_MGR] 新規ペルソナ作成: {len(self.personas)}体")
    
    def save_persona(self, persona: Persona):
        """ペルソナをデータベースに保存"""
        try:
            additional_params = json.dumps({
                'creativity': persona.personality.creativity,
                'curiosity': persona.personality.curiosity,
                'competitiveness': persona.personality.competitiveness,
                'empathy': persona.personality.empathy,
                'patience': persona.personality.patience,
                'humor': persona.personality.humor,
                'skepticism': persona.personality.skepticism,
                'optimism': persona.personality.optimism,
                'independence': persona.personality.independence,
                'leadership': persona.personality.leadership,
                'adaptability': persona.personality.adaptability,
                'risk_taking': persona.personality.risk_taking,
                'perfectionism': persona.personality.perfectionism,
                'sociability': persona.personality.sociability
            }, ensure_ascii=False)
            
            emotion_state = json.dumps(asdict(persona.emotions), ensure_ascii=False)
            
            learning_data = json.dumps({
                'memories': persona.memory.memories[-100:],  # 最新100件
                'topic_preferences': persona.memory.topic_preferences,
                'response_patterns': persona.memory.response_patterns
            }, ensure_ascii=False)
            
            # UPSERTで更新または挿入
            self.db_manager.execute_insert(
                """INSERT OR REPLACE INTO personas 
                   (name, age, occupation, background, extroversion, agreeableness, 
                    conscientiousness, neuroticism, openness, additional_params, 
                    emotion_state, learning_data, is_troll) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (persona.name, persona.age, persona.occupation, persona.background,
                 persona.personality.extroversion, persona.personality.agreeableness,
                 persona.personality.conscientiousness, persona.personality.neuroticism,
                 persona.personality.openness, additional_params, emotion_state,
                 learning_data, persona.is_troll)
            )
            
        except Exception as e:
            logger.error(f"[PERSONA_MGR] ペルソナ保存エラー: {e}")
    
    def generate_auto_post(self, thread_id: int) -> bool:
        """自動投稿生成"""
        try:
            # スレッド情報取得
            thread_info = self.db_manager.execute_query(
                "SELECT category_main, category_sub, title FROM threads WHERE thread_id=?",
                (thread_id,)
            )
            
            if not thread_info:
                return False
            
            category_main, category_sub, title = thread_info[0]
            
            # 最近の投稿取得
            recent_posts = self.db_manager.execute_query(
                """SELECT persona_name, content, posted_at FROM posts 
                   WHERE thread_id=? ORDER BY posted_at DESC LIMIT 10""",
                (thread_id,)
            )
            
            recent_contents = [post[1] for post in recent_posts]
            
            # 投稿するペルソナを選択
            available_personas = [p for p in self.personas.values() if p.is_active]
            if not available_personas:
                return False
            
            # 最近投稿していないペルソナを優先
            now = datetime.now()
            persona_weights = []
            
            for persona in available_personas:
                weight = 1.0
                
                # 最後の投稿からの時間による重み調整
                if persona.last_post_time:
                    time_diff = (now - persona.last_post_time).total_seconds()
                    weight *= min(2.0, time_diff / 3600)  # 1時間で重み2倍
                
                # 投稿判定
                thread_activity = len(recent_posts)
                time_since_last = 300 if not persona.last_post_time else (now - persona.last_post_time).total_seconds()
                
                if persona.should_post_now(thread_activity, time_since_last):
                    weight *= 2.0
                
                persona_weights.append((persona, weight))
            
            # 重み付き選択
            if not persona_weights:
                return False
            
            total_weight = sum(w[1] for w in persona_weights)
            r = random.uniform(0, total_weight)
            
            selected_persona = None
            cumulative_weight = 0
            for persona, weight in persona_weights:
                cumulative_weight += weight
                if r <= cumulative_weight:
                    selected_persona = persona
                    break
            
            if not selected_persona:
                selected_persona = random.choice(available_personas)
            
            # コンテキスト構築
            thread_context = f"{category_main} > {category_sub}: {title}"
            response_context = selected_persona.generate_response_context(thread_context, recent_contents)
            
            # AI応答生成
            response = self.g4f_manager.generate_response(
                f"この掲示板スレッドに適切な返信を生成してください。\n\nスレッド: {thread_context}",
                response_context
            )
            
            if response and len(response.strip()) > 5:
                # 投稿をデータベースに追加
                success = self.db_manager.execute_insert(
                    "INSERT INTO posts (thread_id, persona_name, content) VALUES (?, ?, ?)",
                    (thread_id, selected_persona.name, response.strip())
                ) > 0
                
                if success:
                    # ペルソナの状態更新
                    selected_persona.post_count += 1
                    selected_persona.last_post_time = now
                    selected_persona.update_emotions(response, thread_context)
                    
                    # 学習記録
                    selected_persona.learn_from_interaction(
                        thread_context + " | " + "\n".join(recent_contents[-3:]),
                        response,
                        0.6  # 中程度のポジティブフィードバック
                    )
                    
                    # データベース保存
                    self.save_persona(selected_persona)
                    
                    logger.info(f"[PERSONA_MGR] 自動投稿生成: {selected_persona.name} -> Thread {thread_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"[PERSONA_MGR] 自動投稿生成エラー: {e}")
            return False
    
    def record_user_interaction(self, thread_id: int, user_content: str):
        """ユーザーインタラクション記録"""
        try:
            # スレッド情報取得
            thread_info = self.db_manager.execute_query(
                "SELECT category_main, category_sub, title FROM threads WHERE thread_id=?",
                (thread_id,)
            )
            
            if not thread_info:
                return
            
            category_main, category_sub, title = thread_info[0]
            thread_context = f"{category_main} > {category_sub}: {title}"
            
            # 全ペルソナが学習
            for persona in self.personas.values():
                # ユーザー投稿から感情を更新
                persona.update_emotions(user_content, thread_context)
                
                # 学習記録（ポジティブフィードバック）
                persona.learn_from_interaction(
                    f"ユーザー投稿: {thread_context}",
                    user_content,
                    0.7  # ユーザー投稿はポジティブフィードバック
                )
            
            # 学習履歴テーブルに記録
            self.db_manager.execute_insert(
                """INSERT INTO learning_history (persona_id, interaction_context, response_pattern, learning_weight) 
                   VALUES (?, ?, ?, ?)""",
                (1, thread_context, user_content, 0.7)  # 代表的なペルソナIDを使用
            )
            
            logger.info(f"[PERSONA_MGR] ユーザーインタラクション記録: Thread {thread_id}")
            
        except Exception as e:
            logger.error(f"[PERSONA_MGR] ユーザーインタラクション記録エラー: {e}")
    
    def get_persona_stats(self) -> Dict:
        """ペルソナ統計取得"""
        total_personas = len(self.personas)
        active_personas = sum(1 for p in self.personas.values() if p.is_active)
        troll_personas = sum(1 for p in self.personas.values() if p.is_troll)
        
        total_posts = sum(p.post_count for p in self.personas.values())
        avg_activity = sum(p.activity_level for p in self.personas.values()) / max(total_personas, 1)
        
        return {
            'total_personas': total_personas,
            'active_personas': active_personas,
            'troll_personas': troll_personas,
            'total_posts': total_posts,
            'average_activity': avg_activity
        }
    
    def export_personas(self) -> str:
        """ペルソナデータエクスポート"""
        export_data = {
            'export_time': datetime.now().isoformat(),
            'version': '1.0.0',
            'personas': [persona.to_dict() for persona in self.personas.values()]
        }
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)
    
    def import_personas(self, import_data: str) -> bool:
        """ペルソナデータインポート"""
        try:
            data = json.loads(import_data)
            
            for persona_dict in data['personas']:
                persona = Persona.from_dict(persona_dict)
                self.personas[persona.name] = persona
                self.save_persona(persona)
            
            logger.info(f"[PERSONA_MGR] ペルソナインポート完了: {len(data['personas'])}体")
            return True
            
        except Exception as e:
            logger.error(f"[PERSONA_MGR] ペルソナインポートエラー: {e}")
            return False
