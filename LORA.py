import time
from LoRaRF import SX126x

class LORA:
    """LoRa radio wrapper using SX126x (SX1262) module."""

    def __init__(self):
        self._lora = SX126x()
        self._counter = 0

        # --- HARDWARE INITIALIZATION ---
        # Standard Raspberry Pi Pins: NSS=8, RST=22, BUSY=23, DIO1=25
        # If your HAT uses different pins, change them here.
        if not self._lora.begin(8, 22, 23, 25):
            raise Exception("SX1262 hardware not found. Check wiring/pins.")

        # SPI and initialisation
        self._lora.setSpi(0, 0, 7800000)

        # Transmit power: +22 dBm
        self._lora.setTxPower(22, self._lora.TX_POWER_SX1262)
        # Receive gain: boosted for better range
        self._lora.setRxGain(self._lora.RX_GAIN_BOOSTED)
        # Frequency: 915 MHz
        self._lora.setFrequency(915000000)
        # Spreading factor 8, bandwidth 125 kHz, coding rate 4/5, LDRO off
        self._lora.setLoRaModulation(8, 125000, 5, False)
        # Explicit header, preamble 12, payload 15, CRC on, no invert IQ
        self._lora.setLoRaPacket(self._lora.HEADER_EXPLICIT, 12, 15, True, False)
        # Synchronise word for public network (0x3444)
        self._lora.setSyncWord(0x3444)
        
        # Start in receive mode
        self._lora.request()

    def receive(self) -> str:
        """Non-blocking check for a LoRa packet."""
        # Check if data is waiting in the module buffer
        if self._lora.available() > 0:
            message = ""
            # Read all bytes except the last one (assumed counter)
            while self._lora.available() > 1:
                message += chr(self._lora.read())
            
            # Read the final counter byte
            _rx_counter = self._lora.read()
            
            # Immediately go back to listening mode
            self._lora.request()
            return message
        return ""

    def transmit(self, message: str) -> None:
        """Transmit a string message and return to receive mode."""
        payload = list(message.encode("ascii"))

        self._lora.beginPacket()
        self._lora.write(payload)
        self._lora.write(self._counter & 0xFF)
        self._lora.endPacket()
        
        # Wait for transmission to complete
        self._lora.wait()

        self._counter += 1
        
        # Switch back to receive mode immediately after sending
        self._lora.request()

    # Alias for backwards compatibility
    recieve = receive