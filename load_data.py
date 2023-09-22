import os
import json
import sqlite3
import time
import requests
from bs4 import BeautifulSoup
from matplotlib import colors
from settings import *


def get_projects(cookie):
    """
    爬取每组视图全部数据
    """
    r = requests.get("https://www.omcsa.org/home", )
    soup = BeautifulSoup(r.text, 'html5lib')
    for box in soup.find_all('div', id="thumbZone"):
        name = str(box.h6.string).strip()
        url = str(box.a['href'])
        num = url[url.index('?id=') + 4:url.index('&search')]
        if any(name in x for x in os.listdir("project")):
            continue
        r = requests.post("https://www.omcsa.org/loaddata", data={"id": num}, headers={"cookie": cookie})
        with open(f"project/{name}.json", 'w', encoding='UTF-8') as w:
            w.write(r.text)
        print("下载：%s - %s" % (name, num))
        time.sleep(3)


class JsonSaving:
    """
    对闪闪进行分析，分类存储
    """

    def __init__(self):
        self.db = sqlite3.connect(DB_PATH)

    def __call__(self):
        for fn in os.listdir("project"):
            self.analysis("project/" + fn)
        self.db.close()

    def analysis(self, path):
        with open(path, 'r', encoding='UTF-8') as r:
            data = r.read()
        jsondata = json.loads(data)
        pval = jsondata['id']

        # mi_project
        data = [('value', 'logo', 'name', 'tag')]
        data += [(pval,
                  "http://obs.xlhcq.com/wankang/ct_cover/cover_{}.png".format(pval),
                  jsondata['general']['name'],
                  jsondata['general']['tag'])]
        self.insert('mi_project', data)

        # mi_images
        data = [('value', 'url', 'position', 'series_val', 'project_val')]
        for x in jsondata['images'].values():
            if r'\/' in x['url']:
                x['url'] = x['url'].replace(r'\/', '/')
            data.append((x['id'], x['url'], x['position'], x['series'], pval))
        self.insert('mi_images', data)

        # mi_legends
        data = [('value', 'name', 'en_name', 'structure', 'infomation')]
        data += [(x['id'], x['text']['Chinese_sc'], x['text']['english'], x['structure'], x['description']['en'])
                 for x in jsondata['legends'].values()]
        self.insert('mi_legends', data)

        # mi_structures
        color_maps = colors.CSS4_COLORS
        data = [('value', 'name', 'color', 'project_val')]
        for x in jsondata['structures'].values():
            temp = str(x['color']).lower()
            x['color'] = color_maps[temp]
            data.append((x['id'], x['text'], x['color'], pval))
        self.insert('mi_structures', data)
        del color_maps

        # mi_series
        data = [('value', 'name', 'project_val')]
        data += [(x, jsondata['series'][x]['text'], pval)
                 for x in jsondata['series']]
        self.insert('mi_series', data)

        # mi_coordinate
        data = [('img_val', 'item_val', 'x', 'y')]
        for legends in jsondata['images'].values():
            if 'legends' not in legends:
                continue
            for point in legends['legends'].values():
                data.append((legends['id'], point['id'], point['percentWidth'], point['percentHeight']))

        for structure in jsondata['structures'].values():
            if not len(structure['draw']):
                continue
            for img_val, points in structure['draw'].items():
                if not len(points):
                    continue
                for p in points:
                    data.append([img_val, structure['id'], p[0], p[1]])
        self.insert('mi_coordinate', data)

    def insert(self, tablename: str, data: list):
        """
        Insert data into the specified data table,
        The object with list index 0 is the fields
        """
        if len(data) < 2:
            return
        cur = self.db.cursor()
        fields = data[0]
        data = data[1:]
        cur.executemany(
            "INSERT INTO {} ({}) VALUES ({})".format(tablename, ','.join(fields), ','.join(['?'] * len(fields))),
            data
        )
        self.db.commit()

    def download_images(self, project_val):
        cur = self.db.cursor()
        if not os.path.exists(filepath := f"images/{project_val}"):
            os.mkdir(filepath)
        filenames = [f[:f.index(".jpg")] for f in os.listdir(filepath) if '.jpg' in f]
        cur.execute(f"SELECT value,url FROM mi_images WHERE project_val=?", (project_val,))
        for value, url in cur.fetchall():
            value = value
            if value in filenames:
                continue
            data = requests.get(f"https://www.omcsa.org{url}", headers=WIKI_HEADERS)
            print(f"Download: {value}")
            if data.status_code == 200:
                with open(f"{filepath}/{value}.jpg", 'wb') as f:
                    for chunk in data.iter_content():
                        f.write(chunk)
            else:
                print(url)
            time.sleep(3)
