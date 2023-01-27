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
  # also support *.recipe files as is in Calibre
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
&& npx babel static/site.js --out-file static/site.compiled.js \
&& sass -s compressed --no-source-map static/site.scss static/site.css \
&& sass -s compressed --no-source-map static/reader.scss public/reader.css \
&& sass -s compressed --no-source-map static/viewer-theme.scss public/viewer-theme.css \
&& cp -p static/reader.html public/ \
&& python3 _generate.py "$CI_PAGES_URL" "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY/" "$GITHUB_SHA" \
&& html-minifier-terser --input-dir public/ --output-dir public/ --minify-js --collapse-whitespace --file-ext html \
&& rm -f *.recipe static/site.compiled.js
