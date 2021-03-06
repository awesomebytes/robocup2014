#! /usr/bin/env python
'''
@author: Roger Boldu
'''

import rospy
import actionlib
import sys
import select
import math

from geometry_msgs.msg import Twist
from get_current_robot_pose import get_current_robot_pose
from navigation_states.srv import NavigationTurn,NavigationTurnResponse
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Pose
from util_states.math_utils import *
from tf.transformations import quaternion_from_euler, euler_from_quaternion

SPEED_X=0.3 # that is a forward speed
MAXTIME=15
MARGE=0.017 # 2 grados de error

ENDC = '\033[0m'
FAIL = '\033[91m'
OKGREEN = '\033[92m'

'''
@this is a navigation turn
@The maximum value of turn is 180 degree and -180 degree
@It have a time out of 15 seconds
@Be careful!! this doesn't have navigation control!!
'''

class navigation_turn():
    
    def __init__(self):
        rospy.loginfo("Initializing turn")
        
        self.nav_pub= rospy.Publisher('/mobile_base_controller/cmd_vel', Twist)
        self.nav_srv = rospy.Service('/turn',NavigationTurn, self.nav_turn_srv)
        self.odom_subs = rospy.Subscriber("/mobile_base_controller/odom", Odometry, self.check_Odometry)
        self.init_var()
        
    def init_var(self):
        self.Odometry_actual=Odometry()
        self.Odometry_init=None
        self.enable=False
        
        self.goal_achieved=False
        
        self.time_init= rospy.get_rostime()
        
        self.time_out=False
        
        
    def nav_turn_srv(self,req):
        
        if (req.degree<181 and req.degree>-181) :
            if (req.enable) :
                
                self.time_out=False
                self.time_init= rospy.get_rostime()
                self.enable=True
                self.Odometry_init=self.Odometry_actual 
                
                self.radians=math.radians(req.degree)
                self.degree=req.degree
                
                roll, pitch, yaw = euler_from_quaternion([self.Odometry_init.pose.pose.orientation.x,self.Odometry_init.pose.pose.orientation.y,
                        self.Odometry_init.pose.pose.orientation.z,
                        self.Odometry_init.pose.pose.orientation.w])
                if req.degree>0 :
                    self.speed=-SPEED_X
                    self.yaw_final=yaw-self.radians
                else :
                    self.yaw_final=yaw-self.radians
                    self.speed=+SPEED_X
                    
                    
                    
                self.radians=self.yaw_final
                if self.radians>math.pi :
                    self.radians=-(math.pi-self.radians+math.pi)
                if self.radians<-math.pi :
                    self.radians= math.pi-(abs(self.radians)-math.pi)
                    
                if self.radians>(-math.pi) and self.radians<(math.pi) :
                    rospy.loginfo("eps new order")
                    self.run()
                else :
                    return "error impossible to arrive"
            else :
                rospy.loginfo("harcode stop")
                self.enable=False
                self.pub_stop()
            
            
            if (self.time_out):
                rospy.loginfo("ABORTING!!!")
                if self.time_out :
                    rospy.loginfo("TIME OUT")
                return "ABORTED"
            else :
                return NavigationTurnResponse()
        else :
            self.pub_stop()
            return "Too much degree"
        
        
    def check_Odometry(self,data):
        self.Odometry_actual=data
        
    def proces_odometry(self):
        
        position_navigate=Pose()
        position_navigate.orientation.x=self.Odometry_actual.pose.pose.orientation.x
        position_navigate.orientation.y=self.Odometry_actual.pose.pose.orientation.y
        position_navigate.orientation.z=self.Odometry_actual.pose.pose.orientation.z
        position_navigate.orientation.w=self.Odometry_actual.pose.pose.orientation.w
        
        
        
        roll, pitch, yaw = euler_from_quaternion([position_navigate.orientation.x,position_navigate.orientation.y,
                                position_navigate.orientation.z,
                                position_navigate.orientation.w])
    
        if (yaw<self.radians+MARGE and yaw>self.radians-MARGE) :
           
            self.movment=True
        else :
            self.movment=False
            
    def pub_move(self):
        msg=Twist()
        msg.linear.x= 0
        msg.linear.y=0
        msg.linear.z=0
        msg.angular.x=0
        msg.angular.y=0
        msg.angular.z=self.speed
        self.nav_pub.publish(msg)
        
    def pub_stop(self):
        msg=Twist()
        msg.linear.x=0
        msg.linear.y=0
        msg.linear.z=0
        msg.angular.x=0
        msg.angular.y=0
        msg.angular.z=0

        self.nav_pub.publish(msg)
        
            
            
    def proces_time(self):
        time_actual=rospy.get_rostime()
        time=time_actual.secs-self.time_init.secs
        
        if time<MAXTIME :
            self.time_out = False
            
        else :
            self.time_out = True
            
    def run(self):
        
        while not rospy.is_shutdown() and self.enable:
           
            if self.enable: 
                self.proces_odometry()
                self.proces_time()
                if not self.movment and not self.time_out :
                    self.pub_move()
                else : 
                    self.pub_stop()
                    self.enable=False
                    
                rospy.sleep(0.002)
            else :
                
                rospy.sleep(3)
    def bucle(self):
        while not rospy.is_shutdown():
            rospy.sleep(3)
        
        
        
if __name__ == '__main__':
    rospy.init_node('navigation_turn_service')
    rospy.sleep(1)
    rospy.loginfo("navigation_turn_srv")
    navigation = navigation_turn()
    navigation.bucle()
    
    

  
