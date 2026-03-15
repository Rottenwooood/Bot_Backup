import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    fast_lio_dir = get_package_share_directory('fast_lio')
    livox_driver_dir = get_package_share_directory('livox_ros_driver2')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    
    # 【修改点 1】加载你新写的站立版参数文件
    map_yaml_file = '/home/nvidia/ros2_ws/my_map.yaml'
    stand_nav2_params_file = '/home/nvidia/ros2_ws/stand_nav2_params.yaml'
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),

        # 0. 启动雷达
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(livox_driver_dir, 'launch_ROS2', 'msg_MID360_launch.py')),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
        ),

        # 1. 启动 Fast-LIO
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(fast_lio_dir, 'launch', 'mapping.launch.py')),
            launch_arguments={'rviz': 'false', 'use_sim_time': use_sim_time}.items(),
        ),

        # 2. 【修改点 2】启动站立专用的 TF 节点
        Node(
            package='jetson_node_pkg',
            executable='stand_continuous_tf_pub', # <--- 注意这里名字换了！
            name='stand_continuous_tf_pub',
            output='screen'
        ),

        # 3. 启动点云切片
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pointcloud_to_laserscan',
            remappings=[('cloud_in', '/cloud_registered_body'), ('scan', '/scan')],
            parameters=[{
                'target_frame': 'base_link', 
                'transform_tolerance': 0.05,
                # 【修改点 3】由于传感器变高，我们要切片的高度范围也要调整，重点扫前方0~1.5米的高度
                'min_height': -0.10,  
                'max_height': 1.5,   
                # ... 其他参数保持不变 ...
            }]
        ),

        # 4. 启动 Nav2
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')),
            launch_arguments={
                'map': map_yaml_file,
                'params_file': stand_nav2_params_file, # <--- 加载站立参数
                'use_sim_time': use_sim_time
            }.items()
        ),
        
        # 5. 启动 MQTT
        Node(
            package='mqtt_client',
            executable='mqtt_client',
            name='mqtt_client',
            output='screen',
            parameters=['/home/nvidia/ros2_ws/src/mqtt_client/mqtt_client/config/params.yaml']
        ),

        # 6. 启动控制桥接器
        Node(
            package='jetson_node_pkg',
            executable='stand_cmd_vel_converter',
            name='cmd_vel_converter',
            output='screen'
        )
    ])