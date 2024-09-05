# from mininet.net import Mininet
# from mininet.cli import CLI
# from minicps.mcps import MiniCPS
# from mininet.node import OVSController, RemoteController

# from .topo import SwatTopo
# from .run import SwatS1CPS

import gymnasium as gym
# from gymnasium.utils import seeding
# from gymnasium.spaces import Dict, Discrete, Box
# from ray.rllib.env.multi_agent_env import MultiAgentEnv
# from mininet.cli import CLI
# import numpy as np

# import sys
# import os
# import subprocess

# import requests
# import json

# class SingleAgentSwatEnv(gym.Env):

#     def __init__(self, env, agent_id, episode_length, epsilon_start=1.0, epsilon_decay=0.9, epsilon_min=0.01):

#         # self.env = net
#         self.agent_id = agent_id
#         self.env = env
#         print("STARTING SWAT ENVIRONMENT " + str(agent_id))

#         self.observation_space = gym.spaces.Discrete(2)

#         self.action_space = gym.spaces.Discrete(2)

#         self.episode_length = episode_length
#         self.i = 0
#         self.epsilon = epsilon_start
#         self.epsilon_decay = epsilon_decay
#         self.epsilon_min = epsilon_min

#         self.seed()
#         self.reset()


#     def reset(self, *, seed=None, options=None):

#         self.reward = 0
#         self.done = False
#         self.truncated = False
#         self.info = {}
#         self.i = 0

#         return (0, 0)

#     def step(self, action):
#         self.i += 1
#         self.reward = 1


#         if self.i >= self.episode_length:
#             self.truncated = True
#             self.done = True

#         self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

#         if self.i >= self.episode_length:
#             print(f"Episode finished after {self.i} steps with total reward: {self.reward}")
#         return (0, 0), self.reward, self.i >= self.episode_length, self.i >= self.episode_length, self.info
    
#     def render(self, mode='human'):
#         print('Rendering the environment')

#     def cli(self):
#         CLI(self.env.net)

#     def seed(self, seed=None):
#         self.np_random, seed = seeding.np_random(seed)
#         return [seed]
    
#     def close(self):
#         pass

class SingleAgentSwatEnv(gym.Env):
    pass