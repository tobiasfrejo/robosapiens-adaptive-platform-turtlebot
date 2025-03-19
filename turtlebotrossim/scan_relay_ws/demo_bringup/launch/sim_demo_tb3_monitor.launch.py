from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
import os
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterFile
from nav2_common.launch import RewrittenYaml


TURTLEBOT3_SIM_SCAN_SIZE = 360


def generate_launch_description():
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
    params_path = PathJoinSubstitution([demo_bringup_dir, "config", "tb3_nav2.yaml"])
    rviz_path = PathJoinSubstitution(
        [demo_bringup_dir, "launch", "other", "nav2_default_view.rviz"]
    )

    nav2_launch_file = os.path.join(
        get_package_share_directory("nav2_bringup"),
        "launch/tb3_simulation_launch.py",
    )

    nav2_ld = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_launch_file),
        launch_arguments=[
            ("headless", "False"),
            ("params_file", params_path),
            ("rviz_config_file", rviz_path),
        ],
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

    monitor_dir = get_package_share_directory("nav2_collision_monitor")
    monitor_params_file = os.path.join(monitor_dir, 'params', 'collision_monitor_params.yaml')
    # monitor_params = ParameterFile(
    #     RewrittenYaml(
    #         source_file=monitor_params_file,
    #         root_key='collision_monitor',
    #         convert_types=True),
    #     allow_substs=True)

    monitor_node = Node(
        package="nav2_collision_monitor",
        executable="collision_monitor",
        output='screen',
        emulate_tty=True,  # https://github.com/ros2/launch/issues/188
        parameters=[monitor_params_file]
    )

    start_lifecycle_manager_cmd = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='collision_lifecycle_manager',
        output='screen',
        emulate_tty=True,  # https://github.com/ros2/launch/issues/188
        parameters=[{'use_sim_time': True},
                    {'autostart': True},
                    {'node_names': ['collision_monitor']}])

    # monitor_ld = PythonLaunchDescriptionSource(
    #     os.path.join([monitor_dir, 'launch', 'collision_monitor_node.launch.py'])
    # )

    ld.add_action(start_lifecycle_manager_cmd)
    ld.add_action(nav2_ld)
    ld.add_action(scan_node)
    ld.add_action(spin_config_node)
    ld.add_action(monitor_node)
    # ld.add_action(monitor_ld)

    return ld
