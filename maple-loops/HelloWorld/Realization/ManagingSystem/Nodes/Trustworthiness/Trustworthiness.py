# **********************************************************************************
# * Copyright (C) 2024-present Bert Van Acker (B.MKR) <bert.vanacker@uantwerpen.be>
# *
# * This file is part of the roboarch R&D project.
# *
# * RAP R&D concepts can not be copied and/or distributed without the express
# * permission of Bert Van Acker
# **********************************************************************************
from rpio.clientLibraries.rpclpy.node import Node
import json
import time

#<!-- cc_include END--!>

#<!-- cc_code START--!>

### USER Defined Functions

#<!-- cc_code END--!>

class Trustworthiness(Node):

    def __init__(self, config='config.yaml',verbose=True):
        super().__init__(config=config,verbose=verbose)

        self._name = "Trustworthiness"
        self.logger.info("Trustworthiness instantiated")

        #<!-- cc_init START--!>



        #<!-- cc_init END--!>

    # -----------------------------AUTO-GEN SKELETON FOR planner-----------------------------
    def t_ms(self, msg):
        self.publish_event('atomicstage', json.dumps({'Str': 'start_m'}))
    def t_me(self, msg):
        self.publish_event("stage", json.dumps({'Str':'m'}))
        self.publish_event('atomicstage', json.dumps({'Str': 'end_m'  }))

    def t_as(self, msg):
        self.publish_event('atomicstage', json.dumps({'Str': 'start_a'}))
    def t_ae(self, msg):
        #self.publish_event("stage", json.dumps({'Str': 'a'}))
        self.publish_event('atomicstage', json.dumps({'Str': 'end_a'  }))

    def t_aok(self, msg):
        self.publish_event("stage", json.dumps({'Str': 'aok'}))
    def t_anom(self, msg):
        self.publish_event("stage", json.dumps({'Str': 'anom'}))

    def t_ps(self, msg):
        self.publish_event('atomicstage', json.dumps({'Str': 'start_p'}))
    def t_pe(self, msg):
        self.publish_event("stage", json.dumps({'Str': 'p'}))
        self.publish_event('atomicstage', json.dumps({'Str': 'end_p'  }))

    def t_ls(self, msg):
        self.publish_event('atomicstage', json.dumps({'Str': 'start_l'}))
    def t_le(self, msg):
        self.publish_event("stage", json.dumps({'Str': 'l'}))
        self.publish_event('atomicstage', json.dumps({'Str': 'end_l'  }))

    def t_es(self, msg):
        self.publish_event('atomicstage', json.dumps({'Str': 'start_e'}))
    def t_ee(self, msg):
        self.publish_event("stage", json.dumps({'Str': 'e'}))
        self.publish_event('atomicstage', json.dumps({'Str': 'end_e'  }))


    def trust_check(self, msg):
        self.logger.info(msg)

    def register_callbacks(self):
        # self.register_event_callback(event_key='anomaly', callback=self.t_a)     # LINK <eventTrigger> anomaly
        # self.register_event_callback(event_key='new_plan', callback=self.t_p)
        # self.register_event_callback(event_key='isLegit', callback=self.t_l)
        # self.register_event_callback(event_key='/spin_config', callback=self.t_e)
        self.register_event_callback(event_key='maple', callback=self.trust_check)
        # self.register_event_callback(event_key='anomaly', callback=self.planner)        # LINK <inport> anomaly

        self.register_event_callback('start_m',      self.t_ms)
        self.register_event_callback('start_a',      self.t_as)
        self.register_event_callback('start_p',      self.t_ps)
        self.register_event_callback('start_l',      self.t_ls)
        self.register_event_callback('start_e',      self.t_es)
        self.register_event_callback('new_data',     self.t_me)
        self.register_event_callback('no_anomaly',   self.t_ae)
        self.register_event_callback('no_anomaly',   self.t_aok)
        self.register_event_callback('anomaly',      self.t_ae)
        self.register_event_callback('anomaly',      self.t_anom)
        self.register_event_callback('new_plan',     self.t_pe)
        self.register_event_callback('isLegit',      self.t_le)
        self.register_event_callback('/spin_config', self.t_ee)

        self.register_event_callback('test_a',   lambda s: self.publish_event('test_a', json.dumps({'Str': str(s)})))

def main(args=None):

    node = Trustworthiness(config='config.yaml')
    node.register_callbacks()
    node.start()

if __name__ == '__main__':
    main()
    try:
       while True:
           time.sleep(1)
    except:
       exit()