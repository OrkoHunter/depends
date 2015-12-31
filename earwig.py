import glob
import json
import os
import re
import requests
import shutil
import tarfile
import tempfile
import zipfile


def get_latest_version(package_name, dest="pypi"):
    """Returns the latest version of the release on pypi."""
    if dest == "pypi":
        url = "https://pypi.python.org/pypi/"
        r = requests.get(url + package_name + "/json")
        version = json.loads(r.text)["info"]["version"]
    return version


def is_outdated(package_name, version, dest="pypi"):
    """Return true if a new package has been released over pypi."""
    if dest == "pypi":
        url = "https://pypi.python.org/pypi/"
        r = requests.get(url + package_name + "/json")
        new_version = json.loads(r.text)["info"]["version"]
    return new_version > version


def execute():
    """Return data with dependecies."""
    PATH = os.getcwd()

    files_dict = dict()

    for path, dirs, files in os.walk(PATH):
        files_dict[path] = list()
        for i in files:
            if i.endswith('.py') and not i.startswith("test_") \
                    and not i in ("__init__.py", "version.py", "release.py"):
                files_dict[path].append(i)

    files_list = list()

    # Clean up the empty data
    for path, files in files_dict.items():
        if len(files) == 0:
            del files_dict[path]
        else:
            for i in files:
                if (path+i).find("/doc") != -1 or (path+i).find("/docs") \
                        != -1 or (path+i).find("/examples") != -1:
                    pass
                else:
                    files_list.append(path + "/" + i)

    modules = dict()

    for module in files_list:
        f = open(module)
        docstring = False
        for line in f.readlines():
            if line.find("\"\"\"") != -1 and line.count("\"\"\"")%2!=0:
                if docstring:
                    docstring = False
                else:
                    docstring = True
            if line.find("\'\'\'") != -1 and line.count("\'\'\'")%2!=0:
                if docstring:
                    docstring = False
                else:
                    docstring = True
            if not docstring:
                try:  # For blank lines
                    line = line.strip()
                    if line.find(" as ") != -1:
                        line = line[:line.find(" as ")].strip()
                    if line[0:7] == "import ":
                        if line.find(",") == -1:
                            lib = line.split()[1].split('.')[0]
                        else:
                            libs = re.compile('\w+').findall(line)
                        try:
                            temp = module.split("/")
                            temp = temp[:-1]
                            temp.append(lib + ".py")
                            if not os.path.exists('/'.join(temp)):
                                if lib not in ("release"):
                                    try:
                                        modules[lib] += 1
                                    except KeyError:
                                        modules[lib] = 1
                        except NameError:  # lib doesn't exist
                            for lib in libs:
                                temp = module.split("/")
                                temp = temp[:-1]
                                temp.append(lib + ".py")
                                if not os.path.exists('/'.join(temp)):
                                    if lib not in ("release"):
                                        try:
                                            modules[lib] += 1
                                        except KeyError:
                                            modules[lib] = 1
                    elif line[0:5] == "from ":
                        if line.split()[1][0] != ".":  # Ignore local imports
                            lib = line.split()[1].split('.')[0]
                            temp = module.split("/")
                            temp = temp[:-1]
                            temp.append(lib + ".py")
                            if not os.path.exists('/'.join(temp)):
                                if lib not in ("release"):
                                    try:
                                        modules[lib] += 1
                                    except KeyError:
                                        modules[lib] = 1
                except IndexError:
                    pass

    return modules


