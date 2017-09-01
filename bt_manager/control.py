from __future__ import unicode_literals

from device import BTGenericDevice
import dbus


class BTControl(BTGenericDevice):
    """Wrapper around Dbus to encapsulate the BT control entity"""

    SIGNAL_CONNECTED = 'Connected'
    SIGNAL_DISCONNECTED = 'Disconnected'
    MEDIA_CONTROL_INTERFACE_BLUEZ5 = 'org.bluez.MediaControl1'

    def __init__(self, *args, **kwargs):
        if (self.get_version() <= self.BLUEZ4_VERSION):
            BTGenericDevice.__init__(self, addr='org.bluez.Control',
                                     *args, **kwargs)
            self._register_signal_name(BTControl.SIGNAL_CONNECTED)
            self._register_signal_name(BTControl.SIGNAL_DISCONNECTED)
        else:
            BTGenericDevice.__init__(self,
                                     addr=self.MEDIA_CONTROL_INTERFACE_BLUEZ5,
                                     *args, **kwargs)
            self._init_properties()

    def _init_properties(self):
        self._props_interface = dbus.Interface(self._object, self.DBUS_PROPERTIES)
        props = self._props_interface.GetAll(self.MEDIA_CONTROL_INTERFACE_BLUEZ5)
        self._properties = list(props.keys())
        self._register_signal_name(self.SIGNAL_PROPERTIES_CHANGED)

    def get_property(self, name=None):
        """
        Helper to get a property value by name or all
        properties as a dictionary.

        See also :py:meth:`set_property`

        :param str name: defaults to None which means all properties
            in the object's dictionary are returned as a dict.
            Otherwise, the property name key is used and its value
            is returned.
        :return: Property value by property key, or a dictionary of
            all properties
        :raises dbus.Exception: org.bluez.Error.DoesNotExist
        :raises dbus.Exception: org.bluez.Error.InvalidArguments
        """
        # BlueZ 4
        if (self.get_version() <= self.BLUEZ4_VERSION):
            raise Exception('Not handled with bluez 4')

        # BlueZ 5
        else:
            if (name):
                return self._props_interface.Get(self.DEVICE_INTERFACE_BLUEZ5, name)
            else:
                return self._props_interface.GetAll(self.DEVICE_INTERFACE_BLUEZ5)

    def is_connected(self):
        if (self.get_version() <= self.BLUEZ4_VERSION):
            return self._interface.IsConnected()
        else:
            self.get_property('Connected')
            pass

    def volume_up(self):
        """Adjust remote volume one step up"""
        self._interface.VolumeUp()

    def volume_down(self):
        """Adjust remote volume one step down"""
        self._interface.VolumeDown()

    def next(self):
        """  """
        self._interface.Next()

    def previous(self):
        """  """
        self._interface.Previous()

    def pause(self):
        """  """
        self._interface.Pause()

    def play(self):
        """  """
        self._interface.Play()

    def rewind(self):
        """  """
        self._interface.Rewind()

    def fast_forward(self):
        """  """
        self._interface.FastForward()
