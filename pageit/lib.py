#!/usr/bin/python
# coding: utf-8

'''Generic namespace.'''

import collections


def getattrs(obj, *names):
    '''Return multiple attributes of an object.

    >>> x = Namespace(a=1, b=2, c=3)
    >>> a, c = getattrs(x, 'a', 'c')
    >>> a == x.a and c == x.c
    True
    '''
    return (getattr(obj, name) for name in names)


def extend(*items):
    '''Extend a dictionary with a set of dictionaries.

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
    """A simple namespace.

    Access attributes of this object with dot or array notation.

    >>> ns = Namespace(a=1, b=2)
    >>> (1 == ns.a) and (2 == ns['b'])
    True
    >>> (ns.c is None) and (ns['c'] is None)
    True
    >>> ns['d'] = 'present'
    >>> 'd' in ns
    True
    >>> del ns['d']
    >>> 'd' not in ns
    True
    >>> ns.d = 'Foo'
    >>> ns.d == 'Foo'
    True
    >>> del ns.d
    >>> 'd' not in ns
    True
    """

    def __init__(self, *args, **kwds):
        """Construct a namespace from parameters.

        >>> Namespace(a=1, b=2) == Namespace({'a': 1, 'b': 2})
        True
        """
        args = list(args)
        args.append(kwds)
        for arg in args:
            if arg is None:
                pass  # nothing to do
            elif isinstance(arg, dict):
                self.__dict__ = extend(self.__dict__, arg)
            elif isinstance(arg, object):
                self.__dict__ = extend(self.__dict__, arg.__dict__)
            else:
                assert False, '[{0}] cannot be merged'.format(arg)

    def __contains__(self, name):
        """Returns True if name is in the Namespace.

        >>> 'a' in Namespace(a=1)
        True
        >>> 'b' not in Namespace(a=1)
        True
        """
        return name in self.__dict__

    def __delattr__(self, name):
        """Deletes an attribute."""
        del self.__dict__[name]

    def __delitem__(self, name):
        """Deletes an attribute."""
        del self.__dict__[name]

    def __getattr__(self, name):
        """Returns None since the given attribute does not exist."""
        return None

    def __getitem__(self, name):
        """Returns the value or None if name is not in the Namespace."""
        return self.__dict__.get(name)

    def __setitem__(self, name, val):
        """Sets the value of an attribute."""
        self.__dict__[name] = val

    def __len__(self):
        """Return the number of attributes set.

        >>> len(Namespace(a=1, b=2)) == 2
        True
        """
        return len(self.__dict__)

    def __iter__(self):
        """Return an iterator.

        >>> [attr for attr in Namespace(a=1)] == ['a']
        True
        """
        return iter(self.__dict__)

    def __repr__(self):
        """Return a representation of the object.

        >>> repr(Namespace(a=1))
        'Namespace(a=1)'
        """
        result = ', '.join([k + '=' + str(self[k]) for k in self])
        return 'Namespace(' + result + ')'

    def __eq__(self, other):
        """Return True if the items are equal.

        >>> Namespace(a=1) == Namespace({'a': 1})
        True
        """
        return isinstance(other, Namespace) and self.__dict__ == other.__dict__

    def __add__(self, other):
        """Add another object to this object.

        >>> Namespace(a=1) + {'b': 2} == Namespace(a=1, b=2)
        True
        """
        return Namespace(self, other)

    def __radd__(self, other):
        """Add this object to another object.

        >>> {'a': 1} + Namespace(b=2) == Namespace(a=1, b=2)
        True
        """
        return Namespace(other, self)
