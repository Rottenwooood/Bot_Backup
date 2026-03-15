import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # 获取各包路径
    fast_lio_dir = get_package_share_directory('fast_lio')
    livox_driver_dir = get_package_share_directory('livox_ros_driver2')

    # 获取仿真时间参数 (回放数据设为 true，真雷达设为 false)
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),

        # 0. 启动 Livox 雷达驱动 (真雷达)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(livox_driver_dir, 'launch_ROS2', 'msg_MID360_launch.py')),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
        ),

        # 1. 启动 Fast-LIO (负责 camera_init -> body 的变换)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(fast_lio_dir, 'launch', 'mapping.launch.py')),
            launch_arguments={'rviz': 'false', 'use_sim_time': use_sim_time}.items(),
        ),

        # 2. 静态 TF 发布: 将 lidar_link 挂在 body 下 (根据你之前的命令)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='body_to_lidar',
            arguments=['0', '0', '0.2', '0', '0', '0', 'body', 'lidar_link'],
            parameters=[{'use_sim_time': use_sim_time}]
        ),

        # 3. 启动点云切片节点 (替代 slice.launch.py)
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pointcloud_to_laserscan',
            remappings=[('cloud_in', '/cloud_registered_body'), ('scan', '/scan')],
            parameters=[{
                'target_frame': 'body', 
                'transform_tolerance': 0.05,
                'min_height': -0.1,  
                'max_height': 2.0,   
                'angle_min': -3.14159,
                'angle_max': 3.14159,
                'angle_increment': 0.0087,
                'scan_time': 0.1,
                'range_min': 0.3,
                'range_max': 20.0,
                'use_inf': False,
                'use_sim_time': use_sim_time
            }]
        ),

        # 4. 启动 SLAM Toolbox (负责 map -> camera_init 的变换)
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[
                '/home/nvidia/ros2_ws/my_slam.yaml',
                {'use_sim_time': False}
            ]
        )
    ])