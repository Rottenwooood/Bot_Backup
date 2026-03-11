import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from motion_msgs.msg import MotionCtrl

class CmdVelConverter(Node):
    def __init__(self):
        super().__init__('cmd_vel_converter')
        
        # 订阅 Nav2 的速度和我们自定义的姿态指令
        self.sub_vel = self.create_subscription(Twist, '/cmd_vel', self.cmd_callback, 10)
        self.sub_stand = self.create_subscription(Bool, '/stand_cmd', self.stand_callback, 10)
        
        # 发布给 Diablo 底层
        self.pub = self.create_publisher(MotionCtrl, '/diablo/MotionCmd', 10)
        
        # --- 核心状态缓存 ---
        self.is_standing = False
        self.current_forward = 0.0
        self.current_left = 0.0
        self.current_up = 0.0
        
        # 模拟官方的 25Hz (0.04s) 心跳定时器
        self.timer = self.create_timer(0.04, self.timer_callback)
        
        self.get_logger().info("Diablo Control Bridge Started (Official Logic Version).")
        self.get_logger().info("Ready for Nav2 and Posture Control.")

    def cmd_callback(self, msg: Twist):
        # 收到导航速度时，只更新缓存，绝不触发 mode_mark
        self.current_forward = float(msg.linear.x)
        self.current_left = float(msg.angular.z)

    def stand_callback(self, msg: Bool):
        self.is_standing = msg.data
        
        # 变形瞬间，为了安全强制清零水平速度
        self.current_forward = 0.0
        self.current_left = 0.0
        
        if self.is_standing:
            self.get_logger().info("执行官方起立序列连招...")
            # 第一击：触发模式切换
            self.publish_state(mode_mark=True, stand_mode=True, up=0.0)
            
            # 第二击：拉高机身，并关闭模式触发器
            self.current_up = 1.0
            self.publish_state(mode_mark=False, stand_mode=True, up=self.current_up)
        else:
            self.get_logger().info("执行官方趴下序列...")
            self.current_up = 0.0
            # 触发趴下，模式切换
            self.publish_state(mode_mark=True, stand_mode=False, up=0.0)

    def timer_callback(self):
        # 官方精髓：平时持续发送心跳，且 mode_mark 必须严格为 False！
        self.publish_state(mode_mark=False, stand_mode=self.is_standing, up=self.current_up)

    def publish_state(self, mode_mark, stand_mode, up):
        msg = MotionCtrl()
        
        # 严格遵守官方机制：标志位只在变形瞬间为 True
        msg.mode_mark = mode_mark 
        msg.mode.stand_mode = stand_mode
        
        # 其他模式默认关闭
        msg.mode.pitch_ctrl_mode = False 
        msg.mode.roll_ctrl_mode = False
        msg.mode.height_ctrl_mode = False
        msg.mode.jump_mode = False
        msg.mode.split_mode = False
        
        # 速度和高度
        msg.value.forward = self.current_forward
        msg.value.left = self.current_left
        msg.value.up = up
        msg.value.roll = 0.0
        msg.value.pitch = 0.0
        msg.value.leg_split = 0.0
        
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = CmdVelConverter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()