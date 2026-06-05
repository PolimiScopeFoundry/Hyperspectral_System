import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,QGroupBox,QCheckBox, QPushButton,
    QProgressBar, QFormLayout, QLineEdit, QLabel, QSpinBox, QDoubleSpinBox, QFileDialog, QLineEdit, QPushButton,
    QGroupBox, QCheckBox, QProgressBar
)
from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import time
import pyqtgraph as pg



def add_path(path):
    import sys
    import os
    # add path to ospath list, assuming that the path is in a sybling folder
    from os.path import dirname
    sys.path.append(os.path.abspath(os.path.join(dirname(dirname(__file__)),path)))




class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hyperspectral Control Panel")

        #--------GUI SETUP--------
        #Scaling the window to 80% of the screen size
        screen = QApplication.primaryScreen().availableGeometry()

        w = int(screen.width() * 0.8)
        h = int(screen.height() * 0.8)

        self.resize(w, h)

        # center the window
        x = (screen.width() - w) // 2
        y = (screen.height() - h) // 2

        self.move(x, y)

        layout = QHBoxLayout()
        left_panel = QVBoxLayout()
        right_panel = QVBoxLayout()
        form = QFormLayout()


        self.camera = None
        self.motor = None

        # ---- Camera acquisition parameters ----
        
        self.frames = QSpinBox()
        self.frames.setRange(1, 10000)
        self.frames.setValue(20)

        self.exposure = QDoubleSpinBox()
        self.exposure.setRange(3, 10000)
        self.exposure.setValue(5)
        # self.exposure.setSuffix(" ms")

        self.binning = QSpinBox()
        self.binning.setRange(1, 10)
        self.binning.setValue(2)

        self.H_pos = QSpinBox()
        self.H_pos.setRange(1, 10000)
        self.H_pos.setValue(500)

        self.V_pos = QSpinBox()
        self.V_pos.setRange(1, 10000)
        self.V_pos.setValue(500)

        # ---- Stage acquisition parameters ----
        self.start_pos = QDoubleSpinBox()
        self.start_pos.setRange(-1000, 1000)
        self.start_pos.setValue(5)
        # self.start_pos.setSuffix(" mm")

        self.step = QDoubleSpinBox()
        self.step.setRange(0.001, 100)
        self.step.setValue(4)
        # self.step.setSuffix(" mm")

        self.velocity = QDoubleSpinBox()
        self.velocity.setRange(0.01, 7.5)
        self.velocity.setValue(5)
        # self.velocity.setSuffix(" mm/s")

        self.step_num = QSpinBox()
        self.step_num.setRange(1, 10000)
        self.step_num.setValue(20)

        # ---- default inputs ----
        self.W = QLineEdit("500")
        self.H = QLineEdit("500")
        self.H_pos = QLineEdit("500")
        self.V_pos = QLineEdit("500")



        camera_box = QGroupBox("Camera")
        self.camera_init = QCheckBox("Connect Camera")
        self.camera_init.setChecked(False)
        self.camera_init.stateChanged.connect(self.connect_camera)
        camera_layout = QFormLayout()
        camera_layout.addRow(self.camera_init)
        camera_layout.addRow("Width:", self.W)
        camera_layout.addRow("Height:", self.H)
        camera_layout.addRow("Horizontal pos:", self.H_pos)
        camera_layout.addRow("Vertical pos:", self.V_pos)
        camera_layout.addRow("Exposure:", self.exposure)
        camera_layout.addRow("Binning:", self.binning)
        camera_box.setLayout(camera_layout)

        stage_box = QGroupBox("Stage")
        self.stage_init = QCheckBox("Connect Stage")
        self.stage_init.setChecked(False)
        self.stage_init.stateChanged.connect(self.connect_stage)
        stage_layout = QFormLayout()
        stage_layout.addRow(self.stage_init)
        stage_layout.addRow("Start position:", self.start_pos)
        stage_layout.addRow("Step:", self.step)
        stage_layout.addRow("Step number:", self.step_num)
        stage_layout.addRow("Velocity:", self.velocity)
        stage_box.setLayout(stage_layout)


        saving_box = QGroupBox("Saving")
        self.filename = QLineEdit("dataset_001")
        self.save_dir = QLineEdit()
        self.save_dir.setReadOnly(True)
        self.browse_btn = QPushButton("Browse Folder")
        self.browse_btn.clicked.connect(self.choose_folder)
        saving_layout = QFormLayout()
        # directory row (label + widget container)
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.save_dir)
        dir_layout.addWidget(self.browse_btn)
        saving_layout.addRow("Save directory:", dir_layout)
        saving_layout.addRow("File name:", self.filename)
        saving_box.setLayout(saving_layout)

        left_panel.addLayout(form)
        left_panel.addWidget(camera_box)
        left_panel.addWidget(stage_box)
        left_panel.addWidget(saving_box)



        

        # ---- LIVE IMAGE VIEW ----
        self.viewer = pg.ImageView()
        right_panel.addWidget(self.viewer)

        # ---- progress bar ----
        self.progress = QProgressBar()
        left_panel.addWidget(self.progress)

        # ---- buttons ----
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("STOP")

        left_panel.addWidget(self.start_btn)
        left_panel.addWidget(self.stop_btn)


        self.setLayout(layout)
        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 2)

        # ---- thread ----
        self.thread = None

        self.start_btn.clicked.connect(self.start_acquisition)
        self.stop_btn.clicked.connect(self.stop_acquisition)

        self.setStyleSheet("""
        QWidget {
            font-size: 15px;
        }

        QGroupBox {
            font-weight: bold;
            border: 1px solid #ccc;
            border-radius: 8px;
            margin-top: 10px;
            padding: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }


        QProgressBar {
            border: 1px solid #ccc;
            border-radius: 5px;
            text-align: center;
        }
        """)

    def connect_camera(self, state):
        
        add_path('Hamamatsu_ScopeFoundry')
        from CameraDevice import PVcamDevice
            
        from PyQt5.QtCore import Qt

        if state == Qt.Checked:
            try:
                self.camera = PVcamDevice()
                print("Camera initialized")
            except Exception as e:
                print("Camera init failed:", e)
                self.camera = None
                self.camera_init.setChecked(False)

        else:
            if self.camera is not None:
                try:
                    self.camera.close()
                    print("Camera closed")
                except:
                    pass
            self.camera = None

    def connect_stage(self, state):
        add_path('PI_ScopeFoundry')
        from PI_VC_device import PI_VC_Device
        from PyQt5.QtCore import Qt

        if state == Qt.Checked:
            try:
                self.motor = PI_VC_Device('0024550348')
                print("Motor initialized")
            except Exception as e:
                print("Motor init failed:", e)
                self.motor = None
                self.motor_init.setChecked(False)

        else:
            if self.motor is not None:
                try:
                    self.motor.close()
                    print("Motor closed")
                except:
                    pass
            self.motor = None

    def start_acquisition(self):

        params = {
            "W": int(self.W.text()),
            "H": int(self.H.text()),
            "exposure_time": float(self.exposure.value()),
            "binning": int(self.binning.value()),
            "start_pos": float(self.start_pos.value()),
            "step": float(self.step.value()),
            "velocity": float(self.velocity.value()),
            "step_num": int(self.step_num.value()),
            "V_pos": float(self.V_pos.text()),
            "H_pos": float(self.H_pos.text())
        }

        self.thread = AcquisitionThread(params)

        self.thread.frame_signal.connect(self.update_image)
        self.thread.progress_signal.connect(self.progress.setValue)
        self.thread.log_signal.connect(print)

        self.thread.start()

    def stop_acquisition(self):
        if self.thread:
            self.thread.stop()
            print("STOP signal sent")

    def update_image(self, img):
        self.viewer.setImage(img.T, autoLevels=True)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if folder:
            self.save_dir.setText(folder)




