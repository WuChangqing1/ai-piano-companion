"""测试手型检测模块"""
from ai_models.hand_tracker import detect_hand_issues
from pathlib import Path

issues = detect_hand_issues(Path("test_data/test.mp4"))
print(f"检测到 {len(issues)} 个手型问题:")
for i in issues:
    print(f"  {i['measure']}小节 {i['description']}")
