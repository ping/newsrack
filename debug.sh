# helper script for debuging/developing new recipes
if [ -z "$1" ];
then
    echo "No recipe specified."
    echo "Usage: sh debug.sh example"
    exit 9
fi

get_abs_dirname() {
  # $1 : relative filename
  echo "$(cd "$(dirname "$1")" && pwd)/"
}
# use to get shared code
export recipes_includes=$(get_abs_dirname "recipes/includes/recipes_shared.py")

for recipe_folder in 'recipes' 'recipes_custom'
do
    if [ -f "$recipe_folder/$1.recipe.py" ]; then
      cp -p "$recipe_folder/$1.recipe.py" "$1.recipe"
    fi
    if [ -f "$recipe_folder/$1.recipe" ]; then
      cp -p "$recipe_folder/$1.recipe" "$1.recipe"
    fi
done

rm -rf debug
ebook-convert "$1.recipe" .epub --test --debug-pipeline debug -vv && \
open debug/input/index.html

if [ -f "$1.recipe" ]; then
  rm -f "$1.recipe"
fi
