import tkinter
import argparse
import re
import asyncio
import threading
import struct
import os

from functools import partial
from PIL import Image, ImageTk


class LampWidget(tkinter.Frame):
    """Виджет фонаря, отображающий ссстояние и цвет фонаря"""
    def __init__(self, parent):
        self.photo_lamp_enable = ImageTk.PhotoImage(Image.open(os.path.join(os.path.dirname(__file__),
                                                                            "lamp_enable.png")))
        self.photo_lamp_disable = ImageTk.PhotoImage(Image.open(os.path.join(os.path.dirname(__file__),
                                                                             "lamp_disable.png")))

        tkinter.Frame.__init__(self, parent)

        self.label = tkinter.Label(self)
        self.label.pack(expand=1, fill=tkinter.BOTH)

        self.__power = False
        self.__hex_color = '#000000'
        self.__update_widget()

    @property
    def power(self):
        """Включение/выключение фонаря"""
        return self.__power

    @power.setter
    def power(self, power):
        if self.__power == power:
            return
        self.__power = power
        self.__update_widget()

    @property
    def hex_color(self):
        """Цвет фонаря"""
        return self.__hex_color

    @hex_color.setter
    def hex_color(self, hex_color):
        if self.__hex_color == hex_color:
            return
        self.__hex_color = hex_color
        self.__update_widget()

    def __update_widget(self):
        """отрисовка состояния фонаря"""
        if self.__power:
            self.label.config(background=self.__hex_color, image=self.photo_lamp_enable)
        else:
            self.label.config(background='#000000', image=self.photo_lamp_disable)


class LampApplication(tkinter.Frame):
    def __init__(self, root, host, port):
        tkinter.Frame.__init__(self, root)
        root.title("Фонарь")
        self.lamp_widget = LampWidget(root)
        self.lamp_widget.pack(fill=tkinter.BOTH, expand=1)

        async def _lamp_client(loop):
            while True:
                try:
                    print("Подключение %r:%r" % (host, port))
                    reader, writer = await asyncio.open_connection(host, port, loop=loop)
                    while True:
                        packet_type = int.from_bytes(await reader.read(1), byteorder='big')
                        data_length = int.from_bytes(await reader.read(2), byteorder='big')
                        data = await reader.read(data_length)
                        if packet_type == 0x12:
                            print("Пришла команда включить фонарь")
                            self.lamp_widget.power = True
                        if packet_type == 0x13:
                            print("Пришла команда выключить фонарь")
                            self.lamp_widget.power = False
                        if packet_type == 0x20:
                            color_bytes = struct.unpack("BBB", data)
                            hex_color = '#' + ''.join('%02x' % color for color in color_bytes)
                            print("Пришла команда сменить цвет фонаря на %r" % hex_color)
                            self.lamp_widget.hex_color = hex_color
                except ConnectionError as e:
                    print("Сетевая ошибка:%s" % e)
                await asyncio.sleep(1.0, loop=loop)

        def _run(loop):
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_lamp_client(loop))

        self.loop = asyncio.new_event_loop()
        self.network_thread = threading.Thread(target=partial(_run, self.loop))
        self.network_thread.daemon = True  
        self.network_thread.start() 


def perfect_tcp_host_port(string):
    """валидатор строки, которая должна содержать ip-адрес:порт"""
    result = re.match(r"\b((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))"
                      r":(\d+)\b", string)
    if result is None:
        raise argparse.ArgumentTypeError("Строка %s не содержит ip-адрес:порт или ip-адрес"
                                         "имеет не правильный формат" % string)
    ip_address = result.group(1)
    port = int(result.group(2))
    if not (0 < port <= 65535):
        raise argparse.ArgumentTypeError("Указанный порт %r должен быть в диапазоне [0, 65535]" % port)
    return ip_address, port


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", type=perfect_tcp_host_port, default="127.0.0.1:9999",
                        required=False, help="ip-адрес:порт для подключения к серверу фонаря")
    args = parser.parse_args()
    root = tkinter.Tk()
    lamp_application = LampApplication(root, args.uri[0], args.uri[1])
    lamp_application.pack()
    root.mainloop()


if __name__ == "__main__":
    main()
