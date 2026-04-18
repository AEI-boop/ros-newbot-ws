#!/usr/bin/env python3
# coding=utf-8
"""
任务1：订阅变换场地图像，用颜色检测找到红球并标记
"""
import rospy
import cv2
import numpy as np
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

def callback(data):
    bridge = CvBridge()
    cv_image = bridge.imgmsg_to_cv2(data, "bgr8")

    # 用HSV颜色空间检测红色球
    hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
    # 红色在HSV中分两段
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    mask = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)

    # 找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        # 找最大轮廓（即红球）
        c = max(contours, key=cv2.contourArea)
        ((cx, cy), radius) = cv2.minEnclosingCircle(c)
        if radius > 10:
            # 画圆框和中心点
            cv2.circle(cv_image, (int(cx), int(cy)), int(radius) + 5, (0, 255, 0), 2)
            cv2.circle(cv_image, (int(cx), int(cy)), 3, (0, 255, 0), -1)
            cv2.putText(cv_image, f"Ball: ({int(cx)}, {int(cy)})", (int(cx) + 10, int(cy) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow("Ball Scene Detection", cv_image)
    cv2.waitKey(1)

def main():
    rospy.init_node('ball_scene_sub', anonymous=True)
    cv2.namedWindow("Ball Scene Detection", cv2.WINDOW_AUTOSIZE)
    cv2.startWindowThread()
    rospy.Subscriber('ShowImage', Image, callback)
    rospy.spin()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