def analyze(package_name, downloaded_file, file_type):
    """Get and analyze data."""
    data = execute()
    try:
        del data[package_name]
    except:
        pass

    big_data = dict()

    # Generated using `pkgutil.iter_modules` on a fresh virtualenv
    builtins = [
        'UserDict', '_abcoll', '_weakrefset', 'abc', 'codecs', 'copy_reg',
        'distutils', 'encodings', 'fnmatch', 'genericpath', 'linecache',
        'locale', 'ntpath', 'os', 'posixpath', 're', 'site', 'sre', 'mmap',
        'sre_compile', 'sre_constants', 'sre_parse', 'stat', 'types', 'dbm',
        'warnings', '_bsddb', '_codecs_cn', '_codecs_hk', '_codecs_iso2022',
        '_codecs_jp', '_codecs_kr', '_codecs_tw', '_ctypes', '_curses', 'bdb',
        '_ctypes_test', '_curses_panel', '_elementtree', '_hashlib', '_csv',
        '_hotshot', '_json', '_lsprof', '_multibytecodec', '_multiprocessing',
        '_sqlite3', '_ssl', '_testcapi', '_tkinter', 'audioop', 'crypt',
        'datetime', 'fpectl', 'future_builtins', 'gdbm', 'linuxaudiodev',
        'ossaudiodev', 'parser', 'pyexpat', 'readline', 'resource', 'termios',
        'BaseHTTPServer', 'Bastion', 'CGIHTTPServer', 'ConfigParser', 'Cookie',
        'DocXMLRPCServer', 'HTMLParser', 'MimeWriter', 'Queue', 'bz2', 'nis',
        'SimpleHTTPServer', 'SimpleXMLRPCServer', 'SocketServer', 'StringIO',
        'UserList', 'UserString', '_LWPCookieJar', '_MozillaCookieJar', 'ast',
        '__future__', '_osx_support', '_pyio', '_strptime', '_sysconfigdata',
        '_threading_local', 'aifc', 'antigravity', 'anydbm', 'argparse',
        'asynchat', 'asyncore', 'atexit', 'audiodev', 'base64', 'binhex',
        'bisect', 'bsddb', 'cProfile', 'calendar', 'cgi', 'cgitb', 'chunk',
        'cmd', 'code', 'codeop', 'collections', 'colorsys', 'commands',
        'compileall', 'compiler', 'contextlib', 'cookielib', 'copy', 'csv',
        'ctypes', 'curses', 'dbhash', 'decimal', 'difflib', 'dircache', 'dis',
        'doctest', 'dumbdbm', 'dummy_thread', 'dummy_threading', 'email',
        'filecmp', 'fileinput', 'formatter', 'fpformat', 'fractions',
        'functools', 'getopt', 'getpass', 'gettext', 'glob', 'gzip',
        'heapq', 'hmac', 'hotshot', 'htmlentitydefs', 'htmllib', 'httplib',
        'idlelib', 'ihooks', 'imaplib', 'imghdr', 'importlib', 'imputil',
        'inspect', 'io', 'json', 'keyword', 'lib2to3', 'logging', 'macpath',
        'macurl2path', 'mailbox', 'mailcap', 'markupbase', 'md5', 'mhlib',
        'mimetools', 'mimetypes', 'mimify', 'modulefinder', 'multifile',
        'multiprocessing', 'mutex', 'netrc', 'new', 'nntplib', 'nturl2path',
        'numbers', 'opcode', 'optparse', 'os2emxpath', 'pdb', 'pickle',
        'pickletools', 'pipes', 'pkgutil', 'platform', 'plistlib', 'popen2',
        'poplib', 'posixfile', 'pprint', 'profile', 'pstats', 'pty', 'ftplib',
        'py_compile', 'pyclbr', 'pydoc', 'pydoc_data', 'quopri', 'random',
        'repr', 'rexec', 'rfc822', 'rlcompleter', 'robotparser', 'runpy',
        'sched', 'sets', 'sgmllib', 'sha', 'shelve', 'shlex', 'shutil',
        'sitecustomize', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'sqlite3',
        'ssl', 'statvfs', 'string', 'stringold', 'stringprep', 'struct',
        'subprocess', 'sunau', 'sunaudio', 'symbol', 'symtable', 'sysconfig',
        'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'test', 'textwrap',
        'this', 'threading', 'timeit', 'toaiff', 'token', 'tokenize', 'trace',
        'traceback', 'tty', 'unittest', 'urllib', 'urllib2', 'urlparse',
        'user', 'uu', 'uuid', 'wave', 'weakref', 'webbrowser', 'whichdb',
        'wsgiref', 'xdrlib', 'xml', 'xmllib', 'xmlrpclib', 'zipfile', 'CDROM',
        'DLFCN', 'IN', 'TYPES', '_sysconfigdata_nd', 'Canvas', 'Dialog',
        'FileDialog', 'FixTk', 'ScrolledText', 'SimpleDialog', 'Tix',
        'Tkconstants', 'Tkdnd', 'Tkinter', 'tkColorChooser', 'tkCommonDialog',
        'tkFileDialog', 'tkFont', 'tkMessageBox', 'tkSimpleDialog', 'ttk',
        'turtle', '_markerlib', 'easy_install', 'pip', 'pkg_resources',
        'setuptools', 'hashlib']

    # Generated using `sys.builtin_module_names` on a fresh virtualenv
    builtins.extend(
        ['__builtin__', '__main__', '_ast', '_bisect', '_codecs', '_random',
         '_functools', '_heapq', '_io', '_locale', '_md5', '_sha', '_sha256',
         '_collections', '_sha512', '_socket', '_sre', '_struct', '_symtable',
         '_warnings', '_weakref', 'array', 'binascii', 'cPickle', 'cStringIO',
         'cmath', 'errno', 'exceptions', 'fcntl', 'gc', 'grp', 'itertools',
         'marshal', 'math', 'operator', 'posix', 'pwd', 'select', 'signal',
         'spwd', 'strop', 'sys', 'syslog', 'thread', 'time', 'unicodedata',
         'xxsubtype', 'zipimport', 'zlib', 'imp'])

    big_data["builtins"] = dict()
    big_data["nonbuiltins"] = dict()
    for module, number in data.items():
        if module in builtins:
            big_data["builtins"][module] = number
        else:
            big_data["nonbuiltins"][module] = number

    return big_data


