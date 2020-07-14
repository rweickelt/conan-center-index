import os
import shutil
import itertools
import glob

import configparser
from conans import ConanFile, tools, __version__ as conan_version, RunEnvironment
from conans.errors import ConanInvalidConfiguration
from conans.model import Generator
from conans.tools import Version


class qt(Generator):
    @property
    def filename(self):
        return "qt.conf"

    @property
    def content(self):
        return "[Paths]\nPrefix = %s\n" % self.conanfile.deps_cpp_info["qt"].rootpath.replace("\\", "/")


def _getsubmodules():
    config = configparser.ConfigParser()
    config.read('qtmodules.conf')
    res = {}
    assert config.sections()
    for s in config.sections():
        section = str(s)
        assert section.startswith("submodule ")
        assert section.count('"') == 2
        modulename = section[section.find('"') + 1: section.rfind('"')]
        status = str(config.get(section, "status"))
        if status != "obsolete" and status != "ignore":
            res[modulename] = {"status": status,
                               "path": str(config.get(section, "path")), "depends": []}
            if config.has_option(section, "depends"):
                res[modulename]["depends"] = [str(i) for i in config.get(section, "depends").split()]
    return res


class QtConan(ConanFile):
    _submodules = _getsubmodules()

    generators = "pkg_config"
    name = "qt"
    description = "Qt is a cross-platform framework for graphical user interfaces."
    topics = ("conan", "qt", "ui")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.qt.io"
    license = "LGPL-3.0"
    exports = ["qtmodules.conf", "patches/*.diff"]
    settings = "os", "arch", "compiler", "build_type"

    options = {
        "shared": [True, False],
        "commercial": [True, False],

        "opengl": ["no", "es2", "desktop", "dynamic"],
        "with_vulkan": [True, False],
        "openssl": [True, False],
        "with_pcre2": [True, False],
        "with_glib": [True, False],
        # "with_libiconv": [True, False],  # QTBUG-84708 Qt tests failure "invalid conversion from const char** to char**"
        "with_doubleconversion": [True, False],
        "with_freetype": [True, False],
        "with_fontconfig": [True, False],
        "with_icu": [True, False],
        "with_harfbuzz": [True, False],
        "with_libjpeg": [True, False],
        "with_libpng": [True, False],
        "with_sqlite3": [True, False],
        "with_mysql": [True, False],
        "with_pq": [True, False],
        "with_odbc": [True, False],
        "with_libalsa": [True, False],
        "with_openal": [True, False],
        "with_zstd": [True, False],

        "GUI": [True, False],
        "widgets": [True, False],

        "device": "ANY",
        "cross_compile": "ANY",
        "sysroot": "ANY",
        "config": "ANY",
        "multiconfiguration": [True, False],
    }
    options.update({module: [True, False] for module in _submodules if module != 'qtbase'})

    no_copy_source = True
    default_options = {
        "shared": True,
        "commercial": False,
        "opengl": "desktop",
        "with_vulkan": False,
        "openssl": True,
        "with_pcre2": True,
        "with_glib": False,
        # "with_libiconv": True, # QTBUG-84708
        "with_doubleconversion": True,
        "with_freetype": True,
        "with_fontconfig": True,
        "with_icu": True,
        "with_harfbuzz": False,
        "with_libjpeg": True,
        "with_libpng": True,
        "with_sqlite3": True,
        "with_mysql": True,
        "with_pq": True,
        "with_odbc": True,
        "with_libalsa": False,
        "with_openal": True,
        "with_zstd": True,

        "GUI": True,
        "widgets": True,

        "device": None,
        "cross_compile": None,
        "sysroot": None,
        "config": None,
        "multiconfiguration": False,
    }
    default_options.update({module: False for module in _submodules if module != 'qtbase'})

    requires = "zlib/1.2.11"
    short_paths = True

    def build_requirements(self):
        if tools.os_info.is_windows and self.settings.compiler == "Visual Studio":
            self.build_requires("jom/1.1.3")
        if self.options.qtwebengine:
            self.build_requires("ninja/1.10.0")
            # gperf, bison, flex, python >= 2.7.5 & < 3
            if self.settings.os != "Windows":
                if not tools.which("bison"):
                    self.build_requires("bison/3.5.3")
                if not tools.which("gperf"):
                    self.build_requires("gperf/3.1")
                if not tools.which("flex"):
                    self.build_requires("flex/2.6.4")

            # Check if a valid python2 is available in PATH or it will failflex
            # Start by checking if python2 can be found
            python_exe = tools.which("python2")
            if not python_exe:
                # Fall back on regular python
                python_exe = tools.which("python")

            if not python_exe:
                msg = ("Python2 must be available in PATH "
                       "in order to build Qt WebEngine")
                raise ConanInvalidConfiguration(msg)
            # In any case, check its actual version for compatibility
            from six import StringIO  # Python 2 and 3 compatible
            mybuf = StringIO()
            cmd_v = "{} --version".format(python_exe)
            self.run(cmd_v, output=mybuf)
            verstr = mybuf.getvalue().strip().split('Python ')[1]
            if verstr.endswith('+'):
                verstr = verstr[:-1]
            version = tools.Version(verstr)
            # >= 2.7.5 & < 3
            v_min = "2.7.5"
            v_max = "3.0.0"
            if (version >= v_min) and (version < v_max):
                msg = ("Found valid Python 2 required for QtWebengine:"
                       " version={}, path={}".format(mybuf.getvalue(), python_exe))
                self.output.success(msg)
            else:
                msg = ("Found Python 2 in path, but with invalid version {}"
                       " (QtWebEngine requires >= {} & < "
                       "{})".format(verstr, v_min, v_max))
                raise ConanInvalidConfiguration(msg)

    def config_options(self):
        if self.settings.os != "Linux":
            self.options.with_icu = False
        if self.settings.compiler == "apple-clang":
            if tools.Version(self.settings.compiler.version) < "10.0":
                raise ConanInvalidConfiguration("Old versions of apple sdk are not supported by Qt (QTBUG-76777)")

    def configure(self):
        if self.settings.os != 'Linux':
            #     self.options.with_libiconv = False # QTBUG-84708
            self.options.with_fontconfig = False
        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "5.3":
            self.options.with_mysql = False
        if self.settings.os == "Windows":
            self.options.with_mysql = False
            if not self.options.shared and self.options.with_icu:
                raise ConanInvalidConfiguration("icu option is not supported on windows in static build. see QTBUG-77120.")

        if self.options.widgets and not self.options.GUI:
            raise ConanInvalidConfiguration("using option qt:widgets without option qt:GUI is not possible. "
                                            "You can either disable qt:widgets or enable qt:GUI")
        if not self.options.GUI:
            self.options.opengl = "no"
            self.options.with_vulkan = False
            self.options.with_freetype = False
            self.options.with_fontconfig = False
            self.options.with_harfbuzz = False
            self.options.with_libjpeg = False
            self.options.with_libpng = False

        if not self.options.qtmultimedia:
            self.options.with_libalsa = False
            self.options.with_openal = False

        if self.settings.os != "Linux":
            self.options.with_libalsa = False

        if self.options.qtwebengine:
            if not self.options.shared:
                raise ConanInvalidConfiguration("Static builds of Qt Webengine are not supported")

            if tools.cross_building(self.settings, skip_x64_x86=True):
                raise ConanInvalidConfiguration("Cross compiling Qt WebEngine is not supported")

            if self.settings.compiler == "gcc" and tools.Version(self.settings.compiler.version) < "5":
                raise ConanInvalidConfiguration("Compiling Qt WebEngine with gcc < 5 is not supported")

        if self.settings.os == "Android" and self.options.opengl == "desktop":
            raise ConanInvalidConfiguration("OpenGL desktop is not supported on Android. Consider using OpenGL es2")

        if self.settings.os != "Windows" and self.options.opengl == "dynamic":
            raise ConanInvalidConfiguration("Dynamic OpenGL is supported only on Windows.")

        if self.options.with_fontconfig and not self.options.with_freetype:
            raise ConanInvalidConfiguration("with_fontconfig cannot be enabled if with_freetype is disabled.")

        if self.settings.os == "Macos":
            del self.settings.os.version

        if self.options.multiconfiguration:
            del self.settings.build_type

        if not self.options.with_doubleconversion and str(self.settings.compiler.libcxx) != "libc++":
            raise ConanInvalidConfiguration('Qt without libc++ needs qt:with_doubleconversion. '
                                            'Either enable qt:with_doubleconversion or switch to libc++')

        if tools.os_info.is_linux:
            if self.options.qtwebengine:
                self.options.with_fontconfig = True

        def _enablemodule(mod):
            if mod != 'qtbase':
                setattr(self.options, mod, True)
            for req in self._submodules[mod]["depends"]:
                _enablemodule(req)

        for module in self._submodules:
            if module != 'qtbase' and getattr(self.options, module):
                _enablemodule(module)

    def requirements(self):
        if self.options.openssl:
            self.requires("openssl/1.1.1g")
        if self.options.with_pcre2:
            self.requires("pcre2/10.33")

        if self.options.with_glib:
            self.requires("glib/2.65.0")
        # if self.options.with_libiconv: # QTBUG-84708
        #     self.requires("libiconv/1.16")# QTBUG-84708
        if self.options.with_doubleconversion and not self.options.multiconfiguration:
            self.requires("double-conversion/3.1.5")
        if self.options.with_freetype and not self.options.multiconfiguration:
            self.requires("freetype/2.10.1")
        if self.options.with_fontconfig:
            self.requires("fontconfig/2.13.91")
        if self.options.with_icu:
            self.requires("icu/64.2")
        if self.options.with_harfbuzz and not self.options.multiconfiguration:
            self.requires("harfbuzz/2.6.8")
        if self.options.with_libjpeg and not self.options.multiconfiguration:
            self.requires("libjpeg/9d")
        if self.options.with_libpng and not self.options.multiconfiguration:
            self.requires("libpng/1.6.37")
        if self.options.with_sqlite3 and not self.options.multiconfiguration:
            self.requires("sqlite3/3.32.2")
            self.options["sqlite3"].enable_column_metadata = True
        if self.options.with_mysql:
            self.requires("libmysqlclient/8.0.17")
        if self.options.with_pq:
            self.requires("libpq/12.2")
        if self.options.with_odbc:
            if self.settings.os != "Windows":
                self.requires("odbc/2.3.7")
        if self.options.with_openal:
            self.requires("openal/1.19.1")
        if self.options.with_libalsa:
            self.requires("libalsa/1.1.9")
        if self.options.GUI and self.settings.os == "Linux":
            self.requires("xorg/system")
        if self.options.opengl != "no":
            self.requires("opengl/system")
        if self.options.with_zstd:
            self.requires("zstd/1.4.5")
        if self.options.qtwebengine and self.settings.os == "Linux":
            self.requires("expat/2.2.9")
            self.requires("opus/1.3.1")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        shutil.move("qt-everywhere-src-%s" % self.version, "qt5")

        for p in self.conan_data["patches"][self.version]:
            tools.patch(**p)
        for f in ["renderer", os.path.join("renderer", "core"), os.path.join("renderer", "platform")]:
            tools.replace_in_file(os.path.join(self.source_folder, "qt5", "qtwebengine", "src", "3rdparty", "chromium", "third_party", "blink", f, "BUILD.gn"),
                                  "  if (enable_precompiled_headers) {\n    if (is_win) {",
                                  "  if (enable_precompiled_headers) {\n    if (false) {"
                                  )

    def _make_program(self):
        if self.settings.compiler == "Visual Studio":
            return "jom"
        elif tools.os_info.is_windows:
            return "mingw32-make"
        else:
            return "make"

    def _xplatform(self):
        if self.settings.os == "Linux":
            if self.settings.compiler == "gcc":
                return {"x86": "linux-g++-32",
                        "armv6": "linux-arm-gnueabi-g++",
                        "armv7": "linux-arm-gnueabi-g++",
                        "armv7hf": "linux-arm-gnueabi-g++",
                        "armv8": "linux-aarch64-gnu-g++"}.get(str(self.settings.arch), "linux-g++")
            elif self.settings.compiler == "clang":
                if self.settings.arch == "x86":
                    return "linux-clang-libc++-32" if self.settings.compiler.libcxx == "libc++" else "linux-clang-32"
                elif self.settings.arch == "x86_64":
                    return "linux-clang-libc++" if self.settings.compiler.libcxx == "libc++" else "linux-clang"

        elif self.settings.os == "Macos":
            return {"clang": "macx-clang",
                    "apple-clang": "macx-clang",
                    "gcc": "macx-g++"}.get(str(self.settings.compiler))

        elif self.settings.os == "iOS":
            if self.settings.compiler == "apple-clang":
                return "macx-ios-clang"

        elif self.settings.os == "watchOS":
            if self.settings.compiler == "apple-clang":
                return "macx-watchos-clang"

        elif self.settings.os == "tvOS":
            if self.settings.compiler == "apple-clang":
                return "macx-tvos-clang"

        elif self.settings.os == "Android":
            return {"clang": "android-clang",
                    "gcc": "android-g++"}.get(str(self.settings.compiler))

        elif self.settings.os == "Windows":
            return {"Visual Studio": "win32-msvc",
                    "gcc": "win32-g++",
                    "clang": "win32-clang-g++"}.get(str(self.settings.compiler))

        elif self.settings.os == "WindowsStore":
            if self.settings.compiler == "Visual Studio":
                return {"14": {"armv7": "winrt-arm-msvc2015",
                               "x86": "winrt-x86-msvc2015",
                               "x86_64": "winrt-x64-msvc2015"},
                        "15": {"armv7": "winrt-arm-msvc2017",
                               "x86": "winrt-x86-msvc2017",
                               "x86_64": "winrt-x64-msvc2017"}
                        }.get(str(self.settings.compiler.version)).get(str(self.settings.arch))

        elif self.settings.os == "FreeBSD":
            return {"clang": "freebsd-clang",
                    "gcc": "freebsd-g++"}.get(str(self.settings.compiler))

        elif self.settings.os == "SunOS":
            if self.settings.compiler == "sun-cc":
                if self.settings.arch == "sparc":
                    return "solaris-cc-stlport" if self.settings.compiler.libcxx == "libstlport" else "solaris-cc"
                elif self.settings.arch == "sparcv9":
                    return "solaris-cc64-stlport" if self.settings.compiler.libcxx == "libstlport" else "solaris-cc64"
            elif self.settings.compiler == "gcc":
                return {"sparc": "solaris-g++",
                        "sparcv9": "solaris-g++-64"}.get(str(self.settings.arch))
        elif self.settings.os == "Neutrino" and self.settings.compiler == "qcc":
            return {"armv8": "qnx-aarch64le-qcc",
                    "armv8.3": "qnx-aarch64le-qcc",
                    "armv7": "qnx-armle-v7-qcc",
                    "armv7hf": "qnx-armle-v7-qcc",
                    "armv7s": "qnx-armle-v7-qcc",
                    "armv7k": "qnx-armle-v7-qcc",
                    "x86": "qnx-x86-qcc",
                    "x86_64": "qnx-x86-64-qcc"}.get(str(self.settings.arch))
        elif self.settings.os == "Emscripten" and self.settings.arch == "wasm":
            return "wasm-emscripten"

        return None

    def build(self):
        if self.settings.compiler in ["gcc", "clang"]:
            if tools.Version(self.settings.compiler.version) < "5.0":
                raise ConanInvalidConfiguration("qt 5.15.0 is not support on GCC or clang before 5.0")
        args = ["-confirm-license", "-silent", "-nomake examples", "-nomake tests",
                "-prefix %s" % self.package_folder]
        args.append("-v")
        args.append("-archdatadir  %s" % os.path.join(self.package_folder, "bin", "archdatadir"))
        args.append("-datadir  %s" % os.path.join(self.package_folder, "bin", "datadir"))
        args.append("-sysconfdir  %s" % os.path.join(self.package_folder, "bin", "sysconfdir"))
        if self.options.commercial:
            args.append("-commercial")
        else:
            args.append("-opensource")
        if not self.options.GUI:
            args.append("-no-gui")
        if not self.options.widgets:
            args.append("-no-widgets")
        if not self.options.shared:
            args.insert(0, "-static")
            if self.settings.compiler == "Visual Studio":
                if self.settings.compiler.runtime == "MT" or self.settings.compiler.runtime == "MTd":
                    args.append("-static-runtime")
        else:
            args.insert(0, "-shared")
        if self.options.multiconfiguration:
            args.append("-debug-and-release")
        elif self.settings.build_type == "Debug":
            args.append("-debug")
        elif self.settings.build_type == "Release":
            args.append("-release")
        elif self.settings.build_type == "RelWithDebInfo":
            args.append("-release")
            args.append("-force-debug-info")
        elif self.settings.build_type == "MinSizeRel":
            args.append("-release")
            args.append("-optimize-size")

        for module in self._submodules:
            if module != 'qtbase' and not getattr(self.options, module) \
                    and os.path.isdir(os.path.join(self.source_folder, 'qt5', self._submodules[module]['path'])):
                args.append("-skip " + module)

        args.append("--zlib=system")

        # openGL
        if self.options.opengl == "no":
            args += ["-no-opengl"]
        elif self.options.opengl == "es2":
            args += ["-opengl es2"]
        elif self.options.opengl == "desktop":
            args += ["-opengl desktop"]
        elif self.options.opengl == "dynamic":
            args += ["-opengl dynamic"]

        if self.options.with_vulkan:
            args.append("-vulkan")
        else:
            args.append("-no-vulkan")

        # openSSL
        if not self.options.openssl:
            args += ["-no-openssl"]
        else:
            if self.options["openssl"].shared:
                args += ["-openssl-runtime"]
            else:
                args += ["-openssl-linked"]

        # args.append("--iconv=" + ("gnu" if self.options.with_libiconv else "no"))# QTBUG-84708

        args.append("--glib=" + ("yes" if self.options.with_glib else "no"))
        args.append("--pcre=" + ("system" if self.options.with_pcre2 else "qt"))
        args.append("--fontconfig=" + ("yes" if self.options.with_fontconfig else "no"))
        args.append("--icu=" + ("yes" if self.options.with_icu else "no"))
        args.append("--sql-mysql=" + ("yes" if self.options.with_mysql else "no"))
        args.append("--sql-psql=" + ("yes" if self.options.with_pq else "no"))
        args.append("--sql-odbc=" + ("yes" if self.options.with_odbc else "no"))
        args.append("--zstd=" + ("yes" if self.options.with_zstd else "no"))

        if self.options.qtmultimedia:
            args.append("--alsa=" + ("yes" if self.options.with_libalsa else "no"))

        for opt, conf_arg in [
                              ("with_doubleconversion", "doubleconversion"),
                              ("with_freetype", "freetype"),
                              ("with_harfbuzz", "harfbuzz"),
                              ("with_libjpeg", "libjpeg"),
                              ("with_libpng", "libpng"),
                              ("with_sqlite3", "sqlite")]:
            if getattr(self.options, opt):
                if self.options.multiconfiguration:
                    args += ["-qt-" + conf_arg]
                else:
                    args += ["-system-" + conf_arg]
            else:
                args += ["-no-" + conf_arg]

        libmap = [("zlib", "ZLIB"),
                  ("openssl", "OPENSSL"),
                  ("pcre2", "PCRE2"),
                  ("glib", "GLIB"),
                  # ("libiconv", "ICONV"),# QTBUG-84708
                  ("double-conversion", "DOUBLECONVERSION"),
                  ("freetype", "FREETYPE"),
                  ("fontconfig", "FONTCONFIG"),
                  ("icu", "ICU"),
                  ("harfbuzz", "HARFBUZZ"),
                  ("libjpeg", "LIBJPEG"),
                  ("libpng", "LIBPNG"),
                  ("sqlite3", "SQLITE"),
                  ("libmysqlclient", "MYSQL"),
                  ("libpq", "PSQL"),
                  ("odbc", "ODBC"),
                  ("sdl2", "SDL2"),
                  ("openal", "OPENAL"),
                  ("zstd", "ZSTD"),
                  ("libalsa", "ALSA")]
        for package, var in libmap:
            if package in self.deps_cpp_info.deps:
                if package == 'freetype':
                    args.append("\"%s_INCDIR=%s\"" % (var, self.deps_cpp_info[package].include_paths[-1]))

                args.append("\"%s_LIBS=%s\"" % (var, " ".join(self._gather_libs(package))))

        for package in self.deps_cpp_info.deps:
            args += ["-I " + s for s in self.deps_cpp_info[package].include_paths]
            args += ["-D " + s for s in self.deps_cpp_info[package].defines]
            args += ["-L " + s for s in self.deps_cpp_info[package].lib_paths]

        if 'libmysqlclient' in self.deps_cpp_info.deps:
            args.append("-mysql_config " + os.path.join(self.deps_cpp_info['libmysqlclient'].rootpath, "bin", "mysql_config"))
        if 'libpq' in self.deps_cpp_info.deps:
            args.append("-psql_config " + os.path.join(self.deps_cpp_info['libpq'].rootpath, "bin", "pg_config"))
        if self.settings.os == "Macos":
            args += ["-no-framework"]
        elif self.settings.os == "Android":
            args += ["-android-ndk-platform android-%s" % self.settings.os.api_level]
            args += ["-android-abis %s" % {"armv7": "armeabi-v7a",
                                           "armv8": "arm64-v8a",
                                           "x86": "x86",
                                           "x86_64": "x86_64"}.get(str(self.settings.arch))]

        if self.settings.get_safe("compiler.libcxx") == "libstdc++":
            args += ["-D_GLIBCXX_USE_CXX11_ABI=0"]
        elif self.settings.get_safe("compiler.libcxx") == "libstdc++11":
            args += ["-D_GLIBCXX_USE_CXX11_ABI=1"]

        if self.options.sysroot:
            args += ["-sysroot %s" % self.options.sysroot]

        if self.options.device:
            args += ["-device %s" % self.options.device]
        else:
            xplatform_val = self._xplatform()
            if xplatform_val:
                if not tools.cross_building(self.settings, skip_x64_x86=True):
                    args += ["-platform %s" % xplatform_val]
                else:
                    args += ["-xplatform %s" % xplatform_val]
            else:
                self.output.warn("host not supported: %s %s %s %s" %
                                 (self.settings.os, self.settings.compiler,
                                  self.settings.compiler.version, self.settings.arch))
        if self.options.cross_compile:
            args += ["-device-option CROSS_COMPILE=%s" % self.options.cross_compile]

        def _getenvpath(var):
            val = os.getenv(var)
            if val and tools.os_info.is_windows:
                val = val.replace("\\", "/")
                os.environ[var] = val
            return val

        value = _getenvpath('CC')
        if value:
            args += ['QMAKE_CC="' + value + '"',
                     'QMAKE_LINK_C="' + value + '"',
                     'QMAKE_LINK_C_SHLIB="' + value + '"']

        value = _getenvpath('CXX')
        if value:
            args += ['QMAKE_CXX="' + value + '"',
                     'QMAKE_LINK="' + value + '"',
                     'QMAKE_LINK_SHLIB="' + value + '"']

        if tools.os_info.is_linux and self.settings.compiler == "clang":
            args += ['QMAKE_CXXFLAGS+="-ftemplate-depth=1024"']

        if self.options.qtwebengine and self.settings.os == "Linux":
            args += ['-qt-webengine-ffmpeg',
                     '-system-webengine-opus']

        if self.options.config:
            args.append(str(self.options.config))

        os.mkdir('build_folder')
        with tools.chdir('build_folder'):
            with tools.vcvars(self.settings) if self.settings.compiler == "Visual Studio" else tools.no_op():
                build_env = {"MAKEFLAGS": "j%d" % tools.cpu_count(), "PKG_CONFIG_PATH": [self.build_folder]}
                if self.settings.os == "Windows":
                    build_env["PATH"] = [os.path.join(self.source_folder, "qt5", "gnuwin32", "bin")]
                with tools.environment_append(build_env):
                    self.run("%s/qt5/configure %s" % (self.source_folder, " ".join(args)), run_environment=True)
                    if tools.os_info.is_macos:
                        with open("bash_env", "w") as f:
                            f.write('export DYLD_LIBRARY_PATH="%s"' % ":".join(RunEnvironment(self).vars["DYLD_LIBRARY_PATH"]))
                    with tools.environment_append({
                        "BASH_ENV": os.path.abspath("bash_env")
                    }) if tools.os_info.is_macos else tools.no_op():
                        self.run(self._make_program(), run_environment=True)

    def package(self):
        with tools.chdir('build_folder'):
            self.run("%s install" % self._make_program())
        with open(os.path.join(self.package_folder, "bin", "qt.conf"), 'w') as f:
            f.write("""[Paths]
Prefix = ..
ArchData = bin/archdatadir
HostData = bin/archdatadir
Data = bin/datadir
Sysconf = bin/sysconfdir
LibraryExecutables = bin/archdatadir/bin
Plugins = bin/archdatadir/plugins
Imports = bin/archdatadir/imports
Qml2Imports = bin/archdatadir/qml
Translations = bin/datadir/translations
Documentation = bin/datadir/doc
Examples = bin/datadir/examples""")
        self.copy("*LICENSE*", src="qt5/", dst="licenses")
        for module in self._submodules:
            if module != 'qtbase' and not getattr(self.options, module):
                tools.rmdir(os.path.join(self.package_folder, "licenses", module))
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
        for file_to_remove in glob.glob(os.path.join(self.package_folder, "lib", "*.la*")):
            os.remove(file_to_remove)
        for file_to_remove in glob.glob(os.path.join(self.package_folder, "lib", "*.pdb*")):
            os.remove(file_to_remove)
        for root, dirs, files in os.walk(os.path.join(self.package_folder, "bin")):
            for name in files:
                if name.endswith('.pdb'):
                    os.remove(os.path.join(root, name))

    def package_id(self):
        del self.info.options.cross_compile
        del self.info.options.sysroot
        if self.options.multiconfiguration and self.settings.compiler == "Visual Studio":
            if "MD" in self.settings.compiler.runtime:
                self.info.settings.compiler.runtime = "MD/MDd"
            else:
                self.info.settings.compiler.runtime = "MT/MTd"

    @staticmethod
    def _remove_duplicate(l):
        seen = set()
        seen_add = seen.add
        for element in itertools.filterfalse(seen.__contains__, l):
            seen_add(element)
            yield element

    def _gather_libs(self, p):
        libs = ["-l" + i for i in self.deps_cpp_info[p].libs + self.deps_cpp_info[p].system_libs]
        if tools.is_apple_os(self.settings.os):
            libs += ["-framework " + i for i in self.deps_cpp_info[p].frameworks]
        libs += self.deps_cpp_info[p].sharedlinkflags
        for dep in self.deps_cpp_info[p].public_deps:
            libs += self._gather_libs(dep)
        return self._remove_duplicate(libs)

    def _gather_lib_paths(self, p):
        lib_paths = self.deps_cpp_info[p].lib_paths
        for dep in self.deps_cpp_info[p].public_deps:
            lib_paths += self._gather_lib_paths(dep)
        return self._remove_duplicate(lib_paths)

    def _gather_include_paths(self, p):
        include_paths = self.deps_cpp_info[p].include_paths
        for dep in self.deps_cpp_info[p].public_deps:
            include_paths += self._gather_include_paths(dep)
        return self._remove_duplicate(include_paths)
