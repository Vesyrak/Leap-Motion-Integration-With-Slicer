import os, sys, inspect, thread, time
src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = '../lib/x64' if sys.maxsize > 2**32 else '../lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))
import Leap
# ABC
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture
from pykeyboard import PyKeyboard
k=PyKeyboard()
class SampleListener(Leap.Listener):
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
                    k.tap_key(k.right_key)
                else:
                    k.tap_key(k.left_key)
            time.sleep(1.5)
def main():
    listener=SampleListener()
    controller=Leap.Controller()
    controller.add_listener(listener)
    print "Press enter to quit"
    try:
        sys.stdin.readline()
    except KeyboardInterrupt:
        pass
    finally:
        controller.remove_listener(listener)
if __name__ == "__main__":
    main()