def extract(package_name, downloaded_file, file_type):
    """Extract and archive and navigate inside the directory."""
    if file_type == "tar":
        f = tarfile.open(downloaded_file)
        f.extractall()
        f.close()
    elif file_type == "zip":
        f = zipfile.ZipFile(downloaded_file)
        f.extractall()
    elif file_type == "egg":
        f = zipfile.ZipFile(downloaded_file)
        f.extractall()
    elif file_type == "whl":
        f = zipfile.ZipFile(downloaded_file)
        f.extractall()

    return analyze(package_name, downloaded_file, file_type)


def main(package_name, dest="pypi"):
    """Downloads the latest distribution file and returns path for further
    processing."""
    if dest == "pypi":
        url = "https://pypi.python.org/pypi/"
        r = requests.get(url + package_name + "/json")

        file_url = "unknown"
        file_type = "unknown"
        try:
            urls = [json.loads(r.text)["urls"][i]["url"]
                    for i in range(len(json.loads(r.text)["urls"]))]
        except ValueError as e:
            raise Exception("The package " + package_name +
                            "does not exist over pypi.")

        # First check for a tarball if it is available
        for url in urls:
            if url.endswith(".tar.gz"):
                file_url = url
                file_type = "tar"
                break

        # If no tarballs available, check for a zip archive
        if file_url == "unknown":
            for url in urls:
                if url.endswith(".zip"):
                    file_url = url
                    file_type = "zip"
                    break

        # If no tarball or a zip archive available, go for an egg
        if file_url == "unknown":
            for url in urls:
                if url.endswith(".egg"):
                    file_url = url
                    file_type = "egg"
                    break

        # Yet got nothing, go for wheel
        if file_url == "unknown":
            for url in urls:
                if url.endswith(".whl"):
                    file_url = url
                    file_type = "whl"
                    break

        # If still no luck
        if not file_type in ('tar', 'egg', 'whl', 'zip'):
            raise Exception("Unknown format over pypi.")
        else:
            # Let's move somewhere safe
            tempdir = tempfile.mkdtemp()
            currdir = os.getcwd()
            os.chdir(tempdir)
            os.system("wget " + file_url)
            downloaded_file = glob.glob("*")[0]
            big_data = extract(package_name, downloaded_file, file_type)
            os.chdir(currdir)
            shutil.rmtree(tempdir)
            return big_data
