import time
from dataclasses import dataclass
from pymavlink import mavutil
from pymavlink.dialects.v20 import common
from threading import Thread
import logging
from utils import EventHandler

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)



@dataclass
class MsgMeta:
    id: int
    counter: int = 0


def request_message_interval(self, message_id: int, frequency_hz: float):
    self.master.mav.command_long_send(
        0, 0,
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
        message_id, # The MAVLink message ID
        1e6 / frequency_hz, # The interval between two messages in microseconds. Set to -1 to disable and 0 to request default rate.
        0, 0, 0, 0, # Unused parameters
        0, # Target address of message stream (if message has target address fields). 0: Flight-stack default (recommended), 1: address of requestor, 2: broadcast.
    )

class MavMsgAnalyzer():
    def __init__(self) -> None:
        self.data = {}

    def track_msg(self, msg_id: int):
        if msg_id in self.data:
            self.data[msg_id].counter += 1
        else:
            self.data[msg_id] = MsgMeta(id=msg_id, counter=1)

    def reset(self):
        for _, meta in self.data.items():
            meta.counter = 0

    def snap(self)->dict:
        return self.data
    
    def __str__(self):
        data = ""
        for msg_id, c in self.data.items():
            data += f"{msg_id}, ({c})\n"

        return data        

class MavAnalyzer():
    def __init__(self) -> None:
        self.on_data = EventHandler()
        self.master = mavutil.mavlink_connection('udp:127.0.0.1:14560', source_system=254)
        # Make sure the connection is valid
        self.master.wait_heartbeat()

        # request_message_interval(common.MAVLINK_MSG_ID_BATTERY_STATUS, 10)
        self.last_time = time.time()
        self.mav_analyzer = MavMsgAnalyzer()

    def run(self):
        self.work_thread = Thread(target=self.__runner, daemon=True, name="work_thread")
        self.work_thread.start()

    def __runner(self):
        while True:
            try:
                msg = self.master.recv_match()
                if msg is None:
                    continue
                item = msg.to_dict()
                self.mav_analyzer.track_msg(item["mavpackettype"])
                current_time = time.time()
                delta = current_time - self.last_time
                if  delta >= 1.0:
                    self.last_time = time.time()
                    self.on_data.call(self.mav_analyzer.snap())
                    self.mav_analyzer.reset()
            
            except:
                log.error("error", exc_info=True)
            time.sleep(0.1)

    # bytearray(b'\xfd\t\x00\x00\xa4\x01\x01\x00\x00\x00\x00\x00\x00\x00\x02\x03Q\x03\x03\x94\xd5')