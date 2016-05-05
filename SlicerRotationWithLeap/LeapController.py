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
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

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

#
# LeapControllerWidget
#

class LeapControllerWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
    # logic=None
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = LeapControllerLogic()
        # Instantiate and connect widgets ...

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

#
# LeapControllerLogic
#

class LeapControllerLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        print "Initiation Leap Controller Reads"
        self.leapbinder=LeapBinder()
        self.controller=Leap.Controller()
        self.listener=SampleListener(self.controller, self.leapbinder)
        self.freerunning=False
        self.slicer=Slicer()
        self.controls=["CircleLeft", "CircleRight"]
        self.t0=time.time()
    def stop(self):
        print "Stopping Leap Controller Reads"
        self.listener.stop()
    def stopStart(self, frame, historyframe):
        t1= time.time()-self.t0
        if t1>1.0:
            print t1
            self.t0=time.time()
            if not self.freerunning:
                self.leapbinder.Bind("Zoom", self.slicer.zoom)
            else:
                self.leapbinder.Remove("Zoom",self.slicer.zoom)
            self.freerunning= not self.freerunning
    def bind(self):
        # self.leapbinder.Bind("CircleLeft", self.slicer.rotateLeft)
        # self.leapbinder.Bind("CircleRight", self.slicer.rotateRight)
        self.leapbinder.Bind("CircleLeft", self.stopStart)
        self.leapbinder.Bind("Rotate",self.slicer.rotateWXYZ)
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
        self.camera=slicer.util.getNode('Default Scene Camera')
        self.transform=slicer.vtkMRMLLinearTransformNode()
        slicer.mrmlScene.AddNode(self.transform)
        self.camera.SetAndObserveTransformNodeID(self.transform.GetID())
        self.matrix=vtk.vtkTransform()
        self.degrees=1

    def rotateLeft(self, frame, historyframe): #check axes slicer vs Leap
        self.matrix.RotateZ(self.degrees)
        self.transform.SetMatrixTransformToParent(self.matrix.GetMatrix())
    def rotateRight(self, frame, historyframe):
        self.matrix.RotateZ(-self.degrees)
        self.transform.SetMatrixTransformToParent(self.matrix.GetMatrix())
    def rotateUp(self, frame, historyframe):
        self.matrix.RotateX(-self.degrees)
    def rotateDown(self, frame, historyframe):
        self.matrix.RotateX(self.degrees)
    def rotateCCW(self, frame, historyframe):
        self.matrix.RotateY(-self.degrees)
    def rotateCW(self, frame, historyframe):
        self.matrix.RotateY(self.degrees)
    def zoom(self, frame, historyframe): # link to diameter sphere
        difference= 2*(frame.hands.rightmost.sphere_radius-historyframe.hands.rightmost.sphere_radius)
        self.matrix.Translate(0,-difference,0)
        self.transform.SetMatrixTransformToParent(self.matrix.GetMatrix())
    def moveImg(self, frame, historyframe): # link to x,y,z of handpalm center average
        hand = frame.hands.rightmost
        index_finger_list = hand.fingers.finger_type(Finger.TYPE_INDEX)
        index_finger = index_finger_list[0] #since there is only one per hand
        bonebasis = finger.bone(Bone.TYPE_DISTAL).basis
        x = bonebasis.x_basis
        y = bonebasis.y_basis
        z = bonebasis.z_basis
        self.view.setFocalPoint(x,y,z )
    def rotateToAxis(self,axis, historyframe):
        self.view.lookFromViewAxis(axis)
    def rotateWXYZ(self, frame, historyframe):
        hm = frame.hands.rightmost.stabilized_palm_position
        hmo = historyframe.hands.rightmost.stabilized_palm_position
        print hm.x-hmo.x
        self.matrix.RotateX((hm.x - hmo.x)*180)
        self.matrix.RotateZ((hm.y - hmo.y)*180)
        self.matrix.RotateY((hm.z - hmo.z)*180)
        self.transform.SetMatrixTransformToParent(self.matrix.GetMatrix())
class SampleListener(Leap.Listener):
    def __init__(self,controller, leapbinder):
        super(SampleListener, self).__init__()
        self.leapbinder=leapbinder
        self.controller=controller
        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);
        controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);
        controller.config.set("Gesture.ScreenTap.MinForwardVelocity", 20.0)
        controller.config.set("Gesture.ScreenTap.HistorySeconds", .1)
        controller.config.set("Gesture.ScreenTap.MinDistance", 2.0)
        controller.config.save()
        self.run=False
        self.historyframe=None
    def stop(self):
        self.run=False
    def start(self):
        self.run=True
        self.on_frame()
    def on_connect(self, controller):
        print "Motion Sensor Connected"

    def on_frame(self):
        # Get the most recent frame and report some basic information

        frame = self.controller.frame()
        if self.historyframe is None:
            self.historyframe=frame

        hands = frame.hands
        for hand in frame.hands:
            handType = "Left Hand" if hand.is_left else "Right Hand"

            if handType=="Right Hand":
                self.leapbinder.CallFunction("Zoom", frame, self.historyframe)
                self.leapbinder.CallFunction("Rotate", frame, self.historyframe)
        for gesture in frame.gestures():
            if gesture.type == Leap.Gesture.TYPE_CIRCLE:
                circle = CircleGesture(gesture)

                if circle.pointable.direction.angle_to(circle.normal) <= Leap.PI/2:
                    clockwiseness = "CircleLeft"
                else:
                    clockwiseness = "CircleRight"

                try:
                    self.leapbinder.CallFunction(clockwiseness, frame, self.historyframe)
                except Exception, e:
                    print str(e)
                    print "Exiting due to error"

            if gesture.type is Leap.Gesture.TYPE_SCREEN_TAP:
                # screen_tap = ScreenTapGesture(gesture)
                self.leapbinder.CallFunction("ScreenTap",frame, self.historyframe)
                    # Screen Tap Gesture
                    #print "Screen Tap ID: "+ str(gesture.id) + " State: " + self.state_names[gesture.state] + " Position: " + str(screen_tap.position) + " Directions: " + str(screen_tap.direction)
        self.historyframe=frame
        if self.run:
            qt.QTimer.singleShot(100, self.on_frame)

class LeapControllerTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_LeapController1()

    def test_LeapController1(self):
        pass
