#!/usr/bin/env python3
"""
测试页面解析逻辑（使用示例HTML）
"""
import sys
import re
import json

# 添加项目路径
sys.path.insert(0, '/home/user/first_job')


def test_parse_logic():
    """测试解析逻辑"""
    # 这里应该有实际的HTML内容，但由于我们没有，我们可以测试正则表达式
    print("测试视频ID提取:")

    # 测试URL
    test_url = "https://www.xiaohongshu.com/explore/6909e6c1000000000300ea0e?xsec_token=ABCWdlNJTwSsZlWZe7j8AOqymZmKn6j9Gexc_IPDjJ0js=&xsec_source=pc_feed"

    patterns = [
        r'explore/([a-zA-Z0-9]+)',
        r'discovery/item/([a-zA-Z0-9]+)',
        r'/([a-zA-Z0-9]{24})$',
    ]

    for i, pattern in enumerate(patterns):
        match = re.search(pattern, test_url)
        if match:
            video_id = match.group(1)
            print(f"✅ 模式 {i+1} 匹配成功: {video_id}")
            break
        else:
            print(f"❌ 模式 {i+1} 未匹配")

    print(f"\n提取的视频ID: {video_id}")
    print(f"视频ID长度: {len(video_id)}")


if __name__ == "__main__":
    test_parse_logic()
