#include <ros/ros.h>
#include <geometry_msgs/Twist.h>
#include <geometry_msgs/PoseStamped.h>
#include <iostream>
#include <nav_msgs/Odometry.h>

geometry_msgs::Twist vel;
float error,error_yaw;
void state_callback(const nav_msgs::Odometry p)
{ 
  
  error= 6-p.pose.pose.position.x; 
  error_yaw= -p.pose.pose.orientation.z; 
  vel.linear.x=0.3*error;
  vel.linear.y=-0.3*p.pose.pose.position.y;
  vel.linear.z=0.3*(5-p.pose.pose.position.z);
  vel.angular.x=0;
  vel.angular.y=0;
  vel.angular.z=0.3*error_yaw;


}
int main(int argc, char **argv)
{   
	
	ros::init(argc, argv, "my_node_name");
	ros::NodeHandle n;
	ros::Subscriber sub = n.subscribe("ground_truth/state", 1000, state_callback);
	ros::Publisher chatter_pub = n.advertise<geometry_msgs::Twist>("cmd_vel", 1000);
	while(n.ok())
	{	ROS_INFO("%f",error);
		ros::spinOnce();
		chatter_pub.publish(vel);
	}

}