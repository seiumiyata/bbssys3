#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PC-98時代パソコン通信BBS風アプリケーション - ペルソナ管理モジュール
Version: 2.0.0 - 年代別最適化・人間らしい挙動対応版
AIペルソナの性格システム、感情システム、学習機能、年代別特徴を管理
"""

import json
import random
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import math
import re

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

@dataclass
class TypingCharacteristics:
    """タイピング特性"""
    speed: str = "normal"          # fast, normal, slow
    error_rate: float = 0.05       # 誤字率
    sentence_style: str = "balanced" # short, balanced, long, enthusiastic
    politeness_level: str = "medium" # very_high, high, medium, low
    emoji_usage: float = 0.3       # 絵文字使用率
    punctuation_style: str = "standard" # formal, standard, casual

class LearningMemory:
    """学習記憶システム"""
    
    def __init__(self):
        self.memories: List[Dict] = []
        self.topic_preferences: Dict[str, float] = {}
        self.response_patterns: Dict[str, List[str]] = {}
        self.interaction_history: List[Dict] = []
        self.learning_weights: Dict[str, float] = {}
        self.vocabulary_usage: Dict[str, int] = {}  # 語彙使用頻度
        self.time_patterns: Dict[str, List[int]] = {}  # 時間帯別活動パターン
    
    def add_memory(self, context: str, response: str, feedback_score: float = 0.5):
        """記憶追加"""
        memory = {
            'context': context,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'feedback_score': feedback_score,
            'usage_count': 0,
            'emotional_context': self._analyze_emotional_context(context, response)
        }
        self.memories.append(memory)
        
        # 語彙使用頻度更新
        words = response.split()
        for word in words:
            self.vocabulary_usage[word] = self.vocabulary_usage.get(word, 0) + 1
        
        # 古い記憶を削除（最大1000件）
        if len(self.memories) > 1000:
            self.memories = self.memories[-1000:]
    
    def _analyze_emotional_context(self, context: str, response: str) -> Dict[str, float]:
        """感情的文脈分析"""
        positive_words = ['嬉しい', '楽しい', '面白い', '素晴らしい', '良い', 'いい', '最高', 'すごい']
        negative_words = ['悲しい', '辛い', '嫌', 'むかつく', '最悪', 'ダメ', '困る', '疲れた']
        
        text = context + " " + response
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        return {
            'positive_intensity': min(1.0, positive_count * 0.2),
            'negative_intensity': min(1.0, negative_count * 0.2),
            'neutrality': max(0.0, 1.0 - (positive_count + negative_count) * 0.1)
        }
    
    def get_relevant_memories(self, context: str, limit: int = 5) -> List[Dict]:
        """関連記憶取得（感情的類似性も考慮）"""
        relevant = []
        context_words = set(context.lower().split())
        context_emotion = self._analyze_emotional_context(context, "")
        
        for memory in self.memories:
            memory_words = set(memory['context'].lower().split())
            word_similarity = len(context_words & memory_words) / max(len(context_words), 1)
            
            # 感情的類似性計算
            emotion_similarity = 0.0
            if 'emotional_context' in memory:
                for emotion_type in ['positive_intensity', 'negative_intensity', 'neutrality']:
                    emotion_similarity += 1.0 - abs(
                        context_emotion[emotion_type] - memory['emotional_context'][emotion_type]
                    )
                emotion_similarity /= 3.0
            
            # 総合類似度
            total_similarity = word_similarity * 0.7 + emotion_similarity * 0.3
            
            if total_similarity > 0.2:
                memory['similarity'] = total_similarity
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
    """AIペルソナクラス（年代別最適化版）"""
    
    def __init__(self, template: Dict):
        # 基本情報
        self.name = template["name"]
        self.age = template["age"]
        self.occupation = template["occupation"]
        self.background = template["background"]
        self.mbti = template.get("mbti", "ISFJ")
        self.generation = self._determine_generation()
        self.is_troll = template.get("is_troll", False)
        self.is_active = True
        
        # 性格特性初期化
        self.personality = self._generate_personality_from_template(template)
        
        # 感情状態初期化
        self.emotions = self._generate_emotions_from_template(template)
        
        # タイピング特性初期化
        self.typing = self._generate_typing_characteristics(template)
        
        # 学習記憶初期化
        self.memory = LearningMemory()
        
        # 活動統計
        self.post_count = 0
        self.last_post_time = None
        self.activity_level = self._calculate_base_activity_level()
        
        # 年代別特徴
        self.era_characteristics = self._get_era_characteristics()
        
        logger.info(f"[PERSONA] 作成完了: {self.name} ({self.age}歳, {self.generation}, {self.mbti}, {'荒らし' if self.is_troll else '通常'})")
    
    def _determine_generation(self) -> str:
        """世代判定"""
        if self.age >= 60:
            return "1950s-60s"
        elif self.age >= 40:
            return "1970s-80s"
        elif self.age >= 20:
            return "1990s-2000s"
        else:
            return "2010s-20s"
    
    def _generate_personality_from_template(self, template: Dict) -> PersonalityTraits:
        """テンプレートから性格特性生成"""
        traits = PersonalityTraits()
        
        if "big5" in template:
            big5 = template["big5"]
            traits.extroversion = big5.get("e", 0.5)
            traits.agreeableness = big5.get("a", 0.5)
            traits.conscientiousness = big5.get("c", 0.5)
            traits.neuroticism = big5.get("n", 0.5)
            traits.openness = big5.get("o", 0.5)
        
        # MBTI型による調整
        mbti_adjustments = self._get_mbti_adjustments(self.mbti)
        for trait, adjustment in mbti_adjustments.items():
            if hasattr(traits, trait):
                current_value = getattr(traits, trait)
                setattr(traits, trait, max(0.0, min(1.0, current_value + adjustment)))
        
        # 年代による調整
        age_adjustments = self._get_age_adjustments()
        for trait, adjustment in age_adjustments.items():
            if hasattr(traits, trait):
                current_value = getattr(traits, trait)
                setattr(traits, trait, max(0.0, min(1.0, current_value + adjustment)))
        
        # 荒らしキャラクターの調整
        if self.is_troll:
            traits.agreeableness = random.uniform(0.1, 0.3)
            traits.neuroticism = random.uniform(0.6, 0.9)
            traits.competitiveness = random.uniform(0.7, 1.0)
            traits.skepticism = random.uniform(0.6, 0.9)
            traits.risk_taking = random.uniform(0.7, 1.0)
        
        return traits
    
    def _generate_emotions_from_template(self, template: Dict) -> EmotionalState:
        """テンプレートから感情状態生成"""
        emotions = EmotionalState()
        
        if "emotions" in template:
            emotion_data = template["emotions"]
            emotions.anger = emotion_data.get("anger", 0.0)
            emotions.happiness = emotion_data.get("kindness", 0.5)  # kindnessをhappinessにマップ
            emotions.sadness = emotion_data.get("sadness", 0.0)
            
            # joyをexcitementとhappinessに分散
            joy = emotion_data.get("joy", 0.5)
            emotions.excitement = joy * 0.6
            emotions.happiness = max(emotions.happiness, joy * 0.4)
        
        # 年代による感情調整
        if self.generation == "1950s-60s":
            emotions.calmness += 0.2
            emotions.patience = getattr(emotions, 'patience', 0.7)
        elif self.generation == "2010s-20s":
            emotions.excitement += 0.1
            emotions.surprise += 0.1
        
        return emotions
    
    def _generate_typing_characteristics(self, template: Dict) -> TypingCharacteristics:
        """タイピング特性生成"""
        typing = TypingCharacteristics()
        
        typing.speed = template.get("typing_speed", "normal")
        typing.sentence_style = template.get("sentence_style", "balanced")
        typing.politeness_level = template.get("politeness", "medium")
        
        # 年代別調整
        if self.generation == "1950s-60s":
            typing.error_rate = 0.08  # 変換ミス多め
            typing.punctuation_style = "formal"
            typing.emoji_usage = 0.1
        elif self.generation == "1970s-80s":
            typing.error_rate = 0.05
            typing.punctuation_style = "standard"
            typing.emoji_usage = 0.2
        elif self.generation == "1990s-2000s":
            typing.error_rate = 0.03
            typing.punctuation_style = "standard"
            typing.emoji_usage = 0.4
        else:  # 2010s-20s
            typing.error_rate = 0.02
            typing.punctuation_style = "casual"
            typing.emoji_usage = 0.6
        
        return typing
    
    def _get_mbti_adjustments(self, mbti: str) -> Dict[str, float]:
        """MBTI型による性格調整"""
        adjustments = {}
        
        # 外向性/内向性
        if mbti[0] == 'E':
            adjustments['extroversion'] = 0.3
            adjustments['sociability'] = 0.2
        else:
            adjustments['extroversion'] = -0.3
            adjustments['independence'] = 0.2
        
        # 感覚/直観
        if mbti[1] == 'S':
            adjustments['conscientiousness'] = 0.2
            adjustments['perfectionism'] = 0.1
        else:
            adjustments['creativity'] = 0.3
            adjustments['openness'] = 0.2
        
        # 思考/感情
        if mbti[2] == 'T':
            adjustments['skepticism'] = 0.2
            adjustments['leadership'] = 0.1
        else:
            adjustments['empathy'] = 0.3
            adjustments['agreeableness'] = 0.2
        
        # 判断/知覚
        if mbti[3] == 'J':
            adjustments['conscientiousness'] = 0.2
            adjustments['perfectionism'] = 0.2
        else:
            adjustments['adaptability'] = 0.3
            adjustments['risk_taking'] = 0.1
        
        return adjustments
    
    def _get_age_adjustments(self) -> Dict[str, float]:
        """年齢による性格調整"""
        adjustments = {}
        
        if self.age < 25:
            adjustments['openness'] = 0.2
            adjustments['curiosity'] = 0.2
            adjustments['risk_taking'] = 0.1
            adjustments['patience'] = -0.1
        elif self.age > 50:
            adjustments['conscientiousness'] = 0.2
            adjustments['patience'] = 0.2
            adjustments['wisdom'] = 0.3
            adjustments['risk_taking'] = -0.1
        
        return adjustments
    
    def _calculate_base_activity_level(self) -> float:
        """基本活動レベル計算"""
        base = 0.5
        
        # 年代による調整
        if self.generation == "2010s-20s":
            base += 0.2
        elif self.generation == "1950s-60s":
            base -= 0.1
        
        # 性格による調整
        if hasattr(self, 'personality'):
            base += (self.personality.extroversion - 0.5) * 0.3
            base += (self.personality.sociability - 0.5) * 0.2
        
        return max(0.1, min(0.9, base))
    
    def _get_era_characteristics(self) -> Dict:
        """年代別特徴取得"""
        characteristics = {
            "1950s-60s": {
                "vocabulary": ["そうですね", "なるほど", "ありがたい", "恐縮です", "失礼いたします"],
                "topics": ["戦後復興", "高度経済成長", "家族", "伝統", "礼儀"],
                "communication_style": "formal",
                "tech_familiarity": 0.3,
                "slang_usage": 0.1
            },
            "1970s-80s": {
                "vocabulary": ["要するに", "つまり", "基本的に", "実際のところ", "なるほど"],
                "topics": ["バブル経済", "仕事", "家族", "責任", "効率"],
                "communication_style": "business",
                "tech_familiarity": 0.6,
                "slang_usage": 0.2
            },
            "1990s-2000s": {
                "vocabulary": ["そうですね〜", "なるほど", "確かに", "それって", "みたいな"],
                "topics": ["就職氷河期", "IT革命", "個性", "多様性", "ワークライフバランス"],
                "communication_style": "casual",
                "tech_familiarity": 0.8,
                "slang_usage": 0.4
            },
            "2010s-20s": {
                "vocabulary": ["やばい", "それな", "マジで", "〜って感じ", "エモい"],
                "topics": ["SNS", "YouTuber", "インフルエンサー", "多様性", "環境問題"],
                "communication_style": "very_casual",
                "tech_familiarity": 0.95,
                "slang_usage": 0.7
            }
        }
        
        return characteristics.get(self.generation, characteristics["1990s-2000s"])
    
    def update_emotions(self, stimulus: str, context: str = ""):
        """感情状態更新（年代別反応考慮）"""
        # 基本的な感情分析
        positive_words = ['嬉しい', '楽しい', '面白い', '素晴らしい', '良い', 'いい']
        negative_words = ['悲しい', '辛い', '嫌', 'むかつく', '最悪', 'ダメ']
        surprising_words = ['驚き', 'びっくり', '意外', '予想外']
        
        # 年代別反応強度
        reaction_intensity = {
            "1950s-60s": 0.8,  # 控えめな反応
            "1970s-80s": 1.0,  # 標準的な反応
            "1990s-2000s": 1.1, # やや強い反応
            "2010s-20s": 1.3   # 強い反応
        }
        
        intensity = reaction_intensity.get(self.generation, 1.0)
        
        # 感情変化量計算
        emotion_change = 0.1 * intensity
        if self.personality.neuroticism > 0.7:
            emotion_change *= 1.5
        
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
        """感情の自然減衰（年代別）"""
        # 年代別減衰率
        decay_rates = {
            "1950s-60s": 0.03,  # ゆっくり減衰
            "1970s-80s": 0.05,  # 標準的な減衰
            "1990s-2000s": 0.06, # やや早い減衰
            "2010s-20s": 0.08   # 早い減衰
        }
        
        decay_rate = decay_rates.get(self.generation, 0.05)
        
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
        """応答コンテキスト生成（年代別特徴反映）"""
        # 基本的な性格設定
        personality_desc = f"""
