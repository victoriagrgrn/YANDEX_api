from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import QApplication, QWidget
import requests
import sys
import math

from bis import find_business
from distance import lonlat_distance
from geo import reverse_geocode

LAT_STEP = 0.003  # Шаги при движении карты по широте и долготе
LON_STEP = 0.002
coord_to_geo_x = 0.0000428  # Пропорции пиксельных и географических координат.
coord_to_geo_y = 0.0000428


def ll(x, y):
    return "{0},{1}".format(x, y)


class SearchResult(object):
    def __init__(self, point, address, postal_code=None):
        self.point = point
        self.address = address
        self.postal_code = postal_code


class Main(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("maps.ui", self)
        self.map.setFocus()
        #
        self.lat = 53.543711  # Координаты центра карты на старте.
        self.lon = 49.346974
        self.zoom = 15  # Масштаб карты на старте.
        self.type = "map"  # Тип карты на старте.
        self.search_result = None  # Найденный объект для отображения на карте.
        self.use_postal_code = False

        self.draw()
        self.find_btn.clicked.connect(self.poisk)

    def poisk(self):   # осуществляет поиск
        if self.poisk_Edit.text():
            self.map.setFocus()
            pos = self.obrabotka_zaprosa('+'.join(self.poisk_Edit.text().split())).split()
            self.lon, self.lat = float(pos[0]), float(pos[1])
            self.poisk_Edit.clear()
            self.draw()

    def obrabotka_zaprosa(self, adress):  # выдает точки, искомого адреса
        API = '40d1649f-0493-4b70-98ba-98533de7710b'
        geocoder = f"http://geocode-maps.yandex.ru/1.x/?apikey={API}&geocode={adress}&format=json"
        # print(geocoder)
        response = requests.get(geocoder)
        if response:
            json_response = response.json()
            toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]
            pos = toponym["GeoObject"]["Point"]["pos"]
            return pos
        else:
            print("Ошибка выполнения запроса:")
            print(geocoder)
            print("Http статус:", response.status_code, "(", response.reason, ")")

    def ll(self):
        return ll(self.lon, self.lat)

    def draw(self):
        map_file = load_map(self.zoom, self.type, self.ll(), self.search_result)
        self.map.setPixmap(QtGui.QPixmap(map_file))

    def keyPressEvent(self, event):
        k = event.key()
        if k == 16777235:  # up
            self.lat += LAT_STEP * math.pow(2, 15 - self.zoom)
        elif k == 16777237:  # down
            self.lat -= LAT_STEP * math.pow(2, 15 - self.zoom)
        elif k == 16777236:  # right
            self.lon += LON_STEP * math.pow(2, 15 - self.zoom)
        elif k == 16777234:  # left
            self.lon -= LON_STEP * math.pow(2, 15 - self.zoom)
        elif k == 16777238 and self.zoom < 19:  # PgUp
            self.zoom += 1
        elif k == 16777239 and self.zoom > 2:  # PgDn
            self.zoom -= 1
        else:
            return

        if self.lon > 180:
            self.lon -= 360
        if self.lon < -180:
            self.lon += 360

        self.draw()


# Создание карты с соответствующими параметрами.
def load_map(zoom, type, ll, search_result):
    map_request = f"http://static-maps.yandex.ru/1.x/?ll={ll}&z={zoom}&l={type}"
    if search_result:
        map_request += "&pt={0},{1},pm2grm".format(search_result.point[0],
                                                   search_result.point[1])

    response = requests.get(map_request)
    if not response:
        print("Ошибка выполнения запроса:")
        print(map_request)
        print("Http статус:", response.status_code, "(", response.reason, ")")
        sys.exit(1)

    # Запишем полученное изображение в файл.
    map_file = "map.png"
    try:
        with open(map_file, "wb") as file:
            file.write(response.content)
    except IOError as ex:
        print("Ошибка записи временного файла:", ex)
        sys.exit(2)

    return map_file


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Main()
    ex.show()
    sys.exit(app.exec())
