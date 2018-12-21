import os
import pprint

from stackprinter.extraction import UnresolvedAttribute
from stackprinter.utils import inspect_callable

try:
    import numpy as np
except ImportError:
    np = False


def truncate(string, n):
    if n and len(string) > (n+3):
        string = "%s..." % string[:n].rstrip()
    return string


def format_value(value, indent=0, truncation=None, max_depth=3, depth=0):

    # TODO see how pprint could be used instead https://docs.python.org/3/library/pprint.html
    # (how to extend for e.g. custom array printing though?)

    if depth == max_depth:
        truncation = 16
    elif depth > max_depth:
        return '...'

    if isinstance(value, UnresolvedAttribute):
        reason = "# %s" % (value.exc_type)
        val_tpl = reason + "\n%s = %s"
        lastval_str = format_value(value.last_resolvable_value, indent=3, depth=depth+1)
        val_str = val_tpl % (value.last_resolvable_name, lastval_str)
        indent = 10

    elif isinstance(value, list):
        val_str = format_iterable(value, '[', ']', truncation, max_depth, depth)

    elif isinstance(value, tuple):
        val_str = format_iterable(value, '(', ')', truncation, max_depth, depth)

    elif isinstance(value, set):
        val_str = format_iterable(value, '{', '}', truncation, max_depth, depth)

    elif isinstance(value, dict):
        vstrs = []
        length = len(value)
        for k, v in value.items():
            kstr = truncate(repr(k), 25)
            vstr = format_value(v, indent=len(kstr)+3, truncation=truncation, depth=depth+1)
            vstrs.append("%s: %s" % (kstr, vstr))
        val_str = '{' + ',\n '.join(vstrs) + '}'

    elif np and isinstance(value, np.ndarray):
        val_str = format_array(value)

    elif callable(value):
        name, filepath, method_owner, ln = inspect_callable(value)
        filename = os.path.basename(filepath) if filepath is not None else None
        if filename is None:
            val_str = repr(value)
        elif method_owner is None:
            val_str = "<function '%s' %s:%s>" % (name, filename, ln)
        else:
            val_str = "<method '%s' of %s %s:%s>" % (name, method_owner, filename, ln)

    # maybe just try: repr(value), because try: str(value) may already be implied (doublecheck)
    elif hasattr(value, '__repr__'):
        try:
            val_str = repr(value)
        except:
            val_str = "<error calling __repr__>"
    else:
        try:
            val_str = str(value)
        except:
            val_str = "<error calling __str__>"

    truncate(val_str, truncation)

    if indent > 0:
        nl_indented = '\n' + (' ' * indent)
        val_str = val_str.replace('\n', nl_indented)

    return val_str


def format_iterable(value, prefix, postfix, truncation, max_depth, depth):
    length = len(value)
    val_str = prefix
    if depth == max_depth:
        val_str += '...'
    else:
        linebreak = False
        for i, v in enumerate(value):
            entry = format_value(v, indent=1, truncation=truncation, depth=depth+1)
            sep = ', ' if i < length - 1 else ''
            if '\n' in entry:
                val_str += "\n %s%s" % (entry, sep)
                linebreak = True
            else:
                if linebreak:
                    val_str += '\n'
                    linebreak = False
                val_str += "%s%s" % (entry, sep)

    val_str += postfix

    if len(val_str) > 200:
        dtype = value.__class__.__name__
        val_str = "%s-%s:\n%s" % (length, dtype, val_str)
    return val_str


def format_array(arr):
    if arr.ndim >= 1:
        # shape_str = repr(arr.shape)
        shape = list(arr.shape)
        if len(shape) < 2:
            shape.append('')
        shape_str = "x".join(str(d) for d in shape)
        if len(shape_str) < 10:
            prefix = "%s array(" % shape_str
            msg = prefix
        else:
            prefix = ""
            msg = "%s array(\n" % shape_str
    else:
        msg = prefix = "array("

    suffix = ')'
    msg += np.array2string(arr, max_line_width=9000, threshold=50,
                           edgeitems=2, prefix=prefix, suffix=suffix)
    msg += suffix
    return msg