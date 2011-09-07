This script uses the directory tree topology data to rate files and 
stores the resulting data in .XMP sidecar files.



Here is an example a simple example given for a Nikon camera, same will
apply to any other make:

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


It would be convert this topology into ratings, the deepest files 
having the top rating::

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
  $ xmpgen --search-input


This will generate the needed data as follows::

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



---

NOTE: the naming is configurable, just see xmpgen --help.

NOTE: the --search-input potion is not on by default because of a 
current bug (see TODO.otl), as soon as that gets resolved this 
option will be set by default.
