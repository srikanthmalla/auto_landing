#!/usr/bin/env python
import roslib
roslib.load_manifest('auto_landing')
import sys
import rospy
import cv2

from geometry_msgs.msg import Twist
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import numpy as np
from ardrone_autonomy.msg import Navdata
from geometry_msgs.msg import Twist      # for sending commands to the drone
from std_msgs.msg import Empty         # for land/takeoff/emergency
from nav_msgs.msg import Odometry
pubtakeoff = rospy.Publisher('/ardrone/takeoff', Empty, queue_size=10)
publand = rospy.Publisher('/ardrone/land', Empty, queue_size=100)
pub_xy_control=rospy.Publisher('cmd_vel',Twist,queue_size=10)
uniq=Empty()
status=0
vel=Twist()
def navdata_status_callback(data):
    status=data.state
    # print status


class image_converter:

  def __init__(self):
    self.image_pub = rospy.Publisher("output_topic",Image)

    cv2.namedWindow("Image window", 1)
    self.bridge = CvBridge()
    self.image_sub = rospy.Subscriber("ardrone/bottom/image_raw",Image,self.callback)
    self.status_sub= rospy.Subscriber("ardrone/navdata",Navdata,navdata_status_callback)
    #self.ground_sub= rospy.Subscriber("ground_truth/state",Odometry, ground_state_callback) 
  def callback(self,data):
    try:
      cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
      pubtakeoff.publish(uniq) 
       
    except CvBridgeError, e:
      print e
    
     # read the frames
    frame = cv_image
     
    # smooth it
    frame = cv2.blur(frame,(3,3))
    best_cnt=0
    # convert to hsv and find range of colors
    hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)#226
    thresh = cv2.inRange(hsv,np.array((145, 75, 130)), np.array((170, 255, 255)))
    thresh2 = thresh.copy()

    # find contours in the threshold image
    contours,hierarchy = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)

    # finding contour with maximum area and store it as best_cnt
    max_area = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > max_area:
            max_area = area
            best_cnt = cnt

    # finding centroids of best_cnt and draw a circle there
    M = cv2.moments(best_cnt)
    cx,cy = int(M['m10']/M['m00']), int(M['m01']/M['m00'])
    cv2.circle(frame,(cx,cy),5,255,-1)

    size = frame.shape
    framey = size[0]/2
    framex = size[1]/2

    # ROS_INFO("imgx:%f,imgy:%f,framex:%f,framey:%f",cx,cy,framex,framey)

    # Show it, if key pressed is 'Esc', exit the loop
    cv2.imshow('frame',frame)
    cv2.imshow('thresh',thresh2)
  
   # (rows,cols,channels) = cv_image.shape
   # if cols > 60 and rows > 60 :
   #   cv2.circle(cv_image, (50,50), 10, 255)

    cv2.imshow("Image window", cv_image)
    cv2.waitKey(3)
    
    error_x= -cx+framex
    error_y= -cy+framey
    vel.linear.y=0.001*error_x #image xy are diff from normal xy
    vel.linear.x=0.001*error_y
    vel.linear.z=0
    vel.angular.x=0
    vel.angular.y=0
    vel.angular.z=0
    pub_xy_control.publish(vel)
    print framex, framey, cx, cy, error_x, error_y
       
    if (abs(error_x) <= (20)) & (abs(error_y) <=20) :
      while(1): 
        vel.linear.y=0 #image xy are diff from normal xy
        vel.linear.x=0
        vel.linear.z=-10
        vel.angular.x=0
        vel.angular.y=0
        vel.angular.z=0
        pub_xy_control.publish(vel)
        print "enter"

    
    try:
       self.image_pub.publish(self.bridge.cv2_to_imgmsg(frame, "bgr8"))
    except CvBridgeError, e:
       print e





def main(args):
  
  ic = image_converter()
  rospy.init_node('image_converter', anonymous=True)
  while (status !=6):
    rospy.spin()

  try:
    rospy.spin()
  except KeyboardInterrupt:
    print "Shutting down"
  cv2.destroyAllWindows()

if __name__ == '__main__':
    main(sys.argv)