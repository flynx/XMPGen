This script uses the directory tree topology to rate images and 
stores the resulting ratings in .XMP sidecar files.



Here is a simple example given for a Nikon camera, same will apply to 
any other make:

We start with a simple directory tree, as it comes from the flash card::

  DCIM/
  |  232ND700/
  |  |  DSC_0001.NEF
  |  |  DSC_0002.NEF
  |  |  DSC_0003.NEF
  |  |  DSC_0004.NEF
  |  |  DSC_0005.NEF
  |  |  DSC_0006.NEF
  |  |  ...
     

Then we create a set of previews::

  DCIM/
  |  232ND700/
  |  |  *preview (RAW)/*
  |  |  |  DSC_0001.jpg
  |  |  |  DSC_0002.jpg
  |  |  |  DSC_0003.jpg
  |  |  |  DSC_0004.jpg
  |  |  |  DSC_0005.jpg
  |  |  |  DSC_0006.jpg
  |  |  \  ...
  |  |  DSC_0001.NEF
  |  |  DSC_0002.NEF
  |  |  DSC_0003.NEF
  |  |  DSC_0004.NEF
  |  |  DSC_0005.NEF
  |  |  DSC_0006.NEF
  |  |  ...
     

Next we select the best images on each level...
This can be done trivially with any image viewer or file manager that 
supports copying files::

  DCIM/
  |  232ND700/
  |  |  preview (RAW)/
  |  |  |  *fav/*
  |  |  |  |  *fav/*
  |  |  |  |  |  *DSC_0002.jpg*
  |  |  |  |  \  *DSC_0004.jpg*
  |  |  |  |  *DSC_0001.jpg*
  |  |  |  |  *DSC_0002.jpg*
  |  |  |  |  *DSC_0004.jpg*
  |  |  |  \  *DSC_0006.jpg*
  |  |  |  DSC_0001.jpg
  |  |  |  DSC_0002.jpg
  |  |  \  ...
  |  |  DSC_0001.NEF
  |  |  DSC_0002.NEF
  |  |  ...


It would be logical to convert this topology into ratings, the deepest 
files having the top rating::

  DCIM/
  |  232ND700/
  |  |  preview (RAW)/
  |  |  |  fav/
  |  |  |  |  fav/
  |  |  |  |  |  DSC_0002.jpg  - - - 5*
  |  |  |  |  \  DSC_0004.jpg  - - - 5*
  |  |  |  |  DSC_0001.jpg - - - - - 4*
  |  |  |  |  DSC_0002.jpg - - - - - 4*
  |  |  |  |  DSC_0003.jpg - - - - - 4*
  |  |  |  \  DSC_0004.jpg - - - - - 4*
  |  |  |  DSC_0001.jpg
  |  |  |  DSC_0002.jpg
  |  |  \  ...
  |  |  DSC_0001.NEF
  |  |  DSC_0002.NEF
  |  |  ...


Now, we would like this information to be stored in a way that can be 
used by other software in a non-destructive manner. the best way to do 
this is .XMP sidecar files stored in the same location as the 
corresponding RAW files (.NEFs in this case).

So here is the simplest way to do this::

  $ cd DCIM
  $ xmpgen

``xmpgen`` will automatically find both input -- where the rated 
proviews are located -- and output -- where to write the .XMPs -- 
directories. Both input and output locations can be spread into 
multiple locations.

NOTE:
  it is not *yet* possible to make this do it's job over a large 
  archive containing files with duplicate names in different locations.

The above will generate the needed data as follows::

  DCIM/
  |  232ND700/
  |  |  preview (RAW)/
  |  |  |  fav/
  |  |  |  |  fav/
  |  |  |  |  |  DSC_0002.jpg
  |  |  |  |  \  DSC_0004.jpg
  |  |  |  |  DSC_0001.jpg
  |  |  |  |  DSC_0002.jpg
  |  |  |  |  DSC_0004.jpg
  |  |  |  \  DSC_0006.jpg
  |  |  |  DSC_0001.jpg
  |  |  |  DSC_0002.jpg
  |  |  \  ...
  |  |  DSC_0001.NEF
  |  |  *DSC_0001.XMP*
  |  |  DSC_0002.NEF
  |  |  *DSC_0002.XMP*
  |  |  ...


For more control one can specify all the data on the command line for 
the same effect as the above::

  $ xmpgen --root=DCIM --input="preview (RAW)" --output=232ND700 --raw-extension=.NEF --traverse-dir-name=fav --no-search-output



---------

The data the script uses and its behavior is fully configurable.

Here is the current command-line reference::

  Usage: xmpgen.py [options]

  Options:
    --version             show program's version number and exit
    -h, --help            show this help message and exit
    --root=ROOT           root of the directory tree we will be working at
                          (default: ".").
    --input=INPUT         name of directory containing previews (default:
                          "preview (RAW)"). NOTE: this directory tree can not be
                          used for OUTPUT.
    --output=OUTPUT       name of directory to store .XMP files. if --no-search
                          is not set this is where we search for relevant files
                          (default: ROOT).
    -v, --verbose         increase output verbosity.
    -q, --quiet           decrease output verbosity.
    -m, --mute            mute output.

    Advanced options:
      --rate-top-level    if set, also rate top level previews.
      --no-search-input   if set, this will disable searching for input
                          directories, otherwise ROOT/INPUT will be used
                          directly. NOTE: this will find all matching INPUT
                          directories, including nested ones.
      --no-search-output  if set, this will disable searching for RAW files, and
                          XMPs will be stored directly in the OUTPUT directory.
      --group-threshold=THRESHOLD
                          percentage of elements unique to a level below which
                          the level will be merged with the next one (default:
                          "5").
      --traverse-dir-name=TRAVERSE_DIR
                          directory used to traverse to next level (default:
                          "fav").
      --raw-extension=RAW_EXTENSION
                          use as the extension for RAW files (default: ".NEF").
      --xmp-template=XMP_TEMPLATE
                          use XMP_TEMPLATE instead of the internal template.
      --use-labels        if set, use both labels and ratings.

    Runtime options:
      --dry-run           run but do not create any files.

    Configuration options:
      --config-print      print current configuration and exit.
      --config-defaults-print
                          print default configuration and exit.



NOTE: this may get out of date, so use ``--help`` to get the actual info.

---------

NOTE: to generate a config file just do this::

  xmpgen --config-print > ~/.xmpgen

this can also be combined with options, these will be saved to generated config file::

  xmpgen --raw-extension=.CRW --traverse-dir-name=select --input="RAW previews" --config-print > ~/.xmpgen


NOTE: order of flags does not matter.


NOTE: the ``--search-input`` option is not on by default because of a 
current bug (see TODO.otl), as soon as that gets resolved this 
option will be set by default.

