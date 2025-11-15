"""
小红书API接口封装
"""
import httpx
import json
import re
from typing import Dict, List, Optional
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class XiaohongshuAPI:
    """小红书API封装类"""

    def __init__(self, cookies: Optional[str] = None):
        """
        初始化
        Args:
            cookies: Cookie字符串(JSON格式)
        """
        self.base_url = settings.XHS_BASE_URL
        self.api_base_url = settings.XHS_API_BASE_URL
        self.cookies = self._parse_cookies(cookies) if cookies else {}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": self.base_url,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def _parse_cookies(self, cookies_str: str) -> Dict:
        """解析Cookie字符串"""
        try:
            return json.loads(cookies_str)
        except json.JSONDecodeError:
            # 尝试解析键值对格式的Cookie
            cookies = {}
            for item in cookies_str.split(";"):
                if "=" in item:
                    key, value = item.strip().split("=", 1)
                    cookies[key] = value
            return cookies

    def set_cookies(self, cookies: str):
        """设置Cookie"""
        self.cookies = self._parse_cookies(cookies)

    async def get_video_info(self, video_url: str, debug: bool = False) -> Dict:
        """
        获取视频信息
        Args:
            video_url: 视频URL
            debug: 是否开启调试模式（保存HTML和JSON数据到/tmp目录）
        Returns:
            视频信息字典
        """
        try:
            # 从URL中提取视频ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                raise ValueError("无法从URL中提取视频ID")

            logger.info(f"提取到视频ID: {video_id}")

            async with httpx.AsyncClient(cookies=self.cookies, headers=self.headers, timeout=settings.TIMEOUT) as client:
                # 获取视频详情页
                logger.info(f"正在请求视频页面: {video_url}")
                response = await client.get(video_url, follow_redirects=True)
                response.raise_for_status()

                logger.info(f"页面请求成功，状态码: {response.status_code}, 内容长度: {len(response.text)}")

                # 调试模式：保存HTML内容
                if debug:
                    import os
                    debug_dir = "/tmp/xiaohongshu_debug"
                    os.makedirs(debug_dir, exist_ok=True)

                    html_file = f"{debug_dir}/{video_id}_page.html"
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    logger.info(f"调试模式：已保存HTML到 {html_file}")

                # 解析页面内容获取视频信息
                video_info = self._parse_video_page(response.text, video_id, debug=debug)

                # 调试模式：保存解析结果
                if debug:
                    import json as json_module
                    result_file = f"{debug_dir}/{video_id}_result.json"
                    with open(result_file, 'w', encoding='utf-8') as f:
                        json_module.dump(video_info, f, ensure_ascii=False, indent=2)
                    logger.info(f"调试模式：已保存解析结果到 {result_file}")

                return video_info

        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        从URL中提取视频ID
        支持格式:
        - https://www.xiaohongshu.com/explore/视频ID
        - https://xhslink.com/短链接
        """
        patterns = [
            r'explore/([a-zA-Z0-9]+)',
            r'discovery/item/([a-zA-Z0-9]+)',
            r'/([a-zA-Z0-9]{24})$',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _parse_video_page(self, html: str, video_id: str, debug: bool = False) -> Dict:
        """
        解析视频页面获取信息
        注意: 这是一个简化的实现,实际需要根据小红书页面结构进行调整
        """
        # 尝试多种正则模式来提取__INITIAL_STATE__数据
        state_patterns = [
            r'<script>window\.__INITIAL_STATE__=({.*?})</script>',
            r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>',
            r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*;',
            r'__INITIAL_STATE__\s*=\s*({[\s\S]*?})\s*(?:</script>|;)',
        ]

        state_data = None
        for i, pattern in enumerate(state_patterns):
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1).replace(':undefined', ':null').replace(':null,', ':"",')
                    state_data = json.loads(json_str)
                    logger.info(f"成功使用模式 {i+1} 匹配到 __INITIAL_STATE__")

                    # 调试模式：保存原始JSON
                    if debug:
                        import os
                        debug_dir = "/tmp/xiaohongshu_debug"
                        os.makedirs(debug_dir, exist_ok=True)

                        json_file = f"{debug_dir}/{video_id}_initial_state.json"
                        with open(json_file, 'w', encoding='utf-8') as f:
                            f.write(json.dumps(state_data, ensure_ascii=False, indent=2))
                        logger.info(f"调试模式：已保存 __INITIAL_STATE__ 到 {json_file}")

                    break
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON解析失败，尝试下一个模式: {e}")
                    continue

        if state_data:
            try:
                # 解析视频信息
                note_data = state_data.get('note', {}).get('noteDetailMap', {})
                logger.info(f"noteDetailMap 包含 {len(note_data)} 个条目")

                if note_data:
                    for note_id, note_info in note_data.items():
                        note = note_info.get('note', {})
                        video = note.get('video', {})

                        logger.info(f"正在解析笔记 {note_id}, 类型: {note.get('type', 'unknown')}")

                        # 尝试多种方式提取视频URL
                        video_url = ''

                        # 方式1: 从 media.stream.h264 获取
                        if video:
                            media = video.get('media', {})
                            stream = media.get('stream', {})
                            h264_list = stream.get('h264', [])

                            logger.info(f"h264 列表长度: {len(h264_list)}")

                            if h264_list and len(h264_list) > 0:
                                # 尝试获取 masterUrl
                                video_url = h264_list[0].get('masterUrl', '')

                                # 如果 masterUrl 为空，尝试 backupUrls
                                if not video_url:
                                    backup_urls = h264_list[0].get('backupUrls', [])
                                    if backup_urls and len(backup_urls) > 0:
                                        video_url = backup_urls[0]
                                        logger.info("从 backupUrls 获取视频链接")

                                # 如果还是为空，尝试直接从 stream 获取
                                if not video_url and 'url' in h264_list[0]:
                                    video_url = h264_list[0].get('url', '')
                                    logger.info("从 h264[0].url 获取视频链接")

                            # 方式2: 尝试从 video.consumer.originVideoKey 获取
                            if not video_url:
                                consumer = video.get('consumer', {})
                                origin_video_key = consumer.get('originVideoKey', '')
                                if origin_video_key:
                                    # 通常需要拼接CDN域名
                                    video_url = f"https://sns-video-bd.xhscdn.com/{origin_video_key}"
                                    logger.info("从 originVideoKey 构建视频链接")

                            # 方式3: 尝试从 video.masterUrl 直接获取
                            if not video_url and 'masterUrl' in video:
                                video_url = video.get('masterUrl', '')
                                logger.info("从 video.masterUrl 获取视频链接")

                        if video_url:
                            logger.info(f"成功提取视频URL: {video_url[:100]}...")
                        else:
                            logger.warning("未能提取视频URL，所有方法均失败")

                        return {
                            'video_id': video_id,
                            'title': note.get('title', ''),
                            'desc': note.get('desc', ''),
                            'author': note.get('user', {}).get('nickname', ''),
                            'author_id': note.get('user', {}).get('userId', ''),
                            'cover_url': video.get('cover', {}).get('url', '') if video else '',
                            'video_url': video_url,
                            'duration': video.get('duration', 0) if video else 0,
                            'width': video.get('width', 0) if video else 0,
                            'height': video.get('height', 0) if video else 0,
                            'parts': self._extract_video_parts(video) if video else [],
                            'available_qualities': ['hd', 'sd', 'ld'],  # 示例
                        }
            except Exception as e:
                logger.error(f"解析视频页面失败: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.warning("未找到 __INITIAL_STATE__ 数据")

        # 如果解析失败,返回基本信息
        logger.warning(f"返回默认视频信息，video_id: {video_id}")
        return {
            'video_id': video_id,
            'title': '未知标题',
            'author': '未知作者',
            'cover_url': '',
            'video_url': '',
            'parts': [],
            'available_qualities': ['hd'],
        }

    def _extract_video_parts(self, video_data: Dict) -> List[Dict]:
        """提取视频分P信息"""
        # 小红书通常没有分P,这里返回单个视频信息
        parts = []
        if video_data:
            parts.append({
                'part': 1,
                'title': '正片',
                'duration': video_data.get('duration', 0),
            })
        return parts

    async def get_favorites(self, user_id: str) -> List[Dict]:
        """
        获取用户收藏夹列表
        Args:
            user_id: 用户ID
        Returns:
            收藏夹列表
        """
        try:
            async with httpx.AsyncClient(cookies=self.cookies, headers=self.headers, timeout=settings.TIMEOUT) as client:
                # API endpoint (需要根据实际情况调整)
                url = f"{self.api_base_url}/api/sns/web/v1/user/favlist"
                params = {"user_id": user_id}

                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                return data.get('data', {}).get('list', [])

        except Exception as e:
            logger.error(f"获取收藏夹列表失败: {e}")
            return []

    async def get_favorite_videos(self, favorite_id: str, page: int = 1, page_size: int = 20) -> Dict:
        """
        获取收藏夹中的视频列表
        Args:
            favorite_id: 收藏夹ID
            page: 页码
            page_size: 每页数量
        Returns:
            视频列表数据
        """
        try:
            async with httpx.AsyncClient(cookies=self.cookies, headers=self.headers, timeout=settings.TIMEOUT) as client:
                url = f"{self.api_base_url}/api/sns/web/v1/board/notes"
                params = {
                    "board_id": favorite_id,
                    "page": page,
                    "page_size": page_size,
                }

                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                return data.get('data', {})

        except Exception as e:
            logger.error(f"获取收藏夹视频失败: {e}")
            return {'list': [], 'has_more': False}

    async def check_video_valid(self, video_id: str) -> bool:
        """
        检查视频是否有效(未被删除)
        Args:
            video_id: 视频ID
        Returns:
            是否有效
        """
        try:
            video_url = f"{self.base_url}/explore/{video_id}"
            async with httpx.AsyncClient(cookies=self.cookies, headers=self.headers, timeout=settings.TIMEOUT) as client:
                response = await client.get(video_url, follow_redirects=True)
                # 如果返回404或页面不存在,则视频失效
                return response.status_code == 200 and '404' not in response.text

        except Exception as e:
            logger.error(f"检查视频有效性失败: {e}")
            return False

    async def validate_cookies(self) -> bool:
        """
        验证Cookie是否有效
        Returns:
            Cookie是否有效
        """
        try:
            # 如果没有cookies,直接返回False
            if not self.cookies:
                return False

            async with httpx.AsyncClient(cookies=self.cookies, headers=self.headers, timeout=settings.TIMEOUT) as client:
                # 尝试访问小红书主页,检查是否包含登录标识
                response = await client.get(self.base_url, follow_redirects=True)

                if response.status_code != 200:
                    return False

                # 检查响应中是否包含登录状态的标识
                # 如果页面包含登录后才有的元素,说明cookie有效
                # 小红书登录后页面会包含用户信息相关的JavaScript变量
                content = response.text

                # 检查是否包含用户登录状态的标识
                # 登录后通常会有 window.__INITIAL_STATE__ 且包含用户信息
                if 'window.__INITIAL_STATE__' in content and '"user":' in content:
                    return True

                # 也可以尝试访问API端点验证
                api_response = await client.get(
                    f"{self.api_base_url}/api/sns/web/v1/user/selfinfo",
                    follow_redirects=True
                )

                # 如果API返回200且有数据,说明认证成功
                if api_response.status_code == 200:
                    try:
                        data = api_response.json()
                        # 检查返回数据是否包含用户信息
                        if data.get('success') or data.get('data'):
                            return True
                    except:
                        pass

                return False

        except Exception as e:
            logger.error(f"验证Cookie失败: {e}")
            return False

    async def get_download_url(self, video_id: str, quality: str = 'hd') -> Optional[str]:
        """
        获取视频下载链接
        Args:
            video_id: 视频ID
            quality: 画质 (hd/sd/ld)
        Returns:
            下载链接
        """
        try:
            video_info = await self.get_video_info(f"{self.base_url}/explore/{video_id}")
            return video_info.get('video_url')

        except Exception as e:
            logger.error(f"获取下载链接失败: {e}")
            return None
