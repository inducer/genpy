from importlib import metadata
from urllib.request import urlopen


_conf_url = "https://tiker.net/sphinxconfig-v0.py"
with urlopen(_conf_url) as _inf:
    exec(compile(_inf.read(), _conf_url, "exec"), globals())

copyright = "2011, Andreas Kloeckner"
release = metadata.version("genpy")
version = ".".join(release.split(".")[:2])

intersphinx_mapping = {
        "python": ("https://docs.python.org/3/", None),
        "numpy": ("https://numpy.org/doc/stable/", None),
        "pymbolic": ("https://documen.tician.de/pymbolic/", None),
        }
