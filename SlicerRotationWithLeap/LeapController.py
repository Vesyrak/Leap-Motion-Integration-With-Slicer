import os, sys
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture
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

        self.slicer=Slicer()
        self.controls=["CircleLeft", "CircleRight"]
    def stop(self):
        print "Stopping Leap Controller Reads"
        self.listener.stop()
    def bind(self):
        self.leapbinder.Bind("CircleLeft", self.slicer.rotateLeft)
        self.leapbinder.Bind("CircleRight", self.slicer.rotateRight)
        self.listener.start()
class LeapBinder:
    """Currently used as Event Binder."""
    def __init__(self):
        self.bindings={}
    def Bind(self, state, function):
        if state not in self.bindings:
            self.bindings[state]=[function]
        else: self.bindings[state].append(function)
    def Remove(self, state, function): #check mistakes
        if state in function:
            if len(self.bindings[state])==1:
                self.bindings.pop(state)
            else: self.bindings[state].remove(function)
    def CallFunction(self, state, frame):
        for i in self.bindings[state]:
            try:
                i(frame)
            except Exception, e:
                print str(e)
                print "Exiting due to error"
                # sys.exit()
class Slicer:
    def __init__(self):
        self.lm=slicer.app.layoutManager()
        # self.view=self.lm.threeDWidget(0).threeDView()
        # self.view.setPitchRollYawIncrement(10)
        #This is an axis:
        # self.axis=ctk.ctkAxesWidget()
        # self.axis.Anterior #This equals to 5, it's an enum
        #This gets the volume in MRHead
        self.camera=slicer.util.getNode('Default Scene Camera')
        self.transform=slicer.vtkMRMLLinearTransformNode()
        #This creates a matrix for linear transforms
        slicer.mrmlScene.AddNode(self.transform)
        self.camera.SetAndObserveTransformNodeID(self.transform.GetID())
        self.matrix=vtk.vtkTransform()
        self.degrees=1
        #Linear transformer. We need to combine this(or an alternative) to the Scalar volume
#        self.transform.SetAndObserveMatrixTransformToParent()

    # def TransformMatrix():
        # self.transform.GetMatrixTransformToParent(matrix.GetMatrix())
        # self.newmatrix.RotateX(20)
        # vtk.vtkMatrix4x4.Multiply4x4(matrix.GetMatrix(), newmatrix.GetMatrix(), outmatrix.GetMatrix())
        # self.transform.SetMatrixTransformToParent(outmatrix.GetMatrix())

    def Rotate(direction):
        if direction == "Left":
            rotateLeft()
        elif direction == "Right":
            rotateRight()
        elif direction=="Up":
            rotateUp()
        elif direction=="Down":
            rotateDown()
        elif direction=="CW":
            rotateCW()
        elif direction=="CCW":
            rotateCCW()
        self.transform.SetMatrixTransformToParent(self.matrix.GetMatrix())
    def rotateLeft(self, frame): #check axes slicer vs Leap

        self.matrix.RotateZ(self.degrees)
        self.transform.SetMatrixTransformToParent(self.matrix.GetMatrix())
    def rotateRight(self, frame):
        self.matrix.RotateZ(-self.degrees)
        self.transform.SetMatrixTransformToParent(self.matrix.GetMatrix())
    def rotateUp(self, frame):
        self.matrix.RotateX(-self.degrees)
    def rotateDown(self, frame):
        self.matrix.RotateX(self.degrees)
    def rotateCCW(self, frame):
        self.matrix.RotateY(-self.degrees)
    def rotateCW(self, frame):
        self.matrix.RotateY(self.degrees)
    def zoomOut(self, frame): # link to diameter sphere
        self.matrix.Translate(0, self.zoom, 0)
    def zoomIn(self, frame):
        self.matrix.Translate(0,-self.zoom,0)
    def moveImg(self, frame): # link to x,y,z of handpalm center average
        hand = frame.hands.rightmost
        index_finger_list = hand.fingers.finger_type(Finger.TYPE_INDEX)
        index_finger = index_finger_list[0] #since there is only one per hand
        bone = finger.bone(Bone.TYPE_DISTAL)
        basis = bone.basis
        x = basis.x_basis
        y = basis.y_basis
        z = basis.z_basis
        self.view.setFocalPoint(x,y,z )
    def rotateToAxis(self,axis):
        self.view.lookFromViewAxis(axis)

