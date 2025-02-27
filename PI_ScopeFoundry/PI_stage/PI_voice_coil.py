from ScopeFoundry import HardwareComponent
from collections import OrderedDict
from pipython import GCSDevice, pitools, GCSError, gcserror
from pipython.gcscommands import GCSCommands
from pipython.interfaces.piserial import PISerial
from pipython.gcsmessages import GCSMessages
from pipython import GCSDevice, pitools
import threading
import time
import sys



CONTROLLERNAME = 'C-413.2GA'
STAGES = ['V-524.1AA']  # connect stages to axes
REFMODES = ['FNL']  # reference the connected stages
default_axes = OrderedDict( [(1,'x')] )
# here we use only one axis but more axes can be included...
#self.pidevice=GCSDevice(CONTROLLERNAME)

class PIStage(HardwareComponent):
    
    def __init__(self, app, debug=False, name=None, axes=default_axes):
        # self.pidevice = GCSDevice(CONTROLLERNAME)
        self.axes = axes
        
        HardwareComponent.__init__(self, app, debug=debug, name=name)


    def setup(self):

        ax_name = default_axes[1]
        # some settings are related to the number of axes implemented


        self.settings.New("controller", dtype=str, initial="C-413.2GA", ro=True) # PI controller name
        self.settings.New("stage", dtype=str, initial="V-524.1AA", ro=True) # PI stage name
        self.settings.port = self.add_logged_quantity('port', dtype=str, initial='COM5')
        # Note: the M-405.CG stage has a travel range of 0-50mm and the reference switch is at 25mm

        self.settings.New("ref_mode", dtype=str, choices=[ "None", "FNL", "FPL", "FRF"], initial="None", ro=False) # reference mode for the stage
        # None don't reference the stage position
        # FNL reference the stage position by starting a movement to the Negative limit of the stage!
        # FPL reference the stage position by starting a movement to the Positive limit of the stage!
        # FRF reference the stage position by starting a movement to the Reference switch (center) of the stage!

        self.settings.New(ax_name + "_position", dtype=float,
                          unit='mm', si=False, spinbox_decimals=4,
                          ro=True)

        self.settings.New(ax_name + "_target", dtype=float,
                          unit='mm', si=False, spinbox_decimals=4,
                          ro=False)

        self.settings.New(ax_name + "_relative_target_step", dtype=float,
                          unit='mm', si=False, spinbox_decimals=4, initial=0,
                          ro=False)



        self.settings.New(ax_name + '_servo', dtype=bool, ro=False)

        self.settings.New(ax_name + "_velocity", dtype=float, vmin=0, vmax=0.6, ro=False,
                          si=False, spinbox_decimals=3, unit='mm/s')

        self.settings.New(ax_name + "_on_target", dtype=bool, ro=True)

        #===================================================================
        # self.rangemin = self.add_logged_quantity("rangemin", dtype=float, unit='mm', ro=True)
        # self.rangemax = self.add_logged_quantity("rangemax", dtype=float, unit='mm', ro=True)
        #===================================================================

        self.add_operation("move relative", self.move_relative)
        self.add_operation("stop", self.stop)
        self.add_operation("set home", self.set_home)
        self.add_operation("go home", self.go_home)
        self.add_operation("start reference", self.start_reference)


        

    def connect(self):
            S = self.settings
            self.pidevice = GCSDevice(CONTROLLERNAME)
            """Connect controller via first serial port with 115200 baud."""


            # Choose the interface according to your cabling.

            # self.pidevice.ConnectTCPIP(ipaddress='192.168.90.207')
            self.pidevice.ConnectUSB(serialnum='0119024343')
            # self.pidevice.ConnectRS232(comport=1, baudrate=115200)

            print('connected: {}'.format(self.pidevice.qIDN().strip()))

            # Show the version info which is helpful for PI support when there
            # are any issues.

            if self.pidevice.HasqVER():
                print('version info:\n{}'.format(self.pidevice.qVER().strip()))

            print('initialize connected stages...')
            pitools.startup(self.pidevice, stages=STAGES, refmodes=REFMODES)
            # Now we query the allowed motion range and current position of all
            # connected stages. GCS commands often return an (ordered) dictionary
            # with axes/channels as "keys" and the according values as "values".

            rangemin = self.pidevice.qTMN()
            rangemax = self.pidevice.qTMX()
            curpos = self.pidevice.qPOS()
            print(curpos)

            ax_name=default_axes[1]
            ax_num=1 ##to change if number of stages is >1


            lq = S.get_lq(ax_name + "_position")
            lq.connect_to_hardware(
                read_func=lambda n=ax_num: self.pidevice.qPOS()[str(n)]
            )
            lq.read_from_hardware()

            lq = S.get_lq(ax_name + "_target")
            # move the stage to the specified value
            # Note: the position must be referenced before using this command
            lq.connect_to_hardware(
                read_func=lambda n=ax_num: self.pidevice.qMOV()[str(n)],
                write_func=lambda new_target, n=ax_num: self.pidevice.MOV(n, new_target)
            )
            lq.read_from_hardware()

            lq = S.get_lq(ax_name + "_servo")
            lq.connect_to_hardware(
                read_func=lambda n=ax_num: self.pidevice.qSVO()[str(n)],
                write_func=lambda enable, n=ax_num: self.pidevice.SVO(n, enable)
            )
            lq.read_from_hardware()

            lq = S.get_lq(ax_name + "_on_target")
            lq.connect_to_hardware(
                read_func=lambda n=ax_num: self.pidevice.qONT()[str(n)],
            )
            lq.read_from_hardware()

            lq = S.get_lq(ax_name + "_velocity")
            lq.connect_to_hardware(
                read_func=lambda n=ax_num: self.pidevice.qVEL()[str(n)],
                write_func=lambda new_vel, n=ax_num: self.pidevice.VEL(n, new_vel)
            )
            lq.read_from_hardware()

            self.update_thread_interrupted = False
            self.update_thread = threading.Thread(target=self.update_thread_run)
            self.update_thread.start()

            #             self.pidevice.RON(self.pidevice.axes, False)
    #             self.pidevice.POS(self.pidevice.axes, self.pidevice.qPOS(self.pidevice.axes)['1'])

    # print(self.pidevice.IsMoving(self.pidevice.axes)['1'])

    # ===============================================================================
    #         self.rangemin.hardware_read_func = self.GetRangeMN
    #         self.rangemax.hardware_read_func = self.GetRangeMX
    #
    #         self.rangemin.read_from_hardware()
    #         self.rangemax.read_from_hardware()
    # ===============================================================================

    def disconnect(self):
        for i in self.axes:
            if hasattr(self, 'pidevice'):
                self.pidevice.SVO(i, False) # turn the servo OFF

            self.settings.disconnect_all_from_hardware()

            if hasattr(self, 'update_thread'):
                print("stopping")
                self.update_thread_interrupted = True
                self.update_thread.join(timeout=1.0)
                del self.update_thread

            if hasattr(self, 'pidevice'):
                print("closing")
                self.pidevice.close()
                del self.pidevice




    #===========================================================================
    # def GetRangeMN(self):
    #     return float(list(self.pidevice.qTMN().values())[0])
    # def GetRangeMX(self):
    #     return float(list(self.pidevice.qTMX().values())[0])
    #===========================================================================


    def update_thread_run(self):
        while not self.update_thread_interrupted:
            for ax_num, ax_name in self.axes.items():
                self.settings.get_lq(ax_name + "_position").read_from_hardware()
                self.settings.get_lq(ax_name + "_on_target").read_from_hardware()
            time.sleep(0.050)

    def move_relative(self):
        ''' move relative to the current position of the distance specified with
        the relative_target_step setting.'''
        # can be used even without any reference
        for i in self.axes:
            if hasattr(self, 'pidevice'):
                self.pidevice.MVR(i, self.settings.x_relative_target_step.val)

    def stop(self):
        '''stop any movement (including those for reference)'''

        if hasattr(self, 'pidevice'):
            try:
                self.pidevice.STP()
            except:
                pass # ignores any error

    def set_home(self):
        '''set the current position as 0'''

        if hasattr(self, 'pidevice'):
            for i in self.axes:
                self.pidevice.DFH(i)


    def go_home(self):
        '''start a movement to 0'''
        # Note: the position must be referenced before using this command
        if hasattr(self, 'pidevice'):
            for i in self.axes:
                print("succhia cazzi")
                self.pidevice.GOH(i)

    def start_reference(self):
        '''start a reference move with the mode specified with the ref_mode setting'''

        if hasattr(self, 'pidevice'):
            for i in self.axes:
                if self.settings.ref_mode.val == "FNL":
                    self.pidevice.FNL(i)
                if self.settings.ref_mode.val == "FPL":
                    self.pidevice.FPL(i)
                if self.settings.ref_mode.val == "FRF":
                    self.pidevice.FRF(i)
                if self.settings.ref_mode.val == "None":
                    # *Dangerous*
                    # reference the stage by assuming that the current position is at the center of the stage
                    self.pidevice.RON(i, False)
                    self.pidevice.POS(i, 25)
                    self.set_home()


        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        