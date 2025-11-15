#!/usr/bin/env python3
"""
增强的视频URL提取调试脚本
帮助诊断小红书视频下载链接提取问题
"""
import asyncio
import sys
import os
import json

# 添加项目路径
sys.path.insert(0, '/home/user/first_job')

# 配置日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def debug_extraction(video_url: str):
    """调试视频URL提取过程"""
    from app.services.xiaohongshu_api import XiaohongshuAPI

    print("=" * 100)
    print("小红书视频URL提取调试工具")
    print("=" * 100)
    print(f"\n测试URL: {video_url}\n")

    # 创建API实例
    api = XiaohongshuAPI()

    try:
        # 第1步：提取视频ID
        print("📋 步骤 1: 提取视频ID...")
        video_id = api._extract_video_id(video_url)
        if video_id:
            print(f"   ✅ 成功提取视频ID: {video_id}")
        else:
            print(f"   ❌ 未能提取视频ID")
            return

        # 第2步：获取页面内容（开启调试模式）
        print("\n📋 步骤 2: 获取小红书页面...")
        video_info = await api.get_video_info(video_url, debug=True)

        # 第3步：分析保存的调试文件
        print("\n📋 步骤 3: 分析调试数据...")
        debug_dir = "/tmp/xiaohongshu_debug"

        # 检查HTML文件
        html_file = f"{debug_dir}/{video_id}_page.html"
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            print(f"   ✅ HTML文件: {html_file}")
            print(f"      大小: {len(html_content)} 字符")
            print(f"      包含__INITIAL_STATE__: {'window.__INITIAL_STATE__' in html_content}")
        else:
            print(f"   ❌ 未找到HTML文件")

        # 检查JSON文件
        json_file = f"{debug_dir}/{video_id}_initial_state.json"
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            print(f"\n   ✅ JSON文件: {json_file}")
            print(f"      顶层键: {list(state_data.keys())}")

            # 分析note结构
            if 'note' in state_data:
                note_obj = state_data['note']
                print(f"      note的键: {list(note_obj.keys())}")

                # 检查 noteDetailMap
                if 'noteDetailMap' in note_obj:
                    note_detail_map = note_obj['noteDetailMap']
                    print(f"      noteDetailMap条目数: {len(note_detail_map)}")

                    for note_id, note_info in note_detail_map.items():
                        print(f"\n      📝 笔记 {note_id}:")
                        if 'note' in note_info:
                            n = note_info['note']
                            print(f"         类型: {n.get('type', 'unknown')}")
                            print(f"         标题: {n.get('title', n.get('desc', '')[:50])}")
                            print(f"         包含video: {bool(n.get('video'))}")

                            if n.get('video'):
                                video = n['video']
                                print(f"         video的键: {list(video.keys())}")

                                # 检查各种可能的视频URL字段
                                url_fields = ['masterUrl', 'playAddr', 'videoUrl', 'url']
                                for field in url_fields:
                                    if field in video:
                                        print(f"         video.{field}: 存在")

                                # 检查media.stream.h264
                                if 'media' in video:
                                    media = video['media']
                                    if 'stream' in media:
                                        stream = media['stream']
                                        if 'h264' in stream and stream['h264']:
                                            h264 = stream['h264'][0]
                                            print(f"         media.stream.h264[0]的键: {list(h264.keys())}")

                                # 检查consumer
                                if 'consumer' in video:
                                    consumer = video['consumer']
                                    if 'originVideoKey' in consumer:
                                        print(f"         consumer.originVideoKey: 存在")

                # 检查直接的note路径
                if 'note' in note_obj and isinstance(note_obj.get('note'), dict):
                    print(f"\n      📝 直接note路径:")
                    direct_note = note_obj['note']
                    print(f"         类型: {direct_note.get('type', 'unknown')}")
                    print(f"         包含video: {bool(direct_note.get('video'))}")
        else:
            print(f"   ❌ 未找到JSON文件")

        # 第4步：显示提取结果
        print("\n" + "=" * 100)
        print("📋 步骤 4: 提取结果")
        print("=" * 100)
        print(f"\n视频ID: {video_info.get('video_id')}")
        print(f"标题: {video_info.get('title')}")
        print(f"作者: {video_info.get('author')}")
        print(f"描述: {video_info.get('desc', '')[:100]}...")
        print(f"时长: {video_info.get('duration')}秒")
        print(f"分辨率: {video_info.get('width')}x{video_info.get('height')}")

        if video_info.get('video_url'):
            print(f"\n✅ 成功提取视频URL!")
            print(f"\n完整URL:")
            print(f"{video_info.get('video_url')}")
        else:
            print(f"\n❌ 未能提取视频URL")
            print(f"\n💡 建议:")
            print(f"   1. 检查上面的JSON数据结构分析")
            print(f"   2. 查看调试文件: {debug_dir}/")
            print(f"   3. 确认小红书页面结构是否发生变化")
            print(f"   4. 尝试提供Cookie以访问需要登录的内容")

        print("\n" + "=" * 100)

        # 保存诊断报告
        report_file = f"{debug_dir}/{video_id}_diagnostic_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"视频URL提取诊断报告\n")
            f.write(f"=" * 80 + "\n\n")
            f.write(f"测试URL: {video_url}\n")
            f.write(f"视频ID: {video_id}\n")
            f.write(f"提取结果: {'成功' if video_info.get('video_url') else '失败'}\n")
            f.write(f"\n完整结果:\n")
            f.write(json.dumps(video_info, ensure_ascii=False, indent=2))

        print(f"\n📄 诊断报告已保存: {report_file}\n")

        return video_info

    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """主函数"""
    # 默认测试URL
    default_url = "https://www.xiaohongshu.com/explore/6909e6c1000000000300ea0e"

    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        print(f"使用默认测试URL")
        print(f"提示: 可以通过命令行参数指定URL: python {sys.argv[0]} <URL>\n")
        test_url = default_url

    await debug_extraction(test_url)


if __name__ == "__main__":
    asyncio.run(main())
