from dynamixel_sdk import *
import os
import time

# ---------------- Settings ----------------
ADDR_MX_TORQUE_ENABLE      = 24
ADDR_MX_GOAL_POSITION      = 30
ADDR_MX_PRESENT_POSITION   = 36
ADDR_MX_MOVING_SPEED       = 32
ADDR_MX_CW_ANGLE_LIMIT     = 6
ADDR_MX_CCW_ANGLE_LIMIT    = 8
ADDR_MX_TORQUE_LIMIT       = 34   

PROTOCOL_VERSION           = 1.0
DXL_ID                     = 101
BAUDRATE                   = 57600
DEVICENAME                 = 'com6'

TORQUE_ENABLE              = 1
TORQUE_DISABLE             = 0
DXL_MOVING_SPEED           = 1023     # reasonable default speed
DXL_TORQUE_LIMIT           = 800
DEFAULT_POSITION           = 1023    # midpoint of 0–4095 range

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

# Disable torque before setting limits
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE)

# Allow multi-turn (set angle limits wide)
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_CW_ANGLE_LIMIT, 0)
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_CCW_ANGLE_LIMIT, 4095)

# Enable torque
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_ENABLE)

# Set torque limit
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_LIMIT, DXL_TORQUE_LIMIT)

packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_MOVING_SPEED, 0)

print("  0 → Go to default position")
print("  1 → Continuous clockwise rotation")
print("  2 → Continuous anticlockwise rotation")
print("  3 → Stop")
print("  q → Quit")

# ---------------- State Machine ----------------
state = None

while True:
    key = getch()
    if key == 'q':
        print("Exiting...")
        break

    elif key == '0':
        state = "DEFAULT"
        # print("➡ Going to default position...")
        # packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_MOVING_SPEED, DXL_MOVING_SPEED)
        # packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_GOAL_POSITION, DEFAULT_POSITION)
        # print(ADDR_MX_GOAL_POSITION)    # Restore joint (position) mode
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE)
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_CW_ANGLE_LIMIT, 0)
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_CCW_ANGLE_LIMIT, 4095)
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_ENABLE)

        # Set speed and goal
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_MOVING_SPEED, DXL_MOVING_SPEED)
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_GOAL_POSITION, DEFAULT_POSITION)

        # Print live position until target is reached
        while True:
            dxl_present_position, dxl_comm_result, dxl_error = packetHandler.read2ByteTxRx(
                portHandler, DXL_ID, ADDR_MX_PRESENT_POSITION
            )
            if dxl_comm_result != COMM_SUCCESS:
                print("Comm error:", packetHandler.getTxRxResult(dxl_comm_result))
                break
            elif dxl_error != 0:
                print("Error:", packetHandler.getRxPacketError(dxl_error))
                break

            print(f"Current Position: {dxl_present_position}")

            if abs(dxl_present_position - DEFAULT_POSITION) < 20:
                print("✅ Reached default position.")
                packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_MOVING_SPEED, 0)
                break

            time.sleep(0.1)

    elif key == '1':
        state = "CLOCKWISE"
        print("Continuous clockwise rotation...")
        # For continuous rotation: write speed only
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_MOVING_SPEED, DXL_MOVING_SPEED)

    elif key == '2':
        state = "ANTICLOCKWISE"
        print("Continuous anticlockwise rotation...")
        # Negative speed = anticlockwise
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_MOVING_SPEED, 1024 + DXL_MOVING_SPEED)

    elif key == '3':
        state = "STOP"
        print("Stopping...")
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MX_MOVING_SPEED, 0)

    else:
        print("Invalid input! Use 0, 1, 2, 3, or q.")

    time.sleep(0.1)

# ---------------- Shutdown ----------------
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort()
print("Torque disabled and port closed.")
