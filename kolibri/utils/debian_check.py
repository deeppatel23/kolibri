import getpass
import os
import sys

from builtins import input

from .conf import KOLIBRI_HOME
from .server import installation_type


def check_debian_user(noninteractive=False):
    if noninteractive:
        return

    # Check if Kolibri is installed through the Kolibri Debian package or kolibri-server
    # Debian package
    install_type = installation_type()
    if install_type not in ["dpkg", "apt"] or not install_type.startswith("kolibri"):
        return

    with open("/etc/kolibri/username", "r") as f:
        kolibri_user = f.read().rstrip()

    current_user = getpass.getuser()

    # If kolibri user does not exist or is the same as the current user, then do not
    # prompt the user with the warning.
    if not kolibri_user or kolibri_user == current_user:
        return

    # If the database file exists in the KOLIBRI_HOME directory, then kolibri was
    # started with the current user before. There is no need to prompt the user
    # with the warning.
    if os.path.exists(os.path.join(KOLIBRI_HOME, "db.sqlite3")):
        return

    sys.stderr.write(
        (
            "You are running this command as the user '{current_user}', "
            "but Kolibri was originally installed to run as the user '{kolibri_user}'.\n"
            "This may result in unexpected behavior, "
            "because the two users will each use their own local databases and content.\n\n"
        ).format(current_user=current_user, kolibri_user=kolibri_user)
    )
    sys.stderr.write(
        (
            "If you'd like to run the command as '{}', you can try:\n\n"
            "    sudo su {} -c '<command>'\n\n"
        ).format(kolibri_user, kolibri_user)
    )
    cont = input(
        "Alternatively, would you like to continue and "
        "run the command as '{}'? [y/N] ".format(current_user)
    )
    if not cont.strip().lower() == "y":
        sys.exit(0)
