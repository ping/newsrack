# -------------------------------------------------------
# Install script for calibre
# -------------------------------------------------------

bin_folder="$GITHUB_WORKSPACE/cache/calibre"
mkdir -p "$bin_folder"
platform='x86_64'
bin_file="calibre-${platform}.txz"
sig_file="calibre-${platform}.txz.sha512"

if [ -f "${bin_folder}/${bin_file}" ]; then
  echo "Cached $bin_file exists."
else
  echo "Cached $bin_file does not exist."
  rm -rf "${bin_folder}/calibre-*"
  tag="$(curl -L --retry 3 --show-error --silent --fail 'https://api.github.com/repos/kovidgoyal/calibre/releases/latest' | jq -r .tag_name)" && \
  latest_version="${tag#*v}" && \
  echo "Latest version: ${latest_version}" && \
  dl_url="https://github.com/kovidgoyal/calibre/releases/download/${tag}/calibre-${latest_version}-${platform}.txz" && \
  sig_url="https://calibre-ebook.com/signatures/calibre-${latest_version}-${platform}.txz.sha512" && \
  sig2_url="https://code.calibre-ebook.com/signatures/calibre-${latest_version}-${platform}.txz.sha512" && \
  { echo "Downloading sig $sig_url ..." && curl -L --retry 3 --show-error --silent --fail --output "${bin_folder}/${sig_file}" "$sig_url" || \
    echo "Downloading sig $sig2_url ..." && curl -L --retry 3 --show-error --insecure --fail --silent --output "${bin_folder}/${sig_file}" "$sig2_url"; } && \
  echo "Downloading bin $dl_url ..."
  curl -L --retry 3 --show-error --silent --fail --output "${bin_folder}/${bin_file}.part" "$dl_url" && \
  echo "$(cat "${bin_folder}/${sig_file}")  ${bin_folder}/${bin_file}.part" | sha512sum --check --status && \
  mv "${bin_folder}/${bin_file}.part" "${bin_folder}/${bin_file}"
fi

if [ -f "${bin_folder}/${bin_file}" ]; then
  echo "Install from local..."
  mkdir -p "$HOME/calibre-bin/calibre" && \
  tar xf "${bin_folder}/${bin_file}" -C "$HOME/calibre-bin/calibre" && \
  "$HOME/calibre-bin/calibre/calibre_postinstall" && \
  export PATH=$PATH:$HOME/calibre-bin/calibre && \
  calibre --version && \
  echo "$HOME/calibre-bin/calibre" >> $GITHUB_PATH
fi

calibre --version || {
  echo "Install latest from calibre servers..."
  mkdir -p ~/calibre-bin
  wget --tries=3 --timeout=30 -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin install_dir=~/calibre-bin isolated=y
  export PATH=$PATH:$HOME/calibre-bin/calibre
  calibre --version
  echo "$HOME/calibre-bin/calibre" >> $GITHUB_PATH
}
