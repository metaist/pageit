#!/usr/bin/python
# coding: utf-8

'''Flexible objects and dictionaries.

:py:class:`~pageit.namespace.Namespace` objects provides simple ways to bunch
together key/values while providing both dot- and array-notation setters and
getters.

:py:class:`~pageit.namespace.DeepNamespace` act in a similar manner, except
that they apply theselves recursively.
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
        *items: dictionaries to extend; the first argument will be modified

    Returns:
        dict: the first dictionary extended with values from the other
        dictionaries

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

        >>> class Foo(object):
        ...     pass
        >>> x = Foo()
        >>> x.a = 1
        >>> Namespace(x) == Namespace(a=1)
        True

        >>> x = None
        >>> try:
        ...     x = Namespace([1,2,3])
        ... except AssertionError:
        ...     pass
        >>> x is None
        True
    '''
    # pylint: disable=too-few-public-methods

    def __init__(self, *args, **kwds):
        '''Construct a namespace from parameters.'''
        args = list(args)
        args.append(kwds)
        for arg in args:
            if arg is None:
                continue  # nothing to do
            elif isinstance(arg, Namespace):
                self.__dict__.update(arg.__dict__)
                continue  # avoid recursion
            elif isinstance(arg, dict):
                pass  # arg is already a dict
            elif isinstance(arg, object) and hasattr(arg, '__dict__'):
                arg = arg.__dict__  # extract the relevant dict
            else:
                assert False, '[{0}] cannot be merged'.format(arg)

            extend(self, arg)

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

    def __setattr__(self, name, val):
        '''Sets the value of an attribute (dot notation).

        Args:
            name (str): attribute name
            val: attribute value

        Example:
            >>> ns = Namespace(a=1)
            >>> ns.b = 2
            >>> ns.b == 2
            True

        .. versionadded:: 0.2.2
        '''
        if '__dict__' != name:  # avoid infinite loop
            self[name] = val

    def __setitem__(self, name, val):
        '''Sets the value of an attribute (array notation).

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

    def __hash__(self):
        '''Returns the hash of this object.

        >>> hash(Namespace(a=1)) == hash('Namespace(a=1)')
        True
        '''
        return hash(repr(self))

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

        .. versionchanged:: 0.2.2
           Use the name of the class instead of a hard-coded string.
        '''
        result = ', '.join([k + '=' + str(self[k]) for k in self])
        return self.__class__.__name__ + '(' + result + ')'

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


class DeepNamespace(Namespace):
    '''A recursive namespace.

    Similar to a normal :py:class:`~pageit.namespace.Namespace`, except that
    setting an attribute to a dictionary, converts it into a
    :py:class:`~pageit.namespace.DeepNamespace`.

    Args:
        *args: dictionaries or objects to merge
        **kwds: converted into a dictionary

    Note:
        Variable arguments take precedence over keyword arguments.

    Examples:
        >>> ns = DeepNamespace({"a": {"b": 1}})
        >>> ns.a.b == 1
        True

        >>> ns = DeepNamespace(x=DeepNamespace(y=1))
        >>> ns.x.y == 1
        True

    .. versionadded:: 0.2.2
    '''
    # pylint: disable=too-few-public-methods

    def __init__(self, *args, **kwds):
        '''Construct a namespace from parameters.

        Merely calls the superclass constructor.
        '''
        super(DeepNamespace, self).__init__(*args, **kwds)

    def __getattr__(self, name):
        '''Returns the attribute value (dot notation).

        This lets you safely reference attributes that don't exist in a
        chainable way. You can test for existince using :py:func:`len`.

        Note:
            Since this method is only called when an attribute does not exist,
            by definition this method will always return an empty
            :py:class:`~pageit.namespace.DeepNamespace`.

            However, it also has the side effect of **creating** that attribute
            in the namespace so that you can assign arbitrary values.

        Args:
            name (str): attribute name (ignored)

        Returns:
            DeepNamespace: this method is only called when an attribute does
            not exist

        Example:
            >>> ns = DeepNamespace(a=1)
            >>> ns.b.c is not None
            True
            >>> len(ns.b.c) == 0
            True

            >>> ns.b = 2
            >>> ns.b == 2
            True
        '''
        self.__dict__[name] = DeepNamespace()
        return self.__dict__[name]

    def __setitem__(self, name, val):
        '''Sets the value of an attribute (array notation).

        If ``val`` is a dictionary or an object with attributes, it will
        be recursively converted into a
        :py:class:`~pageit.namespace.DeepNamespace`.

        Args:
            name (str): attribute name
            val: attribute value

        Example:
            >>> ns = DeepNamespace()
            >>> ns['a'] = {"b": {"c": 2}}
            >>> ns.a.b.c == 2
            True

            >>> ns.x.y.z = 'Works'
            >>> ns.x.y.z == 'Works'
            True

            >>> ns.q = Namespace(a=1)
            >>> isinstance(ns.q, DeepNamespace)
            True
            >>> ns.q.a == 1
            True
        '''
        if isinstance(val, DeepNamespace):
            pass  # already a DeepNamespace
        elif isinstance(val, dict):
            val = DeepNamespace(val)
        elif isinstance(val, object) and hasattr(val, '__dict__'):
            val = DeepNamespace(val.__dict__)
        self.__dict__[name] = val
