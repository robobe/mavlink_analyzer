import time
from dataclasses import dataclass
from pymavlink import mavutil
from pymavlink.dialects.v20 import common
from threading import Thread, Timer
import logging
from utils import EventHandler
import copy

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

    def track_msg(self, sys_id: int, comp_id: int, msg_id: int):
        if sys_id not in self.data:
            self.data[sys_id] = {}

        if comp_id not in self.data[sys_id]:
            self.data[sys_id][comp_id] = {}

        msgs = self.data[sys_id][comp_id]
        if msg_id in msgs:
            msgs[msg_id] += 1
        else:
            msgs[msg_id] = 1#MsgMeta(id=msg_id, counter=1)

    def reset(self):
        for sys_id, comps in self.data.items():
            for comp_id, msgs in comps.items():
                for msg_id,_ in msgs.items():
                    self.data[sys_id][comp_id][msg_id] = 0

    def snap(self)->dict:
        data = {}
        for sys_id, comps in self.data.items():
            data[sys_id] = {}
            for comp_id, msgs in comps.items():
                data[sys_id][comp_id] = {}
                for msg_id,_ in msgs.items():
                    data[sys_id][comp_id][msg_id] = self.data[sys_id][comp_id][msg_id]
        
        return data
    
    def __str__(self):
        data = ""
        for msg_id, c in self.data.items():
            data += f"{msg_id}, ({c})\n"

        return data        

class MavAnalyzer():
    def __init__(self) -> None:
        self.__stop = False
        self.on_data = EventHandler()
        self.master = mavutil.mavlink_connection('udp:127.0.0.1:14560', source_system=254)
        # Make sure the connection is valid
        self.master.wait_heartbeat()

        # request_message_interval(common.MAVLINK_MSG_ID_BATTERY_STATUS, 10)
        self.last_time = time.time()
        self.mav_analyzer = MavMsgAnalyzer()
        self.timer = Timer(1.0, self.timer_handler)
        self.timer.start()

    def run(self):
        self.work_thread = Thread(target=self.__runner, daemon=True, name="work_thread")
        self.work_thread.start()

    def timer_handler(self):
        try:
            if self.on_data:
                self.on_data.call(self.mav_analyzer.snap())
                # print(self.mav_analyzer.snap())
                self.mav_analyzer.reset()
        except:
            log.error("data error", exc_info=True)
        finally:
            if not self.__stop:
                self.timer = Timer(1.0, self.timer_handler)
                self.timer.start()
            else:
                log.info("Stopping render loop timer")

    def stop(self):
        self.__stop = True

    def __runner(self):
        while True:
            try:
                if self.__stop:
                    log.info("Stoping mavlink loop")
                    break
                msg = self.master.recv_match()
                if msg is None:
                    time.sleep(0.05)
                    continue
                item = msg.to_dict()
                sys_id = msg._msgbuf[5]
                comp_id = msg._msgbuf[6]
                self.mav_analyzer.track_msg(
                    sys_id,
                    comp_id,
                    item["mavpackettype"]
                )
                
                # if item["mavpackettype"] == "HEARTBEAT":
                #     pass
                # current_time = time.time()
                # delta = current_time - self.last_time
                # if  delta >= 0.99:
                #     self.last_time = time.time()
                    
            
            except:
                log.error("error", exc_info=True)
            time.sleep(0.001)

    # bytearray(b'\xfd\t\x00\x00\xa4\x01\x01\x00\x00\x00\x00\x00\x00\x00\x02\x03Q\x03\x03\x94\xd5')

if __name__ == "__main__":
    obj = MavAnalyzer()
    obj.run()
    while True:
        time.sleep(1)