class SampleListener(Leap.Listener):
    def __init__(self,controller, leapbinder):
        print "ARRIBA ARRIBA"
        super(SampleListener, self).__init__()
        self.leapbinder=leapbinder
        self.controller=controller
        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);
        controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);
        self.run=False
    def stop(self):
        self.run=False
    def start(self):
        self.run=True
        self.on_frame()
    def on_connect(self, controller):
        print "Motion Sensor Connected"

    # def on_disconnect(self, controller):
        # print "Motion Sensor Disconnected"

    # def on_exit(self, coltroller):
        # print "Exited"

    def on_frame(self):
        # Get the most recent frame and report some basic information
        print "Frame"

        frame = self.controller.frame()
        print frame

        hands = frame.hands
        for hand in frame.hands:
            handType = "Left Hand" if hand.is_left else "Right Hand"

            # print handType # + " Hand ID:  " + str(hand.id) + " Palm Position:  " + str(hand.palm_position)

            sphere_center = hand.sphere_center
            sphere_diameter = 2 * hand.sphere_radius
            pinch = hand.pinch_strength
            filtered_hand_position = hand.stabilized_palm_position #stabilized palm position of this Hand
            #print "Diameter: " + str(sphere_diameter) + " Pinch: " + str(pinch) + " Hand pos: " + str(filtered_hand_position)

        for gesture in frame.gestures():
            if gesture.type == Leap.Gesture.TYPE_CIRCLE:
                print "Circle"
                circle = CircleGesture(gesture)
                # Circle Gesture

                if circle.pointable.direction.angle_to(circle.normal) <= Leap.PI/2:
                    clockwiseness = "CircleLeft"
                else:
                    clockwiseness = "CircleRight"

                """swept_angle = 0
                    if circle.state != Leap.Gesture.STATE_START:
                        previous = CircleGesture(controller.frame(1).gesture(circle.id))
                        swept_angle = (circle.progress - previous.progress) * 2 * Leap.PI
                    print "ID: " + str(CircleGesture.id) + " Progress: " + str(circle.progress) + " Radius: " + str(circle.radius) + " Swept Angle: " + str(swept_angle + Leap.RAD_TO_DEG) + "" + clockwiseness"""

                try:
                    self.leapbinder.CallFunction(clockwiseness, frame)
                except Exception, e:
                    print str(e)
                    print "Exiting due to error"
                    sys.exit()

            if gesture.type is Leap.Gesture.TYPE_SCREEN_TAP:
                    screen_tap = ScreenTapGesture(gesture)
                    # Screen Tap Gesture
                    #print "Screen Tap ID: "+ str(gesture.id) + " State: " + self.state_names[gesture.state] + " Position: " + str(screen_tap.position) + " Directions: " + str(screen_tap.direction)
                    controller.config.set("Gesture.ScreenTap.MinForwardVelocity", 50.0)
                    controller.config.set("Gesture.ScreenTap.HistorySeconds", .1)
                    controller.config.set("Gesture.ScreenTap.MinDistance", 5.0)
                    controller.config.save()
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
"""def main():
    # Create a sample listener and controller
    listener = LeapMotionListener()
    controller = Leap.Controller()

    # Have the sample listener receive events from the controller
    controller.add_listener(listener)

    # Keep this process running until Enter is pressed
    print "Press enter to quit..."

    try:
        sys.stdin.readline()
    except KeyboardInterrupt:
        pass
    finally:
        controller.remove_listener(listener)
        # Remove the sample listener when done

if __name__=="__main__":
    main()"""
