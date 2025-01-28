#!/bin/bash
# Basic entrypoint for ROS / Colcon Docker containers

# Source ROS 2
# source /opt/ros/humble/setup.bash

# Source the base workspace, if built
if [ -f /opt/setup.bash ]
then
  source /opt/setup.bash
fi

alias python="python3"

# Execute the command passed into this entrypoint
exec "$@"