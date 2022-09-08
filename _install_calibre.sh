# -------------------------------------------------------
# Install script for calibre
# -------------------------------------------------------

bin_folder='cache/calibre'
mkdir -p "$bin_folder"
bin_file="calibre-x86_64.txz"
sig_file="calibre-x86_64.txz.sha512"

if [ -f "${bin_folder}/${bin_file}" ]; then
  echo "Cached $bin_file exists."
else
  echo "Cached $bin_file does not exist."
  rm -rf "${bin_folder}/calibre-*"
  latest_version=`curl -L --retry 2 --silent 'http://code.calibre-ebook.com/latest'` && \
  dl_url="https://download.calibre-ebook.com/${latest_version}/calibre-${latest_version}-x86_64.txz" && \
  sig_url="https://code.calibre-ebook.com/signatures/calibre-${latest_version}-x86_64.txz.sha512"
  echo "Downloading sig $sig_url ..." && \
  curl -L --retry 2 --show-error --silent --insecure --output "${bin_folder}/${sig_file}" "$sig_url" && \
  echo "Downloading bin $dl_url ..." && \
  curl -L --retry 2 --show-error --silent --output "${bin_folder}/${bin_file}.part" "$dl_url" && \
  echo "$(cat "${bin_folder}/${sig_file}")  ${bin_folder}/${bin_file}.part" | sha512sum --check --status && \
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
