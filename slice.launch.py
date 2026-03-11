from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pointcloud_to_laserscan',
            remappings=[
                # 【关键】吃进 Fast-LIO 吐出的完美局部点云
                ('cloud_in', '/cloud_registered_body'), 
                ('scan', '/scan')
            ],
            parameters=[{
                'target_frame': 'body', 
                'transform_tolerance': 0.05,
                
                # 高度切片：切雷达下方 10cm 到雷达上方 20cm 的障碍物
                'min_height': -0.1,  
                'max_height': 2.0,   
                
                'angle_min': -3.14159,
                'angle_max': 3.14159,
                'angle_increment': 0.0087,
                'scan_time': 0.1,
                'range_min': 0.3,
                'range_max': 20.0,
                'use_inf': True,
                
                # 【极其关键】因为你在放录像，必须开启仿真时间！
                'use_sim_time': True        
            }]
        )
    ])