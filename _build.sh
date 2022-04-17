sh _prebuild.sh
mkdir -p public \
&& cp -p static/favicon.svg public/ \
&& sass -s compressed --no-source-map static/site.scss static/site.css \
&& python3 _generate.py \
&& html-minifier-terser --input-dir public/ --output-dir public/ --minify-js --collapse-whitespace --file-ext html \
&& rm *.recipe
