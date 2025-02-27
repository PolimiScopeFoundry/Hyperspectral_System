from PI_ScopeFoundry.PI_voice_coil import PIStage
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
class PIStageNew(PIStage):
    
    def setup(self):
        
        
        ax_name = default_axes[1]
        # some settings are related to the number of axes implemented


        self.controller = self.add_logged_quantity("controller", dtype=str, initial="C-413.2GA", ro=True) # PI controller name
        self.stage = self.add_logged_quantity("stage", dtype=str, initial="V-524.1AA", ro=True) # PI stage name
        self.pp_amplitude = self.add_logged_quantity("pp_amplitude", dtype=float, unit='mm', si=False, spinbox_decimals=4,initial=3, ro=False)  # Ammplitude for given motion
        #self.number_of_cycles = self.add_logged_quantity("number_of_cycles", dtype=int, unit='', si=False, initial=1, vmin = 1, ro=False) # Number of cycles
        self.settings.port = self.add_logged_quantity('port', dtype=str, initial='COM5')
        self.starting_point = self.add_logged_quantity("starting_point", dtype=str, choices=["NL", "Home", "PL"], initial="Home", ro=False)
        self.scanning_Mode = self.add_logged_quantity("scanning_Mode", dtype=str, choices=["Sinusoidal", "Ramp", "Smoothed Ramp"], initial="Sinusoidal", ro=False)
        self.frequency_periodic_motion = self.add_logged_quantity("frequency_periodic_motion", dtype=int, unit = 'Hz', initial=5, ro=False, vmin = 1, vmax = 50)
        self.number_of_points = self.add_logged_quantity("number_of_points", dtype=int, unit='', si=False, initial=1000, vmin = 1, ro=False)
        self.tablerate = self.add_logged_quantity("tablerate", dtype=int, unit='', si=False, spinbox_step=1, initial=2, vmin = 1, vmax = 10, ro=False)
        self.center_point = self.add_logged_quantity("center_point", dtype=int, unit='', si=False, spinbox_step=1, initial=500, vmin = 1, ro=False)
        self.speed_up_down = self.add_logged_quantity("speed_up_down", dtype=int, unit='', si=False, spinbox_step=1, initial=500, vmin = 0, ro=False)
        self.number_of_cycles = self.add_logged_quantity("number_of_cycles", dtype=int, unit='', si=False, initial = 1, vmin = 1, ro=False)
        
        self.calculated_tablerate = self.tablerate.val
        self.calculated_center_point = self.center_point.val
        self.calculated_speed_up_down = self.speed_up_down.val
        # Note: the M-405.CG stage has a travel range of 0-50mm and the reference switch is at 25mm

        # self.settings.New("ref_mode", dtype=str, choices=[ "None", "FNL", "FPL", "FRF"], initial="None", ro=False) # reference mode for the stage
        # # None don't reference the stage position
        # # FNL reference the stage position by starting a movement to the Negative limit of the stage!
        # # FPL reference the stage position by starting a movement to the Positive limit of the stage!
        # # FRF reference the stage position by starting a movement to the Reference switch (center) of the stage!

        self.settings.New(ax_name + "_position", dtype=float, unit='mm', si=False, spinbox_decimals=4, ro=True)

        self.settings.New(ax_name + "_target", dtype=float, unit='mm', si=False, spinbox_decimals=4, ro=False, initial = -0.45)

        # self.settings.New(ax_name + "_relative_target_step", dtype=float,
        #                   unit='mm', si=False, spinbox_decimals=4, initial=0,
        #                   ro=False)



        self.settings.New(ax_name + '_servo', dtype=bool, ro=False)

        self.settings.New(ax_name + "_velocity", dtype=float, vmin=0, vmax=200, ro=False, si=False, spinbox_decimals=3, initial=100, unit='mm/s')

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
        
        super().connect()
        
        # if self.pidevice.HasCCL(): 
        #     self.pidevice.CCL(level = 1, password='advanced')
        
        # if self.pidevice.HasSPA(): 
        #     self.pidevice.SPA(items = 1, params = 0x06010300, values = 1)
        
        self.pidevice.MOV(1, self.settings.x_target.val)
        self.tablerate.hardware_read_func = self.getTablerate
        self.center_point.hardware_read_func = self.getCenterPoint
        self.speed_up_down.hardware_read_func = self.getSpeedUpDown

    def periodic_motion(self):
        
        assert 1 == len(self.pidevice.axes[1]), 'this sample requires one'

        AMPLITUDE = self.pp_amplitude.val
        NUMCYCLES = self.number_of_cycles.val
        NUMPOINTS = self.number_of_points.val
        wavegens = (1,)
        wavetables = (2,)
        CENTERPOINT = self.center_point.val
        SPEED_UP_DOWN = self.speed_up_down.val
        STARTPOS[0] = 0

        if self.settings.starting_point.val == 'NL':
            STARTPOS[0] = -5
        elif self.settings.starting_point.val == 'PL':
            STARTPOS[0] = 5
            AMPLITUDE = -AMPLITUDE

        if self.settings.scanning_Mode.val == 'Sinusoidal':
            print('define sine and cosine waveforms for wave tables {}'.format(wavetables))
            print("numpoints---> ", NUMPOINTS)
            print("center---> ", int(CENTERPOINT))
            print("offset---> ", self.home-AMPLITUDE/2)
            print("amplitude---> ", AMPLITUDE)
            self.pidevice.WAV_SIN_P(table=wavetables[0], firstpoint=0, numpoints=NUMPOINTS, append='X',
                                     center=int(CENTERPOINT), amplitude=AMPLITUDE, offset=self.home-AMPLITUDE/2, seglength=NUMPOINTS)
#             self.pidevice.WAV_SIN_P(table=wavetables[0], firstpoint=0, numpoints=NUMPOINTS, append='X',
#                                     center=NUMPOINTS / 2, amplitude=AMPLITUDE, offset=STARTPOS[0], seglength=NUMPOINTS)

        elif self.settings.scanning_Mode.val == 'Ramp':
                print('define ramp waveforms for wave tables {}'.format(wavetables))
                self.pidevice.WAV_LIN(table=wavetables[0], firstpoint=0, numpoints=NUMPOINTS, append='X',
                                      speedupdown=SPEED_UP_DOWN, amplitude=AMPLITUDE, offset=STARTPOS[0], seglength=NUMPOINTS)
                print("TABLERATE:", TABLERATE)
                print("CENTERPOINT:", CENTERPOINT)
                print("NUMPOINTS:", NUMPOINTS)
                print("SPEED_UP_DOWN:", SPEED_UP_DOWN)
                print("AMPLITUDE:", AMPLITUDE)
                print("STARTPOS[0]:", STARTPOS[0])
                
        elif self.settings.scanning_Mode.val == 'Smoothed Ramp':
                print("TABLERATE:", TABLERATE)
                print("CENTERPOINT:", CENTERPOINT)
                print("NUMPOINTS:", NUMPOINTS)
                print("SPEED_UP_DOWN:", SPEED_UP_DOWN)
                print("AMPLITUDE:", AMPLITUDE)
                print("STARTPOS[0]:", STARTPOS[0])
                print('define sine and cosine waveforms for wave tables {}'.format(wavetables))

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
#         STARTPOS[0] = 0
#         print('I am going hoooomeeee')
#         self.pidevice.MOV(1, STARTPOS[0])

    def getTablerate(self):
        
        return self.calculated_tablerate
    
    def getCenterPoint(self):
        
        return self.calculated_center_point
    
    def getSpeedUpDown(self):
        
        return self.calculated_speed_up_down
    