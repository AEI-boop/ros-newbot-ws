#!/usr/bin/env python3
# coding=utf-8
import rospy
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError

def callback(data):
    bridge = CvBridge()
    # 将ROS消息转换为OpenCV图像
    cv_image = bridge.imgmsg_to_cv2(data, "bgr8")
    cv2.imshow("Received Image", cv_image)
    cv2.waitKey(1)

def showImage():
    rospy.init_node('showImage', anonymous=True)
    cv2.namedWindow("Received Image", cv2.WINDOW_AUTOSIZE)
    cv2.startWindowThread()
    # 订阅图像话题（需与发布节点一致）
    rospy.Subscriber("ShowImage", Image, callback)
    rospy.spin()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    try:
        showImage()
    except rospy.ROSInterruptException:
        pass
