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
    settings = "arch", "os"
    no_copy_source=True

    def configure(self):
        if self.settings.os not in ["Windows", "Linux", "Macos"]:
            raise ConanInvalidConfiguration("The OS ({}) is not supported by {}.".format(self.settings.os, self.name))
        if self.settings.arch not in ["x86_64"]:
            raise ConanInvalidConfiguration("The arch ({}) is not supported by {}.".format(self.settings.arch, self.name))

    def source(self):
        tools.get(**self._data['sources'])

    def build(self):
        tools.download(**self._data['installer'], filename = "creator.7z")
        self.run("cmake -E tar x creator.7z")

    def package(self):
        for p in self._data['package']:
            self.copy(**p, symlinks=True)

    def package_info(self):
        binpath = os.path.join(self.package_folder, self._data['bin_folder'])
        self.env_info.PATH.append(binpath)

    @property
    def _data(self):
        data = {
            'Linux': {
                'sources': self.conan_data['sources'][self.version][0],
                'installer': self.conan_data['sources'][self.version][1],
                'package': [
                    {'dst': 'bin', 'pattern': 'bin/qbs*'},
                    {'dst': 'bin', 'pattern': 'bin/qt.conf'},
                    {'dst': 'bin', 'pattern': 'lib/qtcreator/libqbs*'},
                    {'dst': 'bin', 'pattern': 'lib/qtcreator/plugins/qbs/*'},
                    {'dst': 'bin', 'pattern': 'lib/Qt/lib/libic*'},
                    {'dst': 'bin', 'pattern': 'lib/Qt/lib/libQt5Core*'},
                    {'dst': 'bin', 'pattern': 'lib/Qt/lib/libQt5Gui*'},
                    {'dst': 'bin', 'pattern': 'lib/Qt/lib/libQt5Network*'},
                    {'dst': 'bin', 'pattern': 'lib/Qt/lib/libQt5Script*'},
                    {'dst': 'bin', 'pattern': 'lib/Qt/lib/libQt5Xml*'},
                    {'dst': 'bin', 'pattern': 'libexec/qtcreator/qbs*'},
                    {'dst': 'bin', 'pattern': 'share/qtcreator/qbs/*'},
                    {'src': 'qbs-src-%s' % self.version, 'dst': 'licenses', 'pattern': 'LICENSE*'},
                    {'src': 'qbs-src-%s' % self.version, 'dst': 'licenses', 'pattern': 'LGPL*'}
                ],
                'bin_folder': 'bin/bin'
            },
            'Macos': {
                'sources': self.conan_data['sources'][self.version][0],
                'installer': self.conan_data['sources'][self.version][2],
                'package': [
                    { 'src': 'Qt Creator.app/Contents', 'dst': 'bin', 'pattern': 'MacOS/qbs*'},
                    { 'src': 'Qt Creator.app/Contents', 'dst': 'bin', 'pattern': 'Frameworks/libqbs*'},
                    { 'src': 'Qt Creator.app/Contents', 'dst': 'bin', 'pattern': 'Frameworks/QtCore*'},
                    { 'src': 'Qt Creator.app/Contents', 'dst': 'bin', 'pattern': 'Frameworks/QtGui*'},
                    { 'src': 'Qt Creator.app/Contents', 'dst': 'bin', 'pattern': 'Frameworks/QtNetwork*'},
                    { 'src': 'Qt Creator.app/Contents', 'dst': 'bin', 'pattern': 'Frameworks/QtScript*'},
                    { 'src': 'Qt Creator.app/Contents', 'dst': 'bin', 'pattern': 'Frameworks/QtXml*'},
                    { 'src': 'Qt Creator.app/Contents', 'dst': 'bin', 'pattern': 'PlugIns/qbs/*'},
                    { 'src': 'Qt Creator.app/Contents', 'dst': 'bin', 'pattern': 'Resources/qbs/*'},
                    { 'src': 'Qt Creator.app/Contents', 'dst': 'bin', 'pattern': 'Resources/libexec/qbs*'},
                    { 'src': 'qbs-src-%s' % self.version, 'pattern': 'LICENSE*', 'dst': 'licenses'},
                    { 'src': 'qbs-src-%s' % self.version, 'pattern': 'LGPL*', 'dst': 'licenses'}
                ],
                'bin_folder': 'bin/MacOS'
            },
            'Windows': {
                'sources': self.conan_data['sources'][self.version][0],
                'installer': self.conan_data['sources'][self.version][3],
                'package': [
                    { 'dst': 'bin', 'pattern': 'bin/qbs*'},
                    { 'dst': 'bin', 'pattern': 'bin/Qt5Core*'},
                    { 'dst': 'bin', 'pattern': 'bin/Qt5Gui*'},
                    { 'dst': 'bin', 'pattern': 'bin/Qt5Network*'},
                    { 'dst': 'bin', 'pattern': 'bin/Qt5Script*'},
                    { 'dst': 'bin', 'pattern': 'bin/Qt5Xml*'},
                    { 'dst': 'bin', 'pattern': 'bin/dw*'},
                    { 'dst': 'bin', 'pattern': 'lib/qtcreator/plugins/qbs*'},
                    { 'dst': 'bin', 'pattern': 'share/qtcreator/qbs*'},
                    { 'src': 'qbs-src-%s' % self.version, 'pattern': 'LICENSE*', 'dst': 'licenses'},
                    { 'src': 'qbs-src-%s' % self.version, 'pattern': 'LGPL*', 'dst': 'licenses'}
                ],
                'bin_folder': 'bin/bin'
            }
        }
        return data[str(self.settings.os)]
