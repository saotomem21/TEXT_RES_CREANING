import unittest
import pandas as pd
from pathlib import Path
from text_res_creaning import clean_csv

class TestTextCleaning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_input = "test_input.csv"
        cls.test_output = "test_output.csv"
        
    def test_clean_csv(self):
        # テスト実行
        result = clean_csv(self.test_input, self.test_output)
        self.assertTrue(result)
        
        # 結果の検証
        self.assertTrue(Path(self.test_output).exists())
        
        df = pd.read_csv(self.test_output)
        self.assertIn("レス番号", df.columns)
        self.assertIn("内容", df.columns)
        
        # 各ケースの検証
        test_cases = [
            (0, "テストメッセージ1 [FACE_TOKEN_1]"),
            (1, "リンク付きメッセージ"),
            (2, "アンカー付きメッセージ"),
            (3, "メッセージ"),
            (4, "テストメッセージ"),
            (5, "空白文字付き メッセージ"),
            (6, "顔文字バリエーション [FACE_TOKEN_1]"),
            (7, "[FACE_TOKEN_2]")
        ]
        
        for idx, expected in test_cases:
            with self.subTest(case=idx):
                self.assertEqual(df.iloc[idx]["内容"], expected)

if __name__ == "__main__":
    unittest.main()
