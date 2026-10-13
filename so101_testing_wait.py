from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig
import time

robot_config = SO101FollowerConfig(port="/dev/ttyACM0", id="demo_follower")
robot = SO101Follower(robot_config)
robot.connect()

JOINT_TOLERANCE = 3.0

def wait_for_pose(pose):
    done = False
    while not done : 
        #time.sleep(0.1) //change polling rate if needed later
        current_pose = robot.get_observation()
        print("\ncurrent pose:\n", current_pose)
        done = True
        done = done and abs(current_pose['shoulder_pan.pos'] - pose['shoulder_pan.pos']) < JOINT_TOLERANCE
        done = done and abs(current_pose['shoulder_lift.pos'] - pose['shoulder_lift.pos']) < JOINT_TOLERANCE
        done = done and abs(current_pose['elbow_flex.pos'] - pose['elbow_flex.pos']) < JOINT_TOLERANCE
        done = done and abs(current_pose['wrist_flex.pos'] - pose['wrist_flex.pos']) < JOINT_TOLERANCE
        done = done and abs(current_pose['wrist_roll.pos'] - pose['wrist_roll.pos']) < JOINT_TOLERANCE
        done = done and abs(current_pose['gripper.pos'] - pose['gripper.pos']) < JOINT_TOLERANCE

def zero_pos():
    position = {
    'shoulder_pan.pos': 0.0,
    'shoulder_lift.pos': -30.0,
    'elbow_flex.pos': 30.0,
    'wrist_flex.pos': 70.0,
    'wrist_roll.pos': 0.0,
    'gripper.pos': 0.0
    }

    # Send joint position to robot
    print("\nSetting SO101 arm to position zero")
    start = time.perf_counter()
    robot.send_action(position)

    # Reading joint posiitons
    wait_for_pose(position)
    joint_pos = robot.get_observation()
    end = time.perf_counter()

    print("Zero position pose: \n", joint_pos)
    print("time taken (ms): ", round((end - start) * 1000, 2))

def one_pos():
    position = {
    'shoulder_pan.pos': 45.0,
    'shoulder_lift.pos': -20.0,
    'elbow_flex.pos': 30.0,
    'wrist_flex.pos': 60.0,
    'wrist_roll.pos': -30.0,
    'gripper.pos': 50.0
    }

    # Send joint position to robot
    print("\nSetting SO101 arm to position one")
    start = time.perf_counter()
    robot.send_action(position)

    # Reading joint posiitons
    wait_for_pose(position)
    joint_pos = robot.get_observation()
    end = time.perf_counter()

    print("position one pose: \n", joint_pos)
    print("time taken (ms): ", round((end - start) * 1000, 2))

def two_pos():
    position = {
    'shoulder_pan.pos': -45.0,
    'shoulder_lift.pos': -10.0,
    'elbow_flex.pos': 0.0,
    'wrist_flex.pos': -30.0,
    'wrist_roll.pos': 30.0,
    'gripper.pos': 30.0
    }

    # Send joint position to robot
    print("\nSetting SO101 arm to position two")
    start = time.perf_counter()
    robot.send_action(position)

    # Reading joint posiitons
    wait_for_pose(position)
    joint_pos = robot.get_observation()
    end = time.perf_counter()

    print("position two pose: \n", joint_pos)
    print("time taken (ms): ", round((end - start) * 1000, 2))

def main():
    
    print("\ninput desired pose... {0, 1, 2, `}")
    user_input = input()

    while (user_input != "`"):
        
        if user_input == "0":
            zero_pos()
        
        if user_input == "1":
            one_pos()
        
        if user_input == "2":
            two_pos()

        print("\ninput desired pose... {0, 1, 2, `}")
        user_input = input()
    

if __name__ == "__main__":
    main()
