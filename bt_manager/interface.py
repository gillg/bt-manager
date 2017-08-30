from __future__ import unicode_literals

import dbus
import types
import pprint

from exceptions import BTSignalNameNotRecognisedException


def translate_to_dbus_type(typeof, value):
    """
    Helper function to map values from their native Python types
    to Dbus types.

    :param type typeof: Target for type conversion e.g., 'dbus.Dictionary'
    :param value: Value to assign using type 'typeof'
    :return: 'value' converted to type 'typeof'
    :rtype: typeof
    """
    if ((isinstance(value, types.UnicodeType) or
         isinstance(value, str)) and typeof is not dbus.String):
        # FIXME: This is potentially dangerous since it evaluates
        # a string in-situ
        return typeof(eval(value))
    else:
        return typeof(value)


class Signal():
    """
    Encapsulation of user callback wrapper for signals
    fired by dbus.  This allows us to prepend the signal
    name and the user callback argument.

    :param str signal: Signal name
    :param func user_callback: User-defined callback function to
        call when the signal triggers
    :param user_arg: User-defined callback argument to be passed
        as callback function
    """
    def __init__(self, signal, user_callback, user_arg):
        self.signal = signal
        self.user_callback = user_callback
        self.user_arg = user_arg

    def signal_handler(self, *args):
        """
        Method to call in order to invoke the user callback.

        :param args: list of signal-dependent arguments
        :return:
        """
        self.user_callback(self.signal, self.user_arg, *args)


class BTSimpleInterface:
    """
    Wrapper around dbus to encapsulated a BT simple interface
    entry point (i.e., has no signals or properties).

    :param str path: Object path pertaining to the interface to open
                     e.g., '/org/bluez/985/hci0'
    :param str addr: dbus address of the interface instance to open
                     e.g., 'org.bluez.Adapter'

    .. note:: This class should always be sub-classed with a concrete
        implementation of a bluez interface which has no signals or
        properties.
    """
    SIGNAL_INTERFACES_ADDED = 'InterfacesAdded'
    """
    :signal InterfacesAdded(signal_name, user_arg, object_path):
        Signal notifying when an adapter is added.
    """
    SIGNAL_INTERFACES_REMOVED = 'InterfacesRemoved'
    """
    :signal InterfacesRemoved(signal_name, user_arg, object_path):
        Signal notifying when an adapter is added.
    """
    SIGNAL_PROPERTIES_CHANGED = 'PropertiesChanged'
    """
    :signal PropertiesChanged(sig_name, user_arg, prop_name, prop_value):
        Signal notifying when a property has changed. (Bluez 5)
    """
    SIGNAL_PROPERTY_CHANGED = 'PropertyChanged'
    """
    :signal PropertyChanged(sig_name, user_arg, prop_name, prop_value):
        Signal notifying when a property has changed. (Bluez 4)
    """

    BLUEZ_DBUS_OBJECT = 'org.bluez'
    DBUS_OBJECT = 'org.freedesktop.DBus'
    #BLUEZ4_VERSION = 1.2
    BLUEZ4_VERSION = 4

    def __init__(self, path, addr):
        self._dbus_addr = addr
        self._init_bus()
        self.get_version()
        self._object = self._bus.get_object(BTSimpleInterface.BLUEZ_DBUS_OBJECT, path)
        self._interface = dbus.Interface(self._object, addr)
        self._path = path

    @staticmethod
    def get_version():
        if (not hasattr(BTSimpleInterface, '_version') or BTSimpleInterface._version is None):
            from subprocess import Popen, PIPE
            from psutil import Process

            dbus_infos = dbus.SystemBus().get_object(BTSimpleInterface.DBUS_OBJECT, '/')
            interface = dbus.Interface(dbus_infos, BTSimpleInterface.DBUS_OBJECT)
            #BTSimpleInterface._version = float(interface.GetNameOwner(BTSimpleInterface.BLUEZ_DBUS_OBJECT)[1:])
            pid = int(interface.GetConnectionUnixProcessID(BTSimpleInterface.BLUEZ_DBUS_OBJECT))

            daemon = Process(pid)
            #daemon.cwd() should contain "bluetoothd"
            cmd = Popen([daemon.exe(),"--version"], stdout=PIPE)
            BTSimpleInterface._version = float(cmd.stdout.read())
        return BTSimpleInterface._version

    def _init_bus(self):
        if (not hasattr(self, '_bus') or self._bus is None):
            self._bus = dbus.SystemBus()


