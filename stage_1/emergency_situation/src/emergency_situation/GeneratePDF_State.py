#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sat May 29 13:30:00 2014

@author: Chang Long Zhu
@email: changlongzj@gmail.com
"""

import smach
import rospy
import rosparam
import roslib

from emergency_situation.image_creator import ImageCreator
from emergency_situation.pdf_creator import create_pdf
from util_states.image_to_cv import image_converter

import os
import shutil
import subprocess

from geometry_msgs.msg._PoseWithCovarianceStamped import PoseWithCovarianceStamped

# Loading the parameters depending on which robot we are using.
# Reduce the size of image file

robot = os.environ.get('PAL_ROBOT')
if robot == 'rh2c' or robot == 'rh2m':
    IMAGE_PATH = roslib.packages.get_pkg_dir('reemh2_maps') + '/configurations/'
    RH2_PATH = roslib.packages.get_pkg_dir('reemh2_maps')
    paramlist = rosparam.load_file(RH2_PATH+"/config/map.yaml", default_namespace="emergency_situation")
    for params, ns in paramlist:
        rosparam.upload_params(ns, params)

elif robot == 'reemh3c' or robot == 'reemh3m':
    IMAGE_PATH = roslib.packages.get_pkg_dir('reem_maps') + '/configurations/'
    REEMH3_PATH = roslib.packages.get_pkg_dir('reem_maps')
    paramlist = rosparam.load_file(REEMH3_PATH+'/config/map.yaml', default_namespace="emergency_situation")
    for params, ns in paramlist:
        rosparam.upload_params(ns, params)

else:
    #IMAGE_PATH = roslib.packages.get_pkg_dir('robocup_iworlds') + '/navigation/'
    IMAGE_PATH = roslib.packages.get_pkg_dir('emergency_situation') + '/config/'
    #ROBOCUP_PATH = roslib.packages.get_pkg_dir('robocup_worlds')
    #paramlist = rosparam.load_file(ROBOCUP_PATH+"/navigation/subMap1.yaml", default_namespace="emergency_situation")
    paramlist = rosparam.load_file(IMAGE_PATH+"/subMap1.yaml",default_namespace="emergency_situation")
    for params, ns in paramlist:
        rosparam.upload_params(ns, params)

PKG_PATH = roslib.packages.get_pkg_dir('emergency_situation')
RESOLUTION = rospy.get_param("/emergency_situation/resolution")
IMAGE_NAME = rospy.get_param("/emergency_situation/image")
IMAGE_ORIGIN = rospy.get_param("/emergency_situation/origin")
IMAGE_ORIGIN = [0, 0]
IMAGE_NAME = "subMap_0.pgm"


class GeneratePDF_State(smach.State):
    def __init__(self):
        smach.State.__init__(self, outcomes=['succeeded', 'aborted', 'preempted'], 
                                    input_keys=['person_location'])
        self.pendrive_location = rospy.get_param('/emergency_situation/pendrive_location')
        print "\nPendrive Location: %s\n" % self.pendrive_location

    def execute(self, userdata):
        rospy.loginfo("Informing Ambulance...............")
        #Creating image from REEM's camera
        image_converter()
        
        image_created_number = ImageCreator(location_list=[userdata.person_location.pose.position.x, userdata.person_location.pose.position.y], 
                                        origin=IMAGE_ORIGIN,
                                        scale=RESOLUTION, 
                                        image_name=IMAGE_NAME, 
                                        pkg_path=PKG_PATH, 
                                        image_path=IMAGE_PATH)
        
        create_pdf(PKG_PATH + '/config/')
        
        print "PDF CREATED in  " + PKG_PATH + '/config/reem3.pdf'
        rospy.loginfo("Copying file to %s/reem3.pdf" % self.pendrive_location)
        #shutil.copy(PKG_PATH + '/config/' + "reem3.pdf", self.pendrive_location + '/reem3.pdf')
        rospy.loginfo("Ambulance informed successfully !!!!")
        
        rospy.loginfo("Secure Copying from Control to Multimedia - Pendrive")
        subprocess.call("copy_to_usb.sh", shell=True)
        subprocess.call("unmountexample.sh", shell=True)
        
        return 'succeeded'

def main():
    rospy.loginfo('GeneratePDF_State')
    rospy.init_node('GeneratePDF_State_node')
    sm = smach.StateMachine(outcomes=['succeeded', 'preempted', 'aborted'])
    with sm:      
        sm.userdata.person_location = PoseWithCovarianceStamped()
        sm.userdata.person_location.pose.position.x = 1.0
        sm.userdata.person_location.pose.position.y = 1.0
        sm.userdata.person_location.pose.position.z = 0.0
        
        smach.StateMachine.add(
            'GeneratePDF_State',
            GeneratePDF_State(),
            transitions={'succeeded': 'succeeded','preempted':'preempted', 'aborted':'aborted'})

    sm.execute()
    rospy.spin()

if __name__=='__main__':
    main()



