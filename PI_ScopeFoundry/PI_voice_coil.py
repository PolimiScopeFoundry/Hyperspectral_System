"""
****************************************
This version uses the pipython library, released by Physik Instrumente.
****************************************
Calisesi Gianmaria (@Gianmaria92 on github), PhD at Politecnico di Milano.
Michele Castriotta (@mikics on github), PhD at Politecnico di Milano.


12/12/18
"""




from ScopeFoundry import HardwareComponent
from collections import OrderedDict
from PI_ScopeFoundry.PIPython.pipython import GCSDevice, GCSError, gcserror
from PI_ScopeFoundry.PIPython.pipython.gcscommands import GCSCommands
from PI_ScopeFoundry.PIPython.pipython.interfaces.piserial import PISerial
from PI_ScopeFoundry.PIPython.pipython.gcsmessages import GCSMessages
from PI_ScopeFoundry.PIPython.pipython import pitools
from PI_ScopeFoundry.PIPython.pipython.pidevice.gcs2.gcs2pitools import startup
import threading
import time
import sys



CONTROLLERNAME = 'C-413.2GA'
STARTPOS = [0]
STAGES = ['V-524.1AA']  # connect stages to axes
REFMODES = ['FRF']  # reference the connected stages
NUMPOINTS = 1000  # number of points for one sine period as integer
TABLERATE = 2  # duration of a wave table point in multiples of servo cycle times as integer

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
        self.settings.New("pp_amplitude", dtype=float, unit='mm', si=False, spinbox_decimals=4,initial=3, ro=False)  # Ammplitude for given motion
        self.settings.New("number_of_cycles", dtype=float, unit='', si=False, spinbox_decimals=0, spinbox_step=1, initial=1, vmin = 1, ro=False) # Number of cycles
        self.settings.port = self.add_logged_quantity('port', dtype=str, initial='COM5')
        self.settings.New("starting_point", dtype=str, choices=["NL", "Home", "PL"], initial="Home", ro=False)
        self.settings.New("scanning_Mode", dtype=str, choices=["Sinusoidal", "Ramp", "Smoothed Ramp"], initial="Sinusoidal", ro=False)
        self.settings.New("frequency_periodic_motion", dtype=int, unit = 'Hz', initial=5, ro=False, vmin = 1, vmax = 50)
        self.settings.New("number_of_points", dtype=float, unit='', si=False, spinbox_decimals=0, spinbox_step=1, initial=1000, vmin = 1, ro=False)
        self.settings.New("tablerate", dtype=float, unit='', si=False,spinbox_decimals=0, spinbox_step=1, initial=2, vmin = 1, vmax = 10, ro=False)
        self.settings.New("center_point", dtype=float, unit='', si=False, spinbox_decimals=0, spinbox_step=1, initial=500, vmin = 1, ro=False)
        self.settings.New("speed_up_down", dtype=float, unit='', si=False, spinbox_decimals=0, spinbox_step=1, initial=500, vmin = 1, ro=False)
        
        # Note: the M-405.CG stage has a travel range of 0-50mm and the reference switch is at 25mm

        # self.settings.New("ref_mode", dtype=str, choices=[ "None", "FNL", "FPL", "FRF"], initial="None", ro=False) # reference mode for the stage
        # # None don't reference the stage position
        # # FNL reference the stage position by starting a movement to the Negative limit of the stage!
        # # FPL reference the stage position by starting a movement to the Positive limit of the stage!
        # # FRF reference the stage position by starting a movement to the Reference switch (center) of the stage!

        self.settings.New(ax_name + "_position", dtype=float, unit='mm', si=False, spinbox_decimals=4, ro=True)

        self.settings.New(ax_name + "_target", dtype=float, unit='mm', si=False, spinbox_decimals=4, ro=False)

        # self.settings.New(ax_name + "_relative_target_step", dtype=float,
        #                   unit='mm', si=False, spinbox_decimals=4, initial=0,
        #                   ro=False)



        self.settings.New(ax_name + '_servo', dtype=bool, ro=False)

        self.settings.New(ax_name + "_velocity", dtype=float, vmin=0, vmax=200, ro=False, si=False, spinbox_decimals=3, unit='mm/s')

        self.settings.New(ax_name + "_on_target", dtype=bool, ro=True)

        #===================================================================
        # self.rangemin = self.add_logged_quantity("rangemin", dtype=float, unit='mm', ro=True)
        # self.rangemax = self.add_logged_quantity("rangemax", dtype=float, unit='mm', ro=True)
        #===================================================================

        # self.add_operation("move relative", self.move_relative)
        self.add_operation("stop", self.stop)
        self.add_operation("start periodic motion", self.threaded_periodic_motion)
        self.add_operation("set_home", self.set_home)
        # self.add_operation("temp_function", self.temp_function)
        # self.add_operation("temp_function1", self.temp_function1)
        # self.add_operation("temp_function2", self.temp_function2)
        # self.add_operation("set home", self.set_home)
        # self.add_operation("go home", self.go_home)
        # self.add_operation("start reference", self.start_reference)

        
        

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

            startup(self.pidevice, stages=STAGES, refmodes=REFMODES)
            #pitools.startup(self.pidevice, stages=STAGES)
            #pitools.startup(self.pidevice, stages=None, refmodes=None, servostates=True)
            # Now we query the allowed motion range and current position of all
            # connected stages. GCS commands often return an (ordered) dictionary
            # with axes/channels as "keys" and the according values as "values".

            rangemin = self.pidevice.qTMN()
            rangemax = self.pidevice.qTMX()
            curpos = self.pidevice.qPOS()['1']
            print('current position is',curpos)

            ax_name = default_axes[1]
            ax_num = 1 ##to change if number of stages is >1


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
            
            self.settings.frequency_periodic_motion.hardware_set_func = self.set_numpoints_from_frequency
            # lq = S.get_lq("pp_amplitude")
            # lq.connect_to_hardware(
            #    write_func=lambda new_Amp, n=ax_num: self.pidevice.VEL(n, new_vel),
            # )
            #
            # lq = S.get_lq("number_of_cycles")
            # lq.connect_to_hardware(
            #     write_func=self.read_cycles,
            # )

            self.update_thread_interrupted = False
            self.update_thread = threading.Thread(target=self.update_thread_run)
            self.update_thread.start()

            #             self.pidevice.RON(self.pidevice.axes, False)
    #             self.pidevice.POS(self.pidevice.axes, self.pidevice.qPOS(self.pidevice.axes)['1'])
            self.numpoints = int(1/(TABLERATE*200*10**(-6)*self.settings.frequency_periodic_motion.val))
            self.home = 0
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
    # def read_amplitude(self, read_amp):
    #     self.AMPLITUDE=read_amp
    #
    # def read_cycles(self, read_cyc):
    #     self.NUMCYLES = read_cyc

    def update_thread_run(self):
        while not self.update_thread_interrupted:
            for ax_num, ax_name in self.axes.items():
                self.settings.get_lq(ax_name + "_position").read_from_hardware()
                self.settings.get_lq(ax_name + "_on_target").read_from_hardware()
            time.sleep(0.050)
    
    def threaded_periodic_motion(self):
        thread = threading.Thread(target=self.periodic_motion)
        thread.start()
        
    def periodic_motion(self):
        assert 1 == len(self.pidevice.axes[1]), 'this sample requires one'
        speed = self.settings.x_velocity.val
        AMPLITUDE = self.settings.pp_amplitude.val
        NUMCYCLES = self.settings.number_of_cycles.val
        wavegens = (1,)
        wavetables = (2,)
        CENTERPOINT = NUMPOINTS*3/4
        SPEED_UP_DOWN = NUMPOINTS/8
        STARTPOS[0] = 0

        if self.settings.starting_point.val == 'NL':
            STARTPOS[0] = -5
        elif self.settings.starting_point.val == 'PL':
            STARTPOS[0] = 5
            AMPLITUDE = -AMPLITUDE

        if self.settings.scanning_Mode.val == 'Sinusoidal':
            print('define sine and cosine waveforms for wave tables {}'.format(wavetables))
            print("numpoints---> ", self.numpoints)
            print("center---> ", self.numpoints/2)
            print("offset---> ", self.home-AMPLITUDE/2)
            print("amplitude---> ", AMPLITUDE)
            self.pidevice.WAV_SIN_P(table=wavetables[0], firstpoint=0, numpoints=self.numpoints, append='X',
                                     center=int(self.numpoints/2), amplitude=AMPLITUDE, offset=self.home-AMPLITUDE/2, seglength=self.numpoints)
