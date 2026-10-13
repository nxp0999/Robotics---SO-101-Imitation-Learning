#  Imitation Learning for Robotic Projectile Throwing

**Training the SO-101 robot arm to throw a ball into a basket using Action Chunking Transformers (ACT)**

<p>
  <img alt="LeRobot" src="https://img.shields.io/badge/framework-LeRobot-yellow">
  <img alt="Policy" src="https://img.shields.io/badge/policy-ACT-blue">
  <img alt="Robot" src="https://img.shields.io/badge/robot-SO--101-orange">
  <img alt="Course" src="https://img.shields.io/badge/UT%20Dallas-CS6341%20Robotics-green">
</p>

Picking up an object and placing it in a basket is a classic robot-arm demo. We wanted to make it harder: instead of placing the ball, the SO-101 **throws** it. Using human demonstrations collected via leader–follower teleoperation, we trained an ACT policy that learns the full throwing motion, including release timing, with **no physics model and no vision-based perception**.

---

##  Highlights

- **End-to-end imitation learning pipeline**: teleoperated demonstrations → ACT training → autonomous throwing, all on [LeRobot](https://github.com/huggingface/lerobot).
- **Data efficient**: trained on only **30 demonstrations** at a single distance (40 cm).
- **96–100% accuracy at 20 cm** across three ball types, generalizing to a distance it was never trained on.
- **Smooth, natural trajectories** thanks to action chunking, with consistent gripper release timing.
- **Low-cost hardware**: two SO-101 arms, a basket, and a few balls.

---

##  Results

Each cell is 30 autonomous trials. A throw counts as a success only if the ball lands completely inside the basket; rim hits and bounce-outs are failures.

| Distance | Pink ball | Orange ball | Rainbow ball | Human demos (pink)* |
|:--------:|:---------:|:-----------:|:------------:|:-------------------:|
| **20 cm** | **100%** | 96% | **100%** | 75% |
| **40 cm** | 50% | **60%** | 46.67% | 80% |

<sub>*Success rate of the pink-ball teleoperated demonstrations, shown as a baseline.</sub>

**Key takeaways**

- **Short throws:** The policy was trained at 40 cm. At 20 cm it reached near-perfect accuracy and *outperformed* the human demonstrations (100% vs 75%).
- **Long throws:** At the trained distance (40 cm), accuracy dropped to 47–60%, below the 80% demonstration rate. More (and more targeted) data is likely needed.
- **Ball properties matter:** Differences between balls were minor at 20 cm but significant at 40 cm. The orange ball performed best at the longer distance.
- **Failures were systematic** (e.g., consistent directional bias) rather than random, which suggests they can be fixed with targeted demonstrations.

---

##  Hardware Setup

| Component | Details |
|-----------|---------|
| Leader arm | SO-101, manipulated by a human operator |
| Follower arm | SO-101, mirrors the leader in real time and performs the throw |
| Target | Basket at a fixed position (20 cm or 40 cm from the robot) |
| Projectiles | Small foam/beanbag-style balls (pink, orange, rainbow), chosen to minimize bouncing |
| Camera | Fixed viewpoint for monitoring (not used as policy input) |
| Measurement | Grid marked on the table for landing positions |

<!-- Add a setup photo: ![Setup](docs/setup.jpg) -->

---

##  Method

### 1. Data collection: leader–follower teleoperation
We compared leader–follower teleoperation with a smartphone-based controller (HEBI Mobile I/O). We chose leader–follower because the physical leader arm gives haptic feedback and produces much smoother, more natural throws.

Recording loop for each episode:
1. Calibrate both arms with the LeRobot calibration procedure.
2. Move the follower to a consistent start pose with the ball in its gripper.
3. Start recording with `lerobot-record`.
4. Perform the throw on the leader arm; the follower mirrors it and releases the ball.
5. Record the landing position and mark the episode as a success or failure.
6. Retrieve the ball, reset the arm, and repeat.

LeRobot records synchronized 6-DoF joint positions and velocities for both arms at **30 Hz**, along with gripper state and episode metadata.

### 2. Policy: Action Chunking Transformer (ACT)
Standard behavioral cloning predicts one action per timestep, which often produces jerky motion. That is a problem for throwing, which depends on smooth acceleration and precise timing. **ACT** instead predicts a *chunk* of future actions at each step, which enforces temporal consistency.

- Transformer encoder–decoder (~80M parameters)
- Predicts chunks of future actions
- Trains in a few hours on a single GPU
- Uses LeRobot's built-in ACT implementation

### 3. Deployment
The trained policy runs autonomously on the follower arm from the same start configuration used during data collection. We measure success rate over 30 trials for each (distance, ball) combination.

---

##  Getting Started

### Prerequisites
- Two SO-101 arms (leader + follower)
- Python environment with [LeRobot](https://github.com/huggingface/lerobot) installed
- (Recommended) a CUDA GPU for training

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
# Install LeRobot by following its official instructions, e.g.:
pip install lerobot
```

> **Note:** LeRobot's CLI flags change between versions. The commands below are examples, so check the [LeRobot docs](https://huggingface.co/docs/lerobot) for the version you've installed.

### Find your ports
```bash
lerobot-find-port
```
On our machine (macOS), the ports were:
- Leader: `/dev/tty.usbmodem58760431551`
- Follower: `/dev/tty.usbmodem585A0076841`

Replace these with your own ports in the commands below.

### Calibrate
```bash
lerobot-calibrate --robot.type=so101_follower --robot.port=<FOLLOWER_PORT> --robot.id=follower
lerobot-calibrate --teleop.type=so101_leader --teleop.port=<LEADER_PORT> --teleop.id=leader
```

### Record demonstrations
```bash
lerobot-record \
  --robot.type=so101_follower --robot.port=<FOLLOWER_PORT> --robot.id=follower \
  --teleop.type=so101_leader --teleop.port=<LEADER_PORT> --teleop.id=leader \
  --dataset.repo_id=<HF_USER>/so101_throwing \
  --dataset.num_episodes=30 \
  --dataset.single_task="Throw the ball into the basket"
```

### Train the ACT policy
```bash
lerobot-train \
  --policy.type=act \
  --dataset.repo_id=<HF_USER>/so101_throwing \
  --output_dir=outputs/throwing_policy \
  --batch_size=8
```

Training configuration we used:

| Setting | Value |
|---------|-------|
| Dataset | 30 demos at 40 cm (pink ball) |
| Train/val split | 90% / 10% |
| Batch size | 8 |
| Learning rate | 1e-4 (default) |


### Run the trained policy
```bash
lerobot-record \
  --robot.type=so101_follower --robot.port=<FOLLOWER_PORT> --robot.id=follower \
  --policy.path=outputs/throwing_policy/checkpoints/last/pretrained_model \
  --dataset.repo_id=<HF_USER>/eval_so101_throwing \
  --dataset.num_episodes=30 \
  --dataset.single_task="Throw the ball into the basket"
```

---

##  Limitations

- **Fixed setup:** robot and basket positions were constant; new configurations were not evaluated.
- **Single training object and distance:** the policy was trained only on the pink ball at 40 cm.
- **Moderate sample size:** 30 trials per condition gives only moderate statistical confidence.
- **Bounce effects:** ball bounce can turn good throws into failures, so true throwing accuracy may be underestimated.

##  Future Work

- **Autonomous ball retrieval:** a grasping policy chained with the throwing policy for continuous operation
- **Distance conditioning:** add target distance as a policy input and train across a continuous range of distances
- **Multi-object generalization:** adapt the throw to the projectile's weight, size, and shape
- **Vision integration:** localize the basket from camera input to throw at arbitrary targets
- **Performance tuning:** targeted demos for failure cases, online fine-tuning, and physics-informed regularization

---

##  Team

Built for **CS6341 – Robotics** at **The University of Texas at Dallas**.

- Navaneeta Padmakumar
- Matthew Jagen
- Anika Nesarikar
- Shreya Soman

##  References

1. Hugging Face, [LeRobot: State-of-the-art Machine Learning for Real-World Robotics](https://github.com/huggingface/lerobot), 2024.
2. A. Zeng et al., [TossingBot: Learning to Throw Arbitrary Objects with Residual Physics](https://arxiv.org/abs/1903.11239), IEEE T-RO, 2020.
3. donutsorelse, [Candy Throwing Robot Arm](https://www.instructables.com/Candy-Throwing-Robot-Arm/), Instructables, 2025.
4. J. McKay, [Penn State Altoona – Robotic Basketball Arm](https://www.a-mc.com/pennstate-robotic-basketball-arm/), 2020.
5. D. Son and S. Park, [LiPo: A Lightweight Post-optimization Framework for Smoothing Action Chunks](https://doi.org/10.48550/arXiv.2506.05165), 2025.
6. M. Zare et al., [A Survey of Imitation Learning: Algorithms, Recent Developments, and Challenges](https://arxiv.org/abs/2309.02473), 2023.
7. T. Z. Zhao et al., [Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware](https://arxiv.org/abs/2304.13705) (ACT), 2023.
