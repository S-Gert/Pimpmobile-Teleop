import rclpy
from rclpy.node import Node
from evdev import InputDevice, categorize, ecodes
import threading
import time
from std_msgs.msg import Int32MultiArray  # Import Int32MultiArray
import evdev

#from std_msgs.msg import String

def get_g29_event_code():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    
    for device in devices:
        if "Logitech G29 Driving Force Racing Wheel" in device.name:
            return device.path 
    
    return None

device = InputDevice(f"{get_g29_event_code()}")

class MinimalPublisher(Node):

    def __init__(self):
        super().__init__('minimal_publisher')
        self.publisher_ = self.create_publisher(Int32MultiArray, 'pimpmobile_teleop', 10)
        timer_period = 0.1 
        self.timer = self.create_timer(timer_period, self.read_events)

        self.time_since_handbrake_toggle = 0
        self.time_since_stanley_toggle = 0
        self.time_since_gps_save_toggle = 0
        self.time_since_reset_press = 0

        self.steering_wheel = 0
        self.gas_pedal = 0
        self.brake_pedal = 0
        self.gear = 0
        self.stanlet_reset = 0
        self.stanley_k = 0
        self.stanley_v = 0

        self.speed_limiter_knob = 100
        self.handbrake_toggle = 0
        self.stanley_drive_toggle = 0
        self.gps_save_toggle = 0

    def m_map(self, value, leftMin, leftMax, rightMin, rightMax):
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin
        valueScaled = float(value - leftMin) / float(leftSpan)
        return rightMin + (valueScaled * rightSpan)

    def read_events(self):
        msg = Int32MultiArray()  # Create an Int32MultiArray message

        for event in device.read_loop():
            self.stanley_reset = 0

            if event.type == ecodes.EV_ABS:
                if event.code == 0:
                    self.steering_wheel = round(self.m_map(event.value, 0, 65535, -255, 255))

                if event.code == 5:
                    self.brake_pedal = event.value
                    if self.brake_pedal < 150:
                        self.brake_pedal = 1
                    else:
                        self.brake_pedal = 0

                if event.code == 2:
                    self.gas_pedal = 255 - event.value

                if event.code == 17:
                    self.stanley_k = -event.value

                if event.code == 16:
                    self.stanley_v = event.value

            elif event.type == ecodes.EV_KEY:
                if event.code == 292:
                    self.gear = 0
                elif event.code == 293: # 
                    self.gear = 1
                elif event.code == 709: # SPEED LIMITER
                    if self.speed_limiter_knob < 100:
                        self.speed_limiter_knob += 1 # The big red circle
                elif event.code == 710: # SPEED LIMITER
                    if self.speed_limiter_knob > 0:
                        self.speed_limiter_knob -= 1
                elif event.code == 711: # HANDBRAKE BUTTON
                    if time.time() > self.time_since_handbrake_toggle + 0.2:                      
                        if self.handbrake_toggle == 0:
                            self.handbrake_toggle = 1
                        else:
                            self.handbrake_toggle = 0
                    self.time_since_handbrake_toggle = time.time()

                elif event.code == 296: # GPS SAVING TOGGLE
                    if time.time() > self.time_since_gps_save_toggle + 0.2:                      
                        if self.gps_save_toggle == 0:
                            self.gps_save_toggle = 1
                        else:
                            self.gps_save_toggle = 0
                        self.time_since_gps_save_toggle = time.time()
                
                elif event.code == 297: # STANLEY PATH STATE RESET
                    if time.time() > self.time_since_reset_press + 0.5:                      
                        self.stanley_reset = 1
                    else:
                        self.stanley_reset = 0
                    self.time_since_reset_press = time.time()

                elif event.code == 712: # STANLEY DRIVE BUTTON
                    if time.time() > self.time_since_stanley_toggle + 0.2:                      
                        if self.stanley_drive_toggle == 0:
                            self.stanley_drive_toggle = 1
                        else:
                            self.stanley_drive_toggle = 0
                        self.time_since_stanley_toggle = time.time()


            data_arr = [self.gas_pedal, self.steering_wheel, self.brake_pedal, 
                        self.gear, self.speed_limiter_knob, self.handbrake_toggle, 
                        self.gps_save_toggle, self.stanley_reset, self.stanley_drive_toggle, 
                        self.stanley_k, self.stanley_v]
            
            msg.data = data_arr
            print(data_arr)
            self.publisher_.publish(msg)  # Publish the array
            #print(event)


def main(args=None):
    rclpy.init(args=args)
    minimal_publisher = MinimalPublisher()
    rclpy.spin(minimal_publisher)
    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()