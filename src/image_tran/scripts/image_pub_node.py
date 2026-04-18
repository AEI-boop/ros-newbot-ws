#!/usr/bin/env python3
# coding=utf-8
import rospy
import sys
import cv2
import os
import numpy as np
from sensor_msgs.msg import Image
import random
from cv_bridge import CvBridge, CvBridgeError

# 图片路径
image_path = "/home/starjie/newbot_ws/src/image_tran/image/ball_env.jpeg"

def pubImage():
    rospy.init_node('pubImage', anonymous=True)
    pub = rospy.Publisher('ShowImage', Image, queue_size=10)
    rate = rospy.Rate(5)
    bridge = CvBridge()

    # 检查文件是否存在
    if not os.path.exists(image_path):
        rospy.logerr(f"Error: Image file not found at {image_path}")
        sys.exit(1)

    # 加载图像
    image = cv2.imread(image_path)
    if image is None:
        rospy.logerr(f"Error: Failed to load image from {image_path}")
        sys.exit(1)

    h, w, _ = image.shape
    rospy.loginfo(f"Image loaded successfully. Shape: {image.shape}")

    while not rospy.is_shutdown():
        # 生成切分后的图片（从随机位置起始，高和宽均为原图的3/4）
        start_h = random.randint(0, h - int(h * 3 / 4))
        height = int(h * 3 / 4)
        start_w = random.randint(0, w - int(w * 3 / 4))
        width = int(w * 3 / 4)

        transfer_image = image[start_h:start_h + height, start_w:start_w + width, :]

        # 发布切分后的图片
        pub.publish(bridge.cv2_to_imgmsg(transfer_image, "bgr8"))
        rate.sleep()

if __name__ == '__main__':
    try:
        pubImage()
    except rospy.ROSInterruptException:
        pass
