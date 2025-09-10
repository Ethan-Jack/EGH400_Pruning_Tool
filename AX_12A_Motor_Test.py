# #!/usr/bin/env python
# # -*- coding: utf-8 -*-

# ################################################################################
# # Copyright 2017 ROBOTIS CO., LTD.
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #     http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# ################################################################################

# # Author: Ryu Woon Jung (Leon)

# #
# # *********     Read and Write Example      *********
# #
# #
# # Available DXL model on this example : All models using Protocol 1.0
# # This example is tested with a DXL MX-28, and an USB2DYNAMIXEL
# # Be sure that DXL MX properties are already set as %% ID : 1 / Baudnum : 34 (Baudrate : 57600)
# #

# import os

# if os.name == 'nt':
#     import msvcrt
#     def getch():
#         return msvcrt.getch().decode()
# else:
#     import sys, tty, termios
#     fd = sys.stdin.fileno()
#     old_settings = termios.tcgetattr(fd)
#     def getch():
#         try:
#             tty.setraw(sys.stdin.fileno())
#             ch = sys.stdin.read(1)
#         finally:
#             termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
#         return ch

# from dynamixel_sdk import *                    # Uses Dynamixel SDK library

# # Control table address
# ADDR_MX_TORQUE_ENABLE      = 24               # Control table address is different in Dynamixel model
# ADDR_MX_GOAL_POSITION      = 30
# ADDR_MX_PRESENT_POSITION   = 36
# ADDR_MX_MOVING_SPEED = 32

# ADDR_MX_CW_ANGLE_LIMIT = 6
# ADDR_MX_CCW_ANGLE_LIMIT = 8

# # Protocol version
# PROTOCOL_VERSION            = 1.0               # See which protocol version is used in the Dynamixel

# # Default setting
# DXL_ID                      = 101                 # Dynamixel ID : 1
# BAUDRATE                    = 1000000             # Dynamixel default baudrate : 57600
# DEVICENAME                  = 'com6'    # Check which port is being used on your controller
#                                                 # ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

# TORQUE_ENABLE               = 1                 # Value for enabling the torque
# TORQUE_DISABLE              = 0                 # Value for disabling the torque
# DXL_MINIMUM_POSITION_VALUE  = 10           # Dynamixel will rotate between this value
# DXL_MAXIMUM_POSITION_VALUE  = 1500            # and this value (note that the Dynamixel would not move when the position value is out of movable range. Check e-manual about the range of the Dynamixel you use.)
# DXL_MOVING_STATUS_THRESHOLD = 20                # Dynamixel moving status threshold
# DXL_MOVING_SPEED = 600#50
# DXL_MOVING_SPEED_STOP       = 0    

# index = 0
# dxl_goal_position = [DXL_MINIMUM_POSITION_VALUE, DXL_MAXIMUM_POSITION_VALUE]         # Goal position


# # Initialize PortHandler instance
# # Set the port path
# # Get methods and members of PortHandlerLinux or PortHandlerWindows
# portHandler = PortHandler(DEVICENAME)

# # Initialize PacketHandler instance
# # Set the protocol version
# # Get methods and members of Protocol1PacketHandler or Protocol2PacketHandler
# packetHandler = PacketHandler(PROTOCOL_VERSION)

# # Open port
# if portHandler.openPort():
#     print("Succeeded to open the port")
# else:
#     print("Failed to open the port")
#     print("Press any key to terminate...")
#     getch()
#     quit()


# # Set port baudrate
# if portHandler.setBaudRate(BAUDRATE):
#     print("Succeeded to change the baudrate")
# else:
#     print("Failed to change the baudrate")
#     print("Press any key to terminate...")
#     getch()
#     quit()

# # Enable Dynamixel Torque
# packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_CW_ANGLE_LIMIT, 0)
# packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_CCW_ANGLE_LIMIT, 0)
# dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_ENABLE)
# if dxl_comm_result != COMM_SUCCESS:
#     print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
# elif dxl_error != 0:
#     print("%s" % packetHandler.getRxPacketError(dxl_error))
# else:
#     print("Dynamixel has been successfully connected")

# while 1:
#     print("Press any key to continue! (or press ESC to quit!)")
#     if getch() == chr(0x1b):
#         break

