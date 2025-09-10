#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dynamixel_sdk import *
import os
import time

# ---------------- Settings ----------------
ADDR_MX_TORQUE_ENABLE      = 24
ADDR_MX_GOAL_POSITION      = 30
ADDR_MX_PRESENT_POSITION   = 36
ADDR_MX_MOVING_SPEED       = 32
ADDR_MX_PRESENT_LOAD       = 40   # Load address (2 bytes)
ADDR_MX_MAX_TORQUE         = 14

PROTOCOL_VERSION           = 1.0
DXL_ID                     = 1
BAUDRATE                   = 1000000
DEVICENAME                 = 'COM3'  # Change to your port

TORQUE_ENABLE              = 1
TORQUE_DISABLE             = 0

# ---------------- State Machine ----------------
STATE_INIT = "INIT"
STATE_START = "START"
STATE_RUN = "RUN"
STATE_PAUSE = "PAUSE"
STATE_EXIT = "EXIT"

# ---------------- Setup ----------------
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

if not portHandler.openPort():
    print("Failed to open port")
    quit()
if not portHandler.setBaudRate(BAUDRATE):
    print("Failed to set baudrate")
    quit()

packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_ENABLE)

# ---------------- Main Loop ----------------
state = STATE_INIT

while state != STATE_EXIT:
    if state == STATE_INIT:
        print(">> State: INIT")
        # Always return to starting position
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_GOAL_POSITION, 512)
        time.sleep(2)
        state = STATE_START

    elif state == STATE_START:
        print(">> State: START (waiting for input)")
        key = input("Press 'r' to run, 'e' to pause, 'q' to quit: ")
        if key == 'r':
            state = STATE_RUN
        elif key == 'e':
            state = STATE_PAUSE
        elif key == 'q':
            state = STATE_EXIT

    elif state == STATE_RUN:
        print(">> State: RUN")
        # Example: spin continuously
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_MOVING_SPEED, 300)
        time.sleep(0.1)
        state = STATE_START  # Return after running one cycle

    elif state == STATE_PAUSE:
        print(">> State: PAUSE (holding position)")
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_MOVING_SPEED, 0)
        time.sleep(1)
        state = STATE_START

# ---------------- Cleanup ----------------
print(">> Disabling torque and closing port")
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort()
