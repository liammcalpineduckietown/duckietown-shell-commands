from dt_shell import DTCommandAbs, DTShell
from utils.assets_utils import get_asset_icon_path
from utils.duckietown_viewer_utils import \
    ensure_duckietown_viewer_installed, launch_viewer

# NOTE: this must match the name of the launcher in the dt-duckietown-viewer project
LAUNCHER_NAME = "image_viewer"
ICON_ASSET = "icon-image-viewer.png"


class DTCommand(DTCommandAbs):
    help = "Runs the image viewer"

    @staticmethod
    def command(shell: DTShell, args, **kwargs):
        parsed = kwargs.get("parsed", None)
        if parsed is None:
            parsed = DTCommand.parser.parse_args(args)
        # ---
        # make sure the app is installed
        ensure_duckietown_viewer_installed()
        # launch viewer
        launch_viewer(
            parsed.robot,
            LAUNCHER_NAME,
            verbose=parsed.vv,
            window_args={
                "icon": get_asset_icon_path(ICON_ASSET),
                "width": 702
            }
        )
