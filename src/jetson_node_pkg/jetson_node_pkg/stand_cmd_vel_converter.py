#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from motion_msgs.msg import MotionCtrl

class StandCmdVelConverter(Node):
    def __init__(self):
        super().__init__('stand_cmd_vel_converter')
        
        self.sub_vel = self.create_subscription(Twist, '/cmd_vel', self.cmd_callback, 10)
        self.sub_stand = self.create_subscription(Bool, '/stand_cmd', self.stand_callback, 10)
        self.pub = self.create_publisher(MotionCtrl, '/diablo/MotionCmd', 10)
        
        # =========================================================
        # 【核心修复】：默认状态设为站立，且高度保持最高！
        # 这样一启动就不会给机器人发“深蹲”指令了
        # =========================================================
        self.is_standing = True 
        self.current_up = 1.0     # 1.0 就是最高位置，你可以改成 0.5 变成半蹲
        self.current_forward = 0.0
        self.current_left = 0.0
        
        self.timer = self.create_timer(0.04, self.timer_callback)
        self.get_logger().info("站立版 Diablo 转换器已启动！锁定高姿态。")

    def cmd_callback(self, msg: Twist):
        self.current_forward = float(msg.linear.x)
        self.current_left = float(msg.angular.z)

    def stand_callback(self, msg: Bool):
        self.is_standing = msg.data
        self.current_forward = 0.0
        self.current_left = 0.0
        
        if self.is_standing:
            self.publish_state(mode_mark=True, stand_mode=True, up=0.0)
            self.current_up = 1.0 # 如果收到起立命令，升到最高
            self.publish_state(mode_mark=False, stand_mode=True, up=self.current_up)
        else:
            self.current_up = 0.0
            self.publish_state(mode_mark=True, stand_mode=False, up=0.0)

    def timer_callback(self):
        self.publish_state(mode_mark=False, stand_mode=self.is_standing, up=self.current_up)

    def publish_state(self, mode_mark, stand_mode, up):
        msg = MotionCtrl()
        msg.mode_mark = mode_mark 
        msg.mode.stand_mode = stand_mode
        msg.mode.pitch_ctrl_mode = False 
        msg.mode.roll_ctrl_mode = False
        msg.mode.height_ctrl_mode = False
        msg.mode.jump_mode = False
        msg.mode.split_mode = False
        msg.value.forward = self.current_forward
        msg.value.left = self.current_left
        msg.value.up = up
        msg.value.roll = 0.0
        msg.value.pitch = 0.0
        msg.value.leg_split = 0.0
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = StandCmdVelConverter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()