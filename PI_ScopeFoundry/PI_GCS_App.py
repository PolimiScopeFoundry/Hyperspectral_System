"""
****************************************
Created on Tue Jun 21 12:45:26 2021
@authors: Victoire Destombes, Andrea Bassi. Politecnico di Milano

"""

from ScopeFoundry import BaseMicroscopeApp

class pi_gcs_app(BaseMicroscopeApp):
    

    name = 'pi_gcs_app'
    
    def setup(self):
        
        #Add hardware components
        print("Adding Hardware Components")
        from PI_GCS_hardware import PI_GCS_HW
        self.add_hardware(PI_GCS_HW(self))
           

        self.ui.show()
        self.ui.activateWindow()


if __name__ == '__main__':
    import sys
    
    app = pi_gcs_app(sys.argv)
    sys.exit(app.exec_())
