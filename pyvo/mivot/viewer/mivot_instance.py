# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MivotInstance is the root of the Python generated classes.
Instances of MivotInstance are built from a dictionary issued
from the XML view of the mapped model.
This dictionary is used to extend the object with all components
(classes, attributes, collections) necessary to reproduce the structure
of the mapped model.
Instances of this class are built by `pyvo.mivot.viewer.mivot_viewer`.
Although attribute values can be changed by users, this class is first
meant to provide a convenient access the mapped VOTable data
"""
from astropy import time
from pyvo.mivot.utils.vocabulary import unit_mapping
from pyvo.utils.prototype import prototype_feature
from pyvo.mivot.utils.mivot_utils import MivotUtils
from pyvo.mivot.utils.dict_utils import DictUtils

# list of model leaf parameters that must be hidden for the final user
hk_parameters = ["astropy_unit", "ref"]


@prototype_feature('MIVOT')
class MivotInstance:
    """
    MivotInstance holds the dictionary (__dict__) similar with the mapped model structure
    where the references have been resolved.
    The dictionary keeps the hierarchy of the XML :
    "key" : {not a leaf} means key is the dmtype of an INSTANCE
    "key" : {leaf}       means key is the dmrole of an ATTRIBUTE
    "key" : "value"      means key is an element of ATTRIBUTE
    "key" : []           means key is the dmtype of a COLLECTION
    """
    def __init__(self, **instance_dict):
        """
        Constructor of the MIVOT class.

        Parameters
        ----------
        kwargs (dict): Dictionary of the XML object.
        """
        self._create_class(**instance_dict)

    def __repr__(self):
        """
        return  a human readable (json) representation of object
        """
        return DictUtils._get_pretty_json(self.dict)

    @property
    def hk_dict(self):
        """
        return a human readable (dict) representation of object with a few
        housekeeping data such as column references. This might be used
        to apply the mapping out of the MivotViewer context
        """
        return self._get_class_dict(self)

    @property
    def dict(self):
        """
        return a human readable (dict) representation of object
        """
        return self._get_class_dict(self, slim=True)

    def _create_class(self, **kwargs):
        """
        Recursively initialize the MIVOT class with the dictionary of the XML object got in MivotViewer.
        For the unit of the ATTRIBUTE, we add the Astropy unit or the Astropy time equivalence by comparing
        the value of the unit with values in time.TIME_FORMATS.keys() which is the list of time formats.
        We do the same with the unit_mapping dictionary, which is the list of Astropy units.

        Parameters
        ----------
        kwargs (dict): Dictionary of the XML object.
        """
        for key, value in kwargs.items():
            if isinstance(value, list):  # COLLECTION
                setattr(self, self._remove_model_name(key), [])
                for item in value:
                    getattr(self, self._remove_model_name(key)).append(MivotInstance(**item))
            elif isinstance(value, dict):  # INSTANCE
                if not self._is_leaf(**value):
                    setattr(self, self._remove_model_name(key, role_instance=True), MivotInstance(**value))
                if self._is_leaf(**value):
                    setattr(self, self._remove_model_name(key), MivotInstance(**value))
            else:  # ATTRIBUTE
                if key == 'value':  # We cast the value read in the row
                    setattr(self, self._remove_model_name(key),
                            MivotUtils.cast_type_value(value, getattr(self, 'dmtype')))
                else:
                    setattr(self, self._remove_model_name(key), self._remove_model_name(value))
                if key == 'unit':  # We convert the unit to astropy unit or to astropy time format if possible
                    # The first Vizier implementation used mas/year for the mapped pm unit: let's correct it
                    value = value.replace("year", "yr") if value else None
                    if value in unit_mapping.keys():
                        setattr(self, "astropy_unit", unit_mapping[value])
                    elif value in time.TIME_FORMATS.keys():
                        setattr(self, "astropy_unit_time", value)

    def update(self, row, ref=None):
        """
        Update the MIVOT class with the new data row.
        For each leaf of the MIVOT class, we update the value with the new data row.

        Parameters
        ----------
        row (astropy.table.row.Row): The new data row.
        ref (str, optional):The reference of the data row, default is None.
        """
        for key, value in vars(self).items():
            if isinstance(value, list):
                for item in value:
                    item.update(row=row)
            elif isinstance(value, MivotInstance):
                if isinstance(vars(value), dict):
                    if 'value' not in vars(value):
                        value.update(row=row)
                    if 'value' in vars(value):
                        value.update(row=row, ref=getattr(value, 'ref'))
            else:
                if key == 'value' and ref is not None and ref != 'null':
                    setattr(self, self._remove_model_name(key),
                            MivotUtils.cast_type_value(row[ref], getattr(self, 'dmtype')))

    @staticmethod
    def _remove_model_name(value, role_instance=False):
        """
        Remove the model name before each colon ":" as well as the type of the object before each point ".".
        If it is an INSTANCE of INSTANCEs, the dmrole represented as the key needs to keep his type object.
        In this case (`role_instance=True`), we just replace the point "." With an underscore "_".
        - if role_instance: a:b.c -> b_c else c

        Parameters
        ----------
        value (str): The string to process.
        role_instance (bool, optional): If True, keeps the type object for dmroles representing
                                        an INSTANCE of INSTANCEs. Default is False.
        """
        if isinstance(value, str):
            # We first find the model_name before the colon
            index_underscore = value.find(":")
            if index_underscore != -1:
                # Then we find the object type before the point
                next_index_underscore = value.rfind(".")
                if next_index_underscore != -1 and not role_instance:
                    value_after_underscore = value[next_index_underscore + 1:]
                else:
                    value_after_underscore = (value[index_underscore + 1:]
                                              .replace(':', '_').replace('.', '_'))
                return value_after_underscore
            return value  # Returns unmodified string if "_" wasn't found
        else:
            return value

    def _is_leaf(self, **kwargs):
        """
        Check if the dictionary is an ATTRIBUTE.

        Parameters
        ----------
        **kwargs (dict): The dictionary to check.
        Returns
        -------
        bool: True if the dictionary is an ATTRIBUTE, False otherwise.
        """
        if isinstance(kwargs, dict):
            for _, value in kwargs.items():
                if isinstance(value, dict):
                    return False
        return True

    def _get_class_dict(self, obj, classkey=None, slim=False):
        """
        Recursively displays a serializable dictionary.
        This function is only used for debugging purposes.

        Parameters
        ----------
        obj (dict or object): The dictionary or object to display.
        classkey (str, optional): The key to use for the object's class name
                                  in the dictionary, default is None.
        slim (bool, optional): if true, only @values and @units (if not empty) are
                               attached to model leaves.
                               @dmtype and @ref attributes are ignored
        Returns
        -------
        dict or object
            The serializable dictionary representation of the input.
        """
        if isinstance(obj, dict):
            data = {}
            for (k, v) in obj.items():
                data[k] = self._get_class_dict(v, classkey, slim=slim)
            return data
        elif hasattr(obj, "_ast"):
            return self._get_class_dict(obj._ast())
        elif hasattr(obj, "__iter__") and not isinstance(obj, str):
            return [self._get_class_dict(v, classkey, slim=slim) for v in obj]
        elif hasattr(obj, "__dict__"):
            data = dict([(key, self._get_class_dict(value, classkey, slim=slim))
                         for key, value in obj.__dict__.items()
                         if not callable(value) and not key.startswith('_')])
            # remove the house keeping parameters
            if slim is True:
                # data is atomic value (e.g. float): the type be hidden
                if "ref" in data or "value" in data:
                    data.pop("dmtype", None)
                # remove unit when not set
                if "unit" in data and not data["unit"]:
                    data.pop("unit", None)
                for hk_parameter in hk_parameters:
                    data.pop(hk_parameter, None)

            if classkey is not None and hasattr(obj, "__class__"):
                data[classkey] = obj.__class__.__name__
            return data
        else:
            return obj
