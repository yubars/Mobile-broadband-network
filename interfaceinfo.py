#!/usr/bin/python

import copy
import fcntl
import netifaces
import socket
import threading
import time

from ctypes import create_string_buffer, Structure, c_uint32, c_uint16
from ctypes import c_uint8, sizeof, addressof, c_int32, string_at


#These are all taken from kernel sources
NETLINK_GENERIC = 16
NLMSG_MAX_LEN   = 0xFFFF
IFNAMSIZ        = 16
SIOCGIFNAME     = 0x8910
ETHFACE         = 'eth1'

#These are a bit arbritary
LINK_DOWN = 0
LINK_UP   = 1

class struct_nlmsghdr(Structure):
    _fields_ = [
        ("nlmsg_len",   c_uint32),
        ("nlmsg_type",  c_uint16),
        ("nlmsg_flags", c_uint16),
        ("nlmsg_seq",   c_uint32),
        ("nlmsg_pid",   c_uint32)]

class struct_multimsg(Structure):
    _pack_ = 1
    _fields_ = [
        ('state', c_uint8),
        ('idx',   c_int32)]

class struct_nlmsg(Structure):
    _fields_ = [
        ("hdr",  struct_nlmsghdr),
        ("data", c_uint8 * (NLMSG_MAX_LEN - sizeof(struct_nlmsghdr)))]

class struct_ifreqidx(Structure):
    _fields_ = [
        ('ifr_name',    c_uint8 * IFNAMSIZ),
        ('ifr_ifindex', c_int32)]


_start_count = 0
_thread      = None
_stop        = True
_multi_dict  = {}


def _get_interface_name(s_ioctl, idx):
    ifreq = struct_ifreqidx()
    ifreq.ifr_ifindex = idx
    try:
        fcntl.ioctl(s_ioctl.fileno(), SIOCGIFNAME, ifreq)
    
    except:
        return ''
    
    devname = string_at(addressof(ifreq.ifr_name))
    return devname


def _listen():
    try:
        # socket used for MULTI
        s = socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM, NETLINK_GENERIC)
        s.bind((0, 1)) # bind to group 1 (MULTI group, temporary)
        
        # socket used for IOCTL
        s_ioctl = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        nlmsg = struct_nlmsg()
        
        try:
            global _multi_dict
            _multi_dict.clear()
            
            global _stop
            while not _stop:
                numbytes = s.recv_into(nlmsg, sizeof(struct_nlmsg))
                multimsg = struct_multimsg.from_address(addressof(nlmsg.data))
                devname  = _get_interface_name(s_ioctl, multimsg.idx)
                
           
                if 'ppp' in devname:
                    ppp_ifaces = [ iface for iface in netifaces.interfaces() if 'ppp' in iface ]
                    if ppp_ifaces.index(devname) >= 0: # is it an actual device?
                        if multimsg.state == LINK_UP:
                            _multi_dict[devname] = 'UP'
                        else:
                            _multi_dict[devname] = 'DOWN'
            
        finally:
            s_ioctl.close()
            s.close()
        
    finally:
        global _thread
        _thread = None # signals that this thread has ended


def getinfo():
    # return a copy of the current state
    global _multi_dict
    return copy.deepcopy(_multi_dict)


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
