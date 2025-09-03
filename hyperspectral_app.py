# -*- coding: utf-8 -*-
"""
Created on thur Mar 06 11:00:00 2025

@authors: Andrea Bassi, Martina Riva, Antonio Composto. Politecnico di Milano
"""

#add for Visual Studio: this allows the code to run even with hardware folders outside the 
#app folder
import sys
from os.path import dirname
sys.path.append(dirname(dirname(__file__)))
print('here:', dirname(dirname(__file__)))


from ScopeFoundry import BaseMicroscopeApp

class hyper_app(BaseMicroscopeApp):
    
    name = 'hyper_app'
    
    def setup(self):
        
        #Add hardware components
        print("Adding Hardware Components")
         
        from Hamamatsu_ScopeFoundry.CameraHardware import HamamatsuHardware
        self.add_hardware(HamamatsuHardware(self))
        
        from PI_ScopeFoundry.PI_CG_hardware import PI_CG_HW
        self.add_hardware(PI_CG_HW(self, serial='024550347'))

        
        # Add measurement components
        print("Create Measurement objects")
        from hyperspectral_measure import hyperMeasure
        self.add_measurement(hyperMeasure(self))
        
        #For ScopeFoundry release 2.0.2 comment these lines:
        #self.ui.show()
        #self.ui.activateWindow()

if __name__ == '__main__':
    
    import sys
    import os

    app = hyper_app(sys.argv)
    
    # Load settings from ini file in Settings, within the same folder as this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    setting_dir = os.path.join(current_dir, 'Settings', 'settings.ini')
    app.settings_load_ini(setting_dir)

    for hc_name, hc in app.hardware.items():
        hc.settings['connected'] = True    # connect all the hardwares  automatically
    
    
    sys.exit(app.exec_())
