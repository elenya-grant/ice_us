from typing import Any

import attrs
import numpy as np
from attrs import Attribute, define


def contains(items):
    """Validates that an item is part of a given list."""

    def validator(instance, attribute, value):
        if value not in items:
            raise ValueError(f"Item {value} not found in list for {attribute}: {items}")

    return validator


def attr_serializer(inst: type, field: Attribute, value: Any):
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def attr_filter(inst: Attribute, value: Any) -> bool:
    if inst.init is False:
        return False
    if value is None:
        return False
    if isinstance(value, np.ndarray):
        if value.size == 0:
            return False
    return True


@define(kw_only=True)
class BaseConfig:
    """
    A Mixin class to allow for kwargs overloading when a data class doesn't
    have a specific parameter defined. This allows passing of larger dictionaries
    to a data class without throwing an error.
    """

    @classmethod
    def from_dict(cls, data: dict):
        """Maps a data dictionary to an `attr`-defined class.

        TODO: Add an error to ensure that either none or all the parameters are passed in

        Args:
            data : dict
                The data dictionary to be mapped.
        Returns:
            cls
                The `attr`-defined class.
        """
        # Check for any inputs that aren't part of the class definition
        class_attr_names = [a.name for a in cls.__attrs_attrs__]
        extra_args = [d for d in data if d not in class_attr_names]
        if len(extra_args):
            raise AttributeError(
                f"The initialization for {cls.__name__} was given extraneous inputs: {extra_args}"
            )

        kwargs = {
            a.name: data[a.name]
            for a in cls.__attrs_attrs__
            if a.name in data and a.init
        }

        # Map the inputs must be provided: 1) must be initialized, 2) no default value defined
        required_inputs = [
            a.name for a in cls.__attrs_attrs__ if a.init and a.default is attrs.NOTHING
        ]
        undefined = sorted(set(required_inputs) - set(kwargs))

        if undefined:
            raise AttributeError(
                f"The class defintion for {cls.__name__} is missing the following inputs: "
                f"{undefined}"
            )
        return cls(**kwargs)

    def as_dict(self) -> dict:
        """Creates a JSON and YAML friendly dictionary that can be save for future reloading.
        This dictionary will contain only `Python` types that can later be converted to their
        proper `Turbine` formats.

        Returns:
            dict: All key, value pairs required for class re-creation.
        """
        return attrs.asdict(self, filter=attr_filter, value_serializer=attr_serializer)
