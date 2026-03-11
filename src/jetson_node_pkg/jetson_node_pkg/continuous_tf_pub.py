#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

class ContinuousTF(Node):
    def __init__(self):
        super().__init__('continuous_tf_pub')
        # 创建动态 TF 广播器 (发布到 /tf 而不是 /tf_static)
        self.broadcaster = TransformBroadcaster(self)
        # 设置定时器，每 0.1 秒 (10Hz) 发布一次
        self.timer = self.create_timer(0.1, self.publish_tf)
        self.get_logger().info("成功启动！正在以 10Hz 持续发布 body -> base_link (旋转180度)")

    def publish_tf(self):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'body'
        t.child_frame_id = 'base_link'
        
        # 坐标偏移为 0
        t.transform.translation.x = 0.0
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.0
        
        # 偏航角(Yaw)转 180 度的四元数固定值
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = 1.0  # sin(180°/2) = 1
        t.transform.rotation.w = 0.0  # cos(180°/2) = 0
        
        self.broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = ContinuousTF()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()