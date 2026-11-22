#!/usr/bin/env bash
# Install the Scribus engine for the sla tools. Safe to re-run (finishes in seconds when done).
#   bash setup.sh [VERSION]      VERSION: 1.6.3 (default) | 1.6.5 | 1.6.1 | native
# The engine is the real Scribus, in its own Ubuntu root under /opt (so the host keeps its
# own libraries). "native" installs the host distribution's scribus package instead.
set -euo pipefail
WANT=${1:-${SLA_SCRIBUS_VERSION:-1.6.3}}
HERE=$(dirname "$(realpath "$0")")
export DEBIAN_FRONTEND=noninteractive
say() { echo "[sla-setup] $*"; }

smoke() {  # export a one-page document and check a PDF comes out
  local t; t=$(mktemp -d /tmp/sla-smoke.XXXX)
  cat >"$t/s.py" <<PY
import scribus, os
try:
    scribus.newDocument(scribus.PAPER_A4, (20, 20, 20, 20), scribus.PORTRAIT, 1, scribus.UNIT_POINTS, scribus.PAGE_1, 0, 1)
    scribus.setText("ok", scribus.createText(50, 50, 200, 50))
    p = scribus.PDFfile(); p.file = "$t/s.pdf"; p.save()
    open("$t/v", "w").write(scribus.scribus_version if hasattr(scribus, "scribus_version") else "")
finally:
    os._exit(0)
PY
  "$HERE/sla-engine" "$t/s.py" >/dev/null 2>&1 || true
  [ -s "$t/s.pdf" ] && pdfinfo "$t/s.pdf" 2>/dev/null | grep -q "Creator: *Scribus"
}
creator_version() { local t; t=$(ls -t /tmp/sla-smoke.*/s.pdf 2>/dev/null | head -1); pdfinfo "$t" 2>/dev/null | sed -n 's/^Creator: *Scribus *//p'; }

if [ -f /opt/sla/engine.env ] && grep -q "^WANT=$WANT$" /opt/sla/engine.env && smoke; then
  for t in sla sla-compare sla-engine; do ln -sf "$HERE/$t" /usr/local/bin/$t 2>/dev/null || true; done
  say "engine already installed: $("$HERE/sla-engine" --info)"; exit 0
fi

[ "$(id -u)" = 0 ] || { echo "setup.sh needs root" >&2; exit 1; }
say "installing host tools"
apt-get update -q >/dev/null 2>&1 || true
apt-get install -y -q --no-install-recommends xvfb xauth poppler-utils mmdebstrap fontconfig >/dev/null
python3 -c "import numpy, PIL" 2>/dev/null || pip install -q --break-system-packages numpy pillow 2>/dev/null || apt-get install -y -q python3-numpy python3-pil >/dev/null
mkdir -p /opt/sla/home/prefs /opt/sla/fonts

native() {
  say "installing the distribution's scribus package"
  apt-get install -y -q --no-install-recommends scribus fonts-dejavu fonts-lmodern fonts-liberation2 >/dev/null
  mkdir -p /usr/local/share/fonts && ln -sfn /opt/sla/fonts /usr/local/share/fonts/sla
  printf 'WANT=%s\nMODE=native\nROOT=\nSCRIBUS=/usr/bin/scribus\n' "$WANT" >/opt/sla/engine.env
}
chroot_engine() {  # $1 = version, rest = Ubuntu suites that ship it
  local ver=$1 root=/opt/scribus-root-$1 suite mirror; shift
  chroot / /bin/true 2>/dev/null || return 1
  if [ -x "$root/usr/bin/scribus" ]; then   # built earlier: reuse
    printf 'WANT=%s\nMODE=chroot\nROOT=%s\nSCRIBUS=/usr/bin/scribus\n' "$WANT" "$root" >/opt/sla/engine.env
    return 0
  fi
  if findmnt -rn -o TARGET | grep -q "^$root/"; then   # never delete through a bind mount
    for m in $(findmnt -rn -o TARGET | grep "^$root/" | sort -r); do umount -l "$m" 2>/dev/null || true; done
    findmnt -rn -o TARGET | grep -q "^$root/" && { say "mounts remain under $root, not touching it"; return 1; }
  fi
  for suite in "$@"; do
    for mirror in http://archive.ubuntu.com/ubuntu http://old-releases.ubuntu.com/ubuntu; do
      curl -sfI "$mirror/dists/$suite/Release" >/dev/null 2>&1 || continue
      say "building Scribus $ver root from Ubuntu $suite (2-4 minutes)"
      rm -rf --one-file-system "$root"
      if mmdebstrap --variant=minbase --components=main,universe \
           --include=scribus,xvfb,xauth,fontconfig,fonts-dejavu,fonts-lmodern,fonts-liberation2,fonts-urw-base35,ca-certificates \
           --aptopt='APT::Install-Recommends "false"' "$suite" "$root" "$mirror" >/tmp/sla-mmdebstrap.log 2>&1; then
        mkdir -p "$root/usr/local/share/fonts" && ln -sfn /opt/sla/fonts "$root/usr/local/share/fonts/sla"
        printf 'WANT=%s\nMODE=chroot\nROOT=%s\nSCRIBUS=/usr/bin/scribus\n' "$WANT" "$root" >/opt/sla/engine.env
        return 0
      fi
      say "could not build from $suite at $mirror (see /tmp/sla-mmdebstrap.log)"
    done
  done
  return 1
}

case "$WANT" in
  native) native ;;
  1.6.1)  chroot_engine 1.6.1 noble || native ;;
  1.6.3)  chroot_engine 1.6.3 questing plucky || { say "WARNING: could not build a 1.6.3 engine, falling back to the distribution package"; native; } ;;
  1.6.5)  chroot_engine 1.6.5 resolute || { say "WARNING: could not build a 1.6.5 engine, falling back to the distribution package"; native; } ;;
  *) echo "unknown version $WANT (use 1.6.3, 1.6.5, 1.6.1 or native)" >&2; exit 1 ;;
esac

smoke || { echo "[sla-setup] the engine did not produce a PDF - setup failed" >&2; exit 1; }
GOT=$(creator_version)
echo "VERSION=$GOT" >>/opt/sla/engine.env
for t in sla sla-compare sla-engine; do ln -sf "$HERE/$t" /usr/local/bin/$t; done
[ "$WANT" = native ] || [ "$GOT" = "$WANT" ] || say "WARNING: wanted Scribus $WANT but the engine is $GOT. Files it saves carry version $GOT."
say "ready: $("$HERE/sla-engine" --info)"
