# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at

  # http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.


# Imports
import os, sys, inspect
src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
lib_dir = os.path.abspath(os.path.join(src_dir, '../lib'))
sys.path.insert(0, lib_dir)
arch_dir = '../lib/x64' if sys.maxsize > 4294967296 else '../lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import Leap
from Leap import CircleGesture

class LeapController(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = 'LeapController'
        self.parent.categories = ['Gesture Control']
        self.parent.dependencies = []
        self.parent.contributors = ['Reinout Eyckerman (HIOA)']
        self.parent.helpText = 'Slicer module that allows 3D model rotation through the LeapMotion Controller'
        self.parent.acknowledgementText = 'This file was created by Reinout Eyckerman, with support from Thomas Chatel, Adrian Oliver Arcon, Andreas Ganal, Alyssa Mastel and Louise Oram, commisioned by Louise Oram and the HiOA university college of Oslo.'

class LeapControllerWidget(ScriptedLoadableModuleWidget):
    """Main widget that controls the UI"""

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = LeapControllerLogic()

        controllerCollapsibleButton = ctk.ctkCollapsibleButton()
        controllerCollapsibleButton.text = 'Controller'
        self.layout.addWidget(controllerCollapsibleButton)
        controllerFormLayout = qt.QFormLayout(controllerCollapsibleButton)

        self.startButton = qt.QPushButton('Start')
        self.startButton.toolTip = 'Start running the Leap'
        self.startButton.connect('clicked()', self.onStartButton)
        controllerFormLayout.addWidget(self.startButton)

        self.stopButton = qt.QPushButton('Stop')
        self.stopButton.toolTip = 'Stop running the Leap'
        self.stopButton.connect('clicked()', self.onStopButton)
        controllerFormLayout.addWidget(self.stopButton)

        self.radioFree = qt.QRadioButton('Free Rotation')
        self.radioFree.connect('clicked()', self.onFreeRotate)
        self.radioFree.checked = True
        self.radioXY = qt.QRadioButton('Lock XY')
        self.radioXY.connect('clicked()', self.onLockXY)
        self.radioXZ = qt.QRadioButton('Lock XZ')
        self.radioXZ.connect('clicked()', self.onLockXZ)
        self.radioYZ = qt.QRadioButton('Lock YZ')
        self.radioYZ.connect('clicked()', self.onLockYZ)
        controllerFormLayout.addWidget(self.radioFree)
        controllerFormLayout.addWidget(self.radioXY)
        controllerFormLayout.addWidget(self.radioXZ)
        controllerFormLayout.addWidget(self.radioYZ)

    def cleanup(self):
        pass

    def onStartButton(self):
        self.logic.bind()

    def onStopButton(self):
        if self.logic != None:
            self.logic.stop()

    def onFreeRotate(self):
        self.logic.slicer.rotateX = self.logic.slicer.rotateY = self.logic.slicer.rotateZ = True

    def onLockXY(self):
        self.logic.slicer.rotateX = self.logic.slicer.rotateY = False
        self.logic.slicer.rotateZ = True

    def onLockXZ(self):
        self.logic.slicer.rotateX = self.logic.slicer.rotateZ = False
        self.logic.slicer.rotateY = True

    def onLockYZ(self):
        self.logic.slicer.rotateZ = self.logic.slicer.rotateY = False
        self.logic.slicer.rotateX = True

class LeapControllerLogic(ScriptedLoadableModuleLogic):
    """The actual brain in the application, this binds all the leapmotion gestures to the slicer commands and executes the script"""
    def __init__(self):
        print 'Initiation Leap Controller Reads'
        self.leapbinder = LeapBinder()
        self.controller = Leap.Controller()
        self.listener = SampleListener(self.controller, self.leapbinder)
        self.freerunning = False
        self.slicer = Slicer()

    def stop(self):
        print 'Stopping Leap Controller Reads'
        self.listener.stop()

    def stopStart(self, frame, historyframe):
        if frame.hands.rightmost.palm_normal.z > -0.6 and not self.freerunning:
            self.leapbinder.Bind('Rotate', self.slicer.rotateWXYZ)
            self.leapbinder.Bind('CircleLeft', self.slicer.rotateCW)
            self.leapbinder.Bind('CircleRight', self.slicer.rotateCCW)
            self.freerunning = not self.freerunning
        elif frame.hands.rightmost.palm_normal.z < -0.6 and self.freerunning:
            self.leapbinder.Remove('Rotate', self.slicer.rotateWXYZ)
            self.leapbinder.Remove('CircleLeft', self.slicer.rotateCW)
            self.leapbinder.Remove('CircleRight', self.slicer.rotateCCW)
            self.freerunning = not self.freerunning

    def bind(self):
        self.leapbinder.Bind('Rotate', self.stopStart)
        self.leapbinder.Bind('CircleLeft', self.slicer.rotateCW)
        self.leapbinder.Bind('CircleRight', self.slicer.rotateCCW)
        self.listener.start()

class LeapBinder:
    """Allows dynamic binding of LeapMotion gestures to 3DSlicer"""
    def __init__(self):
        self.bindings = {}

    def Bind(self, state, function):
        if state not in self.bindings:
            self.bindings[state] = [function]
        else:
            self.bindings[state].append(function)

    def Remove(self, state, function):
        if state in self.bindings:
            if len(self.bindings[state]) == 1:
                self.bindings.pop(state)
            else:
                self.bindings[state].remove(function)

    def CallFunction(self, state, frame, historyframe):
        if state in self.bindings:
            for i in self.bindings[state]:
                try:
                    i(frame, historyframe)
                except Exception as e:
                    print "Error: "+str(e)

class Slicer:
    """Manipulates the camera for looking at the object. Zooming has been disabled because of the lack of properly working gestures for this"""
    def __init__(self):
        self.camera = slicer.util.getNode('Default Scene Camera')
        self.transform = slicer.vtkMRMLLinearTransformNode()
        slicer.mrmlScene.AddNode(self.transform)
        self.camera.SetAndObserveTransformNodeID(self.transform.GetID())
        self.vtkcam = self.camera.GetCamera()
        self.matrix = vtk.vtkTransform()
        self.degrees = 1
        self.rotateX = True
        self.rotateY = True
        self.rotateZ = True

    def rotateCW(self, frame, historyframe):
        if self.rotateY == True:
            self.matrix.RotateY(self.degrees)
            self.transform.SetMatrixTransformToParent(self.matrix.GetMatrix())

    def rotateCCW(self, frame, historyframe):
        if self.rotateY == True:
            self.matrix.RotateY(-self.degrees)
            self.transform.SetMatrixTransformToParent(self.matrix.GetMatrix())

    def rotateWXYZ(self, frame, historyframe):
        bonebasis = frame.hands.rightmost.palm_position
        hbonebasis = historyframe.hands.rightmost.palm_position
        x = bonebasis.x
        z = bonebasis.z
        if self.rotateX == True:
            self.matrix.RotateX((z - hbonebasis.z) / 2)
        if self.rotateZ == True:
            self.matrix.RotateZ(-(x - hbonebasis.x) / 2)
        self.transform.SetMatrixTransformToParent(self.matrix.GetMatrix())

class SampleListener(Leap.Listener):
    """Listener that gets the data from the LeapMotion device. It does not work according to the official LeapMotion way, since Slicer messes this up.
        Instead we poll for the data at 10fps"""
    def __init__(self, controller, leapbinder):
        super(SampleListener, self).__init__()
        self.leapbinder = leapbinder
        self.controller = controller
        self.controller.config.set('Gesture.Circle.MinRadius', 10.0)
        self.controller.config.save()
        self.controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE)
        self.run = False
        self.historyframe = None
        self.historycircle = False
        self.circle = True

    def stop(self):
        self.run = False

    def start(self):
        self.run = True
        self.on_frame()

    def on_connect(self, controller):
        print 'Motion Sensor Connected'

    def on_frame(self):
        frame = self.controller.frame()
        if self.historyframe is None:
            self.historyframe = frame
        gestureDetected = False
        hands = frame.hands
        for hand in frame.hands:
            handType = 'Left Hand' if hand.is_left else 'Right Hand'
            if handType == 'Right Hand':
                self.leapbinder.CallFunction('Zoom', frame, self.historyframe)
                self.leapbinder.CallFunction('Rotate', frame, self.historyframe)

        for gesture in frame.gestures():
            if gesture.type == Leap.Gesture.TYPE_CIRCLE:
                gestureDetected = True
                circle = CircleGesture(gesture)
                if circle.pointable.is_finger:
                    tappingFinger = Leap.Finger(circle.pointable)
                    if tappingFinger.type == Leap.Finger.TYPE_INDEX:
                        self.circle = True
                        if not self.historycircle:
                            self.historycircle = True
                            if circle.pointable.direction.angle_to(circle.normal) <= Leap.PI / 2:
                                clockwiseness = 'CircleLeft'
                            else:
                                clockwiseness = 'CircleRight'
                            try:
                                self.leapbinder.CallFunction(clockwiseness, frame, self.historyframe)
                                self.leapbinder.CallFunction(clockwiseness, frame, self.historyframe)
                            except Exception as e:
                                print str(e)

        if self.circle and not gestureDetected:
            self.circle = False
        if self.circle == False and self.historycircle == True:
            self.historycircle = False
        self.historyframe = frame
        if self.run:
            qt.QTimer.singleShot(100, self.on_frame)

class LeapControllerTest(ScriptedLoadableModuleTest):
    """Required by 3DSlicer, but not used"""
    def setUp(self):
        pass

    def runTest(self):
        pass

    def test_LeapController1(self):
        pass
