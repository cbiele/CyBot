#!/usr/bin/env python
# license removed for brevity
import rospy
import time
from std_msgs.msg import String

timeSleep = 1
def talker():
    pub = rospy.Publisher('/cybot_btt_cmd', String, queue_size=10)
    rospy.init_node('serial_node', anonymous=True)
    time.sleep(timeSleep)
    rate = rospy.Rate(10) # 10hz 
    hello_str = "MOVE<X>20000</X>" 
    rospy.loginfo(hello_str)
    pub.publish(hello_str)
    rate.sleep()
    time.sleep(timeSleep)
    hello_str = "MOVE<X>-20000</X>" 
    rospy.loginfo(hello_str)
    pub.publish(hello_str)
    rate.sleep()
    time.sleep(timeSleep)
    hello_str = "MOVE<Y>20000</Y>" 
    rospy.loginfo(hello_str)
    pub.publish(hello_str)
    rate.sleep()
    time.sleep(timeSleep)
    hello_str = "MOVE<Y>-20000</Y>" 
    rospy.loginfo(hello_str)
    pub.publish(hello_str)
    rate.sleep()
    time.sleep(timeSleep)
    hello_str = "MOVE<Z>5000</Z>" 
    rospy.loginfo(hello_str)
    pub.publish(hello_str)
    rate.sleep()
    time.sleep(timeSleep)
    hello_str = "MOVE<Z>-5000</Z>" 
    rospy.loginfo(hello_str)
    pub.publish(hello_str)
    rate.sleep()
    time.sleep(timeSleep)
    hello_str = "MOVE<E0>20000</E0>" 
    rospy.loginfo(hello_str)
    pub.publish(hello_str)
    rate.sleep()
    time.sleep(timeSleep)
    hello_str = "MOVE<E0>-20000</E0>" 
    rospy.loginfo(hello_str)
    pub.publish(hello_str)
    rate.sleep()
    time.sleep(timeSleep)
    hello_str = "MOVE<E1>-20000</E1>" 
    rospy.loginfo(hello_str)
    pub.publish(hello_str)
    rate.sleep()
    time.sleep(timeSleep)
    hello_str = "MOVE<E1>20000</E1>" 
    rospy.loginfo(hello_str)
    pub.publish(hello_str)
    rate.sleep()
    time.sleep(timeSleep)
    hello_str = "MOVE<E2>5000</E2>" 
    rospy.loginfo(hello_str)
    pub.publish(hello_str)
    rate.sleep()
    time.sleep(timeSleep)
    hello_str = "MOVE<E2>-5000</E2>" 
    rospy.loginfo(hello_str)
    pub.publish(hello_str)
    rate.sleep()
    time.sleep(timeSleep)

if __name__ == '__main__':
    try:
        talker()
    except rospy.ROSInterruptException:
        pass
