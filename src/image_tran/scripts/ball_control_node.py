#!/usr/bin/env python3
# coding=utf-8
"""
任务2：红球虚拟遥控控制小海龟
原理：检测红球在画面中的位置，映射为海龟的运动方向
  - 球在画面上方 → 海龟前进
  - 球在画面下方 → 海龟后退
  - 球在画面左边 → 海龟左转
  - 球在画面右边 → 海龟右转
  - 球越偏离中心，速度越大
"""
import rospy
import cv2
import numpy as np
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge

# 全局发布者
cmd_pub = None

def callback(data):
    global cmd_pub
    bridge = CvBridge()
    cv_image = bridge.imgmsg_to_cv2(data, "bgr8")
    h, w, _ = cv_image.shape
    center_x, center_y = w // 2, h // 2

    # HSV颜色空间检测红球
    hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    mask = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    twist = Twist()

    # 画十字参考线（把画面分为上下左右四个区域）
    cv2.line(cv_image, (center_x, 0), (center_x, h), (100, 100, 100), 1)
    cv2.line(cv_image, (0, center_y), (w, center_y), (100, 100, 100), 1)

    # 画区域提示
    cv2.putText(cv_image, "Forward", (center_x - 30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(cv_image, "Backward", (center_x - 35, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(cv_image, "Left", (10, center_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(cv_image, "Right", (w - 55, center_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    if contours:
        c = max(contours, key=cv2.contourArea)
        ((ball_x, ball_y), radius) = cv2.minEnclosingCircle(c)

        if radius > 10:
            bx, by = int(ball_x), int(ball_y)

            # 画检测框
            cv2.circle(cv_image, (bx, by), int(radius) + 5, (0, 255, 0), 2)
            cv2.circle(cv_image, (bx, by), 3, (0, 255, 0), -1)

            # 计算球相对于画面中心的偏移量（归一化到 -1 ~ 1）
            offset_x = (ball_x - center_x) / center_x   # 正=右, 负=左
            offset_y = (center_y - ball_y) / center_y    # 正=上(前进), 负=下(后退)

            # 映射为海龟速度
            twist.linear.x = offset_y * 2.0     # 前后速度，最大2.0
            twist.angular.z = -offset_x * 2.0   # 左右角速度，球在右边→海龟右转(负)

            # 显示控制信息
            direction = ""
            if offset_y > 0.2:
                direction += "Forward "
            elif offset_y < -0.2:
                direction += "Backward "
            if offset_x < -0.2:
                direction += "Left"
            elif offset_x > 0.2:
                direction += "Right"
            if not direction:
                direction = "Center(Stop)"

            cv2.putText(cv_image, f"Control: {direction}", (10, h - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(cv_image, f"Linear: {twist.linear.x:.2f}  Angular: {twist.angular.z:.2f}",
                        (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    cmd_pub.publish(twist)
    cv2.imshow("Ball Remote Control", cv_image)
    cv2.waitKey(1)

def main():
    global cmd_pub
    rospy.init_node('ball_control', anonymous=True)

    # 发布速度命令到海龟
    cmd_pub = rospy.Publisher('/turtle1/cmd_vel', Twist, queue_size=10)

    cv2.namedWindow("Ball Remote Control", cv2.WINDOW_AUTOSIZE)
    cv2.startWindowThread()

    rospy.Subscriber('ShowImage', Image, callback)
    rospy.loginfo("Ball Remote Control started! Move the red ball to control the turtle.")
    rospy.spin()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
