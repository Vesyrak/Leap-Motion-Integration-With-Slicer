import os, sys, inspect, thread, time
src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = 'C:\Program Files (x86)\Leap Motion\LeapDeveloperKit_2.3.1+31549_win\LeapSDK\lib/x64' if sys.maxsize > 2**32 else 'C:\Program Files (x86)\Leap Motion\LeapDeveloperKit_2.3.1+31549_win\LeapSDK\lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))
import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

class LeapMotionListener(Leap.Listener):
    finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    bone_names = ['Metacarpal', 'Proximal', 'Intermediate', 'Ring', 'Distal']
    state_names = ['STATE_INVALID', 'STATE_START', 'STATE_UPDATE', 'STATE_END']
    
    def on_init(self, controller):
        print "Initialized"
        #listener initialized

    def on_connect(self, controller):
        print "Motion Sensor Connected!"

        controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);
        controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

    def on_disconnect(self, controller):
        print "Motion Sensor Disconnected"

    def on_exit(self, coltroller):
        print "Exited"

    def on_frame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame(0)

        hand = frame.hands.rightmost
        position = hand.palm_position
        velocity = hand.palm_velocity
        direction = hand.direction

        sphere_center = hand.sphere_center
        sphere_diameter = 2 * hand.sphere_radius
        print sphere_diameter

        """print "Frame ID:   " + str(frame.id) \
            + " # of Hands " + str(len(frame.hands))
            + " # of Fingers " + str(len(frame.fingers))
            + " Timestamp:  " + str(frame.timestamp) \
            + " # of Tools " + str(len(frame.tools)) \
            + " # of Gestures " + str(len(frame.gestures())) """

        for hand in frame.hands:
            handType = "Left Hand" if hand.is_left else "Right Hand"

            #print handType + " Hand ID:  " + str(hand.id) + " Palm Position:  " + str(hand.palm_position)

            normal = hand.palm_normal
            direction = hand.direction
            #vector perpendicular to the plane formed by the palm of the hand. The vector points downward out of the palm

            pitch = hand.direction.pitch #angle around the x-axis
            yaw = hand.direction.yaw #angle around the y-axis
            roll = hand.palm_normal.roll #angle around the z-axis

            print "Pitch:  "+ str(direction.pitch * Leap.RAD_TO_DEG) + "Roll: " + str(normal.roll * Leap.RAD_TO_DEG) + " Yaw: " + str(direction.yaw * Leap.RAD_TO_DEG)


            """arm = hand.arm
            print "Arm Direction " + str(arm.direction) + " Wrist Position " + str(arm.wrist_position) + " Elbow Position: " + str(arm.elbow_position) 

            for finger in hand.fingers:
                print "Type: " + self.finger_names[finger.type()] + " ID: " + str(finger_names.id) + " length (mm): " str(finger.length) + " Width (mm): " + str(finger.width)

                for b in range(0, 4): 
                    bone - finger.bone()
                    print "Bone: " + self.bone_names[bone.type] + " Start: " + str(bone_names.prev_joint) + " End: " + str(bone.next_joint) + " Direction: " + str(bone.direction) """
                   
        """  for tool in frame.tools:
        print "tool ID: " + str(toold.id) + " Tip Position: " + str(tool.tip_position) + " Direction: " + str(tool.direction) """
        
        for gesture in frame.gestures():
            """if gesture.type == Leap.Gesture.TYPE_CIRCLE:
                    circle = CircleGesture(gesture)
                    # Circle Gesture (working)

                    if circle.pointable.direction.angle_to(circle.normal) <= Leap.PI/2:
                        clockwiseness = "clockwise"
                    else:
                        clockwiseness = "counter-clockwise"

                    swept_angle = 0
                    if circle.state != Leap.Gesture.STATE_START:
                        previous = CircleGesture(controller.frame(1).gesture(circle.id))
                        swept_angle = (circle.progress - previous.progress) * 2 * Leap.PI

                    print "ID: " + str(CircleGesture.id) + " Progress: " + str(circle.progress) + " Radius: " + str(circle.radius) + " Swept Angle: " + str(swept_angle + Leap.RAD_TO_DEG) + "" + clockwiseness

            if gesture.type == Leap.Gesture.TYPE_SWIPE:
                    swipe = SwipeGesture(gesture)
                    print "Swipe ID: " + str(swipe.id) + " State: " + self.state_names[gesture.state] + " Position: " + str(swipe.position) + " Directions: " + str(swipe.direction) + " Speed (m/s): " + str(swipe.speed)
                    # Swipe Gesture (working)"""

            """if gesture.type == Leap.Gesture.TYPE_KEY_TAP:
                    keytap = KeyTapGesture(gesture)
                    print "Key Tap ID: " + str(gesture.id) + " State: " + self.state_names[gesture.state] + " Position: " + str(keytap.position) + " Directions: " + str(keytap.direction) + " Speed (m/s): " + str(keytap.speed)
                    # Key Tap Gesture (not working)"""

            if gesture.type is Leap.Gesture.TYPE_SCREEN_TAP:
                    screen_tap = ScreenTapGesture(gesture)
                    print "Screen Tap ID: "+ str(gesture.id) + " State: " + self.state_names[gesture.state] + " Position: " + str(screen_tap.position) + " Directions: " + str(screen_tap.direction)
                    # Screen Tap Gesture
                    controller.config.set("Gesture.ScreenTap.MinForwardVelocity", 50.0)
                    controller.config.set("Gesture.ScreenTap.HistorySeconds", .1)
                    controller.config.set("Gesture.ScreenTap.MinDistance", 5.0)
                    controller.config.save()

def main():
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
    main()
