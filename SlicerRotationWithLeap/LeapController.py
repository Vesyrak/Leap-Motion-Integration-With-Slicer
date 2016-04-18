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

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

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

        # Start Button
        self.stopButton = qt.QPushButton("Stop")
        self.stopButton.toolTip = "Stop running the Leap"
        self.stopButton.connect('clicked()',self.onStopButton)
        controllerFormLayout.addWidget(self.stopButton)
    def cleanup(self):
        pass


    def onStartButton(self):
        self.logic = LeapControllerLogic()
        self.logic.bind()
    def onStopButton(self):
        self.logic.stop()

#
# LeapControllerLogic
#

class LeapControllerLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        print "Initiation Leap Controller Reads"
        self.leapbinder=LeapBinder()
        self.listener=SampleListener(self.leapbinder)
        self.controller=Leap.Controller()
        self.controller.add_listener(self.listener)
        self.slicer=Slicer()
        self.controls=["CircleLeft", "CircleRight"]
    def stop(self):
        print "Stopping Leap Controller Reads"
        self.controller.remove_listener(self.listener)
    def bind(self):
        self.leapbinder.Bind("CircleLeft", self.slicer.yaw)

class LeapBinder:
    """Currently used as Event Binder."""
    def __init__(self):
        self.bindings={}

    def Bind(self, state, function):
        if state not in self.bindings:
            self.bindings[state]=[function]
        else: self.bindings[state].append(function)
    def Remove(self, state, function):
        if len(self.bindings[state])==1:
            self.bindings.pop(state)
        else: self.bindings[state].remove(function)
    def CallFunction(self, state):
        for i in self.bindings[state]:
            try:
                i()
            except Exception, e:
                print str(e)
                print "Exiting due to error"
                sys.exit()
class Slicer:
    def __init__(self):
        self.lm=slicer.app.layoutManager()
        self.view=self.lm.threeDWidget(0).threeDView()
        self.view.setPitchRollYawIncrement(10)
        #This is an axis:
        self.axis=ctk.ctkAxesWidget()
        self.axis.Anterior #This equals to 5, it's an enum
        #This gets the volume in MRHead
        self.camera=slicer.util.getNode('Default Scene Camera')
        self.transform=slicer.vtkMRMLLinearTransformNode()
        #This creates a matrix for linear transforms
        slicer.mrmlScene.AddNode(transform)
        camera.SetAndObserveTransformNodeID(transform.GetID())
        self.matrix=vtk.vtkTransform()
        #Linear transformer. We need to combine this(or an alternative) to the Scalar volume
#        self.transform.SetAndObserveMatrixTransformToParent()

    def TransformMatrix():
        transform.GetMatrixTransformToParent(matrix.GetMatrix())
        newmatrix.RotateX(20)
        vtk.vtkMatrix4x4.Multiply4x4(matrix.GetMatrix(), newmatrix.GetMatrix(), outmatrix.GetMatrix())

        transform.SetMatrixTransformToParent(outmatrix.GetMatrix())

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
    def rotateLeft(self):
        self.matrix.RotateZ(self.degrees)
    def rotateRight(self):
        self.matrix.RotateZ(-self.degrees)
    def rotateUp(self):
        self.matrix.RotateX(-self.degrees)
    def rotateDown(self):
        self.matrix.RotateX(self.degrees)
    def rotateCCW(self):
        self.matrix.RotateY(-self.degrees)
    def rotateCW(self):
        self.matrix.RotateY(self.degrees)
    def zoomOut(self):
        self.matrix.Translate(0, self.zoom, 0)
    def zoomIn(self):
        self.matrix.Translate(0,-self.zoom,0)
    def moveImg(self,x, y, z):
        self.view.setFocalPoint(x,y,z)
    def rotateToAxis(self,axis):
        self.view.lookFromViewAxis(axis)

class SampleListener(Leap.Listener):
    def __init__(self, leapbinder):
        super(SampleListener, self).__init__()
        self.leapbinder=leapbinder
    def on_connect(self, controller):
        print "Connected"
        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);

    def on_frame(self, controller):
        frame = controller.frame()
        for gesture in frame.gestures():
            if gesture.type == Leap.Gesture.TYPE_CIRCLE:
                print "Circle"
                circle = CircleGesture(gesture)
                if circle.pointable.direction.angle_to(circle.normal)<=Leap.PI/2:
                    try:
                        self.leapbinder.CallFunction("CircleLeft")
                    except Exception, e:
                        print str(e)
                        print "Exiting due to error"
                        sys.exit()

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
        """ Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")
        #
        # first, get some data
        #
        import urllib
        downloads = (
            ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
            )

        for url,name,loader in downloads:
            filePath = slicer.app.temporaryPath + '/' + name
            if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
                logging.info('Requesting download %s from %s...\n' % (name, url))
                urllib.urlretrieve(url, filePath)
            if loader:
                logging.info('Loading %s...' % (name,))
                loader(filePath)
        self.delayDisplay('Finished with download and loading')

        volumeNode = slicer.util.getNode(pattern="FA")
        logic = LeapControllerLogic()
        self.assertTrue( logic.hasImageData(volumeNode) )
        self.delayDisplay('Test passed!')
