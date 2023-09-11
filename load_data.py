import os
import shutil
import json
import sqlite3
import time
from enum import Enum

import requests
from bs4 import BeautifulSoup
from matplotlib import colors


class Table(Enum):
    project = 'mi_project'
    images = 'mi_images'
    legends = 'mi_legends'
    structures = 'mi_structures'
    series = 'mi_series'
    coordinate = 'mi_coordinate'


class JsonAnalysis:
    def __init__(self):
        self.db = sqlite3.connect("database/medicalimages.db")

    def auto_run(self):
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
                  jsondata['general']['logo'],
                  jsondata['general']['name'],
                  jsondata['general']['tag'])]
        self.insert(Table.project, data)

        # mi_images
        data = [('value', 'url', 'position', 'series_val', 'project_val')]
        for x in jsondata['images'].values():
            if r'\/' in x['url']:
                x['url'] = x['url'].replace(r'\/', '/')
            data.append((x['id'], x['url'], x['position'], x['series'], pval))
        self.insert(Table.images, data)

        # mi_legends
        data = [('value', 'name', 'en_name', 'structure')]
        data += [(x['id'], x['text']['Chinese_sc'], x['text']['english'], x['structure'])
                 for x in jsondata['legends'].values()]
        self.insert(Table.legends, data)

        # mi_structures
        color_maps = colors.CSS4_COLORS
        data = [('value', 'name', 'color', 'project_val')]
        for x in jsondata['structures'].values():
            temp = str(x['color']).lower()
            x['color'] = color_maps[temp]
            data.append((x['id'], x['text'], x['color'], pval))
        self.insert(Table.structures, data)
        del color_maps

        # mi_series
        data = [('value', 'name', 'project_val')]
        data += [(x, jsondata['series'][x]['text'], pval)
                 for x in jsondata['series']]
        self.insert(Table.series, data)

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
        self.insert(Table.coordinate, data)

    def insert(self, tablename: Table, data: list):
        if len(data) < 2:
            return
        cur = self.db.cursor()
        fields = data[0]
        data = data[1:]
        cur.executemany(
            f"INSERT INTO {tablename.value} ({','.join(fields)}) VALUES ({','.join(['?' for _ in fields])})", data
        )
        self.db.commit()

    def update_url(self):
        with open("project/thumb.json", 'r', encoding='UTF-8') as r:
            data = r.read()
        jsondata = json.loads(data)

        cur = self.db.cursor()
        count = 0
        for x in jsondata['images'].values():
            if r'\/' in x['url']:
                x['url'] = x['url'].replace(r'\/', '/')
            cur.execute(f"UPDATE mi_images SET url='{x['url']}' WHERE value='{x['id']}'")
            count += 1
        print(count)


def get_projects(cookie):
    r = requests.get("https://www.omcsa.org/home", )
    soup = BeautifulSoup(r.text, 'html5lib')
    for box in soup.find_all('div', id="thumbZone"):
        name = str(box.h6.string).strip()
        url = str(box.a['href'])
        num = url[url.index('?id=') + 4:url.index('&search')]
        if any(name in x for x in os.listdir("project")):
            continue
        r = requests.post("https://www.omcsa.org/loaddata", data={"id": num}, headers={"cookie": cookie})
        r = requests.post("https://www.omcsa.org/loaddata", data={"id": num}, headers={"cookie": cookie})
        with open(f"project/{name}.json", 'w', encoding='UTF-8') as w:
            w.write(r.text)
        print("下载：%s - %s" % (name, num))
        time.sleep(3)


def download_images():
    db = sqlite3.connect("database/medicalimages.db")
    cur = db.cursor()
    cur.execute("SELECT value,url FROM mi_images WHERE project_val='25328888515'")
    filenames = [f[:f.index(".jpg")] for f in os.listdir("images/") if '.jpg' in f]
    for value, url in cur.fetchall():
        value = value
        if value in filenames:
            continue
        while True:
            try:
                data = requests.get(f"https://www.omcsa.org{url}")
                print(f"Download: {value}")
                break
            except requests.exceptions.RequestException:
                time.sleep(60)
        if data.status_code == 200:
            with open(f"images/{value}.jpg", 'wb') as f:
                for chunk in data.iter_content():
                    f.write(chunk)
        else:
            print(url)
        time.sleep(3)


def covers_classification():
    db = sqlite3.connect("database/medicalimages.db")
    cur = db.cursor()
    for fn in os.listdir("covers/"):
        val = fn[:fn.index(".png")]
        cur.execute(f"SELECT project_val FROM mi_images WHERE value='{val}'")
        pval, = cur.fetchone()
        os.rename(f"covers/{fn}", f"covers/cover_{pval}.png")


def images_classification():
    db = sqlite3.connect("database/medicalimages.db")
    cur = db.cursor()
    cur.execute("SELECT value FROM mi_project")
    for project, in cur.fetchall():
        try:
            os.mkdir(f"images/imgs_{project}", )
        except FileExistsError:
            continue
        _cur = db.cursor()
        _cur.execute(f"SELECT value FROM mi_images WHERE project_val='{project}'")
        for image, in _cur.fetchall():
            if os.path.exists(f"images/{image}.jpg"):
                shutil.move(f"images/{image}.jpg", f"images/imgs_{project}/{image}.jpg")
            else:
                print(image, "Not Found.")
        _cur.close()


def edit_url():
    db = sqlite3.connect("database/medicalimages.db")
    cur = db.cursor()
    cur.execute("SELECT id,value FROM mi_project")
    for _id, value in cur.fetchall():
        cur.execute("UPDATE mi_project SET logo='{}' WHERE id={}".format(
            f"http://obs.xlhcq.com/wankang/ct_cover/cover_{value}.png", _id)
        )
        db.commit()
    db.close()


def get_infomation_url():
    db = sqlite3.connect("database/medicalimages.db")
    cur = db.cursor()
    for fn in os.listdir("project/"):
        with open("project/{}".format(fn), 'r', encoding='UTF-8') as f:
            datajson = f.read()
            datajson = json.loads(datajson)

        for legend in datajson["legends"].values():
            val = str(legend["id"])
            url = str(legend["description"]["en"])
            idx0 = url.find("\"") + 1
            idx1 = url.find("\"", idx0)
            url = url[idx0:idx1]
            cur.execute("UPDATE mi_legends SET infomation=? WHERE value=?", (url, val))
            db.commit()

    db.close()


if __name__ == '__main__':
    pass
