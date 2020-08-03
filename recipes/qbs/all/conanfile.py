from conans import ConanFile, tools
from conans.errors import ConanInvalidConfiguration
import os

class QbsConan(ConanFile):
    name = "qbs"
    description = "The Qbs build system"
    topics = ("conan", "qbs", "build", "automation")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://qbs.io"
    license = "LGPL-2.1-only", "LGPL-3.0-only", "Nokia-Qt-exception-1.1"
    settings = "arch", "build_type", "compiler", "os"
    no_copy_source=True

    build_requires = "qt/5.15.0@conan/stable"

    def build_requirements(self):
        if tools.os_info.is_windows and self.settings.compiler == "Visual Studio":
            self.build_requires("jom/1.1.3")

    def configure(self):
        if self.settings.os not in ["Windows", "Linux", "Macos"]:
            raise ConanInvalidConfiguration("The OS ({}) is not supported by {}.".format(self.settings.os, self.name))
        if self.settings.arch not in ["x86_64"]:
            raise ConanInvalidConfiguration("The arch ({}) is not supported by {}.".format(self.settings.arch, self.name))

        self.options["qt"].shared = False
        self.options["qt"].widgets=False
        self.options["qt"].GUI=False
        self.options["qt"].qtscript=True
        for dep, options in self._data["options"].items():
            for key, value in options.items():
                setattr(self.options[dep], key, value)

    def source(self):
        tools.get(**self.conan_data['sources'][self.version][0])

    def build(self):
        qmake = os.path.join(self.deps_cpp_info["qt"].bin_paths[0], "qmake")
        source_dirpath = os.path.join(self.source_folder, "qbs-src-%s" % self.version)
        project_filepath = os.path.join(source_dirpath, "qbs.pro")
        args = [
            "-r", project_filepath,
            "QT-=gui",
            "CONFIG+=release",
            "CONFIG-=debug",
            "CONFIG-=debug_and_release"
        ]
        ncores = tools.cpu_count()

        with tools.vcvars(self.settings) if self.settings.compiler == "Visual Studio" else tools.no_op():
            self.run("%s %s" % (qmake, " ".join(args)), run_environment=True)
            self.run("%s -j%s" % (self._data["build_tool"], ncores), run_environment=True)

    def package(self):
         for p in self._data["package"]:
            self.copy(**p, symlinks=True)

    def package_info(self):
        binpath = os.path.join(self.package_folder, self._data['bin_folder'])
        self.env_info.PATH.append(binpath)

    @property
    def _data(self):
        data = {
            'Linux': {
                "build_tool": "make",
                'options': {
                    'qt': {
                        'with_pq': False,
                        'config': "QMAKE_CXX_FLAGS+=-ffunction-sections QMAKE_CXX_FLAGS+=-fdata-sections"
                    }
                },
                'package': [
                    {'dst': '', 'pattern': 'bin/*'},
                    {'dst': '', 'pattern': 'lib/*'},
                    {'dst': '', 'pattern': 'libexec/*'},
                    {'dst': '', 'pattern': 'share/*'},
                    {'src': 'qbs-src-%s' % self.version, 'dst': 'licenses', 'pattern': 'LICENSE*'},
                    {'src': 'qbs-src-%s' % self.version, 'dst': 'licenses', 'pattern': 'LGPL*'}
                ],
                'bin_folder': 'usr/local/bin'
            },
            'Macos': {
                "build_tool": "make",
                'options': {
                    'qt': {
                        'config': "QMAKE_CXXFLAGS+=-Wno-deprecated-declarations QMAKE_CXXFLAGS+=-Wno-tautological-constant-out-of-range-compare"
                    }
                },
                'package': [
                    {'dst': '', 'pattern': 'bin/*'},
                    {'dst': '', 'pattern': 'lib/*'},
                    {'dst': '', 'pattern': 'libexec/*'},
                    {'dst': '', 'pattern': 'share/*'},
                    {'src': 'qbs-src-%s' % self.version, 'dst': 'licenses', 'pattern': 'LICENSE*'},
                    {'src': 'qbs-src-%s' % self.version, 'dst': 'licenses', 'pattern': 'LGPL*'}
                ],
                'bin_folder': 'bin'
            },
            'Windows': {
                "build_tool": "jom" if self.settings.compiler == "Visual Studio" else "mingw32-make",
                'options': {},
                'package': [
                    {'dst': '', 'pattern': 'bin/*'},
                    {'dst': '', 'pattern': 'lib/*'},
                    {'dst': '', 'pattern': 'libexec/*'},
                    {'dst': '', 'pattern': 'share/*'},
                    {'src': 'qbs-src-%s' % self.version, 'dst': 'licenses', 'pattern': 'LICENSE*'},
                    {'src': 'qbs-src-%s' % self.version, 'dst': 'licenses', 'pattern': 'LGPL*'}
                ],
                'bin_folder': 'bin'
            }
        }
        return data[str(self.settings.os)]
