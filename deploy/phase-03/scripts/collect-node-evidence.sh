#!/usr/bin/env bash
set -euo pipefail

section() {
  printf '\n## %s\n' "$1"
}

section identity
printf 'collected_at_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'hostname=%s\n' "$(hostname)"
if [[ -r /sys/class/dmi/id/product_uuid ]]; then
  product_uuid="$(cat /sys/class/dmi/id/product_uuid)"
elif product_uuid="$(sudo -n cat /sys/class/dmi/id/product_uuid 2>/dev/null)"; then
  :
else
  product_uuid="UNAVAILABLE_REQUIRES_SUDO"
fi
printf 'product_uuid=%s\n' "$(printf '%s' "$product_uuid" | tr '[:lower:]' '[:upper:]')"

section os
cat /etc/os-release
uname -a

section cpu
lscpu

section memory
free -h

section disks
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL

section network
ip -brief address
ip route
for interface in /sys/class/net/*; do
  name="${interface##*/}"
  [[ "$name" == "lo" ]] && continue
  printf '%s=%s\n' "$name" "$(cat "$interface/address")"
done

section time
timedatectl status
chronyc tracking
chronyc sources -v

section services
systemctl is-enabled containerd kubelet chrony
systemctl is-active containerd kubelet chrony

section runtime
containerd --version
kubeadm version -o short
kubelet --version

section persistence
printf 'swap_entries=%s\n' "$(swapon --noheadings | wc -l)"
sysctl net.ipv4.ip_forward net.bridge.bridge-nf-call-iptables net.bridge.bridge-nf-call-ip6tables
grep -R --no-filename -E 'SystemdCgroup|disabled_plugins' /etc/containerd/config.toml || true
