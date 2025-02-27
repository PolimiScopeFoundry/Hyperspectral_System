# -*- coding: utf-8 -*-
"""
Created on wed Jun 16 01:33:32 2021

@authors: Andrea Bassi. Politecnico di Milano
"""
from ScopeFoundry import BaseMicroscopeApp

class hyper_app(BaseMicroscopeApp):
    
    name = 'hyper_app'
    
    def setup(self):
        
        #Add hardware components
        print("Adding Hardware Components")
        #modificato da Martina 13-02-2025
        #from QImaging_ScopeFoundry.camera_hw import QImagingHW
        #self.add_hardware(QImagingHW(self))
         
        from Hamamatsu_ScopeFoundry.CameraHardware import HamamatsuHardware
        self.add_hardware(HamamatsuHardware(self))
        
        from PI_ScopeFoundry.PI_GCS_hardware import PI_GCS_HW
        self.add_hardware(PI_GCS_HW(self))

        
        # Add measurement components
        print("Create Measurement objects")
        from hyperspectral_measure import hyperMeasure
        self.add_measurement(hyperMeasure(self))
        
        #from Hamamatsu_ScopeFoundry.CameraMeasurement import HamamatsuMeasurement
        #self.add_measurement(HamamatsuMeasurement(self))

        self.ui.show()
        self.ui.activateWindow()

if __name__ == '__main__':
    
    import sys
    
    app = hyper_app(sys.argv)
    #app.settings_load_ini(".\\Settings\\settings.ini")
    for hc_name, hc in app.hardware.items():
        hc.settings['connected'] = True    # connect all the hardwares  
    
    
    sys.exit(app.exec_())