あなたは{self.name}、{self.age}歳の{self.occupation}です。
世代: {self.generation}
MBTI: {self.mbti}
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

タイピング特性:
- 速度: {self.typing.speed}
- 文体: {self.typing.sentence_style}
- 丁寧さ: {self.typing.politeness_level}
"""
        
        # 年代別特徴追加
        era_char = self.era_characteristics
        personality_desc += f"""
年代別特徴:
- コミュニケーションスタイル: {era_char['communication_style']}
- 技術慣れ: {era_char['tech_familiarity']:.1f}
- よく使う言葉: {', '.join(era_char['vocabulary'][:3])}
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
        
        # 年代別指示
        generation_instructions = self._get_generation_instructions()
        
        personality_desc += f"""
指示:
1. {self.name}として、上記の性格と現在の感情状態に基づいて自然に応答してください
2. 日本語で{self._get_sentence_length_instruction()}の投稿をしてください
3. {generation_instructions}
4. 同じような内容の繰り返しは避けてください
5. トピック: {thread_context}
"""
        
        return personality_desc
    
    def _get_sentence_length_instruction(self) -> str:
        """文章長指示取得"""
        if self.typing.sentence_style == "short":
            return "1-2文程度の短い"
        elif self.typing.sentence_style == "long":
            return "3-5文程度の詳しい"
        elif self.typing.sentence_style == "enthusiastic":
            return "熱心で詳細な"
        else:
            return "2-3文程度の"
    
    def _get_generation_instructions(self) -> str:
        """世代別指示取得"""
        instructions = {
            "1950s-60s": "丁寧で礼儀正しい口調で、人生経験を活かした発言をしてください。改行を多めに使い、相手への気遣いを忘れずに。",
            "1970s-80s": "簡潔で要点を明確にした、ビジネス調の発言をしてください。経験に基づいた実践的なアドバイスを心がけて。",
            "1990s-2000s": "親しみやすく自然な口調で、バランスの取れた発言をしてください。適度に絵文字を使用しても構いません。",
            "2010s-20s": "カジュアルで親しみやすい口調で、短めの文章を心がけてください。流行語や若者言葉を適度に使用してください。"
        }
        
        return instructions.get(self.generation, instructions["1990s-2000s"])
    
    def apply_typing_characteristics(self, text: str) -> str:
        """タイピング特性適用"""
        # 誤字の導入
        if random.random() < self.typing.error_rate:
            text = self._introduce_typos(text)
        
        # 絵文字追加
        if random.random() < self.typing.emoji_usage:
            text = self._add_emojis(text)
        
        # 句読点スタイル調整
        text = self._adjust_punctuation(text)
        
        return text
    
    def _introduce_typos(self, text: str) -> str:
        """誤字導入"""
        # 年代別誤字パターン
        if self.generation == "1950s-60s":
            # 変換ミス
            typo_patterns = {
                'です': 'でs', 'ます': 'masu', 'ありがとう': 'ありがとお'
            }
        elif self.generation == "2010s-20s":
            # タイプミス
            typo_patterns = {
                'そう': 'そお', 'やっぱり': 'やっぱ', 'すごい': 'すごっ'
            }
        else:
            # 一般的な誤字
            typo_patterns = {
                'という': 'とゆう', 'そういう': 'そうゆう'
            }
        
        for correct, typo in typo_patterns.items():
            if correct in text and random.random() < 0.3:
                text = text.replace(correct, typo, 1)
                break
        
        return text
    
    def _add_emojis(self, text: str) -> str:
        """絵文字追加"""
        emojis = {
            "1950s-60s": ["(^^)", "(^_^)"],
            "1970s-80s": ["(^_^)", "(-_-)", "(^^;)"],
            "1990s-2000s": ["(^^)", "(^_^;)", "(*^^*)", "(>_<)"],
            "2010s-20s": ["😊", "😂", "🤔", "😅", "✨", "👍"]
        }
        
        generation_emojis = emojis.get(self.generation, emojis["1990s-2000s"])
        
        if random.random() < 0.5:
            emoji = random.choice(generation_emojis)
            text += emoji
        
        return text
    
    def _adjust_punctuation(self, text: str) -> str:
        """句読点調整"""
        if self.typing.punctuation_style == "formal":
            # 正式な句読点
            text = text.replace('、', '，').replace('。', '．')
        elif self.typing.punctuation_style == "casual":
            # カジュアルな句読点
            text = text.replace('。', '！' if random.random() < 0.3 else '。')
        
        return text
    
    def learn_from_interaction(self, context: str, response: str, feedback: float = 0.5):
        """インタラクションから学習（強化版）"""
        # 記憶に追加
        self.memory.add_memory(context, response, feedback)
        
        # トピック嗜好更新
        topic_keywords = context.lower().split()
        for keyword in topic_keywords:
            if len(keyword) > 2:
                sentiment = feedback
                self.memory.update_topic_preference(keyword, sentiment)
        
        # 時間パターン学習
        current_hour = datetime.now().hour
        if 'posting_times' not in self.memory.time_patterns:
            self.memory.time_patterns['posting_times'] = []
        self.memory.time_patterns['posting_times'].append(current_hour)
        
        # 性格の微調整（長期的な学習効果）
        if len(self.memory.memories) > 50:
            self._adjust_personality_from_learning()
    
    def _adjust_personality_from_learning(self):
        """学習から性格微調整（年代別考慮）"""
        recent_memories = self.memory.memories[-20:]
        
        positive_interactions = sum(1 for m in recent_memories if m['feedback_score'] > 0.6)
        negative_interactions = sum(1 for m in recent_memories if m['feedback_score'] < 0.4)
        
        # 年代別学習速度
        learning_rates = {
            "1950s-60s": 0.005,  # ゆっくり変化
            "1970s-80s": 0.008,
            "1990s-2000s": 0.010,
            "2010s-20s": 0.015   # 早く変化
        }
        
        adjustment = learning_rates.get(self.generation, 0.010)
        
        if positive_interactions > negative_interactions:
            self.personality.agreeableness = min(1.0, self.personality.agreeableness + adjustment)
            self.personality.extroversion = min(1.0, self.personality.extroversion + adjustment * 0.5)
        elif negative_interactions > positive_interactions:
            self.personality.neuroticism = min(1.0, self.personality.neuroticism + adjustment)
            self.personality.skepticism = min(1.0, self.personality.skepticism + adjustment * 0.5)
    
    def should_post_now(self, thread_activity: int, time_since_last_post: int) -> bool:
        """投稿判定（年代別活動パターン考慮）"""
        # 基本的な活動レベル
        base_probability = self.activity_level
        
        # 年代別活動パターン
        current_hour = datetime.now().hour
        generation_activity = {
            "1950s-60s": {
                'peak_hours': [6, 7, 8, 18, 19, 20],  # 朝と夕方
                'low_hours': [22, 23, 0, 1, 2, 3, 4, 5]
            },
            "1970s-80s": {
                'peak_hours': [7, 8, 12, 18, 19, 20, 21],  # 通勤時間と夜
                'low_hours': [23, 0, 1, 2, 3, 4, 5, 6]
            },
            "1990s-2000s": {
                'peak_hours': [8, 12, 13, 19, 20, 21, 22],  # 昼休みと夜
                'low_hours': [0, 1, 2, 3, 4, 5, 6, 7]
            },
            "2010s-20s": {
                'peak_hours': [12, 15, 16, 20, 21, 22, 23],  # 午後と深夜
                'low_hours': [4, 5, 6, 7, 8, 9, 10]
            }
        }
        
        activity_pattern = generation_activity.get(self.generation, generation_activity["1990s-2000s"])
        
        if current_hour in activity_pattern['peak_hours']:
            base_probability *= 1.3
        elif current_hour in activity_pattern['low_hours']:
            base_probability *= 0.5
        
        # 性格による調整
        if self.personality.extroversion > 0.7:
            base_probability *= 1.3
        elif self.personality.extroversion < 0.3:
            base_probability *= 0.7
        
        # スレッド活動度による調整
        if thread_activity > 10:
            base_probability *= 1.2
        elif thread_activity < 3:
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
            'mbti': self.mbti,
            'generation': self.generation,
            'is_troll': self.is_troll,
            'personality': asdict(self.personality),
            'emotions': asdict(self.emotions),
            'typing': asdict(self.typing),
            'era_characteristics': self.era_characteristics,
            'memory': {
                'memories': self.memory.memories[-50:],
                'topic_preferences': self.memory.topic_preferences,
                'response_patterns': self.memory.response_patterns,
                'vocabulary_usage': dict(list(self.memory.vocabulary_usage.items())[-100:])
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
        # テンプレート形式に変換
        template = {
            'name': data['name'],
            'age': data['age'],
            'occupation': data['occupation'],
            'background': data['background'],
            'mbti': data.get('mbti', 'ISFJ'),
            'is_troll': data.get('is_troll', False),
            'big5': {
                'e': data['personality']['extroversion'],
                'a': data['personality']['agreeableness'],
                'c': data['personality']['conscientiousness'],
                'n': data['personality']['neuroticism'],
                'o': data['personality']['openness']
            },
            'emotions': {
                'anger': data['emotions']['anger'],
                'kindness': data['emotions']['happiness'],
                'sadness': data['emotions']['sadness'],
                'joy': data['emotions']['excitement']
            },
            'typing_speed': data.get('typing', {}).get('speed', 'normal'),
            'sentence_style': data.get('typing', {}).get('sentence_style', 'balanced'),
            'politeness': data.get('typing', {}).get('politeness_level', 'medium')
        }
        
        persona = cls(template)
        
        # 記憶復元
        if 'memory' in data:
            persona.memory.memories = data['memory'].get('memories', [])
            persona.memory.topic_preferences = data['memory'].get('topic_preferences', {})
            persona.memory.response_patterns = data['memory'].get('response_patterns', {})
            persona.memory.vocabulary_usage = data['memory'].get('vocabulary_usage', {})
        
        # 統計復元
        if 'stats' in data:
            persona.post_count = data['stats'].get('post_count', 0)
            persona.activity_level = data['stats'].get('activity_level', 0.5)
            if data['stats'].get('last_post_time'):
                persona.last_post_time = datetime.fromisoformat(data['stats']['last_post_time'])
        
        return persona

class PersonaManager:
    """ペルソナ管理クラス（年代別最適化版）"""
    
    def __init__(self, db_manager, g4f_manager):
        self.db_manager = db_manager
        self.g4f_manager = g4f_manager
        self.personas: Dict[str, Persona] = {}
        
        self.persona_templates = self._create_detailed_persona_templates()
        self.initialize_personas()
        
        logger.info(f"[PERSONA_MGR] 初期化完了: {len(self.personas)}体のペルソナ")
    
    def _create_detailed_persona_templates(self) -> List[Dict]:
        """詳細ペルソナテンプレート作成（年代別100名）"""
        templates = []
        
        # 1950s-60s世代（25名）
        elderly_names = [
            ("田中昭夫", "男性"), ("佐藤和子", "女性"), ("鈴木正雄", "男性"), ("高橋花子", "女性"),
            ("伊藤清", "男性"), ("渡辺きみ子", "女性"), ("山田勇", "男性"), ("中村静江", "女性"),
            ("小林茂", "男性"), ("加藤文子", "女性"), ("吉田忠", "男性"), ("山本春子", "女性"),
            ("佐々木義雄", "男性"), ("松本千代子", "女性"), ("木村博", "男性"), ("井上美代子", "女性"),
            ("林武夫", "男性"), ("清水節子", "女性"), ("森信夫", "男性"), ("池田良子", "女性"),
            ("橋本正", "男性"), ("山口みどり", "女性"), ("石川健", "男性"), ("前田恵子", "女性"),
            ("藤田光雄", "男性")
        ]
        
        elderly_occupations = [
            "元電気技師", "元小学校教師", "元銀行員", "元看護師", "元公務員",
            "元製造業", "元商店主", "元事務員", "元運転手", "元農業",
            "年金生活者", "元郵便局員", "元鉄道員", "元工場長", "元美容師"
        ]
        
        elderly_mbti = ["ISTJ", "ESFJ", "ISFJ", "ESTJ", "ISTP", "ESFP"]
        
        for i, (name, gender) in enumerate(elderly_names):
            age = random.randint(60, 75)
            occupation = random.choice(elderly_occupations)
            mbti = random.choice(elderly_mbti)
            
            template = {
                "name": name,
                "age": age,
                "mbti": mbti,
                "occupation": occupation,
                "background": f"戦後復興期育ち、{random.choice(['千葉県', '神奈川県', '埼玉県', '茨城県'])}出身、{random.choice(['兄弟が多い家庭', '厳格な家庭', '商家の出身', '農家の出身'])}",
                "typing_speed": "normal" if "技師" in occupation else "slow",
                "sentence_style": "caring" if gender == "女性" else "balanced",
                "politeness": "very_high",
                "big5": {
                    "e": random.uniform(0.2, 0.7),
                    "a": random.uniform(0.6, 0.9),
                    "c": random.uniform(0.6, 0.9),
                    "n": random.uniform(0.2, 0.6),
                    "o": random.uniform(0.3, 0.6)
                },
                "emotions": {
                    "anger": random.uniform(0.0, 0.2),
                    "kindness": random.uniform(0.7, 1.0),
                    "sadness": random.uniform(0.1, 0.3),
                    "joy": random.uniform(0.5, 0.8)
                },
                "is_troll": False
            }
            templates.append(template)
        
        # 1970s-80s世代（25名）
        middle_names = [
            ("山田健一", "男性"), ("鈴木美紀", "女性"), ("田中浩二", "男性"), ("佐藤由美", "女性"),
            ("高橋誠", "男性"), ("伊藤恵子", "女性"), ("渡辺隆", "男性"), ("山本真理", "女性"),
            ("中村修", "男性"), ("小林順子", "女性"), ("加藤明", "男性"), ("吉田智子", "女性"),
            ("佐々木勝", "男性"), ("松本直美", "女性"), ("木村進", "男性"), ("井上裕子", "女性"),
            ("林俊夫", "男性"), ("清水典子", "女性"), ("森雅彦", "男性"), ("池田京子", "女性"),
            ("橋本和夫", "男性"), ("山口洋子", "女性"), ("石川豊", "男性"), ("前田美穂", "女性"),
            ("藤田秀樹", "男性")
        ]
        
        middle_occupations = [
            "IT企業管理職", "化粧品販売", "製造業課長", "病院事務", "公務員",
            "不動産営業", "銀行員", "保険営業", "運送会社", "小売店長",
            "建設会社", "旅行会社", "経理事務", "人事担当", "システムエンジニア"
        ]
        
        middle_mbti = ["INTJ", "ENFP", "ESTJ", "ISFP", "ENTP", "ISFJ"]
        
        for i, (name, gender) in enumerate(middle_names):
            age = random.randint(40, 59)
            occupation = random.choice(middle_occupations)
            mbti = random.choice(middle_mbti)
            
            template = {
                "name": name,
                "age": age,
                "mbti": mbti,
                "occupation": occupation,
                "background": f"高度経済成長期育ち、{random.choice(['東京都', '大阪府', '愛知県', '福岡県'])}出身、{random.choice(['転勤族', '地元育ち', '大学で上京', '就職で転居'])}",
                "typing_speed": "normal" if "IT" in occupation else "slow",
                "sentence_style": "business" if "管理職" in occupation or "営業" in occupation else "balanced",
                "politeness": "high" if "営業" in occupation else "medium",
                "big5": {
                    "e": random.uniform(0.4, 0.8),
                    "a": random.uniform(0.4, 0.8),
                    "c": random.uniform(0.5, 0.9),
                    "n": random.uniform(0.2, 0.7),
                    "o": random.uniform(0.3, 0.7)
                },
                "emotions": {
                    "anger": random.uniform(0.1, 0.4),
                    "kindness": random.uniform(0.5, 0.9),
                    "sadness": random.uniform(0.2, 0.5),
                    "joy": random.uniform(0.4, 0.8)
                },
                "is_troll": False
            }
            templates.append(template)
        
        # 1990s-2000s世代（25名）
        young_adult_names = [
            ("佐々木翔太", "男性"), ("田村彩", "女性"), ("山田拓也", "男性"), ("鈴木愛美", "女性"),
            ("田中大輔", "男性"), ("佐藤麻衣", "女性"), ("高橋亮", "男性"), ("伊藤沙織", "女性"),
            ("渡辺健太", "男性"), ("山本香織", "女性"), ("中村雄太", "男性"), ("小林美咲", "女性"),
            ("加藤翔", "男性"), ("吉田優香", "女性"), ("佐々木大樹", "男性"), ("松本彩花", "女性"),
            ("木村拓海", "男性"), ("井上美穂", "女性"), ("林翔平", "男性"), ("清水愛", "女性"),
            ("森大和", "男性"), ("池田莉奈", "女性"), ("橋本颯", "男性"), ("山口美月", "女性"),
            ("石川蓮", "男性")
        ]
        
        young_adult_occupations = [
            "保育士", "アパレル販売員", "Webデザイナー", "看護師", "システムエンジニア",
            "美容師", "調理師", "介護士", "営業", "事務員",
            "フリーランサー", "カフェ店員", "配達員", "塾講師", "グラフィックデザイナー"
        ]
        
        young_adult_mbti = ["ISTJ", "ESFJ", "ENFP", "INFP", "ESTP", "ISFP"]
        
        for i, (name, gender) in enumerate(young_adult_names):
            age = random.randint(20, 39)
            occupation = random.choice(young_adult_occupations)
            mbti = random.choice(young_adult_mbti)
            
            template = {
                "name": name,
                "age": age,
                "mbti": mbti,
                "occupation": occupation,
                "background": f"デジタルネイティブ世代、{random.choice(['東京都', '大阪府', '福岡県', '北海道', '沖縄県'])}出身、{random.choice(['一人暮らし', '実家暮らし', 'シェアハウス', '同棲中'])}",
                "typing_speed": "fast",
                "sentence_style": "friendly" if "保育士" in occupation or "看護師" in occupation else "balanced",
                "politeness": "medium",
                "big5": {
                    "e": random.uniform(0.3, 0.8),
                    "a": random.uniform(0.4, 0.8),
                    "c": random.uniform(0.4, 0.8),
                    "n": random.uniform(0.2, 0.6),
                    "o": random.uniform(0.5, 0.9)
                },
                "emotions": {
                    "anger": random.uniform(0.1, 0.4),
                    "kindness": random.uniform(0.5, 0.9),
                    "sadness": random.uniform(0.1, 0.4),
                    "joy": random.uniform(0.5, 0.9)
                },
                "is_troll": False
            }
            templates.append(template)
        
        # 2010s-20s世代（23名）+ 荒らし（2名）
        gen_z_names = [
            ("高橋陽翔", "男性"), ("小林結愛", "女性"), ("山田蒼空", "男性"), ("鈴木心春", "女性"),
            ("田中颯真", "男性"), ("佐藤美桜", "女性"), ("高橋湊", "男性"), ("伊藤咲良", "女性"),
            ("渡辺大翔", "男性"), ("山本愛莉", "女性"), ("中村悠人", "男性"), ("小林花音", "女性"),
            ("加藤陸斗", "男性"), ("吉田莉子", "女性"), ("佐々木蒼", "男性"), ("松本心愛", "女性"),
            ("木村海翔", "男性"), ("井上美羽", "女性"), ("林大雅", "男性"), ("清水結菜", "女性"),
            ("森蓮", "男性"), ("池田心結", "女性"), ("橋本翔太", "男性")
        ]
        
        gen_z_occupations = [
            "高校生", "中学生", "大学生", "専門学生", "アルバイト",
            "YouTuber志望", "インフルエンサー", "ゲーム実況者", "イラストレーター志望",
            "音楽活動", "ダンサー", "配信者", "コスプレイヤー"
        ]
        
        gen_z_mbti = ["ENFP", "INTP", "ESFP", "INFP", "ENTP", "ISFP"]
        
        for i, (name, gender) in enumerate(gen_z_names):
            age = random.randint(13, 19)
            occupation = random.choice(gen_z_occupations)
            mbti = random.choice(gen_z_mbti)
            
            template = {
                "name": name,
                "age": age,
                "mbti": mbti,
                "occupation": occupation,
                "background": f"SNS世代、{random.choice(['東京都', '神奈川県', '大阪府', '愛知県', '福岡県'])}出身、{random.choice(['両親と同居', '寮生活', '祖父母と同居', '兄弟姉妹と仲良し'])}",
                "typing_speed": "normal",  # スマホは速いがPCは普通
                "sentence_style": "short" if age < 16 else "enthusiastic",
                "politeness": "low",
                "big5": {
                    "e": random.uniform(0.4, 0.9),
                    "a": random.uniform(0.3, 0.8),
                    "c": random.uniform(0.3, 0.8),
                    "n": random.uniform(0.2, 0.6),
                    "o": random.uniform(0.6, 1.0)
                },
                "emotions": {
                    "anger": random.uniform(0.2, 0.5),
                    "kindness": random.uniform(0.6, 1.0),
                    "sadness": random.uniform(0.1, 0.3),
                    "joy": random.uniform(0.6, 1.0)
                },
                "is_troll": False
            }
            templates.append(template)
        
        # 荒らしペルソナ（2名）
        troll_templates = [
            {
                "name": "匿名の批評家",
                "age": 30,
                "mbti": "ENTP",
                "occupation": "フリーター",
                "background": "様々な仕事を転々とする。批判的で議論好き。ネット掲示板の常連。",
                "typing_speed": "fast",
                "sentence_style": "long",
                "politeness": "low",
                "big5": {"e": 0.6, "a": 0.2, "c": 0.3, "n": 0.8, "o": 0.7},
                "emotions": {"anger": 0.5, "kindness": 0.2, "sadness": 0.3, "joy": 0.4},
                "is_troll": True
            },
            {
                "name": "炎上マニア",
                "age": 25,
                "mbti": "ESTP",
                "occupation": "ニート",
                "background": "ネット掲示板の常連。挑発的な発言を好む。注目を集めたがる性格。",
                "typing_speed": "fast",
                "sentence_style": "short",
                "politeness": "low",
                "big5": {"e": 0.8, "a": 0.1, "c": 0.2, "n": 0.9, "o": 0.5},
                "emotions": {"anger": 0.7, "kindness": 0.1, "sadness": 0.2, "joy": 0.6},
                "is_troll": True
            }
        ]
        
        templates.extend(troll_templates)
        
        logger.info(f"[PERSONA_MGR] ペルソナテンプレート作成完了: {len(templates)}体")
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
                
                # 復元用データ構築
                restore_data = {
                    'name': name,
                    'age': age,
                    'occupation': occupation,
                    'background': background,
                    'is_troll': bool(is_troll),
                    'personality': {
                        'extroversion': extroversion,
                        'agreeableness': agreeableness,
                        'conscientiousness': conscientiousness,
                        'neuroticism': neuroticism,
                        'openness': openness
                    },
                    'emotions': {
                        'anger': 0.0,
                        'happiness': 0.5,
                        'sadness': 0.0,
                        'excitement': 0.3
                    },
                    'typing': {
                        'speed': 'normal',
                        'sentence_style': 'balanced',
                        'politeness_level': 'medium'
                    }
                }
                
                # 拡張パラメータ復元
                if additional_params:
                    try:
                        additional_data = json.loads(additional_params)
                        restore_data['personality'].update(additional_data)
                    except:
                        pass
                
                # 感情状態復元
                if emotion_state:
                    try:
                        emotion_data = json.loads(emotion_state)
                        restore_data['emotions'].update(emotion_data)
                    except:
                        pass
                
                persona = Persona.from_dict(restore_data)
                
                # 学習データ復元
                if learning_data:
                    try:
                        learning_dict = json.loads(learning_data)
                        persona.memory.memories = learning_dict.get('memories', [])
                        persona.memory.topic_preferences = learning_dict.get('topic_preferences', {})
                        persona.memory.response_patterns = learning_dict.get('response_patterns', {})
                        persona.memory.vocabulary_usage = learning_dict.get('vocabulary_usage', {})
                    except:
                        pass
                
                self.personas[name] = persona
                
            logger.info(f"[PERSONA_MGR] 既存ペルソナ復元: {len(existing_personas)}体")
        else:
            # 新規ペルソナ作成
            for template in self.persona_templates:
                persona = Persona(template)
                self.personas[template["name"]] = persona
                self.save_persona(persona)
            
            logger.info(f"[PERSONA_MGR] 新規ペルソナ作成: {len(self.personas)}体")
    
    def save_persona(self, persona: Persona):
        """ペルソナをデータベースに保存（年代別特徴含む）"""
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
                'sociability': persona.personality.sociability,
                # 年代別特徴も保存
                'mbti': persona.mbti,
                'generation': persona.generation,
                'typing_characteristics': asdict(persona.typing),
                'era_characteristics': persona.era_characteristics
            }, ensure_ascii=False)
            
            emotion_state = json.dumps(asdict(persona.emotions), ensure_ascii=False)
            
            learning_data = json.dumps({
                'memories': persona.memory.memories[-100:],  # 最新100件
                'topic_preferences': persona.memory.topic_preferences,
                'response_patterns': persona.memory.response_patterns,
                'vocabulary_usage': dict(list(persona.memory.vocabulary_usage.items())[-100:]),
                'time_patterns': persona.memory.time_patterns
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
        """自動投稿生成（年代別特徴反映版）"""
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
            
            # 投稿するペルソナを選択（年代別重み付け）
            available_personas = [p for p in self.personas.values() if p.is_active]
            if not available_personas:
                return False
            
            # 年代別・時間帯別重み付け
            now = datetime.now()
            current_hour = now.hour
            persona_weights = []
            
            for persona in available_personas:
                weight = 1.0
                
                # 最後の投稿からの時間による重み調整
                if persona.last_post_time:
                    time_diff = (now - persona.last_post_time).total_seconds()
                    weight *= min(2.0, time_diff / 3600)  # 1時間で重み2倍
                
                # 年代別時間帯活動パターン
                generation_activity = {
                    "1950s-60s": {6: 1.5, 7: 1.5, 8: 1.3, 18: 1.4, 19: 1.5, 20: 1.3, 22: 0.3, 23: 0.2},
                    "1970s-80s": {7: 1.3, 8: 1.4, 12: 1.2, 18: 1.3, 19: 1.4, 20: 1.3, 21: 1.2, 23: 0.3},
                    "1990s-2000s": {8: 1.2, 12: 1.4, 13: 1.3, 19: 1.3, 20: 1.4, 21: 1.3, 22: 1.2},
                    "2010s-20s": {12: 1.3, 15: 1.2, 16: 1.2, 20: 1.4, 21: 1.5, 22: 1.4, 23: 1.3}
                }
                
                activity_pattern = generation_activity.get(persona.generation, {})
                hour_weight = activity_pattern.get(current_hour, 1.0)
                weight *= hour_weight
                
                # トピック関連性による重み調整
                thread_context = f"{category_main} {category_sub} {title}"
                topic_relevance = self._calculate_topic_relevance(persona, thread_context)
                weight *= (0.5 + topic_relevance)
                
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
                # 年代別特徴を適用
                processed_response = selected_persona.apply_typing_characteristics(response.strip())
                
                # 投稿をデータベースに追加
                success = self.db_manager.execute_insert(
                    "INSERT INTO posts (thread_id, persona_name, content) VALUES (?, ?, ?)",
                    (thread_id, selected_persona.name, processed_response)
                ) > 0
                
                if success:
                    # ペルソナの状態更新
                    selected_persona.post_count += 1
                    selected_persona.last_post_time = now
                    selected_persona.update_emotions(processed_response, thread_context)
                    
                    # 学習記録
                    selected_persona.learn_from_interaction(
                        thread_context + " | " + "\n".join(recent_contents[-3:]),
                        processed_response,
                        0.6  # 中程度のポジティブフィードバック
                    )
                    
                    # データベース保存
                    self.save_persona(selected_persona)
                    
                    logger.info(f"[PERSONA_MGR] 自動投稿生成: {selected_persona.name} ({selected_persona.generation}) -> Thread {thread_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"[PERSONA_MGR] 自動投稿生成エラー: {e}")
            return False
    
    def _calculate_topic_relevance(self, persona: Persona, thread_context: str) -> float:
        """トピック関連性計算"""
        relevance = 0.0
        
        # 年代別興味トピック
        era_topics = persona.era_characteristics.get('topics', [])
        context_lower = thread_context.lower()
        
        for topic in era_topics:
            if topic in context_lower:
                relevance += 0.2
        
        # 職業関連性
        occupation_keywords = {
            '教師': ['教育', '学校', '勉強', '子供'],
            '技師': ['技術', 'パソコン', 'システム', '機械'],
            '営業': ['仕事', '会社', '経済', 'ビジネス'],
            '看護師': ['健康', '医療', '病院', 'ケア'],
            '保育士': ['子供', '教育', '遊び', '成長']
        }
        
        for job_type, keywords in occupation_keywords.items():
            if job_type in persona.occupation:
                for keyword in keywords:
                    if keyword in context_lower:
                        relevance += 0.15
        
        # 学習済みトピック嗜好
        for topic, preference in persona.memory.topic_preferences.items():
            if topic in context_lower:
                relevance += preference * 0.1
        
        return min(1.0, relevance)
    
    def record_user_interaction(self, thread_id: int, user_content: str):
        """ユーザーインタラクション記録（年代別反応考慮）"""
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
            
            # 全ペルソナが年代別に学習
            for persona in self.personas.values():
                # 年代別反応強度
                reaction_intensity = {
                    "1950s-60s": 0.8,
                    "1970s-80s": 1.0,
                    "1990s-2000s": 1.1,
                    "2010s-20s": 1.3
                }
                
                intensity = reaction_intensity.get(persona.generation, 1.0)
                
                # ユーザー投稿から感情を更新
                persona.update_emotions(user_content, thread_context)
                
                # 年代別学習重み
                learning_weight = 0.7 * intensity
                
                # 学習記録
                persona.learn_from_interaction(
                    f"ユーザー投稿: {thread_context}",
                    user_content,
                    learning_weight
                )
            
            # 学習履歴テーブルに記録
            self.db_manager.execute_insert(
                """INSERT INTO learning_history (persona_id, interaction_context, response_pattern, learning_weight) 
                   VALUES (?, ?, ?, ?)""",
                (1, thread_context, user_content, 0.7)
            )
            
            logger.info(f"[PERSONA_MGR] ユーザーインタラクション記録: Thread {thread_id}")
            
        except Exception as e:
            logger.error(f"[PERSONA_MGR] ユーザーインタラクション記録エラー: {e}")
    
    def get_persona_stats(self) -> Dict:
        """ペルソナ統計取得（年代別詳細）"""
        total_personas = len(self.personas)
        active_personas = sum(1 for p in self.personas.values() if p.is_active)
        troll_personas = sum(1 for p in self.personas.values() if p.is_troll)
        
        total_posts = sum(p.post_count for p in self.personas.values())
        avg_activity = sum(p.activity_level for p in self.personas.values()) / max(total_personas, 1)
        
        # 年代別統計
        generation_stats = {}
        for generation in ["1950s-60s", "1970s-80s", "1990s-2000s", "2010s-20s"]:
            gen_personas = [p for p in self.personas.values() if p.generation == generation]
            generation_stats[generation] = {
                'count': len(gen_personas),
                'active': sum(1 for p in gen_personas if p.is_active),
                'total_posts': sum(p.post_count for p in gen_personas),
                'avg_activity': sum(p.activity_level for p in gen_personas) / max(len(gen_personas), 1)
            }
        
        return {
            'total_personas': total_personas,
            'active_personas': active_personas,
            'troll_personas': troll_personas,
            'total_posts': total_posts,
            'average_activity': avg_activity,
            'generation_stats': generation_stats
        }
    
    def get_generation_distribution(self) -> Dict[str, int]:
        """世代別分布取得"""
        distribution = {}
        for persona in self.personas.values():
            generation = persona.generation
            distribution[generation] = distribution.get(generation, 0) + 1
        
        return distribution
    
    def get_mbti_distribution(self) -> Dict[str, int]:
        """MBTI分布取得"""
        distribution = {}
        for persona in self.personas.values():
            mbti = persona.mbti
            distribution[mbti] = distribution.get(mbti, 0) + 1
        
        return distribution
    
    def export_personas(self) -> str:
        """ペルソナデータエクスポート（年代別特徴含む）"""
        export_data = {
            'export_time': datetime.now().isoformat(),
            'version': '2.0.0',
            'generation_distribution': self.get_generation_distribution(),
            'mbti_distribution': self.get_mbti_distribution(),
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
    
    def simulate_conversation_flow(self, thread_id: int, topic: str) -> List[Dict]:
        """会話フロー・シミュレーション（年代別反応パターン）"""
        """
        特定のトピックに対する年代別反応パターンをシミュレーション
        実際の投稿前にどのような会話になるかを予測
        """
        simulation_results = []
        
        # 年代別反応パターン
        generation_reactions = {
            "1950s-60s": {
                'response_style': 'thoughtful_detailed',
                'reaction_time': 'slow',
                'typical_responses': ['経験談', '人生の教訓', '若い人へのアドバイス']
            },
            "1970s-80s": {
                'response_style': 'practical_business',
                'reaction_time': 'moderate',
                'typical_responses': ['実践的アドバイス', '効率的な方法', '責任ある行動']
            },
            "1990s-2000s": {
                'response_style': 'balanced_friendly',
                'reaction_time': 'moderate',
                'typical_responses': ['共感', 'バランス取れた意見', '多角的視点']
            },
            "2010s-20s": {
                'response_style': 'quick_casual',
                'reaction_time': 'fast',
                'typical_responses': ['感情的反応', 'トレンド言及', '短文コメント']
            }
        }
        
        for generation, pattern in generation_reactions.items():
            gen_personas = [p for p in self.personas.values() if p.generation == generation and p.is_active]
            if gen_personas:
                sample_persona = random.choice(gen_personas)
                
                simulation_results.append({
                    'generation': generation,
                    'persona_name': sample_persona.name,
                    'predicted_style': pattern['response_style'],
                    'estimated_reaction_time': pattern['reaction_time'],
                    'likely_response_types': pattern['typical_responses'],
                    'topic_relevance': self._calculate_topic_relevance(sample_persona, topic)
                })
        
        return simulation_results
    
    def adjust_persona_activity_by_time(self):
        """時間帯による活動レベル調整"""
        """
        現在時刻に基づいて各ペルソナの活動レベルを動的調整
        """
        current_hour = datetime.now().hour
        
        for persona in self.personas.values():
            base_activity = persona.activity_level
            
            # 年代別時間帯調整
            if persona.generation == "1950s-60s":
                if 6 <= current_hour <= 8 or 18 <= current_hour <= 20:
                    persona.activity_level = min(1.0, base_activity * 1.3)
                elif 22 <= current_hour or current_hour <= 5:
                    persona.activity_level = max(0.1, base_activity * 0.3)
                else:
                    persona.activity_level = base_activity
                    
            elif persona.generation == "2010s-20s":
                if 20 <= current_hour <= 23:
                    persona.activity_level = min(1.0, base_activity * 1.4)
                elif 4 <= current_hour <= 10:
                    persona.activity_level = max(0.1, base_activity * 0.4)
                else:
                    persona.activity_level = base_activity
    
    def get_active_personas_by_time(self) -> Dict[str, List[str]]:
        """時間帯別アクティブペルソナ取得"""
        current_hour = datetime.now().hour
        active_by_generation = {}
        
        for generation in ["1950s-60s", "1970s-80s", "1990s-2000s", "2010s-20s"]:
            active_personas = []
            for persona in self.personas.values():
                if persona.generation == generation and persona.is_active:
                    if persona.activity_level > 0.5:  # 活動的なペルソナのみ
                        active_personas.append(persona.name)
            
            active_by_generation[generation] = active_personas
        
        return active_by_generation
