import torch

from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.datasets.lerobot_dataset import LeRobotDatasetMetadata
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.policies.factory import make_pre_post_processors
from lerobot.policies.utils import build_inference_frame, make_robot_action
from lerobot.robots.so101_follower import SO101FollowerConfig
from lerobot.robots.so101_follower import SO101Follower

device = torch.device("cuda")  # or "cuda" or "cpu"
print("enter distance: ")
DIST = input()
JOINT=""
MAX_STEPS_PER_EPISODE = 75
model_id = ""
if(DIST == "20"):
    model_id = "CS6341g3/throwbotact20cm"
    JOINT = "elbow_flex.pos"
    MAX_STEPS_PER_EPISODE = 50
if(DIST == "40"):
    model_id = "CS6341g3/throwbotact40cm"
    JOINT = "shoulder_lift.pos"
if(DIST =="50"):
    model_id = "CS6341g3/throwbotact50cm"

model = ACTPolicy.from_pretrained(model_id)

dataset_id = "CS6341g3/throwbot_"+DIST+"cm"
# This only downloads the metadata for the dataset, ~10s of MB even for large-scale datasets
dataset_metadata = LeRobotDatasetMetadata(dataset_id)
##print(dataset_metadata.features)
preprocess, postprocess = make_pre_post_processors(model.config, dataset_stats=dataset_metadata.stats)

# # find ports using lerobot-find-port
follower_port = ...  # something like "/dev/tty.usbmodem58760431631"

# # the robot ids are used the load the right calibration files
follower_id = ...  # something like "follower_so100"

MAX_EPISODES = 1

RELEASE_ANGLE_DELTA = 63
GRIPPER_OPEN = 33
GRIPPER_CLOSE = 15

# Robot and environment configuration
# Camera keys must match the name and resolutions of the ones used for training!
# You can check the camera keys expected by a model in the info.json card on the model card on the Hub
#camera_config = {
#    "side": OpenCVCameraConfig(index_or_path=0, width=640, height=480, fps=30),
#    "up": OpenCVCameraConfig(index_or_path=1, width=640, height=480, fps=30),
#
#obs['observation.images.front'] = dummy_image
#        #print(obs.keys())
#}
#camera_config = {"front": OpenCVCameraConfig(
#    index_or_path=0,
#    fps=30,
#   width=640,
#    height=480,
#)}

robot_config = SO101FollowerConfig(port="COM13", id="demo_follower")
robot = SO101Follower(robot_config)
robot.connect()
zero_pos = robot.get_observation()
#print("starting position: \n" , zero_pos)

#dummy image to feed to model
import numpy as np
dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)

#frequency checks
import time
dt = 1.0 / 15



# obs = robot.get_observation()
# #print('in loop, #printing this fresh')
# dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
# obs['front'] = dummy_image
# #print(obs.keys())


# obs_frame = build_inference_frame(
#     observation=obs, ds_features=dataset_metadata.features, device=device
# )

#obs = preprocess(obs_frame)

#start = time.time()
#action_sequence = model.predict_action_chunk(obs)
#action_sequence = model.select_action(obs)
##print(model.config)
#action_sequence = actions.squeeze(0) 
#action_sequence = postprocess(action_sequence)
#duration = time.time() - start
#if duration < dt: time.sleep(dt - duration)
#else: #print("WARNING: taking longer. Real time is : ",duration,"time needs to be : ",dt)

# action = postprocess(action)
# import os
# os._exit(1)
# #print(model.config)
# import os
# os._exit(1)


def elementWiseDiff(a, b):
    output = {}
    #print('in elem wise diff: ',output)
    for key in a.keys():
        output[key] = a[key] - b[key]
    return output

def elementWiseAdd(a, b):
    output = {}
    #print('elem wise add',output)
    for key in a.keys():
        output[key] = a[key] + b[key]
    return output

def scale_joints(a, s):
    output = {}
    #print('in elem wise scale: ',output)
    #print("scaling by: ", s)
    for key in a.keys():
        output[key] = s * a[key]
    return output

# for _ in range(MAX_EPISODES):
def throw40cm():
    start_pos = zero_pos.copy()
    start_pos["gripper.pos"] = GRIPPER_CLOSE
    robot.send_action(start_pos)
    time.sleep(1)
    for _ in range(MAX_STEPS_PER_EPISODE):
        start = time.time()
        obs = robot.get_observation()
        orig_obs = obs
        #print('in loop, #printing this fresh')
        #print(obs)
        dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
        obs['front'] = dummy_image      
        
        obs_frame = build_inference_frame(
            observation=obs, ds_features=dataset_metadata.features, device=device
        )

        obs = preprocess(obs_frame)

        action = model.select_action(obs)
        
        action = postprocess(action)

        action = make_robot_action(action, dataset_metadata.features)
        action["wrist_roll.pos"] = zero_pos["wrist_roll.pos"]
        action["shoulder_pan.pos"] = zero_pos["shoulder_pan.pos"]
        if orig_obs[JOINT] - zero_pos[JOINT] < RELEASE_ANGLE_DELTA:
            action["gripper.pos"] = GRIPPER_CLOSE
        #print(action)
        robot.send_action(action)

        #timing information
        duration = time.time() - start
        if duration < dt: time.sleep(dt - duration)
        else: print("WARNING: taking longer")

    print("Ep done")
    time.sleep(1)
    end_pos = robot.get_observation()
    #print('end pos',end_pos)
    target_time = 2
    return_steps = 20
    for i in range(return_steps):
        time.sleep(target_time/(return_steps*2))
        delta_joints = elementWiseDiff(zero_pos, end_pos)
        #print('delta joints',delta_joints)
        delta_joints = scale_joints(delta_joints, (i/float(return_steps)))
        #print('delta joints',delta_joints)
        add = elementWiseAdd(end_pos, delta_joints)
        #print("target ", add)
        robot.send_action(add)

    reset_pos = zero_pos.copy()
    reset_pos["gripper.pos"] = GRIPPER_OPEN
    robot.send_action(reset_pos)

print("enter any key, press ` to exit")
kbd_in = input()
while not kbd_in == "`" :
    throw40cm()
    kbd_in = input()



# for step, action in enumerate(action_sequence):
#     start = time.time()
    
#     robot_action = make_robot_action(action, dataset_metadata.features)
#     robot.send_action(robot_action)
#     duration = time.time() - start
#     if duration < dt: time.sleep(dt - duration)
#     else: #print("WARNING: taking longer")
#     #print("iteration done, on to the next movement.")




# #print("Ep done")
