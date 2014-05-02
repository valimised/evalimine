#!/bin/bash

set -e

if ! [ -d "$1" ] || [ -z "$2" ] || ! [ -z "$3" ]; then
	cat <<-HELP 2>&1
		$0 <source> <destination>

		   <source>      - source directory
		   <destination> - destination directory where image files
		                   will be written
HELP
	exit 1
fi

if ! mkdir -p "$2"; then
	echo "Cannot create destination directory ($2)" 2>&1
	exit 1
fi

NOBACKUP=/etc/evote/nobackup
EVOTE_MOUNT_DIR=/mnt
EVOTE_SNAPSHOT_NAME=evote_snapshot
DVD_CHUNK_SIZE=$((1024 * 1024 * 1024))

[ -f /etc/default/evote ] && . /etc/default/evote

src_from_df() {
	SRC_DEV="$1"
	SRC_DIR_DIR="$(dirname "$SRC_DIR")"
	SNAPSHOT_DIR="${SRC_DIR_DIR:${#6}}"
}

cd "$2"
SRC_DIR="$1"
SRC_DIR_BASE="$(basename "$SRC_DIR")"
src_from_df `df -P "$SRC_DIR" | tail -1`
LVM_GROUP="$(echo `lvs --noheadings -o vg_name "$SRC_DEV"`)"
SNAPSHOT_MOUNT="$EVOTE_MOUNT_DIR/$EVOTE_SNAPSHOT_NAME-$LVM_GROUP"

if [ -z "$LVM_GROUP" ]; then
	echo "Could not determine LVM group for path $SRC_DIR" >&2
	exit 1
fi


lvm_cleanup() {
	umount "$SNAPSHOT_MOUNT" || echo "Cannot unmount $SNAPSHOT_MOUNT"
	lvremove -f "/dev/$LVM_GROUP/$EVOTE_SNAPSHOT_NAME"
}

umask $UMASK

# try to unmount mount point
mkdir -p "$SNAPSHOT_MOUNT"
while umount "$SNAPSHOT_MOUNT" 2>/dev/null; do
	true
done

# get available volume group space
FREE_SPACE="$(vgdisplay -c "$LVM_GROUP" | awk -F : '{print $16}')"
if [ "$FREE_SPACE" -lt 32 ]; then
	echo "Not enough snapshot space (available $FREE_SPACE extents)"
	exit 1
fi

sync

BACKUP_PREFIX="evote-$SRC_DIR_BASE-$(date +%Y%m%d%-H%M%S)"

# create snapshot volume
lvcreate -l "$FREE_SPACE" -s -p r -n "$EVOTE_SNAPSHOT_NAME" "$SRC_DEV"

trap lvm_cleanup ERR EXIT

# copy the data
mount -o ro "/dev/$LVM_GROUP/$EVOTE_SNAPSHOT_NAME" "$SNAPSHOT_MOUNT"
tar --exclude-from "$NOBACKUP" -C "$SNAPSHOT_MOUNT/$SNAPSHOT_DIR" -cz "$SRC_DIR_BASE" | \
	split -b "$DVD_CHUNK_SIZE" -d - "$BACKUP_PREFIX"
