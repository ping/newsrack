# -------------------------------------------------------
# Install script for calibre
# -------------------------------------------------------

bin_folder='cache/calibre'
mkdir -p "$bin_folder"
bin_file="calibre-x86_64.txz"


if [ -f "${bin_folder}/${bin_file}" ]; then
  echo "Cached $bin_file exists."
else
  echo "Cached $bin_file does not exist."
  rm -rf "${bin_folder}/calibre-*"
  latest_version=`curl --retry 2 --silent http://code.calibre-ebook.com/latest` && \
  dl_url="https://download.calibre-ebook.com/${latest_version}/calibre-${latest_version}-x86_64.txz" && \
  echo "Downloading $dl_url ..." && \
  curl "$dl_url" --retry 2 --show-error --silent --output "${bin_folder}/${bin_file}.part" && \
    mv "${bin_folder}/${bin_file}.part" "${bin_folder}/${bin_file}"
fi

if [ -f "${bin_folder}/${bin_file}" ]; then
  echo "Install from cache..."
  mkdir -p ~/calibre-bin/calibre && \
  tar xf "${bin_folder}/${bin_file}" -C ~/calibre-bin/calibre && \
  ~/calibre-bin/calibre/calibre_postinstall && \
  export PATH=$PATH:$HOME/calibre-bin/calibre && \
  calibre --version && \
  echo "$HOME/calibre-bin/calibre" >> $GITHUB_PATH
fi

calibre --version || {
  echo "Install latest from calibre servers..."
  mkdir -p ~/calibre-bin
  wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin install_dir=~/calibre-bin isolated=y
  export PATH=$PATH:$HOME/calibre-bin/calibre
  calibre --version
  echo "$HOME/calibre-bin/calibre" >> $GITHUB_PATH
}