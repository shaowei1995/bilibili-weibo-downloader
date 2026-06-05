#!/usr/bin/env python3
"""
视频下载器使用示例
"""

from video_downloader import VideoDownloader

def main():
    # 创建下载器实例
    downloader = VideoDownloader(
        output_dir="./downloads",
        max_workers=3
    )
    
    print("=" * 60)
    print("🎬 视频下载器 - 支持B站和微博")
    print("=" * 60)
    
    while True:
        print("\n请选择操作:")
        print("1. 下载B站视频")
        print("2. 下载微博视频")
        print("3. 批量下载")
        print("4. 退出")
        
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == "1":
            url = input("请输入B站视频链接: ").strip()
            quality = input("清晰度 (high/medium/low, 默认high): ").strip() or "high"
            downloader.download_bilibili(url, quality)
        
        elif choice == "2":
            url = input("请输入微博视频链接: ").strip()
            downloader.download_weibo(url)
        
        elif choice == "3":
            print("\n输入视频链接，每行一个，输入 'done' 完成:")
            urls = []
            while True:
                url = input().strip()
                if url.lower() == 'done':
                    break
                if url:
                    urls.append(url)
            
            if urls:
                results = downloader.batch_download(urls)
                print("\n" + "=" * 60)
                print("下载结果:")
                print("=" * 60)
                for url, success in results.items():
                    status = "✅ 成功" if success else "❌ 失败"
                    print(f"{status}: {url}")
        
        elif choice == "4":
            print("👋 再见！")
            break
        
        else:
            print("❌ 无效选项，请重试")

if __name__ == "__main__":
    main()
