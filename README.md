# Pimpmobile-Teleop
Ros2 teleop package for the Pimpmobile.

Bash script for activation:

------------------------------

#!/bin/bash

gnome-terminal -- bash -c "cd ros2_humble; source install/setup.bash; ros2 run teleop to; exec bash"

sleep 2

gst-launch-1.0 udpsrc port=5000 caps="application/x-rtp, media=video, encoding-name=H264, payload=96" ! \
    rtph264depay ! avdec_h264 ! videoconvert ! autovideosink sync=false

