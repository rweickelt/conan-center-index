import os
from six import StringIO
from conans import ConanFile, tools


class QbsTestConan(ConanFile):
    settings = "arch_build", "os_build"

    def test(self):
        if not tools.cross_building(self.settings):
            output = StringIO()
            self.run("qbs show-version")
            self.run("qbs show-version", output=output, run_environment=True)
            output_str = str(output.getvalue())
            self.output.info("Installed version: {}".format(output_str))
            require_version = str(self.deps_cpp_info["qbs"].version)
            self.output.info("Expected version: {}".format(require_version))
            assert(require_version in output_str)
