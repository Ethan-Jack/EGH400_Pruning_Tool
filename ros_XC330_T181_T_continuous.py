from dynamixel_sdk import *
import os
import time

# ---------------- Settings ----------------
ADDR_TORQUE_ENABLE      = 64
ADDR_GOAL_POSITION      = 116   # 4 bytes
ADDR_PRESENT_POSITION   = 132   # 4 bytes
ADDR_GOAL_VELOCITY      = 104   # 4 bytes
ADDR_PRESENT_VELOCITY   = 128   # 4 bytes
ADDR_CURRENT_LIMIT      = 38    # 2 bytes
ADDR_OPERATING_MODE     = 11    # 1 byte

PROTOCOL_VERSION        = 2.0
DXL_ID                  = 3
BAUDRATE                = 57600
DEVICENAME              = 'com6'

TORQUE_ENABLE           = 1
TORQUE_DISABLE          = 0
DEFAULT_POSITION        = 100   # midpoint of 0–4095 range
DEFAULT_VELOCITY        = 400     # small velocity value for safe testing

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

# Disable torque before setting mode
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)

# Set to Position Control Mode (3)
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(
    portHandler, DXL_ID, ADDR_OPERATING_MODE, 3
)
if dxl_comm_result != COMM_SUCCESS:
    print("Comm error:", packetHandler.getTxRxResult(dxl_comm_result))
elif dxl_error != 0:
    print("Packet error:", packetHandler.getRxPacketError(dxl_error))

# Enable torque
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

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
        print("➡ Going to default position...")

        # Switch to Position Control
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_OPERATING_MODE, 3)  # Position Mode
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

        # Send goal position
        packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION, DEFAULT_POSITION)

        # Monitor until reached
        while True:
            dxl_present_position, dxl_comm_result, dxl_error = packetHandler.read4ByteTxRx(
                portHandler, DXL_ID, ADDR_PRESENT_POSITION
            )
            if dxl_comm_result != COMM_SUCCESS:
                print("Comm error:", packetHandler.getTxRxResult(dxl_comm_result))
                break
            elif dxl_error != 0:
                print("Error:", packetHandler.getRxPacketError(dxl_error))
                break

            print(f"Current Position: {dxl_present_position}")

            if abs(dxl_present_position - DEFAULT_POSITION) < 20:
                print(" Reached default position.")
                break

            time.sleep(0.1)

    elif key == '1':
        state = "CLOCKWISE"
        print("Continuous clockwise rotation...")

        # Switch to Velocity Control
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_OPERATING_MODE, 1)  # Velocity Mode
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

        # Positive velocity = clockwise
        packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_VELOCITY, DEFAULT_VELOCITY)

    elif key == '2':
        state = "ANTICLOCKWISE"
        print("Continuous anticlockwise rotation...")

        # Switch to Velocity Control
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_OPERATING_MODE, 1)  # Velocity Mode
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

        # Negative velocity = anticlockwise
        # Must be written as signed 32-bit integer
        velocity_value = (1 << 32) + (-DEFAULT_VELOCITY)  # convert negative to unsigned 32-bit
        packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_VELOCITY, velocity_value)

    elif key == '3':
        state = "STOP"
        print("Stopping...")
        packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_VELOCITY, 0)

    else:
        print("Invalid input! Use 0, 1, 2, 3, or q.")

    time.sleep(0.1)

# ---------------- Shutdown ----------------
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort()
print("Torque disabled and port closed.")