class AcquisitionThread(QThread):
    frame_signal = pyqtSignal(object)   # sends image
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            self.log_signal.emit("Initializing hardware...")

            # --- imports INSIDE thread (important for hardware stability) ---

            W = self.params["W"]
            H = self.params["H"]
            binning = self.params["binning"]
            exposure = self.params["exposure_time"]
            start_pos = self.params["start_pos"]
            step = self.params["step"]
            n_frames = self.params["step_num"]
            velocity = self.params["velocity"]

            self.camera.set_trigger_mode('Internal Trigger')
            self.camera.set_exposure(exposure)
            self.camera.set_binning(binning)
            self.camera.set_roi(
                self.params["H_pos"],
                self.params["V_pos"],
                W, H
            )

            self.motor.set_velocity(velocity)
            self.motor.move_absolute(start_pos)
            self.motor.wait_on_target()

            HyperMatrix = np.zeros(
                (H // binning, W // binning, n_frames),
                dtype=np.float32
            )

            positions = np.zeros(n_frames, dtype=np.float32)

            target_pos = np.arange(
                start_pos,
                start_pos + n_frames * step / 1000,
                step / 1000
            )

            self.log_signal.emit("Starting acquisition loop...")

            for i in range(n_frames):

                if self._stop:
                    self.log_signal.emit("STOP requested → shutting down safely.")
                    break

                self.motor.move_absolute(target_pos[i])
                self.motor.wait_on_target()

                self.camera.acq_start_seq(1)
                img = self.camera.get_nparray()
                self.camera.acq_stop()

                HyperMatrix[:, :, i] = img
                positions[i] = self.motor.get_position() * 1000

                # ---- LIVE FEEDBACK ----
                self.frame_signal.emit(img)
                self.progress_signal.emit(int((i + 1) / n_frames * 100))

            # --- SAFE SHUTDOWN ---
            self.camera.close()
            self.motor.close()

            self.log_signal.emit("Acquisition finished.")

        except Exception as e:
            self.log_signal.emit(f"ERROR: {str(e)}")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())