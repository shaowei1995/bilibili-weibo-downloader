import os
import re
import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, List
from urllib.parse import urlparse, parse_qs
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

class VideoDownloader:
    """B站和微博视频下载器"""
    
    def __init__(self, output_dir: str = "./downloads", max_workers: int = 3):
        """
        初始化下载器
        
        Args:
            output_dir: 视频保存目录
            max_workers: 最大并发下载数
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        
        # 标准请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def download_bilibili(self, url: str, quality: str = "high") -> bool:
        """
        下载B站视频
        
        Args:
            url: B站视频链接 (支持 bv/av/番剧等)
            quality: 清晰度 ("high"/"medium"/"low")
        
        Returns:
            bool: 下载是否成功
        """
        try:
            # 提取视频ID
            video_id = self._extract_bilibili_id(url)
            if not video_id:
                print("❌ 无效的B站链接")
                return False
            
            print(f"📥 开始下载B站视频: {video_id}")
            
            # 获取视频信息
            video_info = self._get_bilibili_info(video_id)
            if not video_info:
                return False
            
            # 获取下载链接
            download_url = self._get_bilibili_download_url(
                video_info, 
                quality
            )
            if not download_url:
                print("❌ 无法获取下载链接")
                return False
            
            # 下载视频
            title = video_info.get('title', video_id)
            return self._download_file(download_url, title, source="bilibili")
        
        except Exception as e:
            print(f"❌ B站下载失败: {str(e)}")
            return False
    
    def download_weibo(self, url: str) -> bool:
        """
        下载微博视频
        
        Args:
            url: 微博视频链接
        
        Returns:
            bool: 下载是否成功
        """
        try:
            # 提取微博ID
            weibo_id = self._extract_weibo_id(url)
            if not weibo_id:
                print("❌ 无效的微博链接")
                return False
            
            print(f"📥 开始下载微博视频: {weibo_id}")
            
            # 获取视频页面
            video_url = self._get_weibo_video_url(weibo_id)
            if not video_url:
                print("❌ 无法获取视频链接")
                return False
            
            # 下载视频
            return self._download_file(video_url, weibo_id, source="weibo")
        
        except Exception as e:
            print(f"❌ 微博下载失败: {str(e)}")
            return False
    
    def batch_download(self, urls: List[str], source: str = "auto") -> Dict[str, bool]:
        """
        批量下载视频
        
        Args:
            urls: 视频链接列表
            source: 视频源 ("bilibili"/"weibo"/"auto")
        
        Returns:
            Dict: 下载结果 {url: 成功与否}
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for url in urls:
                if source == "auto":
                    detected_source = self._detect_source(url)
                else:
                    detected_source = source
                
                if detected_source == "bilibili":
                    future = executor.submit(self.download_bilibili, url)
                elif detected_source == "weibo":
                    future = executor.submit(self.download_weibo, url)
                else:
                    results[url] = False
                    continue
                
                futures[future] = url
            
            # 收集结果
            for future in as_completed(futures):
                url = futures[future]
                try:
                    results[url] = future.result()
                except Exception as e:
                    print(f"❌ 处理失败 {url}: {str(e)}")
                    results[url] = False
        
        return results
    
    # ==================== 私有方法 ====================
    
    def _extract_bilibili_id(self, url: str) -> Optional[str]:
        """提取B站视频ID"""
        patterns = [
            r'bilibili\.com/video/(BV[a-zA-Z0-9]+)',
            r'bilibili\.com/video/(av\d+)',
            r'b23\.tv/([a-zA-Z0-9]+)',
            r'BV[a-zA-Z0-9]+',
            r'av\d+'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1) if '(' in pattern else match.group(0)
        
        return None
    
    def _extract_weibo_id(self, url: str) -> Optional[str]:
        """提取微博视频ID"""
        patterns = [
            r'weibo\.com/.*?(\d+)',
            r'weibo\.com/tv/show/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _get_bilibili_info(self, video_id: str) -> Optional[Dict]:
        """获取B站视频信息"""
        try:
            # 注：实际使用需要接入B站API或使用第三方库如 bilibili-api
            # 这里提供基础框架，实际需要根据最新API调整
            api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={video_id}"
            
            response = requests.get(api_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    return data.get('data', {})
            
            return None
        except Exception as e:
            print(f"⚠️ 获取B站信息失败: {str(e)}")
            return None
    
    def _get_bilibili_download_url(self, video_info: Dict, quality: str) -> Optional[str]:
        """获取B站视频下载链接"""
        try:
            # 从视频信息中提取下载链接
            # 注：需要根据视频结构调整
            pages = video_info.get('pages', [])
            if not pages:
                return None
            
            # 获取第一个分P的下载链接
            page = pages[0]
            cid = page.get('cid')
            
            # 获取播放链接
            playurl = self._get_bilibili_playurl(video_info.get('bvid'), cid, quality)
            return playurl
        
        except Exception as e:
            print(f"⚠️ 获取B站下载链接失败: {str(e)}")
            return None
    
    def _get_bilibili_playurl(self, bvid: str, cid: int, quality: str) -> Optional[str]:
        """获取B站播放链接"""
        try:
            quality_map = {
                "high": 112,    # 1080p
                "medium": 80,   # 720p
                "low": 64       # 480p
            }
            
            qn = quality_map.get(quality, 80)
            api_url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn={qn}"
            
            response = requests.get(api_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    durl = data.get('data', {}).get('durl', [])
                    if durl:
                        return durl[0].get('url')
            
            return None
        except Exception as e:
            print(f"⚠️ 获取B站播放链接失败: {str(e)}")
            return None
    
    def _get_weibo_video_url(self, weibo_id: str) -> Optional[str]:
        """获取微博视频下载链接"""
        try:
            # 微博视频页面
            page_url = f"https://weibo.com/tv/show/{weibo_id}"
            
            response = requests.get(page_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                # 从页面中提取视频URL
                # 注：微博经常改变结构，可能需要使用Selenium或其他方案
                patterns = [
                    r'"playPageUrl":"([^"]+)',
                    r'<video[^>]*src="([^"]+)',
                    r'"mp4Url":"([^"]+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        url = match.group(1)
                        # 处理转义符
                        url = url.replace('\\/', '/')
                        return url
            
            return None
        except Exception as e:
            print(f"⚠️ 获取微博视频链接失败: {str(e)}")
            return None
    
    def _download_file(
        self, 
        url: str, 
        title: str, 
        source: str,
        chunk_size: int = 8192
    ) -> bool:
        """
        下载文件并保存为MP4
        
        Args:
            url: 文件URL
            title: 文件标题
            source: 视频源
            chunk_size: 分块大小
        
        Returns:
            bool: 下载是否成功
        """
        try:
            # 清理文件名
            safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
            output_path = self.output_dir / f"{safe_title}.mp4"
            
            print(f"⬇️  正在下载: {safe_title}")
            
            # 发起请求
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=30, 
                stream=True
            )
            response.raise_for_status()
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            # 下载并保存
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 显示进度
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self._show_progress(progress, downloaded, total_size)
            
            print(f"\n✅ 下载完成: {output_path}")
            return True
        
        except Exception as e:
            print(f"❌ 文件下载失败: {str(e)}")
            return False
    
    def _show_progress(self, progress: float, downloaded: int, total: int):
        """显示下载进度"""
        bar_length = 40
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        size_mb = downloaded / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        
        print(
            f"\r进度: |{bar}| {progress:.1f}% "
            f"({size_mb:.1f}MB / {total_mb:.1f}MB)",
            end='',
            flush=True
        )
    
    def _detect_source(self, url: str) -> str:
        """检测视频源"""
        if 'bilibili' in url or 'b23' in url:
            return "bilibili"
        elif 'weibo' in url:
            return "weibo"
        return "unknown"


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 创建下载器
    downloader = VideoDownloader(output_dir="./videos", max_workers=2)
    
    # 单个下载示例
    # downloader.download_bilibili("https://www.bilibili.com/video/BV1xx411c7mD")
    # downloader.download_weibo("https://weibo.com/tv/show/1234567890")
    
    # 批量下载示例
    urls = [
        # "https://www.bilibili.com/video/BVxxxxxx",
        # "https://weibo.com/tv/show/1234567890",
    ]
    
    results = downloader.batch_download(urls, source="auto")
    
    # 打印结果
    print("\n" + "="*50)
    print("下载结果统计:")
    print("="*50)
    for url, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{status}: {url}")
