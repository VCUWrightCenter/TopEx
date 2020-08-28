# Exclude notebooks prefixed with underscore
nbdev_build_lib --fname=[!_]*.ipynb
nbdev_build_docs --fname=[!_]*.ipynb
# nbdev_test_nbs --fname=[!_]*.ipynb
# make docs_serve