#             self.pidevice.WAV_SIN_P(table=wavetables[0], firstpoint=0, numpoints=NUMPOINTS, append='X',
#                                     center=NUMPOINTS / 2, amplitude=AMPLITUDE, offset=STARTPOS[0], seglength=NUMPOINTS)

        elif self.settings.scanning_Mode.val == 'Ramp':
                print('define ramp waveforms for wave tables {}'.format(wavetables))
                self.pidevice.WAV_LIN(table=wavetables[0], firstpoint=0, numpoints=NUMPOINTS, append='X',
                                      speedupdown=0, amplitude=AMPLITUDE, offset=STARTPOS[0], seglength=NUMPOINTS)
        elif self.settings.scanning_Mode.val == 'Smoothed Ramp':
                print("TABLERATE:", TABLERATE)
                print("CENTERPOINT:", CENTERPOINT)
                print("NUMPOINTS:", NUMPOINTS)
                print("SPEED_UP_DOWN:", SPEED_UP_DOWN)
                print("AMPLITUDE:", AMPLITUDE)
                print("STARTPOS[0]:", STARTPOS[0])
                print('define sine and cosine waveforms for wave tables {}'.format(wavetables))
                print(SPEED_UP_DOWN, CENTERPOINT, AMPLITUDE, STARTPOS[0], NUMPOINTS)
                self.pidevice.WAV_RAMP(table=wavetables[0], firstpoint=1, numpoints=NUMPOINTS, append='X',
                                       center=CENTERPOINT, speedupdown=SPEED_UP_DOWN, amplitude=AMPLITUDE,
                                       offset=STARTPOS[0], seglength=NUMPOINTS)

        pitools.waitonready(self.pidevice)
        
        if self.pidevice.HasWSL():  # you can remove this code block if your controller does not support WSL()
            print('connect wave generators {} to wave tables {}'.format(wavegens, wavetables))
            self.pidevice.WSL(wavegens, wavetables)
        
        if self.pidevice.HasWGC():  # you can remove this code block if your controller does not support WGC()
            print('set wave generators {} to run for {} cycles'.format(wavegens, NUMCYCLES))
            self.pidevice.WGC(wavegens, [NUMCYCLES] * len(wavegens))
        
        if self.pidevice.HasWTR():  # you can remove this code block if your controller does not support WTR()
            print('set wave table rate to {} for wave generators {}'.format(TABLERATE, wavegens))
            self.pidevice.WTR(wavegens, [TABLERATE] * len(wavegens), interpol=[0] * len(wavegens))
        
        #startpos = (STARTPOS[0])
        #print('move axes {} to their start positions {}'.format(self.pidevice.axes[1], startpos))
        #self.pidevice.MOV(1, startpos)  # 1 is for the axes to be moved
        pitools.waitontarget(self.pidevice)
        print('start wave generators {}'.format(wavegens))
        t1 = time.time()
        self.pidevice.WGO(wavegens, mode=[1] * len(wavegens))
        t2 = time.time()
        thread = threading.Thread(target=self.query_position)
        thread.start()
        while any(list(self.pidevice.IsGeneratorRunning(wavegens).values())) and t2-t1<=60:
            print('.', end='')
            time.sleep(1.0)
            
        t2=time.time()
        print('\n', t2-t1)
        print('\nreset wave generators {}'.format(wavegens))
        self.pidevice.WGO(wavegens, mode=[0] * len(wavegens))
        print('done')
        STARTPOS[0] = 0
        print('I am going hoooomeeee')
        self.pidevice.MOV(1, STARTPOS[0])

    def stop(self):
        '''stop any movement (including those for reference)'''

        if hasattr(self, 'pidevice'):
            # try:
            self.pidevice.STP(noraise=True)
            self.pidevice.MOV(1, self.home)
            # except
            # pass # ignores any error
            
    def set_home(self):
        self.home = self.settings["x_position"]

    def set_numpoints_from_frequency(self, value):
        self.numpoints = int(1/(TABLERATE*200*10**(-6)*value))
        
    def query_position(self):
        
        positions = []
        index = 0
        while any(list(self.pidevice.IsGeneratorRunning((1,)).values())):
            positions.append(self.pidevice.qPOS()['1'])
            print(positions[index])
            index += 1
        print("il min is--->", min(positions))
        print("il max is--->", max(positions))
    # def set_home(self):
    #     '''set the current position as 0'''
    #
    #     if hasattr(self, 'pidevice'):
    #         self.pidevice.DFH()
    #
    #
    # def go_home(self):
    #     '''start a movement to 0'''
    #     # Note: the position must be referenced before using this command
    #     if hasattr(self, 'pidevice'):
    #         print("going home")
    #         self.pidevice.GOH()
