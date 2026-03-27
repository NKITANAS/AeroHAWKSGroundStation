import gpiod
from LoRaRF import SX126x


class LORA:
    """LoRa radio wrapper using SX126x (SX1262) module."""

    def __init__(self):
        self._lora = SX126x()
        self._counter = 0

        # SPI and initialisation
        self._lora.setSpi(0, 0, 7800000)
        self._lora.begin()

        # Transmit power: +22 dBm
        self._lora.setTxPower(22, self._lora.TX_POWER_SX1262)
        # Receive gain: power-saving (comment out if LoRa doesn't work)
        self._lora.setRxGain(self._lora.RX_GAIN_POWER_SAVING)
        # Frequency: 915 MHz
        self._lora.setFrequency(915000000)
        # Spreading factor 8, bandwidth 125 kHz, coding rate 4/5, LDRO off
        self._lora.setLoRaModulation(8, 125000, 5, False)
        # Explicit header, preamble 12, payload 15, CRC on, no invert IQ
        self._lora.setLoRaPacket(self._lora.HEADER_EXPLICIT, 12, 15, True, False)
        # Synchronise word for public network (0x3444)
        self._lora.setSyncWord(0x3444)

    def receive(self) -> str:
        """Block until a LoRa packet is received and return the message string."""
        self._lora.request()
        self._lora.wait()

        message = ""
        while self._lora.available() > 1:
            message += chr(self._lora.read())
        _counter = self._lora.read()  # counter byte (last byte)
        return message

    # Keep old spelling as an alias so existing callers don't break
    recieve = receive

    def transmit(self, message: str) -> None:
        """Transmit a string message over LoRa."""
        payload = list(message.encode("ascii"))

        self._lora.beginPacket()
        self._lora.write(payload)
        self._lora.write(self._counter & 0xFF)
        self._lora.endPacket()
        self._lora.wait()

        self._counter += 1

