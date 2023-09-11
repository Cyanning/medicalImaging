from mi_exception import *
from load_wiki import ImgsDownloader, WikiDownloader
from translator_bd import *
from translator_yd import TranslateYd
from model import *
import threading
import time


def downlaoding_text():
    medical_image = MedicalImage()
    for info_url in medical_image.generate_infomations():
        try:  # 下载网页
            wiki = WikiDownloader.getting(info_url)
        except GetLinkFailed as e:
            medical_image.saving_failed_link(e.link, e.kind, e.name)
            continue
        except FileExistsError:
            continue

        # 单独线程下载图片
        imgs = ImgsDownloader(wiki.title, wiki.soup)
        download_imgs = threading.Thread(target=imgs.imgs_download)
        time.sleep(1)
        download_imgs.start()

        # 分析网页文本
        wiki.text_anlysis()

        # 处理下载错误的图片
        download_imgs.join()
        medical_image.saving_failed_links(imgs.failed_urls)
        time.sleep(5)

    medical_image.close()


def translating_main1():
    medical_image = MedicalImage()
    zhtranslate = TranslateBd()
    for infourl in medical_image.generate_infomations():
        wiki = WikiDownloader(infourl)
        if wiki.state != 1:
            continue
        try:
            zhtranslate.current_file = TransFileBd.create(wiki.download_fpath)
            print("Initiate a translation request: {}".format(wiki.title))
            zhtranslate.create_trans_handle()
            is_done = False
            while not is_done:
                time.sleep(5)
                print("Initiate result request: {}".format(wiki.title))
                is_done = zhtranslate.query_trans_handle()
        except TranslateError as e:
            medical_image.saving_failed_link(wiki.download_fpath, "translate", wiki.title)
            print(e)
            if str(e) == "hold amount not enough":
                exit(0)
        except TimeoutError:
            time.sleep(30)
        finally:
            time.sleep(1)
    medical_image.close()


def translating_main2():
    medical_image = MedicalImage()
    zhtranslate = TranslateYd()
    for infourl in medical_image.generate_infomations():
        wiki = WikiDownloader(infourl)
        if wiki.state != 1:
            continue
        try:
            zhtranslate.current_file = TransFile.create(wiki.download_fpath)
            print("Initiate a translation request: {}".format(wiki.title))
            zhtranslate.connect()
        except TranslateError as e:
            medical_image.saving_failed_link(wiki.download_fpath, "translate", wiki.title)
            print(e)
        except TimeoutError:
            time.sleep(30)
        finally:
            time.sleep(1)
    medical_image.close()


def check_lost_item():
    medical_image = MedicalImage()
    noany = 0
    haddown = 0
    haddown_error = 0
    hadzh = 0
    for url in medical_image.generate_infomations():
        wiki = WikiDownloader(url)
        match wiki.state:
            case 0:
                noany += 1
            case 1:
                if medical_image.check_in_failed_link(link=wiki.download_fpath, kind="translate") > 0:
                    haddown_error += 1
                else:
                    haddown += 1
            case 2:
                hadzh += 1
    print("未下载：{}\n未翻译：{}\n已记录：{}\n已完成：{}".format(noany, haddown, haddown_error, hadzh))
    medical_image.close()


if __name__ == '__main__':
    check_lost_item()