# ******************************************************************************************
    # def temp_function(self):
    #     wavegens = (1,)
    #     wavetables = (2,)
    #     self.pidevice.WAV_SIN_P(table=2, firstpoint=0, numpoints=2000, append='X',
    #                             center=1000, amplitude=10, offset=-5, seglength=2000)
    #     self.pidevice.WSL(wavegens, wavetables)
    #     self.pidevice.WGC(wavegens, [3] * len(wavegens))
    #     self.pidevice.WTR(wavegens, [20] * len(wavegens), interpol=[0] * len(wavegens))
    #     pitools.waitontarget(self.pidevice)
    #     self.pidevice.WGO(wavegens, mode=[1] * len(wavegens))

    # def temp_function1(self):
    #     lista = []
    #     wavegens = (1,)
    #     wavetables = (2,)
    #     self.pidevice.WAV_LIN(table=2, firstpoint=0, numpoints=3000, append='X',
    #                           speedupdown=0, amplitude=10, offset=-5, seglength=3000)
    #     self.pidevice.WSL(wavegens, wavetables)
    #     self.pidevice.WGC(wavegens, [3] * len(wavegens))
    #     self.pidevice.WTR(wavegens, [10] * len(wavegens), interpol=[0] * len(wavegens))
    #     pitools.waitontarget(self.pidevice)
    #     self.pidevice.WGO(wavegens, mode=[1] * len(wavegens))
    #     for i in range(50):
    #         lista.append(self.pidevice.qPOS())
    #         print(self.pidevice.qPOS())
    #     print(min(lista))
