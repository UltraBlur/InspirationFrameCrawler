# InspirationFrameCrawler

这是一个Python脚本，可以用来自动化地从豆瓣和IMDB网站获取电影的详细信息。

## 功能

- **自动搜索电影ID**：根据电影名称自动从豆瓣网站搜索并获取电影的ID。
- **抓取电影详细信息**：根据豆瓣ID爬取电影的详细信息，包括导演、编剧、类型、制片国家等。
- **抓取IMDB信息**：从IMDB获取更多电影信息，如摄影师、技术规格等。

## 使用方法

1. 安装依赖：

   确保您的Python环境已安装以下依赖：

   ```bash
   pip install pandas requests beautifulsoup4 selenium
   ```
2. 配置WebDriver：
   脚本使用Selenium的WebDriver来处理网页加载和解析，您需要下载与您的浏览器匹配的WebDriver。
3. 准备输入文件：
   修改 Crawler.py 中的文件路径，准备一个包含影片中文名称的 .csv。或者可以跳过ID搜索，直接输入一个包含豆瓣影片 ID 的 .csv 文件。
4. 运行脚本：
   运行 `Crawler.py` 来启动爬虫。
5. 查看结果：
   爬取的结果将会输出在指定目录中。

## 更新日志

* 0.1.0 初始化版本，实现基础功能。

## 许可

该项目根据MIT许可证发布。
