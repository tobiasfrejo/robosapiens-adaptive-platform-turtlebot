# **********************************************************************************
# * Copyright (C) 2024-present Bert Van Acker (B.MKR) <bert.vanacker@uantwerpen.be>
# *
# * This file is part of the roboarch R&D project.
# *
# * RAP R&D concepts can not be copied and/or distributed without the express
# * permission of Bert Van Acker
# **********************************************************************************
import json

from rpio.clientLibraries.rpclpy.node import Node
from rv_tools.knowledge import knowledge_rv
from .messages import *
import time
from rv_tools.constants import *
from rv_tools.timing_workaround import trustworthiness_output2
#<!-- cc_include START--!>
# user includes here
#<!-- cc_include END--!>

#<!-- cc_code START--!>
# user code here
#<!-- cc_code END--!>

class Execute(Node):

    def __init__(self, config='config.yaml',verbose=True):
        super().__init__(config=config,verbose=verbose)

        self._name = "Execute"
        self.logger.info("Execute instantiated")

        #<!-- cc_init START--!>
        # user includes here
        #<!-- cc_init END--!>

    # -----------------------------AUTO-GEN SKELETON FOR executer-----------------------------
    def executer(self,msg):
        # self.publish_event('start_e')
        trustworthiness_output2(self, 'start')
        isLegit = knowledge_rv.read(self, "isLegit",queueSize=1)
        directions = knowledge_rv.read(self, "directions",queueSize=1)
        _Direction = Direction()

        #<!-- cc_code_executer START--!>

        for i in range(3):
            self.logger.info("Executing")
            time.sleep(0.1)
        self.logger.info(f"Executed with directions = {directions}");
        self.publish_event(event_key='/spin_config',message=json.dumps(directions))    # LINK <outport> spin_config
        knowledge_rv.write(self, "handling_anomaly", 0)
        trustworthiness_output2(self, 'end')
        #<!-- cc_code_executer END--!>

    def register_callbacks(self):
        self.register_event_callback(event_key='isLegit', callback=self.executer)        # LINK <inport> isLegit

def main(args=None):

    node = Execute(config='config.yaml')
    node.register_callbacks()
    node.start()

if __name__ == '__main__':
    main()
    try:
       while True:
           time.sleep(1)
    except:
       exit()
