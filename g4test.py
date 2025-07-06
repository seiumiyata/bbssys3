import g4f
import time
import json
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

class G4FProviderTester:
    def __init__(self):
        # デバッグログを有効化
        g4f.debug.logging = True
        g4f.debug.version_check = False
        
        # テスト用のメッセージ
        self.test_message = "Hello, how are you?"
        
        # 結果を格納する辞書
        self.results = {
            'successful': [],
            'failed': [],
            'test_time': datetime.now().isoformat()
        }
        
        # 主要なモデル一覧
        self.models_to_test = [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-0613",
            "claude-2",
            "claude-instant",
            "palm",
            "llama-2-7b",
            "llama-2-13b"
        ]
    
    def get_all_providers(self):
        """利用可能なすべてのプロバイダを取得"""
        try:
            # 動作中のプロバイダのみを取得
            providers = [
                provider for provider in g4f.Provider.__providers__ 
                if hasattr(provider, 'working') and provider.working
            ]
            print(f"検出されたプロバイダ数: {len(providers)}")
            return providers
        except Exception as e:
            print(f"プロバイダ取得エラー: {e}")
            return []
    
    def test_provider_model_combination(self, provider, model, timeout=30):
        """プロバイダとモデルの組み合わせをテスト"""
        start_time = time.time()
        
        try:
            # 接続テスト実行
            response = g4f.ChatCompletion.create(
                model=model,
                provider=provider,
                messages=[{"role": "user", "content": self.test_message}],
                timeout=timeout
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # レスポンスが有効かチェック
            if response and len(str(response).strip()) > 0:
                return {
                    'status': 'success',
                    'provider': provider.__name__,
                    'model': model,
                    'response_time': round(response_time, 2),
                    'response_preview': str(response)[:100] + "..." if len(str(response)) > 100 else str(response)
                }
            else:
                return {
                    'status': 'failed',
                    'provider': provider.__name__,
                    'model': model,
                    'error': 'Empty response',
                    'response_time': round(response_time, 2)
                }
                
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                'status': 'failed',
                'provider': provider.__name__,
                'model': model,
                'error': str(e),
                'response_time': round(response_time, 2)
            }
    
    def run_comprehensive_test(self, max_workers=5):
        """包括的なテストを実行"""
        providers = self.get_all_providers()
        
        if not providers:
            print("利用可能なプロバイダが見つかりませんでした。")
            return
        
        print(f"\n=== G4F プロバイダ接続テスト開始 ===")
        print(f"テスト対象プロバイダ数: {len(providers)}")
        print(f"テスト対象モデル数: {len(self.models_to_test)}")
        print(f"総テスト数: {len(providers) * len(self.models_to_test)}")
        print("=" * 50)
        
        # 並行処理でテスト実行
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # すべての組み合わせのテストタスクを作成
            future_to_test = {}
            
            for provider in providers:
                for model in self.models_to_test:
                    future = executor.submit(
                        self.test_provider_model_combination, 
                        provider, 
                        model
                    )
                    future_to_test[future] = (provider.__name__, model)
            
            # 結果を収集
            completed_tests = 0
            total_tests = len(future_to_test)
            
            for future in as_completed(future_to_test):
                provider_name, model = future_to_test[future]
                completed_tests += 1
                
                try:
                    result = future.result()
                    
                    if result['status'] == 'success':
                        self.results['successful'].append(result)
                        print(f"✅ [{completed_tests}/{total_tests}] {provider_name} + {model} - 成功 ({result['response_time']}s)")
                    else:
                        self.results['failed'].append(result)
                        print(f"❌ [{completed_tests}/{total_tests}] {provider_name} + {model} - 失敗: {result['error'][:50]}...")
                        
                except Exception as e:
                    error_result = {
                        'status': 'failed',
                        'provider': provider_name,
                        'model': model,
                        'error': f"テスト実行エラー: {str(e)}",
                        'response_time': 0
                    }
                    self.results['failed'].append(error_result)
                    print(f"❌ [{completed_tests}/{total_tests}] {provider_name} + {model} - 実行エラー")
    
    def display_results(self):
        """テスト結果を表示"""
        successful_count = len(self.results['successful'])
        failed_count = len(self.results['failed'])
        total_count = successful_count + failed_count
        
        print(f"\n" + "=" * 60)
        print(f"🎯 テスト結果サマリー")
        print(f"=" * 60)
        print(f"総テスト数: {total_count}")
        print(f"成功: {successful_count} ({successful_count/total_count*100:.1f}%)")
        print(f"失敗: {failed_count} ({failed_count/total_count*100:.1f}%)")
        
        if successful_count > 0:
            print(f"\n✅ 接続成功した組み合わせ ({successful_count}件):")
            print("-" * 60)
            
            for result in sorted(self.results['successful'], key=lambda x: x['response_time']):
                print(f"📍 {result['provider']} + {result['model']}")
                print(f"   応答時間: {result['response_time']}秒")
                print(f"   応答例: {result['response_preview']}")
                print()
        
        if failed_count > 0:
            print(f"\n❌ 接続失敗した組み合わせ (上位10件):")
            print("-" * 60)
            
            # エラーの種類別に集計
            error_types = {}
            for result in self.results['failed']:
                error_key = result['error'][:50]
                if error_key not in error_types:
                    error_types[error_key] = []
                error_types[error_key].append(f"{result['provider']}+{result['model']}")
            
            for error, combinations in list(error_types.items())[:10]:
                print(f"🔸 エラー: {error}")
                print(f"   該当組み合わせ数: {len(combinations)}")
                print(f"   例: {', '.join(combinations[:3])}")
                print()
    
    def save_results_to_file(self, filename="g4f_test_results.json"):
        """結果をJSONファイルに保存"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"📁 結果を {filename} に保存しました。")
        except Exception as e:
            print(f"ファイル保存エラー: {e}")
    
    def get_recommended_combinations(self):
        """推奨される組み合わせを取得"""
        if not self.results['successful']:
            return []
        
        # 応答時間でソートして上位を推奨
        sorted_results = sorted(
            self.results['successful'], 
            key=lambda x: x['response_time']
        )
        
        return sorted_results[:5]  # 上位5つを推奨

# メイン実行部分
def main():
    """メイン関数"""
    print("🚀 G4F プロバイダ接続テストツールを開始します...")
    
    # テスターインスタンスを作成
    tester = G4FProviderTester()
    
    # 包括的テストを実行
    tester.run_comprehensive_test(max_workers=3)  # 並行数を調整可能
    
    # 結果を表示
    tester.display_results()
    
    # 推奨組み合わせを表示
    recommended = tester.get_recommended_combinations()
    if recommended:
        print(f"\n🌟 推奨される組み合わせ (応答速度順):")
        print("-" * 60)
        for i, result in enumerate(recommended, 1):
            print(f"{i}. {result['provider']} + {result['model']} ({result['response_time']}秒)")
    
    # 結果をファイルに保存
    tester.save_results_to_file()
    
    print(f"\n🎉 テスト完了！")

# プログラム実行
if __name__ == "__main__":
    main()
