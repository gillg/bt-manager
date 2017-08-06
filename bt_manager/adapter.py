from __future__ import unicode_literals

import dbus
from dbus import DBusException
from interface import BTInterface, translate_to_dbus_type


class BTAdapter(BTInterface):
    """
    Wrapper around dbus to encapsulate org.bluez.adapter interface.

    :param str adapter_path: Object path to bluetooth adapter.
        If not given, can use adapter_id instead.
    :param str adapter_id: Adapter's MAC address to look-up to find
        path e.g., '11:22:33:44:55:66'

    :Properties:

    * **Address(str) [readonly]**: The Bluetooth device address
        of the adapter.
    * **Name(str) [readonly]**: The Bluetooth system name
        (pretty hostname).
        This property is either a static system default
        or controlled by an external daemon providing
        access to the pretty hostname configuration.
    * **Alias(str) [readwrite]**: The Bluetooth friendly name.
        This value can be changed.
        In case no alias is set, it will return the system
        provided name. Setting an empty string as alias will
        convert it back to the system provided name.
        When resetting the alias with an empty string, the
        property will default back to system name.
        On a well configured system, this property never
        needs to be changed since it defaults to the system
        name and provides the pretty hostname. Only if the
        local name needs to be different from the pretty
        hostname, this property should be used as last
        resort.
    * **Class(uint32) [readonly]**: The Bluetooth class of
        device.
        This property represents the value that is either
        automatically configured by DMI/ACPI information
        or provided as static configuration.
    * **Powered(boolean) [readwrite]**: Switch an adapter on or
        off. This will also set the appropriate connectable
        state of the controller.
        The value of this property is not persistent. After
        restart or unplugging of the adapter it will reset
        back to false.
    * **Discoverable(boolean) [readwrite]**: Switch an adapter
        to discoverable or non-discoverable to either make it
        visible or hide it. This is a global setting and should
        only be used by the settings application.
        If DiscoverableTimeout is set to a non-zero
        value then the system will set this value back to
        false after the timer expired.
        In case the adapter is switched off, setting this
        value will fail.
        When changing the Powered property the new state of
        this property will be updated via a
        :py:attr:`.BTInterface.SIGNAL_PROPERTY_CHANGED`
        signal.
        For any new adapter this settings defaults to false.
    * **Pairable(boolean) [readwrite]**: Switch an adapter to
        pairable or non-pairable. This is a global setting and
        should only be used by the settings application.
    * **PairableTimeout(uint32) [readwrite]**:
        The pairable timeout in seconds. A value of zero
        means that the timeout is disabled and it will stay in
        pairable mode forever.
        The default value for pairable timeout should be
        disabled (value 0).
    * **DiscoverableTimeout(uint32) [readwrite]**:
        The discoverable timeout in seconds. A value of zero
        means that the timeout is disabled and it will stay in
        discoverable/limited mode forever.
        The default value for the discoverable timeout should
        be 180 seconds (3 minutes).
    * **Discovering(boolean) [readonly]**:
        Indicates that a device discovery procedure is active.
    * **UUIDs(array{str}) [readonly]**:
        List of 128-bit UUIDs that represents the available
        local services.
    * **Modalias(str) [readonly, optional]**:
        Local Device ID information in modalias format
        used by the kernel and udev.

    See also: :py:class:`.BTManager`
    """

    SIGNAL_DEVICE_FOUND = 'DeviceFound'
    """
    :signal DeviceFound(signal_name, user_arg, device_path): Signal
        notifying when a new device has been found
    """
    SIGNAL_DEVICE_REMOVED = 'DeviceRemoved'
    """
    :signal DeviceRemoved(signal_name, user_arg, device_path):
        Signal notifying when a device has been removed
    """
    SIGNAL_DEVICE_CREATED = 'DeviceCreated'
    """
    :signal DeviceCreated(signal_name, user_arg, device_path):
        Signal notifying when a new device is created
    """
    SIGNAL_DEVICE_DISAPPEARED = 'DeviceDisappeared'
    """
    :signal DeviceDisappeared(signal_name, user_arg, device_path):
        Signal notifying when a device is now out-of-range
    """

    ADAPTER_INTERFACE_BLUEZ4 = 'org.bluez.Adapter'
    ADAPTER_INTERFACE_BLUEZ5 = 'org.bluez.Adapter1'
    DEVICE_INTERFACE_BLUEZ5 = 'org.bluez.Device1'
    AGENT_INTERFACE = 'org.bluez.AgentManager1'

    def __init__(self, adapter_path):
        self.adapter_path = adapter_path
        if (self.get_version() <= self.BLUEZ4_VERSION):
            BTInterface.__init__(self, adapter_path, BTAdapter.ADAPTER_INTERFACE_BLUEZ4)
            self._properties = self._interface.GetProperties().keys()
            self._register_signal_name(BTAdapter.SIGNAL_PROPERTY_CHANGED)
            self._register_signal_name(BTAdapter.SIGNAL_DEVICE_FOUND)
            self._register_signal_name(BTAdapter.SIGNAL_DEVICE_REMOVED)
            self._register_signal_name(BTAdapter.SIGNAL_DEVICE_CREATED)
            self._register_signal_name(BTAdapter.SIGNAL_DEVICE_DISAPPEARED)

        else:
            BTInterface.__init__(self, adapter_path, self.ADAPTER_INTERFACE_BLUEZ5)
            self._init_agent()
            self._init_object_manager()
            self._init_properties()

    def _init_properties(self):
        self._props_interface = dbus.Interface(self._object, self.DBUS_PROPERTIES)
        self._properties = list(self._props_interface.GetAll(self.ADAPTER_INTERFACE_BLUEZ5).keys())
        self._register_signal_name(self.SIGNAL_PROPERTIES_CHANGED)

    def _init_agent(self):
        bluez_path = self._bus.get_object(self.BLUEZ_DBUS_OBJECT, '/org/bluez')
        self._agent_interface = dbus.Interface(bluez_path, self.AGENT_INTERFACE)

    def _init_object_manager(self):
        root_path = self._bus.get_object(self.BLUEZ_DBUS_OBJECT, '/')
        self._ojects_interface = dbus.Interface(root_path, self.DBUS_OBJ_MANAGER)
        self._register_signal_name(self.SIGNAL_INTERFACES_ADDED)
        self._register_signal_name(self.SIGNAL_INTERFACES_REMOVED)

    def get_path(self):
        return self.adapter_path

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
        #BlueZ 4
        if (self.get_version() <= self.BLUEZ4_VERSION):
            if (name):
                return self._interface.GetProperties()[name]
            else:
                return self._interface.GetProperties()

        #BlueZ 5
        else:
            if (name):
                return self._props_interface.Get(self.ADAPTER_INTERFACE_BLUEZ5, name)
            else:
                return self._props_interface.GetAll(self.ADAPTER_INTERFACE_BLUEZ5)

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
        #BlueZ 4
        if (self.get_version() <= self.BLUEZ4_VERSION):
            typeof = type(self.get_property(name))
            self._interface.SetProperty(name,
                        translate_to_dbus_type(typeof, value))

        #BlueZ 5
        else:
            typeof = type(self.get_property(name))
            self._props_interface.Set(BTAdapter.ADAPTER_INTERFACE_BLUEZ5, name,
                        translate_to_dbus_type(typeof, value))

    def start_discovery(self):
        """
        This method starts the device discovery session. This
        includes an inquiry procedure and remote device name
        resolving. Use :py:meth:`stop_discovery` to release the sessions
        acquired.

        This process will start emitting :py:attr:`SIGNAL_DEVICE_FOUND`
        and :py:attr:`.SIGNAL_PROPERTY_CHANGED` 'discovering' signals.

        :return:
        :raises dbus.Exception: org.bluez.Error.NotReady
        :raises dbus.Exception: org.bluez.Error.Failed
        """
        return self._interface.StartDiscovery()

    def stop_discovery(self):
        """
        This method will cancel any previous :py:meth:`start_discovery`
        transaction.

        Note that a discovery procedure is shared between all
        discovery sessions thus calling py:meth:`stop_discovery` will
        only release a single session.

        :return:
        :raises dbus.Exception: org.bluez.Error.NotReady
        :raises dbus.Exception: org.bluez.Error.Failed
        :raises dbus.Exception: org.bluez.Error.NotAuthorized
        """
        return self._interface.StopDiscovery()

    def find_device(self, dev_id, property='Address'):
        """
        Returns the object path of device for given address.
        The device object needs to be first created via
        :py:meth:`create_device` or
        :py:meth:`create_paired_device`

        :param str dev_id: Device MAC address to look-up e.g.,
            '11:22:33:44:55:66'
        :return: Device object path e.g.,
            '/org/bluez/985/hci0/dev_00_11_67_D2_AB_EE'
        :rtype: str
        :raises dbus.Exception: org.bluez.Error.DoesNotExist
        :raises dbus.Exception: org.bluez.Error.InvalidArguments
        """
        #BlueZ 4
        if (self.get_version() <= self.BLUEZ4_VERSION):
            return self._interface.FindDevice(dev_id)
        #BlueZ 5
        else:
            for (key, object) in self._ojects_interface.GetManagedObjects().items():
                if self.DEVICE_INTERFACE_BLUEZ5 in object:
                    if object[self.DEVICE_INTERFACE_BLUEZ5][property] == dev_id:
                        return key
            raise DBusException('org.bluez.Error.DoesNotExist')

    def list_devices(self):
        """
        Returns list of device object paths.

        :return: List of device object paths
        :rtype: list
        :raises dbus.Exception: org.bluez.Error.InvalidArguments
        :raises dbus.Exception: org.bluez.Error.Failed
        :raises dbus.Exception: org.bluez.Error.OutOfMemory
        """
        #BlueZ 4
        if (self.get_version() <= self.BLUEZ4_VERSION):
            return self._interface.ListDevices()
        #BlueZ 5
        else:
            objects = self._ojects_interface.GetManagedObjects().items()
            devices = []
            for (key, object) in objects:
                if self.DEVICE_INTERFACE_BLUEZ5 in object:
                    devices.append(key)
            return devices

    def create_paired_device(self, dev_id, agent_path,
                             capability, cb_notify_device, cb_notify_error):
        """
        Creates a new object path for a remote device. This
        method will connect to the remote device and retrieve
        all SDP records and then initiate the pairing.

        If a previously :py:meth:`create_device` was used
        successfully, this method will only initiate the pairing.

        Compared to :py:meth:`create_device` this method will
        fail if the pairing already exists, but not if the object
        path already has been created. This allows applications
        to use :py:meth:`create_device` first and then, if needed,
        use :py:meth:`create_paired_device` to initiate pairing.

        The agent object path is assumed to reside within the
        process (D-Bus connection instance) that calls this
        method. No separate registration procedure is needed
        for it and it gets automatically released once the
        pairing operation is complete.

        :param str dev_id: New device MAC address create
            e.g., '11:22:33:44:55:66'
        :param str agent_path: Path used when creating the
            bluetooth agent e.g., '/test/agent'
        :param str capability: Pairing agent capability
            e.g., 'DisplayYesNo', etc
        :param func cb_notify_device: Callback on success.  The
            callback is called with the new device's object
            path as an argument.
        :param func cb_notify_error: Callback on error.  The
            callback is called with the error reason.
        :return:
        :raises dbus.Exception: org.bluez.Error.InvalidArguments
        :raises dbus.Exception: org.bluez.Error.Failed
        """
        #BlueZ 4
        if (self.get_version() <= self.BLUEZ4_VERSION):
            return self._interface.CreatePairedDevice(dev_id,
                                                  agent_path,
                                                  capability,
                                                  reply_handler=cb_notify_device,  # noqa
                                                  error_handler=cb_notify_error)   # noqa
        #BlueZ 5  TODO !?
        else:
            pass

    def remove_device(self, dev_path):
        """
        This removes the remote device object at the given
        path. It will remove also the pairing information.

        :param str dev_path: Device object path to remove
            e.g., '/org/bluez/985/hci0/dev_00_11_67_D2_AB_EE'
        :return:
        :raises dbus.Exception: org.bluez.Error.InvalidArguments
        :raises dbus.Exception: org.bluez.Error.Failed
        """
        return self._interface.RemoveDevice(dev_path)

    def register_agent(self, path, capability):
        """
        This registers the adapter wide agent.

        The object path defines the path the of the agent
        that will be called when user input is needed.

        If an application disconnects from the bus all
        of its registered agents will be removed.

        :param str path: Freely definable path for agent e.g., '/test/agent'
        :param str capability: The capability parameter can have the values
            "DisplayOnly", "DisplayYesNo", "KeyboardOnly" and "NoInputNoOutput"
            which reflects the input and output capabilities of the agent.
            If an empty string is used it will fallback to "DisplayYesNo".
        :return:
        :raises dbus.Exception: org.bluez.Error.InvalidArguments
        :raises dbus.Exception: org.bluez.Error.AlreadyExists
        """
        #BlueZ 4
        if (self.get_version() <= self.BLUEZ4_VERSION):
            return self._interface.RegisterAgent(path, capability)
        #BlueZ 5
        else:
            return self._agent_interface.RegisterAgent(path, capability)

    def unregister_agent(self, path):
        """
        This unregisters the agent that has been previously
        registered. The object path parameter must match the
        same value that has been used on registration.

        :param str path: Previously defined path for agent
            e.g., '/test/agent'
        :return:
        :raises dbus.Exception: org.bluez.Error.DoesNotExist
        """
        #BlueZ 4
        if (self.get_version() <= self.BLUEZ4_VERSION):
            return self._interface.UnregisterAgent(path)
        #BlueZ 5
        else:
            return self._agent_interface.UnregisterAgent(path)
