#!/usr/bin/env python3
# coding=utf-8
import os
import rospy
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import numpy as np

root = "/home/starjie/newbot_ws/src/image_tran/image"

def callback(data):
    bridge = CvBridge()
    cv_image = bridge.imgmsg_to_cv2(data, "bgr8")

    # 转灰度图，加载模板
    cv_image_gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    template_path = os.path.join(root, "ball.jpeg")
    template_image = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

    # 模板匹配（最小差值法）
    res = cv2.matchTemplate(cv_image_gray, template_image, cv2.TM_SQDIFF)

    # 找到最优匹配位置
    index_position = np.where(res == np.min(res))
    index_h, index_w = index_position[0][0], index_position[1][0]
    template_h, template_w = template_image.shape

    # 计算匹配区域中心点
    center_x = index_w + template_w // 2
    center_y = index_h + template_h // 2
    rospy.loginfo(f"Template center point: ({center_x}, {center_y})")

    # 在原图上画出匹配框（红色）
    cv2.rectangle(cv_image, (index_w, index_h), (index_w + template_w, index_h + template_h), [0, 0, 255], 2)
    cv2.imshow("view", cv_image)

def showImage():
    rospy.init_node('showImage', anonymous=True)
    cv2.namedWindow("view", cv2.WINDOW_AUTOSIZE)
    cv2.startWindowThread()
    rospy.Subscriber('ShowImage', Image, callback)
    rospy.spin()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    try:
        showImage()
    except rospy.ROSInterruptException:
        pass
