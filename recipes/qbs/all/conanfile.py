from conans import ConanFile, tools
from pathlib import Path


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

    @property
    def _data(self):
        return self.conan_data['sources'][self.version][str(self.settings.os)]

    def source(self):
        pass

    def build(self):
        tools.download(url = self._data['url'], sha256 = self._data['sha256'],
                       filename = "creator.7z")

        self.run("cmake -E tar x creator.7z")

    def package(self):
        for p in self._data['patterns']:
            self.copy(p, symlinks=True)

    def package_info(self):
        binpath = Path(self.package_folder, self._data['binpath'])
        self.env_info.PATH.append(str(binpath))
