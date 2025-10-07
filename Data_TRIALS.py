from dynamixel_sdk import *
import os
import time
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ---------------- Settings ----------------
ADDR_TORQUE_ENABLE      = 64
ADDR_GOAL_POSITION      = 116
ADDR_PRESENT_POSITION   = 132
ADDR_GOAL_VELOCITY      = 104
ADDR_PRESENT_VELOCITY   = 128
ADDR_PRESENT_CURRENT    = 126   # Present current (2 bytes, signed)
ADDR_OPERATING_MODE     = 11

PROTOCOL_VERSION        = 2.0
DXL_ID                  = 3
BAUDRATE                = 57600
DEVICENAME              = 'com6'

TORQUE_ENABLE           = 1
TORQUE_DISABLE          = 0
DEFAULT_POSITION        = 600
DEFAULT_VELOCITY        = 456
VELOCITY_UNIT_RPM       = 0.229  # 1 unit = 0.229 rpm
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
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_OPERATING_MODE, 1)  # Velocity Mode
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

print("  0 → Go to default position")
print("  1 → Start continuous clockwise rotation + logging")
print("  2/3/other → Stop logging, plot graph and show averages")
print("  q → Quit")

# ---------------- Data storage ----------------
time_data = []
velocity_data = []
current_data = []
rpm_data = []
torque_data = []   # derived from current
recording = False
start_time = None

def read_signed_2bytes(addr):
    """Reads a signed 16-bit value"""
    value, _, _ = packetHandler.read2ByteTxRx(portHandler, DXL_ID, addr)
    if value > 32767:  # convert unsigned to signed
        value -= 65536
    return value

# ---------------- Main loop ----------------
while True:
    key = getch()
    if key == 'q':
        print("Exiting...")
        break

    elif key == '0':
        print("➡ Going to default position...")
        # Switch to Position Mode
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_OPERATING_MODE, 3)
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
        packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION, DEFAULT_POSITION)

    elif key == '1':
        print("▶ Starting clockwise rotation and recording...")
        recording = True
        start_time = time.time()
        time_data, velocity_data, current_data, torque_data = [], [], [], []

        # Switch to Velocity Mode
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_OPERATING_MODE, 1)
        packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
        packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_VELOCITY, DEFAULT_VELOCITY)

        # Continuous logging until another key is pressed
        while True:
            if msvcrt.kbhit():  # check if key was pressed
                stop_key = msvcrt.getch().decode()
                if stop_key in ['2','3','0','q']:
                    print("⏹ ing and plotting...")
                    packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_VELOCITY, 0)
                    recording = False
                    break

            # Read velocity (ticks per 0.229 rpm unit)
            vel, _, _ = packetHandler.read4ByteTxRx(portHandler, DXL_ID, ADDR_PRESENT_VELOCITY)
            if vel > (1 << 31):  # signed conversion
                vel -= (1 << 32)

            # Read current (mA units)
            curr = read_signed_2bytes(ADDR_PRESENT_CURRENT)
            rpm = vel * VELOCITY_UNIT_RPM
            elapsed = time.time() - start_time
            torque_est = curr * 0.001  # placeholder: convert mA to Nm (calibrate experimentally)

            time_data.append(elapsed)
            velocity_data.append(vel)
            current_data.append(curr)
            rpm_data.append(rpm)
            torque_data.append(torque_est)

            print(f"t={elapsed:.2f}s | vel={vel} | current={curr}mA | torque={torque_est:.3f}Nm | rpm={rpm:.2f}")
            time.sleep(0.1)

        # ---- Plot results ----
        if len(time_data) > 0:
            plt.figure(figsize=(10,6))
            plt.subplot(2,1,1)
            plt.plot(time_data, velocity_data, label="Velocity")
            plt.ylabel("Velocity (ticks)")
            plt.legend()
            plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(12))  # More ticks
            plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(12))

            plt.subplot(2,1,2)
            plt.plot(time_data, rpm_data, label="RPM", color="blue")
            plt.xlabel("Time (s)")
            plt.ylabel("RPM")
            plt.legend()
            plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(12))  # More ticks
            plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(12))

            plt.figure(figsize=(10,6))
            plt.subplot(2,1,1)
            plt.plot(time_data, current_data, label="Current", color="orange")
            plt.ylabel("Current (mA)")
            plt.legend()
            plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(12))  # More ticks
            plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(12))

            plt.subplot(2,1,2)
            plt.plot(time_data, torque_data, label="Torque (Nm)", color="green")
            plt.xlabel("Time (s)")
            plt.ylabel("Torque (Nm)")
            plt.legend()
            plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(12))  # More ticks
            plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(12))            
            plt.tight_layout()
            plt.show()
            print("\nAverages:")
            print(f" Avg Velocity = {sum(velocity_data)/len(velocity_data):.2f}")
            print(f" Avg Current = {sum(current_data)/len(current_data):.2f} mA")
            print(f" Avg Torque  = {sum(torque_data)/len(torque_data):.3f} Nm")
            print(f" Avg RPM     = {sum(rpm_data)/len(rpm_data):.2f} RPM\n")
        else:
            print("⚠ No data collected!")

# ---------------- Shutdown ----------------
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort()
print("Torque disabled and port closed.")
 