import argparse
import os
import webbrowser

from dt_shell import DTCommandAbs, dtslogger


class DTCommand(DTCommandAbs):
    help = "Opens the current project's documentation"

    @staticmethod
    def command(shell, args):
        # configure arguments
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-C",
            "--workdir",
            default=os.getcwd(),
            help="Directory containing the project's docs to open"
        )
        parsed, _ = parser.parse_known_args(args=args)
        # ---
        parsed.workdir = os.path.abspath(parsed.workdir)
        dtslogger.info("Project workspace: {}".format(parsed.workdir))

        # file locators
        repo_file = lambda *p: os.path.join(parsed.workdir, *p)
        docs_file = lambda *p: os.path.join(repo_file("html", "out"), *p)

        # check if index.html exists
        dtslogger.info("Checking if the documentation files are in order...")
        if not os.path.exists(docs_file("index.html")):
            dtslogger.error(f"File {docs_file('index.html')} not found. Aborting.")
            exit(1)
        dtslogger.info("Done!")

        # Open browser
        webbrowser.open(docs_file('index.html'), new=2)
        dtslogger.info("Happy reading!")

    @staticmethod
    def complete(shell, word, line):
        return []