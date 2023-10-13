for recipe_folder in 'recipes' 'recipes_custom'
do
  # copy recipe_folder/*.recipe.py files to *.recipe
  if [ -n "$(ls -A "${recipe_folder}"/*.recipe.py 2>/dev/null)" ]
  then
    for f in "$recipe_folder"/*.recipe.py; do
        b="$(basename -- $f)"
        cp -p "$f" "${b%.py}"
    done
  fi
  # also support *.recipe files as is in calibre
  # copy recipe_folder/*.recipe files to *.recipe
  if [ -n "$(ls -A "${recipe_folder}"/*.recipe 2>/dev/null)" ]
  then
    for f in "$recipe_folder"/*.recipe; do
        b="$(basename -- $f)"
        cp -p "$f" "$b"
    done
  fi
done

mkdir -p public meta \
&& cp -p static/*.svg public/ \
&& cp -p static/opds.xsl public/ \
&& npx babel static/site.js --out-file static/site.compiled.js \
&& npx babel static/reader.js --out-file static/reader.compiled.js \
&& npx babel static/theme.js --out-file static/theme.compiled.js \
&& cp -p static/theme.compiled.js public/theme.min.js \
&& npx sass -s compressed --no-source-map static/site.scss:static/site.css static/reader.scss:static/reader.css static/viewer-theme-light.scss:public/viewer-theme-light.css static/viewer-theme-dark.scss:public/viewer-theme-dark.css static/opds.scss:public/opds.css \
&& python3 _generate.py "$CI_PAGES_URL" "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY/" "$GITHUB_SHA" "https://github.com/${GITHUB_REPOSITORY}/commit/${GITHUB_SHA}" "${GITHUB_RUN_ID}" "https://github.com/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}" \
&& node build-index.js < public/lunr_docs.json > public/lunr.json \
&& npx html-minifier-terser --input-dir public/ --output-dir public/ --collapse-whitespace --file-ext html \
&& rm -f *.recipe static/*.compiled.js public/lunr_docs.json
