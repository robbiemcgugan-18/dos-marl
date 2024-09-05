"""
swat-s1 run.py
"""

from mininet.net import Mininet
from mininet.cli import CLI
from minicps.mcps import MiniCPS
from mininet.node import RemoteController

from topo import SwatTopo

import sys
from rl_envs.envs.gym_env import SwatEnv

class SwatS1CPS(MiniCPS):

    """Main container used to run the simulation."""

    def __init__(self, name, net):

        self.name = name
        self.net = net

        net.start()

        net.pingAll()

        # start devices
        plc1, plc2, plc3, s1 = self.net.get(
            'plc1', 'plc2', 'plc3', 's1')

        # SPHINX_SWAT_TUTORIAL RUN(
        plc2.cmd(sys.executable + ' -u ' +' plc2.py &> logs/plc2.log &')
        plc3.cmd(sys.executable + ' -u ' + ' plc3.py  &> logs/plc3.log &')
        plc1.cmd(sys.executable + ' -u ' + ' plc1.py  &> logs/plc1.log &')
        s1.cmd(sys.executable + ' -u ' + ' physical_process.py  &> logs/process.log &')
        # SPHINX_SWAT_TUTORIAL RUN)


        s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow s1 priority=10,ip,in_port=1,actions=output:2,3,4')
        s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow s1 priority=10,ip,in_port=2,actions=output:1,3,4')
        s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow s1 priority=10,ip,in_port=3,actions=output:1,2,4')
        s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow s1 priority=10,ip,in_port=4,actions=output:1,2,3')

        s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow s1 priority=10,arp,in_port=1,actions=output:2,3,4')
        s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow s1 priority=10,arp,in_port=2,actions=output:1,3,4')
        s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow s1 priority=10,arp,in_port=3,actions=output:1,2,4')
        s1.cmd('ovs-ofctl --protocols=OpenFlow13 add-flow s1 priority=10,arp,in_port=4,actions=output:1,2,3')

        print("Network interfaces:")
        print(s1.cmd('ifconfig'))

        CLI(net)


if __name__ == "__main__":

    topo = SwatTopo()
    net = Mininet(topo=topo, controller=RemoteController('c0', ip='localhost', port=5555))

    env = swat_s1_cps = SwatS1CPS(
        name='swat_s1',
        net=net)
    
    mini = SwatEnv(env, 1, 10)
    mini.step(2)
