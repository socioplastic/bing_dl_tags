import hashlib
import ssl
from pathlib import Path
import urllib.request
import urllib
import imghdr
import re
import logging
import traceback
import os, sys
from pathlib import Path
import concurrent.futures
from io import BytesIO
from PIL import Image
import codecs
from time import sleep
from random import randint
import unicodedata
from dataclasses import dataclass
from termcolor import cprint

img_types = [ str(f).replace('.','') for f,u in Image.registered_extensions().items()]

@dataclass
class CFG:

    query: str = "Lambda Lambda Lambda"

    output_dir: str = "p:/bing/" #yes, put the slash at the end
    adult_filter: str = "off" # or "on"
    timeout: int = 60
    filter: str = "+filterui:photo-photo"

                # "+filterui:photo-linedrawing"
                # "+filterui:photo-photo"
                # "filterui:photo-clipart"
                # "+filterui:photo-animatedgif"
                # "+filterui:photo-transparent"
    limit: int = 1000
    cust_w = 640 # Custom Width Filter
    cust_h = 640 # Custom Width Filter


class Bing:
    def __init__(self, config: CFG):
        try:
            with open("error_log.txt","w") as fi:
                fi.write("start\n")
            self.config = config
            self.download_count = self.config.limit
            self.output_dir = self.config.output_dir
            self.adult = self.config.adult_filter
            self.filter = self.config.filter
            self.timeout = self.config.timeout
            self.query = str(self.config.query).replace(chr(32),chr(43))
            self.limit = self.config.limit
            self.filter = self.config.filter
            self.cust_w = self.config.cust_w
            self.cust_h = self.config.cust_h
            self.page_counter = 0
            self.page_counter = 0
            self.download_count = 0
            self.headers = {'User-Agent': #'Mozilla/5.0 (X11; Linux x86_64) ' 
                            'AppleWebKit/537.11 (KHTML, like Gecko) '
                            'Chrome/23.0.1271.64 Safari/537.11',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                            'Accept-Encoding': 'none',
                            'Accept-Language': 'en-US,en;q=0.8',
                            'Connection': 'keep-alive'}
            self.image_dir = Path(self.output_dir[:-1:]).joinpath(re.sub(r'[^A-Za-z0-9_]+/g','', str(self.query).replace(chr(32),chr(95)))).absolute()
            try:
                if not Path.is_dir(self.image_dir):
                    Path.mkdir(self.image_dir, parents=True)
            except Exception as e:
                print('[Error]Failed to create directory.', e)
                sys.exit(1)
            cprint("[%] Downloading Images to {}".format(str(self.image_dir.absolute())),"blue")
            self.seen = set([f[:(len(f))-len(f[-(f[::-1].find('.')):])] \
                            for f in os.listdir(str(self.image_dir)) \
                                if os.path.isfile(str(self.image_dir)+f) \
                                    and f[-(f[::-1].find('.')):] in img_types])
            self.run()
        except KeyboardInterrupt:
            sys.exit()
        except Exception as e:
            logging.error(traceback.format_exc())
            with open("error_log.txt","a") as fi:
                fi.write(str(logging.error(traceback.format_exc())))
        finally:
            pass

    def save_image(self, link):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            request = urllib.request.Request(link[0], None, self.headers)
            image = urllib.request.urlopen(request, timeout=self.timeout, context=ctx).read()
            sleep(randint(1,3))
            cprint("[!] Request-Get!","red")
            if not imghdr.what(None, image):
                print(f"[Error]Invalid image, not saving {link[0]}\n")
                raise ValueError(f"[Error]Invalid image, not saving {link[0]}\n")
            md5_calc = hashlib.md5(image).hexdigest()
            cprint(md5_calc,"green")
            img_buf = BytesIO(image)
            img = Image.open(img_buf).convert("RGB")
            print(str(self.output_dir).replace(chr(92),'/') +"/" + md5_calc + ".jpg")
            img.save(f"{self.image_dir}/{str(md5_calc)}.jpg", "JPEG", quality=95)
            cprint("[!!] ACTUAL SAVE GET","blue") 
            with open(f"{self.image_dir}/{str(md5_calc)}.txt", 'w') as f:
                f.write(str(link[1]))
            self.download_count = self.download_count + 1
        except KeyboardInterrupt:
            sys.exit()
        except Exception as e:
            logging.error(traceback.format_exc())
            with open("error_log.txt","a") as fi:
                fi.write(str(logging.error(traceback.format_exc())))
        finally:
            pass
    
    def download_image(self, link):
        self.download_count += 1
        try:
            self.save_image(link)
            print("[%] File Downloaded !\n")
        except KeyboardInterrupt:
            sys.exit()
        except Exception as e:
            logging.error(traceback.format_exc())
            with open("error_log.txt","a") as fi:
                fi.write(str(logging.error(traceback.format_exc())))
    
    def html_request_gen(self,page_counter):
        count_me = str(self.limit - (page_counter*35))
        self.pg_count = page_counter
        f_large = "+filterui:imagesize-large+"
        f_x_large = "+filterui:imagesize-wallpaper+"
        f_cust = f"+filterui:imagesize-custom_{self.cust_w}_{self.cust_h}+"
        rq_l_url = f"https://www.bing.com/images/async?q={str(self.query)}&first={self.pg_count}&count={str(count_me)}&adlt={self.adult}&qft={self.filter}{f_large}"
        rq_x_url = f"https://www.bing.com/images/async?q={str(self.query)}&first={self.pg_count}&count={str(count_me)}&adlt={self.adult}&qft={self.filter}{f_x_large}"
        rq_c_url = f"https://www.bing.com/images/async?q={str(self.query)}&first={self.pg_count}&count={str(count_me)}&adlt={self.adult}&qft={self.filter}{f_cust}"
        return [rq_l_url, rq_x_url, rq_c_url]

    def link_list_gen(self,html):
        link_list = []
        link_list.clear()          
        links = re.findall('url&quot;:&quot;(.*?)&quot;}"', html)
        for link in links:
            link = link + r"&quot;}"
            s_link = re.findall(r"murl&quot;:&quot;(.*?)&quot",link)[0]
            tags_1 = bytes(re.findall(r"&quot;,&quot;t&quot;:&quot;(.*?)&quot;,&quot",link)[0],'utf-8')
            tags_1 = codecs.decode(unicodedata.normalize('NFKD', codecs.decode(tags_1)).encode('ascii', 'ignore'))
            tags_1 = re.sub(r'[^A-Za-z0-9_ ]+/g','', str(tags_1))
            tags_2 = bytes(re.findall(r"desc&quot;:&quot;(.*?)&quot;}",link)[0],'utf-8')
            tags_2 = codecs.decode(unicodedata.normalize('NFKD', codecs.decode(tags_2)).encode('ascii', 'ignore'))
            tags_2 = re.sub(r'[^A-Za-z0-9_ ]+/g','', str(tags_2))
            tags = tags_1 + chr(32) + tags_2
            tags = tags.replace("respond","").replace("comment","").replace("related","").replace("posts","").replace("flags","").replace("notes","").replace("edit","").replace("...","")
            link_list.append([s_link, tags])                
        link_list = [x for x in link_list]
        self = link_list
        return self

    def html_gen(self,page_counter):
        self.page_counter = page_counter
        ret_link_list = []
        ret_link_list.clear()
        request_list = []
        request_list.clear()
        request_list = self.html_request_gen(self.page_counter)
        link_list = []        
        for request_url in request_list:
            link_list.clear            
            request = urllib.request.Request(request_url, None, headers=self.headers)
            response = urllib.request.urlopen(request, context=self.ctx)
            html = response.read().decode('utf8')
            if html ==  "":
                print("[%] No more images are available")
                break
            ret_link_list = self.link_list_gen(html)
            ret_link_list = [link_list.append(x) for x in ret_link_list]
        return link_list

    def run(self):
        try:
            self.ctx = ssl.create_default_context()
            self.ctx.check_hostname = False
            self.ctx.verify_mode = ssl.CERT_NONE
            self.page_counter = 1
            while self.download_count < self.limit:
                cprint(f"\n\n[!!]Indexing page: {self.page_counter}\n","yellow")
                sleep(randint(1,5))
                link_list = []
                link_list.clear()
                link_list = self.html_gen(self.page_counter)
                link_list = [x for x in link_list if x[0] not in self.seen]
                cprint(f"[%] Indexed {len(link_list)} Images on Page {self.page_counter + 1}","green")
                cprint("\n===============================================\n","yellow")
                with concurrent.futures.ThreadPoolExecutor(5) as executor:
                    executor.map(self.download_image, link_list)
                for link in link_list:
                    if self.download_count < self.limit and link[0] not in self.seen:
                        self.seen.add(str(link[0]))
                self.page_counter = self.page_counter + 1
            print(f"\n\n[%] Done. Downloaded {self.download_count} images")
        except KeyboardInterrupt:
            sys.exit()
        except Exception as e:
            logging.error(traceback.format_exc())
            with open("error_log.txt","a") as fi:
                fi.write(str(logging.error(traceback.format_exc())))
        finally:
            pass

Bing(config=CFG)

