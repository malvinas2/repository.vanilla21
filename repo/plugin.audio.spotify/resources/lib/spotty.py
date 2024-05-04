import os
import subprocess
from typing import Dict, List

import xbmc
from xbmc import LOGDEBUG, LOGERROR

from utils import log_msg

# IMPORTANT: To allow 'spotty' to run on Android, we need to run it from the
#            kodi package's internal writeable directory. Same with temp files
#            - they need to be written to the same directory.
KODI_ANDROID_INTERNAL_WRITABLE_DIR = "/data/data/org.xbmc.kodi"

SPOTTY_PORT = 54443
SPOTTY_PLAYER_NAME = "temp-spotty"
SPOTTY_DEFAULT_ARGS = [
    "--verbose",
    "--enable-audio-cache",
    "--name",
    SPOTTY_PLAYER_NAME,
]


class Spotty:
    def __init__(self):
        self.__spotty_binary = ""
        self.__spotty_cache = ""
        self.__spotify_username = ""
        self.__spotify_password = ""
        self.__spotty_rust_env = None

        self.__playback_supported = True

    def set_spotty_paths(self, spotty_binary: str, spotty_cache: str) -> None:
        self.__spotty_binary = spotty_binary
        self.__spotty_cache = spotty_cache

        if self.__spotty_binary:
            self.__playback_supported = True
            xbmc.executebuiltin("SetProperty(spotify.supportsplayback, true, Home)")
        else:
            self.__playback_supported = False
            log_msg("Error while verifying spotty. Local playback is disabled.", loglevel=LOGERROR)

    def set_spotty_env(self, env: Dict[str, str]):
        self.__spotty_rust_env = env

    def set_spotify_user(self, username: str, password: str) -> None:
        self.__spotify_username = username
        self.__spotify_password = password

    def run_spotty(
        self, extra_args: List[str] = None, use_creds: bool = False, ap_port: str = SPOTTY_PORT
    ) -> subprocess.Popen:
        log_msg("Running spotty...", LOGDEBUG)

        try:
            # os.environ["RUST_LOG"] = "debug"
            args = [
                self.__spotty_binary,
                "--cache",
                self.__spotty_cache,
                "--ap-port",
                str(ap_port),
            ] + SPOTTY_DEFAULT_ARGS

            if extra_args:
                args += extra_args

            loggable_args = args.copy()

            if use_creds:
                args += ["-u", self.__spotify_username, "-p", self.__spotify_password]
                loggable_args += ["-u", self.__spotify_username, "-p", "****"]

            log_msg(f"Spotty args: {' '.join(loggable_args)}", LOGDEBUG)

            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            return subprocess.Popen(
                args,
                startupinfo=startupinfo,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=self.__spotty_rust_env,
            )
        except Exception as ex:
            raise Exception(f"Run spotty error: {ex}")
