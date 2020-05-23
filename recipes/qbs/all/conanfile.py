from conans import ConanFile, tools
import os


class QbsConan(ConanFile):
    name = "qbs"
    description = "The Qbs build system"
    topics = ("conan", "qbs", "build", "automation")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://qbs.io"
    license = "LGPL-2.1-only", "LGPL-3.0-only", "Nokia-Qt-exception-1.1"
    settings = {
        "arch": ["x86_64"],
        "os": ["Linux", "Macos", "Windows"]
    }

    def source(self):
        pass

    def build(self):
        data = dict(**self.conan_data["sources"][self.version][str(self.settings.os_build)])
        tools.download(**data, filename="creator.7z")
        self.run("cmake -E tar x creator.7z")

    def package(self):
        if self.settings.os_build == "Linux":
            self.copy("bin/qbs*", symlinks=True)
            self.copy("bin/qt.conf", symlinks=True)
            self.copy("lib/qtcreator/libqbs*", symlinks=True)
            self.copy("lib/qtcreator/plugins/qbs/*", symlinks=True)
            self.copy("lib/Qt/lib/libic*", symlinks=True)
            self.copy("lib/Qt/lib/libQt5Core*", symlinks=True)
            self.copy("lib/Qt/lib/libQt5DBus*", symlinks=True)
            self.copy("lib/Qt/lib/libQt5Gui*", symlinks=True)
            self.copy("lib/Qt/lib/libQt5Network*", symlinks=True)
            self.copy("lib/Qt/lib/libQt5PrintSupport*", symlinks=True)
            self.copy("lib/Qt/lib/libQt5Script*", symlinks=True)
            self.copy("lib/Qt/lib/libQt5Widgets*", symlinks=True)
            self.copy("lib/Qt/lib/libQt5Xml*", symlinks=True)
            self.copy("lib/Qt/lib/libQt5XcbQpa*", symlinks=True)
            self.copy("lib/Qt/plugins/platforms/libqxcb*", symlinks=True)
            self.copy("lib/Qt/plugins/platformthemes/libqgtk3*", symlinks=True)
            self.copy("libexec/qtcreator/qbs/*", symlinks=True)
            self.copy("share/qtcreator/qbs/*", symlinks=True)

        elif self.settings.os_build == "Macos":
            self.copy("Qt Creator.app/Contents/MacOS/qbs*", symlinks=True)
            self.copy("Qt Creator.app/Contents/MacOS/qbs/*", symlinks=True)
            self.copy("Qt Creator.app/Contents/Frameworks/libqbs*", symlinks=True)
            self.copy("Qt Creator.app/Contents/Frameworks/QtCore*", symlinks=True)
            self.copy("Qt Creator.app/Contents/Frameworks/QtDBus*", symlinks=True)
            self.copy("Qt Creator.app/Contents/Frameworks/QtGui*", symlinks=True)
            self.copy("Qt Creator.app/Contents/Frameworks/QtNetwork*", symlinks=True)
            self.copy("Qt Creator.app/Contents/Frameworks/QtPrintSupport*", symlinks=True)
            self.copy("Qt Creator.app/Contents/Frameworks/QtScript*", symlinks=True)
            self.copy("Qt Creator.app/Contents/Frameworks/QtWidgets*", symlinks=True)
            self.copy("Qt Creator.app/Contents/Frameworks/QtXml*", symlinks=True)
            self.copy("Qt Creator.app/Contents/PlugIns/qbs/*", symlinks=True)
            self.copy("Qt Creator.app/Contents/PlugIns/platforms/*", symlinks=True)
            self.copy("Qt Creator.app/Contents/PlugIns/styles/*", symlinks=True)
            self.copy("Qt Creator.app/Contents/Resources/qbs/*", symlinks=True)

        elif self.settings.os_build == "Windows":
            self.copy("bin/qbs*", symlinks=True)
            self.copy("bin/Qt5Core*", symlinks=True)
            self.copy("bin/Qt5DBus*", symlinks=True)
            self.copy("bin/Qt5Gui*", symlinks=True)
            self.copy("bin/Qt5Network*", symlinks=True)
            self.copy("bin/Qt5PrintSupport*", symlinks=True)
            self.copy("bin/Qt5Script*", symlinks=True)
            self.copy("bin/Qt5Widgets*", symlinks=True)
            self.copy("bin/Qt5Xml*", symlinks=True)
            self.copy("bin/dw*", symlinks=True)
            self.copy("lib/Qt/plugins/platforms/qwindows*", symlinks=True)
            self.copy("lib/Qt/plugins/styles/qwindowsvistastyle*", symlinks=True)

    def package_info(self):
        if self.settings.os_build == "Macos":
            binpath = os.path.join(self.package_folder, "Qt Creator.app", "Contents", "MacOS")
        else:
            binpath = os.path.join(self.package_folder, "bin")

        self.env_info.PATH.append(binpath)
