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

    async def get_video_info(self, video_url: str) -> Dict:
        """
        获取视频信息
        Args:
            video_url: 视频URL
        Returns:
            视频信息字典
        """
        try:
            # 从URL中提取视频ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                raise ValueError("无法从URL中提取视频ID")

            async with httpx.AsyncClient(cookies=self.cookies, headers=self.headers, timeout=settings.TIMEOUT) as client:
                # 获取视频详情页
                response = await client.get(video_url, follow_redirects=True)
                response.raise_for_status()

                # 解析页面内容获取视频信息
                video_info = self._parse_video_page(response.text, video_id)
                return video_info

        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
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

    def _parse_video_page(self, html: str, video_id: str) -> Dict:
        """
        解析视频页面获取信息
        注意: 这是一个简化的实现,实际需要根据小红书页面结构进行调整
        """
        # 从HTML中提取__INITIAL_STATE__数据
        state_pattern = r'<script>window\.__INITIAL_STATE__=({.*?})</script>'
        match = re.search(state_pattern, html, re.DOTALL)

        if match:
            try:
                state_data = json.loads(match.group(1).replace(':undefined', ':null'))
                # 解析视频信息
                note_data = state_data.get('note', {}).get('noteDetailMap', {})

                if note_data:
                    for note_id, note_info in note_data.items():
                        note = note_info.get('note', {})
                        video = note.get('video', {})

                        return {
                            'video_id': video_id,
                            'title': note.get('title', ''),
                            'desc': note.get('desc', ''),
                            'author': note.get('user', {}).get('nickname', ''),
                            'author_id': note.get('user', {}).get('userId', ''),
                            'cover_url': video.get('cover', {}).get('url', ''),
                            'video_url': video.get('media', {}).get('stream', {}).get('h264', [{}])[0].get('masterUrl', ''),
                            'duration': video.get('duration', 0),
                            'width': video.get('width', 0),
                            'height': video.get('height', 0),
                            'parts': self._extract_video_parts(video),
                            'available_qualities': ['hd', 'sd', 'ld'],  # 示例
                        }
            except Exception as e:
                logger.error(f"解析视频页面失败: {e}")

        # 如果解析失败,返回基本信息
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
