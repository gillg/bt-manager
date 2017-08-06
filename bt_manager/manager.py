from __future__ import unicode_literals

from interface import BTInterface
from adapter import BTAdapter
from dbus import DBusException


class BTManager(BTInterface):
    """
    Wrapper around dbus to encapsulate the org.bluez.manager interface
    which notionally is used to manage available bluetooth adapters.

    :Properties:

    * **Adapters(list{str}) [readonly]**: List of adapter object paths.

    See also :py:class:`.BTAdapter`
    """

    SIGNAL_ADAPTER_ADDED = 'AdapterAdded'
    """
    :signal AdapterAdded(signal_name, user_arg, object_path):
        Signal notifying when an adapter is added.
    """
    SIGNAL_ADAPTER_REMOVED = 'AdapterRemoved'
    """
    :signal AdapterRemoved(signal_name, user_arg, object_path):
        Signal notifying when an adapter is removed.
        .. note: In case all adapters are removed this signal will not
        be emitted. The AdapterRemoved signal has to be used to
        detect that no default adapter is selected or available
        anymore.
    """
    SIGNAL_DEFAULT_ADAPTER_CHANGED = 'DefaultAdapterChanged'
    """
    :signal DefaultAdapterChanged(signal_name, user_arg, object_path):
        Signal notifying when the default adapter has been changed.
    """

    def __init__(self, adapter_path=None, adapter_id=None):
        if (self.get_version() <= self.BLUEZ4_VERSION):
            BTInterface.__init__(self, '/', 'org.bluez.Manager')
            self._register_signal_name(BTManager.SIGNAL_ADAPTER_ADDED)
            self._register_signal_name(BTManager.SIGNAL_ADAPTER_REMOVED)
            self._register_signal_name(BTManager.SIGNAL_DEFAULT_ADAPTER_CHANGED)
            self._properties = self._interface.GetProperties().keys()
            self._register_signal_name(BTManager.SIGNAL_PROPERTY_CHANGED)

        else:
            BTInterface.__init__(self, '/', self.DBUS_OBJ_MANAGER)
            self._register_signal_name(self.SIGNAL_INTERFACES_ADDED)
            self._register_signal_name(self.SIGNAL_INTERFACES_REMOVED)

        if (adapter_path is None):
            if (adapter_id is None):
                adapter_path = self.default_adapter()
            else:
                adapter_path = self.find_adapter(adapter_id)

        self._adapter = BTAdapter(adapter_path)

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
            adapters = {}
            adapters.Adapters = self.list_adapters()
            if (name):
                return adapters[name]
            else:
                return adapters

    def default_adapter(self):
        """
        Obtain the default BT adapter object path.

        :return: Object path of default adapter
        :rtype: str
        :raises dbus.Exception: org.bluez.Error.InvalidArguments
        :raises dbus.Exception: org.bluez.Error.NoSuchAdapter
        """
        #BlueZ 4
        if (self.get_version() <= self.BLUEZ4_VERSION):
            return self._interface.DefaultAdapter()

        #BlueZ 5
        else:
            adapters = self.list_adapters()
            if (len(adapters) == 0):
                raise DBusException('org.bluez.Error.NoSuchAdapter')
            return adapters.pop()

    def find_adapter(self, pattern):
        """
        Returns object path for the specified adapter.

        :param str pattern:  Valid patterns are "hci0" or "00:11:22:33:44:55".
        :return: Object path of adapter
        :rtype: str
        :raises dbus.Exception: org.bluez.Error.InvalidArguments
        :raises dbus.Exception: org.bluez.Error.NoSuchAdapter
        """
        #BlueZ 4
        if (self.get_version() <= self.BLUEZ4_VERSION):
            return self._interface.FindAdapter(pattern)

        #BlueZ 5
        else:
            for (key, object) in self._interface.GetManagedObjects().items():
                if BTAdapter.ADAPTER_INTERFACE_BLUEZ5 in object:
                    if pattern in key or object[BTAdapter.ADAPTER_INTERFACE_BLUEZ5]['Address'] == pattern:
                        return key
            raise DBusException('org.bluez.Error.NoSuchAdapter')

    def list_adapters(self):
        """
        Returns list of adapter object paths under /org/bluez

        :return: List of object paths or each adapter attached
        :rtype: list
        :raises dbus.Exception: org.bluez.Error.InvalidArguments
        :raises dbus.Exception: org.bluez.Error.Failed
        :raises dbus.Exception: org.bluez.Error.OutOfMemory
        """
        #BlueZ 4
        if (self.get_version() <= self.BLUEZ4_VERSION):
            return self._interface.ListAdapters()

        #BlueZ 5
        else:
            objects = self._interface.GetManagedObjects().items()
            adapters = []
            for (key, object) in objects:
                if BTAdapter.ADAPTER_INTERFACE_BLUEZ5 in object:
                    adapters.append(key)
            return adapters

    def get_adapter(self):
        return self._adapter