#     # Set the moving speed
#     dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_MOVING_SPEED, DXL_MOVING_SPEED)
#     if dxl_comm_result != COMM_SUCCESS:
#         print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
#     elif dxl_error != 0:
#         print("%s" % packetHandler.getRxPacketError(dxl_error))

#     # # Write goal position
#     # dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_GOAL_POSITION, dxl_goal_position[index])
#     # if dxl_comm_result != COMM_SUCCESS:
#     #     print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
#     # elif dxl_error != 0:
#     #     print("%s" % packetHandler.getRxPacketError(dxl_error))

#     while 1:
#         # Read present position
#         dxl_present_position, dxl_comm_result, dxl_error = packetHandler.read2ByteTxRx(portHandler, DXL_ID, ADDR_MX_PRESENT_POSITION)
#         if dxl_comm_result != COMM_SUCCESS:
#             print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
#         elif dxl_error != 0:
#             print("%s" % packetHandler.getRxPacketError(dxl_error))

#         print("[ID:%03d] GoalPos:%03d  PresPos:%03d" % (DXL_ID, dxl_goal_position[index], dxl_present_position))

#         if not abs(dxl_goal_position[index] - dxl_present_position) > DXL_MOVING_STATUS_THRESHOLD:

#             break

#     # Change goal position
#     if index == 0:
#         index = 1
#     else:
#         index = 0

# # Disable Dynamixel Torque
# dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE)
# if dxl_comm_result != COMM_SUCCESS:
#     print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
# elif dxl_error != 0:
#     print("%s" % packetHandler.getRxPacketError(dxl_error))

# # Close port
# portHandler.closePort()
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
from dynamixel_sdk import *

# Control table address
ADDR_MX_TORQUE_ENABLE      = 24
ADDR_MX_GOAL_POSITION      = 30
ADDR_MX_PRESENT_POSITION   = 36
ADDR_MX_MOVING_SPEED       = 32
ADDR_MX_CW_ANGLE_LIMIT     = 6
ADDR_MX_CCW_ANGLE_LIMIT    = 8
ADDR_MX_TORQUE_LIMIT       = 34

# Protocol version
PROTOCOL_VERSION            = 1.0

# Default setting
DXL_ID                      = 101
BAUDRATE                     = 1000000
DEVICENAME                  = 'com6'

TORQUE_ENABLE               = 1
TORQUE_DISABLE              = 0
DXL_MOVING_SPEED            = 300
DXL_TORQUE_LIMIT            = 800
POSITION_THRESHOLD          = 10   # ticks tolerance

# Initialize PortHandler & PacketHandler
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

if not portHandler.openPort() or not portHandler.setBaudRate(BAUDRATE):
    print("❌ Failed to open port or set baudrate")
    quit()

# ---------------- Set Joint Mode ----------------
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE)
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_CW_ANGLE_LIMIT, 0)
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_CCW_ANGLE_LIMIT, 1023)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_ENABLE)

# Set torque limit and speed
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_LIMIT, DXL_TORQUE_LIMIT)
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_MOVING_SPEED, DXL_MOVING_SPEED)

print("✅ Joint mode enabled. Type a position (0-1023) or 'q' to quit.")

while True:
    user_input = input("Enter goal position: ")
    if user_input.lower() == 'q':
        break
    try:
        goal_position = int(user_input)
        if not 0 <= goal_position <= 1023:
            print("⚠️ Position must be between 0 and 1023")
            continue
    except ValueError:
        print("⚠️ Invalid input")
        continue

    # Move to the typed position
    packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_GOAL_POSITION, goal_position)

    # Wait until the position is reached
    while True:
        present_position, _, _ = packetHandler.read2ByteTxRx(portHandler, DXL_ID, ADDR_MX_PRESENT_POSITION)
        print(f"[ID:{DXL_ID}] GoalPos:{goal_position}  PresentPos:{present_position}", end='\r')
        if abs(present_position - goal_position) <= POSITION_THRESHOLD:
            print(f"\n✅ Reached position {goal_position}")
            break
        time.sleep(0.05)

# Disable torque and close port
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort()
print("✅ Torque disabled, port closed.")
