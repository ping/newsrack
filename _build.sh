# change .recipe.py files to .recipe
for f in *.recipe.py; do
    cp -p "$f" "${f%.py}"
done

mkdir -p public cache \
&& cp -p static/*.svg public/ \
&& sass -s compressed --no-source-map static/site.scss static/site.css \
&& sass -s compressed --no-source-map static/nonkindle.scss public/nonkindle.css \
&& python3 _generate.py "$CI_PAGES_URL" \
&& html-minifier-terser --input-dir public/ --output-dir public/ --minify-js --collapse-whitespace --file-ext html \
&& rm -f *.recipe
