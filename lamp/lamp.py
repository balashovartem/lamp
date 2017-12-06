import tkinter
import argparse
import re
import asyncio
import threading
import struct
import os

from functools import partial
from PIL import Image, ImageTk

class LampWidget( tkinter.Frame ):
    def __init__( self, parent ):
        self.photo_lamp_enable = ImageTk.PhotoImage( Image.open( os.path.join( os.path.dirname(__file__), "lamp_enable.png" ) ) )
        self.photo_lamp_disable = ImageTk.PhotoImage( Image.open( os.path.join( os.path.dirname(__file__), "lamp_disable.png" ) ) )

        tkinter.Frame.__init__( self, parent )

        self.label = tkinter.Label( self )
        self.label.pack( expand=1, fill=tkinter.BOTH  )

        self.power_enabled = False
        self.hex_color = '#000000'
        self.__updateWidget()

    def set_power_enable( self, enable ):
        if self.power_enabled == enable:
            return False
        self.power_enabled = enable
        self.__updateWidget()
        return True

    def is_power_enabled( self ):
        return power_enabled
    
    def set_color( self, hex_color ):
        if self.hex_color == hex_color:
            return False
        self.hex_color = hex_color
        self.__updateWidget()
        return True

    def color( self ):
        return self.hex_color

    def __updateWidget( self ):
        if self.power_enabled:
            self.label.config( background = self.hex_color, image = self.photo_lamp_enable )
        else:
            self.label.config( background = '#000000', image = self.photo_lamp_disable )

    def get( self ):
        return self.entry.get()


class LampApplication(tkinter.Frame):
    def __init__(self, root, host, port ):
        tkinter.Frame.__init__( self, root )
        root.title("Фонарь")
        self.lamp_widget = LampWidget( root )
        self.lamp_widget.pack( fill=tkinter.BOTH, expand=1 )

        async def _lamp_client( host, port, ioloop ):
            while True:
                try:
                    print( "Подключение %r:%r" % (host, port) )
                    reader, writer = await asyncio.open_connection( host, port, loop=ioloop )
                    while True:
                        type = int.from_bytes( await reader.read(1), byteorder='big') 
                        length = int.from_bytes( await reader.read(2), byteorder='big') 
                        data = await reader.read( length )
                        if type == 0x12:
                            print("Пришла комманда включить фонарь")
                            self.lamp_widget.set_power_enable( True )
                        if type == 0x13:
                            print("Пришла комманда выключить фонарь")
                            self.lamp_widget.set_power_enable( False )
                        if type == 0x20:
                            colorBytes = struct.unpack( "BBB", data )
                            color = '#' + ''.join('%02x'%color for color in colorBytes)
                            print("Пришла комманда сменить цвет фонаря на %r"%color)
                            self.lamp_widget.set_color( color )
                except ConnectionError as e:
                    print( "Сетевая ошибка:%s" % e )
                await asyncio.sleep( 1.0, loop=ioloop )

        def _run( ioloop ):
            asyncio.set_event_loop( ioloop )
            ioloop.run_until_complete( _lamp_client( host, port, ioloop ) )

        self.ioloop = asyncio.new_event_loop()
        self.network_thread = threading.Thread( target=partial(_run, self.ioloop) )
        self.network_thread.daemon = True  
        self.network_thread.start() 

def perfect_tcp_host_port(string):
    result = re.match(r'\b((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))\:(\d+)\b', string )
    if result == None:
        raise argparse.ArgumentTypeError( "Строка %r не содержит ip-адрес:порт или ip-адрес имеет не правильный формат" % string )
    ip_address = result.group(1)
    port = int( result.group(2) )
    if not ( port > 0 and port <= 65535 ):
        raise argparse.ArgumentTypeError( "Указанный порт %r должен быть в диапазоне [0, 65535]" % port )
    return ip_address, port


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument( "--uri", type=perfect_tcp_host_port, default="127.0.0.1:9999", required=False,
                         help="ip-адрес:порт для подключения к серверу фонаря")
    args = parser.parse_args()
    root = tkinter.Tk()
    lamp_application = LampApplication( root, args.uri[0], args.uri[1] )
    lamp_application.pack()
    root.mainloop()

if __name__ == "__main__":
     main()