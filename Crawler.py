import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time

from MyLog import MyLog


title_path = r'Test/title.csv'
douban_id_path = r'Test/input.csv'
output_path = r'Test/output.csv'


def title_to_douban_id(title_path, douban_id_path):
    """_summary_
    
        输入csv包含影片中/英文名称，自动从豆瓣搜索，获得豆瓣ID
    
    """ 
    # Set up the webdriver
    driver = webdriver.Chrome()

    # Read the CSV file containing movie names
    df = pd.read_csv(title_path)
    movie_titles = df['title'].tolist()

    # List to hold the records
    records = []

    # Iterate over each movie title
    for title in movie_titles:
        search_url = "https://movie.douban.com/subject_search?search_text=" + title
        driver.get(search_url)
        time.sleep(1)  # Allow time for the page to load

        # Parse HTML with BeautifulSoup
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        link_element = soup.select_one('a.title-text')

        if link_element:
            url = link_element.get('href')
            douban_id = url.split('/')[-2]  # Extract the Douban ID from the URL
            records.append({'movie_name': title, 'douban_id': douban_id})
        else:
            records.append({'movie_name': title, 'douban_id': ''})
    
    # Close the browser
    driver.close()

    # Create a DataFrame from the records and write it to CSV
    result_df = pd.DataFrame(records)
    result_df.to_csv(douban_id_path, index=False)
    

