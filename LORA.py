import gpiod
from LoRaRF import SX126x

class LORA:
    def __init__(self):
        # Create new LORA object
        self.Lora = SX126x()

        # Configure the self.Lora
        self.Lora.setSpi(0, 0, 7800000)
        self.Lora.begin()

        # set transmit power to +22 dBm
        self.Lora.setTxPower(22, self.Lora.TX_POWER_SX1262)
        # set receive gain to power saving(Comment first if lora dosent work)
        self.Lora.setRxGain(self.Lora.RX_GAIN_POWER_SAVING)
        # Set frequency to 915 Mhz
        self.Lora.setFrequency(915000000)
        # set spreading factor 8, bandwidth 125 kHz, coding rate 4/5, and low data rate optimization off
        self.Lora.setLoRaModulation(8, 125000, 5, False)
        # set explicit header mode, preamble length 12, payload length 15, CRC on and no invert IQ operation
        self.Lora.setLoRaPacket(self.Lora.HEADER_EXPLICIT, 12, 15, True, False)
        # Set syncronize word for public network (0x3444)
        self.Lora.setSyncWord(0x3444)
    
    # Recieve Function
    def recieve(self) -> str:
        self.Lora.request()
        self.Lora.wait()

        # get message and counter in last byte
        message = ""
        while self.Lora.available() > 1:
            message += chr(self.Lora.read())          # read message bytes
        counter = self.Lora.read()                    # read counter (last byte only)
        return message
    
    # Transmit Function
    def transmit(self, message) -> None:
        # message and counter to transmit
        messageList = list(message)
        for i in range(len(messageList)): 
            messageList[i] = ord(messageList[i])
        counter = 0

        self.Lora.beginPacket()
        self.Lora.write(messageList) # write multiple bytes
        self.Lora.write(counter)               # write single byte
        self.Lora.endPacket()
        self.Lora.wait()
        counter += 1

