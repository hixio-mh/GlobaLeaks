#!/bin/bash
CWD=`pwd`
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPTNAME="$(basename "$(test -L "$0" && readlink "$0" || echo "$0")")"
GLBACKEND_GIT_REPO="https://github.com/globaleaks/GLBackend.git"
GLOBALEAKS_DIR=~/
OUTPUT_DIR=/data/website/builds/

if [ "$1" = "-h" ]; then
  echo "Usage: ./${SCRIPTNAME} [glbackend target tag]"
  echo "repository path: is the path to a copy of the GLClient and GLBackend git repositories"
  exit
fi

GLBACKEND_TAG=$1

mkdir $OUTPUT_DIR/GLBackend

if [ ! -d ${GLOBALEAKS_DIR}/GLBackend ]; then
  echo "[+] Cloning GLBackend in ${GLOBALEAKS_DIR}"
  git clone $GLBACKEND_GIT_REPO ${GLOBALEAKS_DIR}/GLBackend
fi

build_glbackend()
{
  echo "[+] Updating GLBackend"
  cd ${GLOBALEAKS_DIR}/GLBackend
  git pull origin master
  GLBACKEND_REVISION=`git rev-parse HEAD | cut -c 1-8`

  if test $GLBACKEND_TAG; then
    git checkout $GLBACKEND_TAG
    $GLBACKEND_REVISION=$GLBACKEND_TAG
  fi

  echo "[+] Building GLBackend"
  cd ${GLOBALEAKS_DIR}/GLBackend
  POSTINST=${GLOBALEAKS_DIR}/GLBackend/debian/postinst
  echo "/etc/init.d/globaleaks start" >> $POSTINST
  echo "# generated by your friendly globaleaks build bot :)" >> $POSTINST
  python setup.py sdist
  echo "[+] Building .deb"

  cd dist
  py2dsc globaleaks-*.tar.gz
  cd deb_dist/globaleaks-*
  rm -rf debian/
  cp -rf ${GLOBALEAKS_DIR}/GLBackend/debian debian
  debuild
  cd ..
  echo "[+] Adding to local repository"
  dput local globaleaks*changes
  mini-dinstall --batch
  cd $CWD

  echo "[+] Signing Release"
  $DIR/sign-release.sh
  rm -rf ${GLOBALEAKS_DIR}/GLBackend/dist
}

build_glbackend

echo "[+] All done!"

