from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
import os
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node

TURTLEBOT3_SIM_SCAN_SIZE = 360


def generate_launch_description():
    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically startup the nav2 stack',
    )

    declare_slam_cmd = DeclareLaunchArgument(
        'slam', default_value='False', description='Whether run a SLAM'
    )

    ld = LaunchDescription(
        [
            SetEnvironmentVariable(name="TURTLEBOT3_MODEL", value="waffle"),
            SetEnvironmentVariable(
                name="GAZEBO_MODEL_PATH",
                value="/opt/ros/humble/share/turtlebot3_gazebo/models",
            ),
        ]
    )
    demo_bringup_dir = get_package_share_directory("demo_bringup")
    params = PathJoinSubstitution([demo_bringup_dir, "config", "tb3_nav2.yaml"])
    rviz_path = PathJoinSubstitution(
        [demo_bringup_dir, "launch", "other", "nav2_default_view.rviz"]
    )

    nav2_launch_file = os.path.join(
        get_package_share_directory("nav2_bringup"),
        "launch/tb3_simulation_launch.py",
    )

    params_ld = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_launch_file),
        launch_arguments=[
            ("headless", "False"),
            ("params_file", params),
            ("rviz_config_file", rviz_path),
        ]
    )

    scan_node = Node(
        package="scan_modifier",
        executable="scan_node",
        parameters=[{"scan_ranges_size": TURTLEBOT3_SIM_SCAN_SIZE}],
    )

    spin_config_node = Node(
        package="topic_param_bridge",
        executable="param_bridge",
    )

    ld.add_action(declare_slam_cmd)
    ld.add_action(declare_autostart_cmd)

    ld.add_action(params_ld)
    ld.add_action(scan_node)
    ld.add_action(spin_config_node)

    return ld
