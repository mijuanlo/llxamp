xgettext -L Python --keyword --keyword=_ -o gui/locale/llxamp-gui.pot gui/llxamp-gui
find gui -name '*.po' -exec msgmerge --update {} gui/locale/llxamp-gui.pot \; > /dev/null 2>&1
