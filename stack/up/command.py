import argparse
import os
import pathlib
from typing import Set

import yaml
from docker.errors import NotFound

from dt_shell import DTCommandAbs, DTShell, dtslogger
from utils.avahi_utils import wait_for_service
from utils.cli_utils import start_command_in_subprocess
from utils.docker_utils import (
    DEFAULT_DOCKER_TCP_PORT,
    get_endpoint_architecture,
    get_registry_to_use,
    pull_image_OLD,
)
from utils.multi_command_utils import MultiCommand
from utils.networking_utils import best_host_for_robot

DEFAULT_STACK = "default"
DUCKIETOWN_STACK = "duckietown"


class DTCommand(DTCommandAbs):
    help = "Easy way to run code on Duckietown robots"

    @staticmethod
    def command(shell: DTShell, args):
        # configure arguments
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-H",
            "--machine",
            required=True,
            help="Docker socket or hostname where to run the image",
        )
        parser.add_argument(
            "-d",
            "--detach",
            action="store_true",
            default=False,
            help="Detach from running containers",
        )
        parser.add_argument(
            "--pull",
            action="store_true",
            default=False,
            help="Pull images before running",
        )
        parser.add_argument(
            "-p",
            "--project",
            required=False,
            default=None,
            help="Name of the project to use for the stack",
        )

        parser.add_argument("stack", nargs=1, default=None)
        parsed, _ = parser.parse_known_args(args=args)
        # ---
        # try to interpret it as a multi-command
        multi = MultiCommand(DTCommand, shell, [("-H", "--machine")], args)
        if multi.is_multicommand:
            multi.execute()
            return True
        # ---
        stack = parsed.stack[0]
        project_name = parsed.project or stack.replace("/", "_")
        robot: str = parsed.machine.replace(".local", "")
        hostname: str = best_host_for_robot(parsed.machine)
        # sanitize stack
        stack = stack if "/" in stack else f"{stack}/{DEFAULT_STACK}"
        # check stack
        stack_cmd_dir = pathlib.Path(__file__).parent.parent.absolute()
        stack_file = os.path.join(stack_cmd_dir, "stacks", stack) + ".yaml"
        if not os.path.isfile(stack_file):
            dtslogger.error(f"Stack [{project_name}]({stack}) not found.")
            return False
        # info about registry
        registry_to_use = get_registry_to_use()

        # get info about docker endpoint
        dtslogger.info("Retrieving info about Docker endpoint...")
        endpoint_arch = get_endpoint_architecture(hostname)
        dtslogger.info(f'Detected device architecture is "{endpoint_arch}".')
        # pull images
        processed: Set[str] = set()
        if parsed.pull:
            with open(stack_file, "r") as fin:
                stack_content = yaml.safe_load(fin)
            for service in stack_content["services"].values():
                image_name = service["image"].replace("${ARCH}", endpoint_arch)
                image_name = image_name.replace("${REGISTRY}", registry_to_use)
                if image_name in processed:
                    continue
                dtslogger.info(f"Pulling image `{image_name}`...")
                processed.add(image_name)
                try:
                    pull_image_OLD(image_name, hostname)
                except NotFound:
                    msg = f"Image '{image_name}' not found on registry '{registry_to_use}'. Aborting."
                    dtslogger.error(msg)
                    return False
        # print info
        dtslogger.info(f"Running stack [{project_name}]({stack})...")
        print("------>")
        # collect arguments
        docker_arguments = [
            "--remove-orphans",
        ]
        # get copy of environment
        env = {}
        env.update(os.environ)
        # add ARCH
        env["ARCH"] = endpoint_arch
        env["REGISTRY"] = registry_to_use
        # -d/--detach
        if parsed.detach:
            docker_arguments.append("--detach")
        # run docker compose stack
        H = f"{hostname}:{DEFAULT_DOCKER_TCP_PORT}"
        start_command_in_subprocess(
            ["docker", f"--host={H}", "compose", "--project-name", project_name, "--file", stack_file, "up"]
            + docker_arguments,
            env=env,
        )
        # ---
        print("<------")
        return True
