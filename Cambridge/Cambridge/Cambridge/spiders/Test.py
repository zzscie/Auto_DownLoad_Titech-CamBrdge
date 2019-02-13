import scrapy
import os
import pandas as pd
from Cambridge.items import *
class PDFdownload(scrapy.Spider):
    name = "Test_downloader"
    def start_requests(self):
        self.csv_path = "./data.csv"
        self.book_list = pd.read_csv(self.csv_path)
        self._list=['Online ISBN', 'Author', 'Series', 'Category','Publisher', 'Product Group', 'Core Subjects']
        self.db=self.book_list.drop(self._list,axis=1);
        self.book_name = []
        self.book_url = []
        for i in range(len(self.db)):
            self.book_url.append(self.db.iloc[i][1])

        #self.book_url=["https://doi.org/10.1017/CBO9781316417744"]
        for url in self.book_url:
            yield scrapy.Request(url=url, callback=self.PageCount)
    def PageCount(self,response):
        #cur_url= response.request.url
        #print(cur_url)
        self.root = "./Content"
        if os.path.exists(self.root):
            print("Path Already exists, Download Begin")
        else:
            os.mkdir(self.root)
        self.book_name = response.xpath('//div[@class="title title-left show-for-print"]/text()').extract()
        self.book_name = self.book_name[0].replace(u'\xa0',u' ')
        self.book_folder = self.root +'/'+ self.book_name
        if os.path.exists(self.book_folder):
            print("folder Alreader exists")
        else:
            os.mkdir(self.book_folder)
            print("Make new Folder %s", self.book_folder)
        PageNum = response.xpath('//div[@class="pagination-centered"]/p/text()').extract_first()
        url_list = [];
        if not PageNum:
            url_list.append(response.request.url+'?pageNum='+'0')
        else:
            Num = int(PageNum[10:])
            for i in range(Num):
                url_list.append(response.request.url + '?pageNum='+str(i+1))
        item = CambridgeItem()
        item['download_path'] = self.book_folder
        for i in range(len(url_list)):
            links = url_list[i]
            print("Processing Page: %s", str(i))
            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            request = scrapy.Request(url=links,callback=self.PageLink)
            request.meta['item'] = item
            yield request
    def PageLink(self,response):
        item = response.meta['item']
        download_urls=response.xpath('//div[@class="representation overview indent-0 " or @class="representation overview indent-0 first"]//ul[@class="access links "]//a/@href').extract()
        print(download_urls)
        for i in download_urls:
            if i != '#':
                download_link = 'https://www.cambridge.org'+i
                request = scrapy.Request(url=download_link,callback=self.save_file)
                request.meta['item'] = item
                yield request
        # with open('link.txt', 'w') as f:
            # for i in download_urls:
                # if i != '#':
                    # f.write(cur_url+i+"\n")
    def save_file(self,response):
        item = response.meta['item']
        self.book_folder = item['download_path']
        path = self.book_folder+'/'+response.url.split('/')[-1]
        self.logger.info('Saving PDF %s',path)
        with open(path,'wb') as f:
            f.write(response.body)
