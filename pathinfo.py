#!/usr/bin/python

import copy
import threading
import time
import zmq
import sys

from usbmodem_msg_pb2 import *

import interfaceinfo


MESSAGES = {
  'event.radio.access.NetworkModeChangeEvent': {
    'class': NetworkModeChangeEvent,
  },
  'event.radio.access.NetworkSubmodeChangeEvent': {
    'class': NetworkSubmodeChangeEvent,
  },
  'event.radio.access.SignalStrengthChangeEvent': {
    'class': SignalStrengthChangeEvent,
  },
  'event.radio.access.LocationChangeEvent': {
    'class': LocationChangeEvent,
  },
  'event.radio.access.SNRChangeEvent': {
    'class': SNRChangeEvent,
  },
  'event.radio.wcdma.RRCStateChangeEvent': {
    'class': RRCStateChangeEvent,
  },
  'state.generic.CurrentNetworkState': {
    'class': CurrentNetworkState,
  },
}

# RRC and network
MODE = { 
 '0': 'No service', '3': 'GSM', '5': 'WCDMA'
}
SUBMODE = { 
 '0': 'No service', '1': 'GSM', '2': 'GPRS',
 '3': 'EDGE', '4': 'WCDMA', '5': 'HSDPA', '6': 'HSUPA',
 '7': 'HSDPA+HSUPA', '9': 'HSPA+'
}
RRC = { 
 '0': 'Disconnected', '1': 'Connecting', '2': 'FACH',
 '3': 'DCH', '4': 'PCH', '5': 'URA-PCH'
}


INTF_TO_MCC_MNC = { 'ppp0': '24201', 'ppp1': '24202', 'ppp2': '24007', 'ppp3': '24205' }
SUB_ADDR        = "tcp://*:5550" # public address and port (for subscribers)

MCC_MNC_TO_INTF = { v:k for k, v in INTF_TO_MCC_MNC.items() } # reverse

_thread       = None
_stop         = True
_mbbn_dict    = {}


def _process_message(intf, event, msg):
    global _mbbn_dict
    if not intf in _mbbn_dict:
        return # not monitoring this one
    
    if event == 'event.radio.access.NetworkModeChangeEvent':
        _mbbn_dict[intf]['mode'] = MODE[str(msg.currentNetworkMode)]
    
    elif event == 'event.radio.access.NetworkSubmodeChangeEvent':
        _mbbn_dict[intf]['submode'] = SUBMODE[str(msg.currentNetworkSubmode)]
    
    elif event == 'event.radio.access.SignalStrengthChangeEvent':
        _mbbn_dict[intf]['rssi'] = msg.currentRssi
    
    elif event == 'event.radio.access.LocationChangeEvent':
        _mbbn_dict[intf]['lac'] = msg.currentLac
        _mbbn_dict[intf]['cellid'] = msg.currentCellId
    
    elif event == 'event.radio.access.SNRChangeEvent':
        _mbbn_dict[intf]['rscp'] = msg.currentRscp
        _mbbn_dict[intf]['ecio'] = msg.currentEcio
    
    elif event == 'event.radio.wcdma.RRCStateChangeEvent':
        _mbbn_dict[intf]['rrc'] = RRC[str(msg.currentRRCState)]
    
    elif event == 'state.generic.CurrentNetworkState':
        # this one comes periodically, every 5 seconds
        _mbbn_dict[intf]['uptime'] = msg.uptime
        #pppiface = msg.iface
        #ipAddr = msg.ipAddress
        _mbbn_dict[intf]['ipAddr']    = str(msg.ipAddress)
        _mbbn_dict[intf]['mode']    = MODE[str(msg.networkMode)]
        _mbbn_dict[intf]['submode'] = SUBMODE[str(msg.networkSubmode)]
        _mbbn_dict[intf]['rssi']    = msg.rssi
        _mbbn_dict[intf]['lac']     = msg.lac
        _mbbn_dict[intf]['cellid']  = msg.cellId
        _mbbn_dict[intf]['rrc']     = RRC[str(msg.RRCState)]
        _mbbn_dict[intf]['rscp']     = msg.rscp
        _mbbn_dict[intf]['ecio']     = msg.ecio


def _read_from_zmq(s_zmq, poller):
    # wait up to 100 msecs for new messages
    timeout = dict(poller.poll(100))
    if timeout.get(s_zmq) != zmq.POLLIN:
        return
    
    msg_parts = s_zmq.recv_multipart(flags=zmq.NOBLOCK)
    try:
        [topic, node, data] = msg_parts
    except:
        [topic, data] = msg_parts

    (mcc_mnc, event) = topic.split(".", 1)
    if not event in MESSAGES:
        print >> sys.stderr, "Unknown message from ZMQ %s!" % event
        return

    msg = MESSAGES[event]["class"]()
    msg.ParseFromString(data)
    _process_message(MCC_MNC_TO_INTF[mcc_mnc], event, msg)


def _update_subscriptions(s_zmq, intf_to_topic):
    global _mbbn_dict
    # query current state of interfaces
    intfs = interfaceinfo.getinfo()
    for intf, state in intfs.items():
        if state == 'UP':
            if not intf in intf_to_topic:
                # interface is up, we are not subscribed
                mcc_mnc = INTF_TO_MCC_MNC[intf]
                intf_to_topic[intf] = mcc_mnc
                _mbbn_dict[intf] = {} # allocate empty dict for interface
                s_zmq.setsockopt(zmq.SUBSCRIBE, mcc_mnc)
        else:
            if intf in intf_to_topic:
                # interface is down, we are subscribed
                s_zmq.setsockopt(zmq.UNSUBSCRIBE, intf_to_topic[intf])
                del _mbbn_dict[intf] # clean up
                del intf_to_topic[intf]
    return intf_to_topic
 

def _listen():
    global _stop
    try:
        context = zmq.Context()
        s_zmq = context.socket(zmq.SUB)
        s_zmq.connect(SUB_ADDR)
        s_zmq.setsockopt(zmq.LINGER, 0)

        time.sleep(0.1) # wait to avoid exception about poller
        poller = zmq.Poller()
        poller.register(s_zmq, zmq.POLLIN)
        try:
            intf_to_topic = {}
            while not _stop:
                intf_to_topic = _update_subscriptions(s_zmq, intf_to_topic)
                _read_from_zmq(s_zmq, poller)
        
        finally:
            poller.unregister(s_zmq)
            s_zmq.close()
            context.term()

    finally:
        global _thread
        _thread = None # signals that this thread has ended


def getinfo():
    # return a copy of the current state
    global _mbbn_dict
    return copy.deepcopy(_mbbn_dict)


def start():
    global _thread
    if not _thread is None:
        raise RuntimeError("interfaceinfo has been started already!")
    
    global _stop
    _stop = False
    _thread = threading.Thread(target = _listen)
    _thread.daemon = True
    _thread.start()


def stop():
    global _stop
    _stop = True
    global _thread
    while not _thread is None:
        time.sleep(0.01) # wait for thread to end
