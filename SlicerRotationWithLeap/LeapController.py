import os, sys
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture
import time

#
# LeapController
#

class LeapController(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "LeapController" #
        self.parent.categories = ["Gesture Control"]
        self.parent.dependencies = []
        self.parent.contributors = ["Reinout Eyckerman (HIOA)"] # replace with "Firstname Lastname (Organization)"
        self.parent.helpText = """
        This is an example of scripted loadable module bundled in an extension.
        It performs a simple thresholding on the input volume and optionally captures a screenshot.
        """
        self.parent.acknowledgementText = """
        This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
        and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
    """ # replace with organization, grant and thanks.

class LeapControllerWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = LeapControllerLogic()
        #
        # Parameters Area
        #
        controllerCollapsibleButton = ctk.ctkCollapsibleButton()
        controllerCollapsibleButton.text = "Controller"
        self.layout.addWidget(controllerCollapsibleButton)
        # Layout within the dummy collapsible button
        controllerFormLayout = qt.QFormLayout(controllerCollapsibleButton)
        # Start Button
        self.startButton = qt.QPushButton("Start")
        self.startButton.toolTip = "Start running the Leap"
        self.startButton.connect('clicked()',self.onStartButton)
        controllerFormLayout.addWidget(self.startButton)
        # Stop Button
        self.stopButton = qt.QPushButton("Stop")
        self.stopButton.toolTip = "Stop running the Leap"
        self.stopButton.connect('clicked()',self.onStopButton)
        controllerFormLayout.addWidget(self.stopButton)
    def cleanup(self):
        pass

    def onStartButton(self):
        self.logic.bind()
    def onStopButton(self):
        if self.logic !=  None:
            self.logic.stop()

class LeapControllerLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        print "Initiation Leap Controller Reads"
        self.leapbinder=LeapBinder()
        self.controller=Leap.Controller()
        self.listener=SampleListener(self.controller, self.leapbinder)
        self.freerunning=False
        self.slicer=Slicer()
    def stop(self):
        print "Stopping Leap Controller Reads"
        self.listener.stop()
    def stopStart(self, frame, historyframe):
        if frame.hands.rightmost.palm_normal.z>-0.6 and not self.freerunning:
            self.leapbinder.Bind("Zoom", self.slicer.zoom)
            self.leapbinder.Bind("Rotate",self.slicer.rotateWXYZ)
            self.freerunning= not self.freerunning
        elif frame.hands.rightmost.palm_normal.z<-0.6 and self.freerunning:
            print "Not Reading"
            self.leapbinder.Remove("Zoom",self.slicer.zoom)
            self.leapbinder.Remove("Rotate",self.slicer.rotateWXYZ)
            self.freerunning= not self.freerunning
    def bind(self):
        self.leapbinder.Bind("Rotate", self.stopStart)
        self.listener.start()

class LeapBinder:
    """Currently used as Event Binder."""
    def __init__(self):
        self.bindings={}
    def Bind(self, state, function):
        if state not in self.bindings:
            self.bindings[state]=[function]
        else: self.bindings[state].append(function)
    def Remove(self, state, function):
        if state in self.bindings:
            if len(self.bindings[state])==1:
                self.bindings.pop(state)
            else: self.bindings[state].remove(function)
    def CallFunction(self, state, frame, historyframe):
        if state in self.bindings:
            print state
            for i in self.bindings[state]:
                try:
                    i(frame, historyframe)
                except Exception, e:
                    print str(e)
                    print "Exiting due to error"

class Slicer:
    def __init__(self):
        self.lm=slicer.app.layoutManager()
        self.view=self.lm.threeDWidget(0).threeDView()
        self.view.yawDirection=self.view.YawLeft
        self.camera=slicer.util.getNode('Default Scene Camera')
        self.transform=slicer.vtkMRMLLinearTransformNode()
        slicer.mrmlScene.AddNode(self.transform)
        self.camera.SetAndObserveTransformNodeID(self.transform.GetID())
        self.vtkcam=self.camera.GetCamera()
        self.matrix=vtk.vtkTransform()
        self.degrees=1

    def zoom(self, frame, historyframe): # link to diameter sphere
        difference= frame.hands.rightmost.sphere_radius-historyframe.hands.rightmost.sphere_radius
        print difference
        self.vtkcam.Dolly(pow(1.1, -0.5 * difference))
    def rotateWXYZ(self, frame, historyframe):
        bonebasis=frame.hands.rightmost.palm_position
        hbonebasis=historyframe.hands.rightmost.palm_position
        x = bonebasis.x
        y = bonebasis.y
        z = bonebasis.z
        self.matrix.RotateX(-(y-hbonebasis.y)/2)
        self.matrix.RotateZ(-(x-hbonebasis.x)/2)
        self.transform.SetMatrixTransformToParent(self.matrix.GetMatrix())

class SampleListener(Leap.Listener):
    def __init__(self,controller, leapbinder):
        super(SampleListener, self).__init__()
        self.leapbinder=leapbinder
        self.controller=controller
        self.controller.config.set("Gesture.ScreenTap.MinForwardVelocity", 20.0)
        self.controller.config.set("Gesture.ScreenTap.HistorySeconds", 1)
        self.controller.config.set("Gesture.ScreenTap.MinDistance", 2.0)
        self.controller.config.save()
        self.controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);
        self.controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        self.controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
        self.controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);
        self.run=False
        self.historyframe=None
    def stop(self):
        self.run=False
    def start(self):
        print "Starting"
        self.run=True
        self.on_frame()
    def on_connect(self, controller):
        print "Motion Sensor Connected"

    def on_frame(self):
        frame = self.controller.frame()
        if self.historyframe is None:
            self.historyframe=frame

        hands = frame.hands
        for hand in frame.hands:
            handType = "Left Hand" if hand.is_left else "Right Hand"
            if handType=="Right Hand":
                self.leapbinder.CallFunction("Zoom", frame, self.historyframe)
                self.leapbinder.CallFunction("Rotate", frame,self.historyframe)

        self.historyframe=frame
        if self.run:
            qt.QTimer.singleShot(100, self.on_frame)

class LeapControllerTest(ScriptedLoadableModuleTest):
    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """

    def test_LeapController1(self):
        pass
