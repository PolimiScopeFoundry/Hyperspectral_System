from ScopeFoundry import HardwareComponent
from PI_ScopeFoundry.PI_GCS_device import PI_GCS_Device

# -*- coding: utf-8 -*-
"""
Created on Tue Jun 21 12:45:26 2021
@authors: Victoire Destombes, Andrea Bassi. Politecnico di Milano
"""

#SERIAL = '0135500826' # serial number of the M-405 linear stage 

SERIAL = '024550342' # serial number of the L-505 linear stage (controller serial number)

class PI_GCS_HW(HardwareComponent):
    name = 'PI_GCS_HW'
    
    def setup(self):
        # create Settings (aka logged quantities)
        self.info = self.settings.New(name='info', dtype=str)
        # self.name = self.settings.New(name='name stages', dtype=str)
        self.target_position = self.settings.New(name='target position', dtype=float,
                                                 spinbox_decimals = 4,
                                                 unit='mm')
        self.position = self.settings.New(name='position', ro = True, dtype=float, unit='mm',
                                          spinbox_decimals = 4,
                                          reread_from_hardware_after_write = True)
        
        self.velocity = self.settings.New(name='velocity', dtype=float, unit='mm/s', initial = 0.5, reread_from_hardware_after_write = True)
        self.servo = self.settings.New(name='servo', initial=False, dtype=bool)
        self.home = self.settings.New(name='home', dtype=float, unit='mm', ro = True)
        
        self.add_operation('SetHome', self.set_home)
        self.add_operation('GoHome', self.go_home)
        self.add_operation('Stop', self.stop)
        self.add_operation('GotoRefSwitch', self.gotoRefSwitch)
        
        
    def connect(self):
        # connect settings to Device methods
        self.motor = PI_GCS_Device(serial = SERIAL, axis = '1')     
        
        self.info.hardware_read_func = self.motor.get_info
        
        self.position.hardware_read_func = self.motor.get_position
        self.target_position.hardware_set_func = self.motor.move_absolute
        
        self.velocity.hardware_read_func = self.motor.get_velocity
        self.velocity.hardware_set_func = self.motor.set_velocity
        
        self.servo.hardware_set_func = self.motor.set_servo        
        self.servo.hardware_read_func = self.motor.get_servo        
        
        self.home.hardware_read_func = self.motor.get_home
        
        self.add_operation('SetHome', self.motor.set_home)
        self.add_operation('GoHome', self.motor.go_home)
        self.add_operation('Stop', self.motor.stop)
        self.add_operation('GotoRefSwitch', self.motor.gotoRefSwitch)
        
        self.read_from_hardware()
        
    def disconnect(self):
        if hasattr(self, 'motor'):
            self.motor.close() 
            del self.motor
            
        for setting in self.settings.as_list():
            setting.hardware_read_func = None
            setting.hardware_set_func = None
            
    def set_home(self):
        self.motor.set_home()
    
    def stop(self):
        self.motor.stop()
        
    def go_home(self):
        self.motor.go_home()
        
    def gotoRefSwitch(self):
        self.motor.gotoRefSwitch()