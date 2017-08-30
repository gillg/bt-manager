from __future__ import unicode_literals
from distutils.version import StrictVersion
import cffi
import os

__version__ = '0.4.0'

if StrictVersion(cffi.__version__) < StrictVersion('0.7'):
        raise RuntimeError(
            'bt_manager requires cffi >= 0.7, but found %s' % cffi.__version__)

ffi = cffi.FFI()
cwd = os.path.dirname(__file__)
header_file = os.path.join(cwd, 'rtpsbc.h')
with open(header_file) as fh:
    header = fh.read()
    ffi.cdef(header)
    fh.close()

from bt_manager.adapter import BTAdapter                 # noqa
from bt_manager.attributes import ATTRIBUTES             # noqa
from bt_manager.cod import BTCoD                         # noqa
from bt_manager.codecs import *                          # noqa
from bt_manager.control import BTControl                 # noqa
from bt_manager.device import BTGenericDevice, BTDevice  # noqa
from bt_manager.discovery import BTDiscoveryInfo         # noqa
from bt_manager.exceptions import *                      # noqa
from bt_manager.headset import BTHeadset                 # noqa
from bt_manager.headset import BTHeadsetGateway          # noqa
from bt_manager.interface import BTSimpleInterface       # noqa
from bt_manager.interface import BTInterface             # noqa
from bt_manager.manager import BTManager                 # noqa
from bt_manager.media import BTMedia, BTMediaTransport   # noqa
from bt_manager.input import BTInput                     # noqa
from bt_manager.serviceuuids import SERVICES             # noqa
from bt_manager.uuid import BTUUID, BTUUID16, BTUUID32   # noqa
from bt_manager.uuid import BASE_UUID                    # noqa
from bt_manager.vendors import VENDORS                   # noqa
from bt_manager.audio import BTAudio, BTAudioSource, BTAudioSink      # noqa
if (BTSimpleInterface.get_version() < BTSimpleInterface.BLUEZ4_VERSION):
    from bt_manager.audio import SBCAudioSource, SBCAudioSink, SBCAudioCodec  # noqa
from bt_manager.audio5 import SBCAudioSource5, SBCAudioSink5, SBCAudioCodec  # noqa
from bt_manager.agent import BTAgent                     # noqa
