try:
    from pyb import Pin, SPI as MICROPYTHON_SPI
except ImportError:
    from machine import Pin, SPI as MICROPYTHON_SPI

from .spi import SPI

SPI_SCK_PIN = 2
SPI_MOSI_PIN = 3
SPI_MISO_PIN = 4
SPI_CS_PIN = 9

class SPIPICO(SPI):
    def init(self, baudrate: int) -> Any :
        return MICROPYTHON_SPI(
            0,
            sck=Pin(SPI_SCK_PIN),
            mosi=Pin(SPI_MOSI_PIN),
            miso=Pin(SPI_MISO_PIN),
            baudrate=baudrate
        )