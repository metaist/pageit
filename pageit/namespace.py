#!/usr/bin/python
# coding: utf-8

'''Flexible objects and dictionaries.

The Namespace object provides simple ways to bunch together key/values while
providing both dot- and array-notation setters and getters.
'''

# Native
import collections


def getattrs(obj, *names):
    '''Returns multiple attributes of an object.

    Args:
        obj (object): object
        *names: variable list names of attributes

    Returns:
        tuple: attribute values

    Example:
        >>> x = Namespace(a=1, b=2, c=3)
        >>> a, c, d = getattrs(x, 'a', 'c', 'd')
        >>> a == x.a and c == x.c and d is None
        True
    '''
    return (getattr(obj, name) for name in names)


def extend(*items):
    '''Extend a dictionary with a set of dictionaries.

    Args:
        *items: dictionary to extend

    Returns:
        dict: all of the dictionaries extended

    Examples:
        >>> extend({}, {'a': 1}, {'a': None}) == {'a': 1}
        True
        >>> extend({'a': 1}, {'b': 2}, {'a': 4}) == {'a': 4, 'b': 2}
        True
        >>> extend({'a': {'b': 3}}, {'a': {'c': 2}}) == {'a': {'b': 3, 'c': 2}}
        True
        >>> extend({'a': {'b': 3}}, {'a': {'b': 2}}) == {'a': {'b': 2}}
        True
    '''
    assert len(items) >= 2, 'Need 2 or more items to merge.'
    result = items[0]
    for other in items:
        for key, val in other.items():
            if val is None:  # ignore None values
                continue
            elif (key in result and
                  isinstance(result[key], dict) and
                  isinstance(val, dict)):
                result[key] = extend(result[key], val)
            else:
                result[key] = val
    return result


class Namespace(collections.MutableMapping):
    '''A simple namespace.

    Access attributes of this object with dot or array notation.

    Args:
        *args: dictionaries or objects to merge
        **kwds: converted into a dictionary

    Note:
        Variable arguments take precedence over keyword arguments.

    Examples:
        >>> ns = Namespace(a=1, b=2)
        >>> (ns.a == 1 and ns['b'] == 2)
        True

        >>> Namespace(a=1, b=2) == Namespace({'a': 1, 'b': 2})
        True

        >>> Namespace(None, a=1) == Namespace(a=1)
        True

        >>> x = None
        >>> try:
        ...     x = Namespace([1,2,3])
        ... except AssertionError:
        ...     pass
        >>> x is None
        True
    '''

    def __init__(self, *args, **kwds):
        '''Construct a namespace from parameters.'''
        args = list(args)
        args.append(kwds)
        for arg in args:
            if arg is None:
                pass  # nothing to do
            elif isinstance(arg, dict):
                self.__dict__ = extend(self.__dict__, arg)
            elif isinstance(arg, object) and hasattr(arg, '__dict__'):
                self.__dict__ = extend(self.__dict__, arg.__dict__)
            else:
                assert False, '[{0}] cannot be merged'.format(arg)

    def __contains__(self, name):
        '''Returns True if name is in the Namespace.

        Args:
            name(str): name of the attribute

        Returns:
            bool: True if the name is in the namespace; False otherwise

        Examples:
            >>> 'a' in Namespace(a=1)
            True
            >>> 'b' not in Namespace(a=1)
            True
        '''
        return name in self.__dict__

    def __delattr__(self, name):
        '''Deletes an attribute (dot notation).

        Args:
            name (str): name of the attribute to delete

        Example:
            >>> ns = Namespace(a=1)
            >>> del ns.a
            >>> 'a' not in ns
            True
        '''
        del self.__dict__[name]

    def __delitem__(self, name):
        '''Deletes an attribute (array notation).

        Args:
            name (str): name of the attribute to delete

        Example:
            >>> ns = Namespace(a=1)
            >>> del ns['a']
            >>> 'a' not in ns
            True
        '''
        del self.__dict__[name]

    def __getattr__(self, name):
        '''Returns the attribute value (dot notation).

        Note:
            Since this method is only called when an attribute does not exist,
            by definition this method will always return ``None``.

        Args:
            name (str): attribute name (ignored)

        Returns:
            None: this method is only called when an attribute does not exist

        Example:
            >>> ns = Namespace(a=1)
            >>> ns.b is None
            True

            >>> ns.b = 2
            >>> ns.b == 2
            True
        '''
        return None

    def __getitem__(self, name):
        '''Returns the attribute value (array notation).

        Args:
            name (str): attribute name

        Returns:
            value of the attribute or None if it does not exist

        Example:
            >>> ns = Namespace(a=1)
            >>> ns['a'] == 1
            True
            >>> ns['b'] is None
            True
        '''
        return self.__dict__.get(name)

    def __setitem__(self, name, val):
        '''Sets the value of an attribute.

        Args:
            name (str): attribute name
            val: attribute value

        Example:
            >>> ns = Namespace(a=1)
            >>> ns['b'] = 2
            >>> ns.b == 2
            True
        '''
        self.__dict__[name] = val

    def __len__(self):
        '''Returns the number of attributes set.

        Example:
            >>> len(Namespace(a=1, b=2)) == 2
            True
        '''
        return len(self.__dict__)

    def __iter__(self):
        '''Returns an iterator.

        Example:
            >>> [attr for attr in Namespace(a=1)] == ['a']
            True
        '''
        return iter(self.__dict__)

    def __repr__(self):
        '''Returns a string representation of the object.

        Example:
            >>> repr(Namespace(a=1))
            'Namespace(a=1)'
        '''
        result = ', '.join([k + '=' + str(self[k]) for k in self])
        return 'Namespace(' + result + ')'

    def __eq__(self, other):
        '''Returns True if the items are equal.

        Args:
            other (Namespace): object of comparison

        Example:
            >>> Namespace(a=1) == Namespace({'a': 1})
            True
        '''
        return isinstance(other, Namespace) and self.__dict__ == other.__dict__

    def __add__(self, other):
        '''Add another object to this object.

        Args:
            other (Namespace, dict, object): object to add

        Example:
            >>> Namespace(a=1) + {'b': 2} == Namespace(a=1, b=2)
            True
        '''
        return Namespace(self, other)

    def __radd__(self, other):
        '''Add this object to another object.

        Args:
            other (dict, object): object to which to add

        Example:
            >>> {'a': 1} + Namespace(b=2) == Namespace(a=1, b=2)
            True
        '''
        return Namespace(other, self)
