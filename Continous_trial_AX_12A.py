from dynamixel_sdk import *
import os
import matplotlib.pyplot as plt
import time

# ---------------- Settings ----------------
ADDR_MX_TORQUE_ENABLE      = 24
ADDR_MX_GOAL_POSITION      = 30
ADDR_MX_PRESENT_POSITION   = 36
ADDR_MX_MOVING_SPEED       = 32
ADDR_MX_PRESENT_SPEED      = 38
ADDR_MX_CW_ANGLE_LIMIT     = 6
ADDR_MX_CCW_ANGLE_LIMIT    = 8
ADDR_MX_PRESENT_LOAD       = 40
ADDR_MX_TORQUE_LIMIT       = 34   # NEW: Torque Limit register

PROTOCOL_VERSION           = 1.0

DXL_ID                     = 101
BAUDRATE                   = 1000000
DEVICENAME                 = 'com6'

TORQUE_ENABLE              = 1
TORQUE_DISABLE             = 0
DXL_MOVING_STATUS_THRESHOLD = 20
DXL_MOVING_SPEED           = 1023   # adjust for desired RPM

TICKS_PER_REV              = 4096
REVOLUTIONS                = 10     # how many full 360° turns

DXL_TORQUE_LIMIT           = 1023    # NEW: 50% of maximum torque (0–1023)

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

# ---------------- Set Torque Limit ----------------
dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(
    portHandler, DXL_ID, ADDR_MX_TORQUE_LIMIT, DXL_TORQUE_LIMIT
)
if dxl_comm_result != COMM_SUCCESS:
    print(f"Comm Error: {packetHandler.getTxRxResult(dxl_comm_result)}")
elif dxl_error != 0:
    print(f"Error: {packetHandler.getRxPacketError(dxl_error)}")
else:
    print(f"Torque limit set to {DXL_TORQUE_LIMIT}/1023")

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
counter_goal_position = REVOLUTIONS*(360 / 300)
threshold = 10  # tolerance for near zero
dxl_present_position_prev = None  # initialize as None for first loop

# ---------------- Record Present Speed ----------------
timestamps = []
rpm_values = []
start_time = time.time()
rpm_average_size = 5
rpm_buffer = []
while True:
    current_time = time.time()
    dxl_present_position_cur, _, _ = packetHandler.read2ByteTxRx(portHandler, DXL_ID, ADDR_MX_PRESENT_POSITION)
    speed_raw, _, _ = packetHandler.read2ByteTxRx(portHandler, DXL_ID, ADDR_MX_PRESENT_SPEED)

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
    # Calculate RPM
    if speed_raw >1023:
        signed_raw = -(speed_raw - 1024)
    else:
        signed_raw = speed_raw
    
    dxl_present_position_prev = dxl_present_position_cur
    # Calculating RPM values
    rpm = speed_raw * 114/1023

    # Calculate current average before appending new value
    if len(rpm_buffer) > 0:
        rpm_average = sum(rpm_buffer) / len(rpm_buffer)
    else:
        rpm_average = rpm  # First value, no average yet

    # Spike check: if new rpm is >30 above average, clamp it
    if DXL_TORQUE_LIMIT > 700:
        adjusted_limit = 60
    else:
        adjusted_limit = 30
    if rpm >70:
        rpm = rpm_average
    if rpm > rpm_average + adjusted_limit:
        rpm_smooth = rpm_average
    else:
        rpm_smooth = rpm

    # Now append the *filtered* value to buffer
    rpm_buffer.append(rpm_smooth)

    # Keep buffer size fixed
    if len(rpm_buffer) > rpm_average_size:
        rpm_buffer.pop(0)

    # Save values
    rpm_values.append(rpm_smooth)
    timestamps.append(current_time - start_time)



    
    if counter >= counter_goal_position:
        print("Reached target position.")
        break

    # Optionally break if close to target position (can remove if not useful)
    if abs(target_position - dxl_present_position_cur) <= DXL_MOVING_STATUS_THRESHOLD:
        break
    
# ---------------- Shutdown ----------------
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort() 
if len(rpm_values) > 0:
    overall_average = sum(rpm_values) / len(rpm_values)
    print(f"Overall Average RPM: {overall_average:.2f}")
else:
    print("No RPM data collected.")

# ---------------- Plot ----------------
plt.figure(figsize=(10,5))
plt.plot(timestamps, rpm_values, label="Present Speed (rev/min)")
plt.xlabel("Time (s)")
plt.ylabel("Speed (rev/min)")
plt.title("AX-12A Present Speed Over Time")
plt.grid(True)
plt.legend()
plt.show()

quit()