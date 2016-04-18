import os, sys, inspect, thread, time
src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
arch_dir = 'C:\_Daten\Hochschule\EPS\Group  E - Integrating Slicer and Leap Motion\Software\Leap_Motion_SDK_Windows_2.3.1\LeapDeveloperKit_2.3.1+31549_win\LeapSDK\lib/x64' if sys.maxsize > 2**32 else 'C:\_Daten\Hochschule\EPS\Group  E - Integrating Slicer and Leap Motion\Software\Leap_Motion_SDK_Windows_2.3.1\LeapDeveloperKit_2.3.1+31549_win\LeapSDK\lib/x86'
sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))
import Leap