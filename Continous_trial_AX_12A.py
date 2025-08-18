#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dynamixel_sdk import *
import os

# ---------------- Settings ----------------
ADDR_MX_TORQUE_ENABLE      = 24
ADDR_MX_GOAL_POSITION      = 30
ADDR_MX_PRESENT_POSITION   = 36
ADDR_MX_MOVING_SPEED       = 32
ADDR_MX_CW_ANGLE_LIMIT     = 6
ADDR_MX_CCW_ANGLE_LIMIT    = 8
ADDR_MX_PRESENT_LOAD       = 40
PROTOCOL_VERSION           = 1.0

DXL_ID                     = 101
BAUDRATE                   = 1000000
DEVICENAME                 = 'com3'

TORQUE_ENABLE              = 1
TORQUE_DISABLE             = 0
DXL_MOVING_STATUS_THRESHOLD = 20
DXL_MOVING_SPEED           = 1000   # adjust for desired RPM

TICKS_PER_REV              = 4096
REVOLUTIONS                = 5     # how many full 360° turns

# ---------------- Utility for getch ----------------
if os.name == 'nt':
    import msvcrt
    def getch(): return msvcrt.getch().decode()
else:
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

# ---------------- Init ----------------
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

if not portHandler.openPort():
    print("Failed to open port")
    quit()
if not portHandler.setBaudRate(BAUDRATE):
    print("Failed to set baudrate")
    quit()
print("Waiting for 's' to start... (Press 'q' to quit)")
while True:
    key = getch().lower()
    if key == 's':
        print("Starting rotation...")
        break
    elif key == 'q':
        print("Quitting program.")
        portHandler.closePort()
        quit()

# ---------------- Set Multi-Turn Limits ----------------
# Disable torque before changing limits
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE)

# Allow CW from 0 ticks to CCW up to 5 turns worth of ticks
max_position_limit = TICKS_PER_REV * REVOLUTIONS
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_CW_ANGLE_LIMIT, 0)
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_CCW_ANGLE_LIMIT, max_position_limit)

# Enable torque again
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_ENABLE)

# ---------------- Set Speed ----------------
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_MOVING_SPEED, DXL_MOVING_SPEED)

# ---------------- Get Start Position ----------------
dxl_present_position, _, _ = packetHandler.read2ByteTxRx(portHandler, DXL_ID, ADDR_MX_PRESENT_POSITION)
print(f"Start position: {dxl_present_position}")

# Target = start position + (5 revolutions worth of ticks)
target_position = dxl_present_position + (TICKS_PER_REV * REVOLUTIONS)
print(f"Target position: {target_position}")

# ---------------- Command Move ----------------
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_GOAL_POSITION, target_position)

# ---------------- Wait Until Done ----------------
counter = 0
counter_goal_position = 5*(360 / 300)
threshold = 10  # tolerance for near zero
dxl_present_position_prev = None  # initialize as None for first loop

while True:
    dxl_present_position_cur, _, _ = packetHandler.read2ByteTxRx(portHandler, DXL_ID, ADDR_MX_PRESENT_POSITION)

    if dxl_present_position_prev is None:
        dxl_present_position_prev = dxl_present_position_cur
        continue

    # Detect crossing from above threshold to within threshold (near zero)
    if abs(dxl_present_position_cur) <= threshold and abs(dxl_present_position_prev) > threshold:
        counter += 1
        print(f"Pass {counter}: Goal Position: {counter_goal_position}")
        if key == 'q':
            print("Quitting program.")
            break

    dxl_present_position_prev = dxl_present_position_cur

    if counter >= counter_goal_position:
        print("Reached target position.")
        break

    # Optionally break if close to target position (can remove if not useful)
    if abs(target_position - dxl_present_position_cur) <= DXL_MOVING_STATUS_THRESHOLD:
        break
    
# ---------------- Shutdown ----------------
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort() 