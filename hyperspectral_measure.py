# -*- coding: utf-8 -*-
"""
Created on wed Jun 16 01:33:32 2021

@authors: Andrea Bassi. Politecnico di Milano
"""
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import os, time

class hyperMeasure(Measurement):
    
    name = "hyper"
    
    def setup(self):
        """
        Runs once during App initialization.
        This is the place to load a user interface file,
        define settings, and set up data structures.
        """
        
        self.ui_filename = sibling_path(__file__, "camera.ui")
        self.ui = load_qt_ui_file(self.ui_filename) 
        
        self.settings.New('start_pos', dtype=float, unit='mm', initial=2.8463, spinbox_decimals=4) 
        # NOTE: adapt the initial motor position to your stage! 
        self.settings.New('step', dtype=float, unit='um', initial=40, spinbox_decimals=2) 
        self.settings.New('step_num', dtype=int, initial=50, vmin = 1) 
        #self.add_operation('measure', self.measure)
        
        
        self.settings.New('save_h5', dtype=bool, initial=False)         
        self.settings.New('refresh_period',dtype = float, unit ='s', spinbox_decimals = 3, initial = 0.05, vmin = 0)        
        
        #dummy values for initialization; they are necessary for HDF5 files visualization in ImageJ 
        self.settings.New('xsampling', dtype=float, unit='um', initial=1.0) 
        self.settings.New('ysampling', dtype=float, unit='um', initial=1.0)
        self.settings.New('zsampling', dtype=float, unit='um', initial=1.0)
        
        self.auto_range = self.settings.New('auto_range', dtype=bool, initial=True)
        self.settings.New('auto_levels', dtype=bool, initial=True)
        self.settings.New('level_min', dtype=int, initial=60)
        self.settings.New('level_max', dtype=int, initial=4000)
        
        self.image_gen = self.app.hardware['HamamatsuHardware'] #modificato da Martina 13-02-2025
        self.stage = self.app.hardware['PI_GCS_HW'] 
        
        
        
    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        
        # connect ui widgets to measurement/hardware settings or functions
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)
        self.settings.auto_levels.connect_to_widget(self.ui.autoLevels_checkbox)
        self.auto_range.connect_to_widget(self.ui.autoRange_checkbox)
        self.settings.level_min.connect_to_widget(self.ui.min_doubleSpinBox) 
        self.settings.level_max.connect_to_widget(self.ui.max_doubleSpinBox) 
                
        # Set up pyqtgraph graph_layout in the UI
        self.imv = pg.ImageView()
        self.ui.imageLayout.addWidget(self.imv)
        colors = [(0, 0, 0),
                  (45, 5, 61),
                  (84, 42, 55),
                  (150, 87, 60),
                  (208, 171, 141),
                  (255, 255, 255)
                  ]
        cmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, 6), color=colors)
        self.imv.setColorMap(cmap)
        
        
    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        
        self.stage.read_from_hardware()
        self.image_gen.read_from_hardware()
        
        self.display_update_period = self.settings['refresh_period'] 
       
        #length = self.image_gen.frame_num.val
        length = self.settings.step_num.val
        self.settings['progress'] = (self.frame_index +1) * 100/length
        
        
        
        if hasattr(self, 'img'):
            self.imv.setImage(self.img.T,
                                autoLevels = self.settings['auto_levels'],
                                autoRange = self.auto_range.val,
                                levelMode = 'mono'
                                )
            
            if self.settings['auto_levels']:
                lmin,lmax = self.imv.getHistogramWidget().getLevels()
                self.settings['level_min'] = lmin
                self.settings['level_max'] = lmax
            else:
                self.imv.setLevels( min= self.settings['level_min'],
                                    max= self.settings['level_max'])
            
            
    def measure(self):
        
        self.image_gen.read_from_hardware()
        first_frame_acquired = False
        step_num  = self.settings.step_num.val # number of acquired frames equals the number of motor steps
        self.image_gen.settings['acquisition_mode'] = 'fixed_length'
        self.image_gen.settings['number_frames'] = 1
        
        self.starting_pos = starting_pos = self.settings.start_pos.val
        step = self.settings.step.val /1000 # step is in um
    
        self.stage.motor.move_absolute(starting_pos)
        self.stage.motor.wait_on_target()
        
        for frame_idx in range(step_num):
            
            current_pos = self.stage.motor.get_position()
            print(f'Position at acquisition {frame_idx}:', current_pos)
            #self.image_gen.camera.acq_start() #Modificato
            self.image_gen.hamamatsu.startAcquisition()
            self.frame_index = frame_idx    
            [frame, dims] = self.image_gen.hamamatsu.getLastFrame()        
            self.np_data = frame.getData()
            self.img = np.reshape(self.np_data,(self.eff_subarrayv, self.eff_subarrayh))
            self.image_gen.hamamatsu.stopAcquisition()
                            
            if self.settings['save_h5']:
                if not first_frame_acquired:
                    self.create_h5_file()
                    first_frame_acquired = True
                self.image_h5[frame_idx,:,:] = self.img
                self.positions_h5[frame_idx] = current_pos
                self.h5file.flush()
            
            if self.interrupt_measurement_called:
                break
            
            if frame_idx < step_num-1: # does not make a step after the last acquisition
                target_pos = starting_pos + (frame_idx+1) * step
                self.stage.motor.move_absolute(target_pos) 
                self.stage.motor.wait_on_target()
                

            self.stage.read_from_hardware()
                  
            
    def run(self):
                   
        try:
            #start the camera
            self.frame_index = -1
            self.eff_subarrayh = int(self.image_gen.subarrayh.val/self.image_gen.binning.val)
            self.eff_subarrayv = int(self.image_gen.subarrayv.val/self.image_gen.binning.val)
            
            self.image_gen.read_from_hardware()
    
            self.image_gen.settings['acquisition_mode'] = 'run_till_abort'
            self.image_gen.hamamatsu.startAcquisition()
            
            # continuously get the last frame and put it in self.image, in order to 
            # show it via self.update_display()
            
            while not self.interrupt_measurement_called:
                
                [frame, dims] = self.image_gen.hamamatsu.getLastFrame()        
                self.np_data = frame.getData()
                self.img = np.reshape(self.np_data,(self.eff_subarrayv, self.eff_subarrayh))
                
                # If measurement is called, stop the acquisition, call self.measure
                # and get out of run()
                if self.settings['save_h5']:
                    self.image_gen.hamamatsu.stopAcquisition()
                    self.measure()
                    break
                
                if self.interrupt_measurement_called:
                    break
            
        finally:
            self.image_gen.hamamatsu.stopAcquisition()
            if self.settings['save_h5'] and hasattr(self, 'h5file'):
                # make sure to close the data file
                self.h5file.close() 
                self.settings['save_h5'] = False
                
                
                
    def create_saving_directory(self):
        
        if not os.path.isdir(self.app.settings['save_dir']):
            os.makedirs(self.app.settings['save_dir'])
        
    
    def create_h5_file(self):                   
        self.create_saving_directory()
        # file name creation
        timestamp = time.strftime("%y%m%d_%H%M%S", time.localtime())
        sample = self.app.settings['sample']
        #sample_name = f'{timestamp}_{self.name}_{sample}.h5'
        if sample == '':
            sample_name = '_'.join([timestamp, self.name])
        else:
            sample_name = '_'.join([timestamp, self.name, sample])
        fname = os.path.join(self.app.settings['save_dir'], sample_name + '.h5')
        
        self.h5file = h5_io.h5_base_file(app=self.app, measurement=self, fname = fname)
        self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
        
        img_size = self.img.shape
        dtype=self.img.dtype
        
        length = self.settings.step_num.val
        
        self.image_h5 = self.h5_group.create_dataset(name  = 't0/c0/image', 
                                                  shape = [length, img_size[0], img_size[1]],
                                                  dtype = dtype)
        self.image_h5.attrs['element_size_um'] =  [self.settings['zsampling'],self.settings['ysampling'],self.settings['xsampling']]
        
        self.positions_h5 = self.h5_group.create_dataset(name  = 't0/c0/position_mm', 
                                                  shape = [length],
                                                  dtype = np.float32)
                   

    