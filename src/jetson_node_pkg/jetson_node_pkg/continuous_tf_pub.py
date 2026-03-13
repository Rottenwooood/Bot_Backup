#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped

class ContinuousTF(Node):
    def __init__(self):
        super().__init__('continuous_tf_pub')
        
        # 只用【动态 TF 广播器】
        self.broadcaster = TransformBroadcaster(self)
        
        # 设置定时器，每 0.1 秒 (10Hz) 持续发布所有 TF
        self.timer = self.create_timer(0.1, self.publish_all_tfs)
        self.get_logger().info("成功启动！正在以 10Hz 持续发布:\n 1. body -> base_link (旋转180度)\n 2. base_link -> camera_link (前10cm, 下10cm)")

    def publish_all_tfs(self):
        # 获取统一的当前时间戳，保证两个 TF 时间完全同步
        now = self.get_clock().now().to_msg()
        
        # ==========================================
        # 1. 持续发布: body -> base_link
        # ==========================================
        t1 = TransformStamped()
        t1.header.stamp = now
        t1.header.frame_id = 'body'
        t1.child_frame_id = 'base_link'
        
        # 坐标偏移为 0
        t1.transform.translation.x = 0.0
        t1.transform.translation.y = 0.0
        t1.transform.translation.z = 0.0
        
        # 偏航角(Yaw)转 180 度
        t1.transform.rotation.x = 0.0
        t1.transform.rotation.y = 0.0
        t1.transform.rotation.z = 1.0  
        t1.transform.rotation.w = 0.0  
        
        self.broadcaster.sendTransform(t1)
        
        # ==========================================
        # 2. 持续发布: base_link -> camera_link
        # ==========================================
        t2 = TransformStamped()
        t2.header.stamp = now
        t2.header.frame_id = 'base_link'
        t2.child_frame_id = 'camera_link'
        
        # 相机位置：前方 10cm, 左右居中, 下方 10cm
        t2.transform.translation.x = 0.1
        t2.transform.translation.y = 0.0
        t2.transform.translation.z = -0.1
        
        # 相机朝向正前方，不旋转
        t2.transform.rotation.x = 0.0
        t2.transform.rotation.y = 0.0
        t2.transform.rotation.z = 0.0
        t2.transform.rotation.w = 1.0
        
        self.broadcaster.sendTransform(t2)

def main(args=None):
    rclpy.init(args=args)
    node = ContinuousTF()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()