# ******************************************************************************************
    # def temp_function2(self):
    #     #booooooooooh
    #     wavegens = (1,)
    #     wavetables = (5,)
    #     self.pidevice.WAV_RAMP(table=5, firstpoint=1, numpoints=500, append='X',
    #                            center=300, speedupdown=200, amplitude=10,
    #                            offset=-4, seglength=200)
    #     self.pidevice.WSL(wavegens, wavetables)
    #     self.pidevice.WGC(wavegens, [3] * len(wavegens))
    #     self.pidevice.WTR(wavegens, [10] * len(wavegens), interpol=[0] * len(wavegens))
    #     pitools.waitontarget(self.pidevice)
    #     self.pidevice.WGO(wavegens, mode=[1] * len(wavegens))

    # def start_reference(self):
    #     '''start a reference move with the mode specified with the ref_mode setting'''
    #
    #     if hasattr(self, 'pidevice'):
    #         for i in self.axes:
    #             if self.settings.ref_mode.val == "FNL":
    #                 self.pidevice.FNL()
    #             if self.settings.ref_mode.val == "FPL":
    #                 self.pidevice.FPL()
    #             if self.settings.ref_mode.val == "FRF":
    #                 self.pidevice.FRF()
    #             if self.settings.ref_mode.val == "None":
    #                 # *Dangerous*
    #                 # reference the stage by assuming that the current position is at the center of the stage
    #                 self.pidevice.RON(i, False)
    #                 self.pidevice.POS(i, 25)
    #                 self.set_home()

 # def move_relative(self):
    #     ''' move relative to the current position of the distance specified with
    #     the relative_target_step setting.'''
    #     # can be used even without any reference
    #     for i in self.axes:
    #         if hasattr(self, 'pidevice'):
    #             self.pidevice.MVR(i, self.settings.x_relative_target_step.val)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        