# This class is not intended to be instantiated directly and should be
# sub-classed with a concrete implementation for an interface
class BTInterface(BTSimpleInterface):
    """
    Wrapper around DBus to encapsulated a BT interface
    entry point e.g., an adapter, a device, etc.

    :param str path: Object path pertaining to the interface to open
                     e.g., '/org/bluez/985/hci0'
    :param str addr: dbus address of the interface instance to open
                     e.g., 'org.bluez.Adapter'

    .. note:: This class should always be sub-classed with a concrete
        implementation of a bluez interface which has both signals
        and properties.
    """
    DBUS_PROPERTIES = 'org.freedesktop.DBus.Properties'
    DBUS_OBJ_MANAGER = 'org.freedesktop.DBus.ObjectManager'

    def __init__(self, path, addr):
        BTSimpleInterface.__init__(self, path, addr)
        self._signals = {}
        self._signal_names = []

    def _register_signal_name(self, name):
        """
        Helper function to register allowed signals on this
        instance.  Need only be called once per signal name and must be done
        for each signal that may be used via :py:meth:`add_signal_receiver`

        :param str name: Signal name to register e.g.,
            :py:attr:`SIGNAL_PROPERTY_CHANGED`
        :return:
        """
        self._signal_names.append(name)

    def add_signal_receiver(self, callback_fn, signal, user_arg, addr=None):
        """
        Add a signal receiver callback with user argument

        See also :py:meth:`remove_signal_receiver`,
        :py:exc:`.BTSignalNameNotRecognisedException`

        :param func callback_fn: User-defined callback function to call when
            signal triggers
        :param str signal: Signal name e.g.,
            :py:attr:`.BTInterface.SIGNAL_PROPERTY_CHANGED`
        :param user_arg: User-defined callback argument to be passed with
            callback function
        :return:
        :raises BTSignalNameNotRecognisedException: if the signal name is
            not registered
        """
        if (signal in self._signal_names):
            addr = self._dbus_addr if addr is None else addr
            s = Signal(signal, callback_fn, user_arg)
            self._signals[signal] = s
            self._bus.add_signal_receiver(s.signal_handler,
                                          signal,
                                          dbus_interface=addr,
                                          path=self._path)
        else:
            raise BTSignalNameNotRecognisedException

    def remove_signal_receiver(self, signal):
        """
        Remove an installed signal receiver by signal name.

        See also :py:meth:`add_signal_receiver`
        :py:exc:`exceptions.BTSignalNameNotRecognisedException`

        :param str signal: Signal name to uninstall
            e.g., :py:attr:`SIGNAL_PROPERTY_CHANGED`
        :return:
        :raises BTSignalNameNotRecognisedException: if the signal name is
            not registered
        """
        if (signal in self._signal_names):
            s = self._signals.get(signal)
            if (s):
                self._bus.remove_signal_receiver(s.signal_handler,
                                                 signal,
                                                 dbus_interface=self._dbus_addr)  # noqa
                self._signals.pop(signal)
        else:
            raise BTSignalNameNotRecognisedException

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
        :raises KeyError: if the property key is not found in the
            object's dictionary
        :raises dbus.Exception: org.bluez.Error.DoesNotExist
        :raises dbus.Exception: org.bluez.Error.InvalidArguments
        """
        raise NotImplementedError("Must override get_property")

    def set_property(self, name, value):
        """
        Helper to set a property value by name, translating to correct
        dbus type

        See also :py:meth:`get_property`

        :param str name: The property name in the object's dictionary
            whose value shall be set.
        :param value: Properties new value to be assigned.
        :return:
        :raises KeyError: if the property key is not found in the
            object's dictionary
        :raises dbus.Exception: org.bluez.Error.DoesNotExist
        :raises dbus.Exception: org.bluez.Error.InvalidArguments
        """
        return

    def __getattr__(self, name):
        """Override default getattr behaviours to allow DBus object
        properties to be exposed in the class for getting"""
        if name in self.__dict__:
            return self.__dict__[name]
        elif '_properties' in self.__dict__ and name in self._properties:
            return self.get_property(name)

    def __setattr__(self, name, value):
        """Override default setattr behaviours to allow DBus object
        properties to be exposed in the class for setting"""
        if '_properties' in self.__dict__ and name not in self.__dict__:
            self.set_property(name, value)
        else:
            self.__dict__[name] = value

    def __repr__(self):
        """Stringify the Dbus interface properties as raw"""
        return self.__str__()

    def __str__(self):
        """Stringify the Dbus interface properties in a nice format"""
        return pprint.pformat(self.get_property())