class MovieCrawler:
    """_summary_
    
        爬虫主体
    
    """
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.movie_data = []
        self.log = MyLog('MovieCrawler').get_logger()
    
        
    def read_douban_ids(self):
        self.log.info("Reading DouBan IDs from CSV")
        df = pd.read_csv(self.csv_file)
        self.douban_ids = df['douban_id'].tolist()
        self.log.debug(f"Douban IDs read: {self.douban_ids}")

    def scrape_movie_data(self):
        
        self.log.info("Starting to scrape movie data")
        
        """
        
        抓取逻辑：根据豆瓣编号，获得中文信息以及IMDB ID。
        
        
        """
        
        headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}
        
        for douban_id in self.douban_ids:
            
            """
                豆瓣部分
                
            """
            # 构建豆瓣电影 URL
            douban_url = f'https://movie.douban.com/subject/{douban_id}/'
            
            # 发送 HTTP 请求并获取网页内容
            douban_response = requests.get(douban_url, headers=headers)
            douban_response.raise_for_status()
            douban_response.encoding = 'utf-8'
            douban_soup = BeautifulSoup(douban_response.text, 'html.parser')
            
            # Attempt to find the 'info' element, get text, and split by newlines
            douban_info_block = douban_soup.find(attrs={'id': 'info'})

            # Check if the 'info' element was successfully found
            if douban_info_block:
                douban_info = douban_info_block.text.split('\n')
                douban_info = [line.strip() for line in douban_info if line.strip()]  # Remove empty strings
            else:
                douban_info = []
                print("Warning: No 'info' section found in the parsed soup.")  # Adjust based on your logging/error handling approach
            
            
            # 在豆瓣上爬取电影信息
            douban_title = self.get_douban_title(douban_soup)
            douban_year = self.get_douban_year(douban_soup)
            douban_director = self.get_douban_director(douban_info)
            douban_scriptwriter = self.get_douban_scriptwriter(douban_info)
            douban_filmtype = self.get_douban_filmtype(douban_info)
            douban_area = self.get_douban_area(douban_info)
            
            # 根据豆瓣页面提取 IMDB ID
            imdb_id = self.get_imdb_id(douban_info)
            
            
            """
                IMDB部分
                
            """
            
            ## IMDB Cast & Crew
            imdb_cast_url = f'https://www.imdb.com/title/{imdb_id}/fullcredits/?ref_=tt_cl_sm'
            
            # 发送 HTTP 请求并获取网页内容
            imdb_cast_response = requests.get(imdb_cast_url, headers=headers)
            imdb_cast_soup = BeautifulSoup(imdb_cast_response.content, 'html.parser')
            
            imdb_cast_table = imdb_cast_soup.find('div', {'id': 'content-2-wide', 'class': 'redesign'})
            
            if imdb_cast_table:
                imdb_cast_dop = self.get_cast_dop(imdb_cast_table)
            else:
                self.log.info(f'{douban_title} with wrong imdb cast&crew')
                
            ## IMDB Tech Spec 部分
            imdb_techSpec_url = f'https://www.imdb.com/title/{imdb_id}/technical/?ref_=tt_spec_sm'
            imdb_techSpec_response = requests.get(imdb_techSpec_url, headers=headers)
            imdb_techSpec_soup = BeautifulSoup(imdb_techSpec_response.content, 'html.parser') 
            
            # 在 IMDB 上爬取 Tech Spec
            tech_table = imdb_techSpec_soup.find(attrs={'data-testid': 'sub-section'})
            
            if tech_table:
                imdb_techSpec_runtime = self.get_techSpec_runtime(tech_table)
                imdb_techSpec_soundMix = self.get_techSpec_SoundMix(tech_table)
                imdb_techSpec_color = self.get_techSpec_Color(tech_table)
                imdb_techSpec_aspectRatio = self.get_techSpec_AspectRatio(tech_table)
                imdb_techSpec_camera = self.get_techSpec_Camera(tech_table)
                imdb_techSpec_negativeFormat = self.get_techSpec_NegativeFormat(tech_table)
                imdb_techSpec_cinematographicProcess = self.get_techSpec_Process(tech_table)
                imdb_techSpec_printedFilmFormat = self.get_techSpec_Print(tech_table)
            
            else:
                self.log.info(f'{douban_title} with wrong tech spec')
            

            # 将电影信息添加到列表中
            self.movie_data.append({
                'douban_title': douban_title,
                'douban_id': douban_id,
                'imdb_id': imdb_id,
                'douban_year': douban_year,
                'douban_director': douban_director,
                'douban_scriptwriter': douban_scriptwriter,
                'imdb_cast_dop': imdb_cast_dop,
                'douban_filmtype': douban_filmtype,
                'douban_area': douban_area,
                'imdb_TechSpec_runtime': imdb_techSpec_runtime,
                'imdb_TechSpec_soundMix': imdb_techSpec_soundMix,
                'imdb_TechSpec_color': imdb_techSpec_color,
                'imdb_TechSpec_aspectRatio': imdb_techSpec_aspectRatio,
                'imdb_TechSpec_camera': imdb_techSpec_camera,
                'imdb_TechSpec_negativeFormat': imdb_techSpec_negativeFormat,
                'imdb_TechSpec_cinematographicProcess': imdb_techSpec_cinematographicProcess,
                'imdb_TechSpec_printedFilmFormat': imdb_techSpec_printedFilmFormat
            })
            
            self.log.info(f"Movie Info - Title: {douban_title}, ID: {douban_id}")
        
        self.log.info(f"Total movies collected: {len(self.movie_data)}")

    # Douban
    def get_douban_title(self, soup):
        title_element = soup.find(attrs={'property': 'v:itemreviewed'}).text.split(' ')[0]
        if title_element:
            return title_element
        else:
            return ''

    def get_douban_year(self, soup):
        year_element = soup.find(attrs={'class': 'year'}).text.replace('(','').replace(')','')
        if year_element:
            return year_element
        else:
            return ''

    def get_douban_director(self, info):
        director_element = info[0].split(': ')[1]
        if director_element:
            return director_element
        else:
            return ''

    def get_douban_scriptwriter(self, info):
        scriptwriter_element = info[1].split(': ')[1]
        if scriptwriter_element:
            return scriptwriter_element
        else:
            return ''

    def get_douban_filmtype(self, info):
        filmtype_element = info[3].split(': ')[1]
        if filmtype_element:
            return filmtype_element
        else:
            return ''
        
    def get_douban_area(self, info):
        area_element = info[4].split(': ')[1]
        if '.' in area_element:
            area_element = info[5].split(': ')[1].split(' / ')[0]
        if area_element:
            return area_element
        else:
            return ''
        
    def get_imdb_id(self, info):
        for item in info:
            if 'IMDb' in item:
                parts = item.split(':')
                if len(parts) > 1:
                    return parts[1].strip() 
                else:
                    return ''

    # IMDB
    #      Cast
    def get_cast_dop(self, tech_table):
        cinematographer_header = tech_table.find('h4', {'name': 'cinematographer', 'id': 'cinematographer'})
        if cinematographer_header:
            cinematographer_element = cinematographer_header.find_next('td', {'class': 'name'})
            if cinematographer_element:
                cinematographer_name = cinematographer_element.text.strip()
                return cinematographer_name
            else:
                return ''
        else:
            return ''
        
    #      TechSpec
    def get_techSpec_runtime(self, tech_table):

        runtime_element =  tech_table.find(
            'li', 
            {'role': 'presentation', 'data-testid': 'list-item', 'id': 'runtime'}
        )
        if runtime_element:
            runtime_value = runtime_element.find(
                'span', 
                {'class': 'ipc-metadata-list-item__list-content-item'}
            ).text.strip()
            try:
                runtime_subtext = runtime_element.find(
                    'span', 
                    {'class': 'ipc-metadata-list-item__list-content-item--subText'}
                ).text.strip()
            except:
                runtime_subtext = ""
        return f"{runtime_value} {runtime_subtext}"
    
    def get_techSpec_SoundMix(self, tech_table):
        soundMix_element = tech_table.find(
            'li', 
            {'role': 'presentation', 'data-testid': 'list-item', 'id': 'soundmixes'}
        )
        if soundMix_element:
            soundMix_value_element = soundMix_element.find(
                'a', 
                {'class': 'ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link'}
            )
            if soundMix_value_element:
                soundMix_value = soundMix_value_element.text.strip()
                return soundMix_value
            else:
                return ''
        else:
            return '' 
    
    def get_techSpec_Color(self, tech_table):
        color_element = tech_table.find(
            'li', 
            {'role': 'presentation', 'data-testid': 'list-item', 'id': 'colorations'}
        )
        if color_element:
            color_value_element = color_element.find(
                'a', 
                {'class': 'ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link'}
            )
            if color_value_element:
                color_value = color_value_element.text.strip()
                return color_value
            else:
                return ''
        else:
            return ''
    
    def get_techSpec_AspectRatio(self, tech_table):
        aspectRatio_element = tech_table.find(
            'li', 
            {'role': 'presentation', 'data-testid': 'list-item', 'id': 'aspectratio'}
        )
        if aspectRatio_element:
            aspectRatio_value_element = aspectRatio_element.find(
                'span', 
                {'class': 'ipc-metadata-list-item__list-content-item'}
            )
            if aspectRatio_value_element:
                aspectRatio_value = aspectRatio_value_element.text.strip()
                return aspectRatio_value
            else:
                return ''
        else:
            return ''
    
    def get_techSpec_Camera(self, tech_table):
        camera_element = tech_table.find(
            'li', 
            {'role': 'presentation', 'data-testid': 'list-item', 'id': 'cameras'}
        )
        if camera_element:
            camera_items = camera_element.find_all(
                'span', 
                {'class': 'ipc-metadata-list-item__list-content-item'}
            )
            camera_details = []
            for item in camera_items:
                # Extract camera detail text
                camera_detail = item.get_text(strip=True)
                # Check for any subtext (for extra details)
                subtext = item.find_next_sibling('span', {'class': 'ipc-metadata-list-item__list-content-item--subText'})
                if subtext:
                    camera_detail += f" ({subtext.get_text(strip=True)})"
                camera_details.append(camera_detail)

            # Join all the camera details into a single string
            all_cameras_detail = ', '.join(camera_details)  # Concatenate all camera details into one string
            return all_cameras_detail
        else:
            return ''
    
    def get_techSpec_NegativeFormat(self, tech_table):
        negativeFormat_element = tech_table.find(
            'li', 
            {'role': 'presentation', 'data-testid': 'list-item', 'id': 'negativeFormat'}
        )
        if negativeFormat_element:

            negative_format_items = negativeFormat_element.find_all('li', {'role': 'presentation', 'class': 'ipc-inline-list__item'})
            negative_formats = []

            for item in negative_format_items:

                format_name_element = item.find('span', {'class': 'ipc-metadata-list-item__list-content-item'})
                sub_text_element = item.find('span', {'class': 'ipc-metadata-list-item__list-content-item--subText'})

                if format_name_element:
                    format_name = format_name_element.text.strip()
                    sub_text = sub_text_element.text.strip() if sub_text_element else ''
                    if sub_text:
                        format_name += f" ({sub_text})"  # 将主格式和子信息合并显示
                    negative_formats.append(format_name)

            all_negative_formats = ', '.join(negative_formats)
            return all_negative_formats

        return ''
    
    def get_techSpec_Process(self, tech_table):
        process_element = tech_table.find(
            'li', 
            {'role': 'presentation', 'data-testid': 'list-item', 'id': 'process'}
        )
        if process_element:
            process_value_elements = process_element.find_all(
                'span', 
                {'class': 'ipc-metadata-list-item__list-content-item'}
            )
            if process_value_elements:
                process_values = []
                for process_value_element in process_value_elements:
                    process_value = process_value_element.text.strip()
                    process_subtext_element = process_value_element.find_next_sibling(
                        'span', 
                        {'class': 'ipc-metadata-list-item__list-content-item--subText'}
                    )
                    if process_subtext_element:
                        process_value += f" {process_subtext_element.text.strip()}"
                    process_values.append(process_value)
                return ', '.join(process_values)
            else:
                return ''
        else:
            return ''
    
    def get_techSpec_Print(self, tech_table):
        printedFormat_element = tech_table.find(
            'li', 
            {'role': 'presentation', 'data-testid': 'list-item', 'id': 'printedFormat'}
        )
        if printedFormat_element:
            printed_format_items = printedFormat_element.find_all('li', {'role': 'presentation', 'class': 'ipc-inline-list__item'})
            printed_formats = []

            for item in printed_format_items:
                format_name_element = item.find('span', {'class': 'ipc-metadata-list-item__list-content-item'})
                sub_text_element = item.find('span', {'class': 'ipc-metadata-list-item__list-content-item--subText'})

                if format_name_element:
                    format_name = format_name_element.text.strip()
                    sub_text = sub_text_element.text.strip() if sub_text_element else ''
                    if sub_text:
                        format_name += f" ({sub_text})"  # 将主格式和子信息合并显示
                    printed_formats.append(format_name)

            all_printed_formats = ', '.join(printed_formats)
            return all_printed_formats

        return ''
    
    def save_to_csv(self, output_path):
        pd.DataFrame(self.movie_data).to_csv(output_path, index=False)


# title_to_douban_id(title_path, douban_id_path)

crawler = MovieCrawler(douban_id_path)
crawler.read_douban_ids()
crawler.scrape_movie_data()
crawler.save_to_csv(output_path)