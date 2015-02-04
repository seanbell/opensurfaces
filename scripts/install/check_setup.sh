# This file should be sourced by the installer
#
# Check setup
#

# make sure we're not root
if [[ "$USER" == "root" ]]; then
	echo "Error: don't run this as root"
	echo "The script will request your password later"
	exit 1
fi

# make sure sudo works
echo "Log in to access root:"
sudo echo "success"

# make sure we're on Ubuntu
if command -v apt-get >/dev/null 2>&1 && [[ $(uname -a | grep -c "Ubuntu") -ge 1 ]]; then
	uname -a
	echo ""
else
	echo "Error: this script only works for Ubuntu"
	exit 1
fi

# check Ubuntu version
sudo apt-get install -y base-files
source /etc/os-release
if [[ ${VERSION%%.*} -lt 12 ]]; then
	echo "Error: this script requires Ubuntu >= 12.04"
	echo "This machine:"
	cat /etc/os-release
	exit 1
fi

# make sure repo exists
if [[ ! -d "$REPO_DIR" ]]; then
	echo "Error: Repository not found at $REPO_DIR"
	echo "Either check out repository at $REPO_DIR or adjust the REPO_DIR variable to point to the repository"
	exit 1
fi

# make sure we're at root directory of repo
echo "Changing to root directory ($REPO_DIR)"
cd "$REPO_DIR"

# fix permissions (just in case repo was checked out as root)
echo "Fixing $REPO_DIR owner..."
sudo chown -R $USER:$USER $REPO_DIR
echo "Fixing $REPO_DIR permissions"
# note: not recursive
sudo chmod 755 $REPO_DIR
