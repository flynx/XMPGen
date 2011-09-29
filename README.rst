======
XMPGen
======

This script uses the directory tree topology to rate images and 
stores the resulting ratings in .XMP sidecar files.


.. contents::


General Description
===================

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
previews are located -- and output -- where to write the .XMPs -- 
directories. Both input and output locations can be spread into 
multiple locations.

.. NOTE:: 
   It is not *yet* possible to make this do it's job over a large 
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

  $ xmpgen --root=DCIM --input="preview (RAW)" --output=232ND700 --raw-extension=.NEF --traverse-dir-name=fav --no-search-output --no-search-input


Complex Situations
------------------

In some cases ``XMPGen`` needs to do some more work than is obvoius:

#. **There are multiple occurrences of RAW files with the same name in a 
   directory tree.**

   Here, we will determine which file is the target by closeness to the preview 
   in the topology. 
   The criteria used to judge distance are as follows:
  
   * Depth/size of sub-tree.  
     A tree at a deeper location (smaller) beats the more general (larger)
     sub-tree. e.g. max length of identical path section starting from 
     root wins::
  
             A
            / \          Path AB is closer to AB(T) than A (obvious)
           /   B
          /   / \        Path ABD is closer to AB(T) than AC
         C   D  (T)
  
   * Within a minimal sub-tree the shortest distance to sub-tree root wins::
  
            A
           /|\
          / | \
         B  C (T)        Path AB is closer to T than ACD         
            |
            D
  
   This situation can occur if we are processing a large archive all at once,
   there, preview directories usually are in the same sub-tree as their 
   corresponding RAW files.
  
   If there are two or more target files at the same topological distance 
   from the preview we will fail.

   .. NOTE::
      There could be topologies that will make this fail or do the wrong 
      thing, please submit an issue or mail me if this is your case.
  
#. **There are more preview levels than there are ratings and labels.**

   By default the first *N-1* levels are rated and the rest merged into one, 
   where *N* is the number of ratings and labels.
   there are several strategies supported:
  
   * *merge-bottom*, described above.
  
   * *skip-bottom* - levels *N* through *M* are not rated, here *M* is the 
     number of levels.
  
   * *abort* - rate until we reach the end of the ratings, then fail.
  
   This is customizable via the ``--overflow-strategy`` option.



Control and Data
================

The data the script uses and its behavior is fully configurable.


Current command-line reference::

        Usage: xmpgen.py [options]

        Options:
          --version             show program's version number and exit
          -h, --help            show this help message and exit
          --root=PATH           root of the directory tree we will be working at
                                (default: ".").
          --input=DIR_NAME      name of directory containing previews (default:
                                "preview (RAW)"). NOTE: this directory tree can not be
                                used for output.
          --output=DIR_NAME     name of directory to store .XMP files. if --no-search
                                is not set this is where we search for relevant files
                                (default: ROOT).
          -v, --verbose         increase output verbosity.
          -q, --quiet           decrease output verbosity.
          -m, --mute            mute output.

          Ratings & Labels:
            --use-labels        if set, use both labels and ratings.
            --clear-labels      clear list of labels, shorthand to removing all the
                                labels one by one.
            --label=LABEL       add label to list of labels (default: ['Second',
                                'Review']). NOTE: the order in which labels are added
                                is significant - first is higher priority last lower.
            --remove-label=LABEL
                                remove label from list of labels (default: []).
            --rate-top-level    if set, also rate top level previews.
            --group-threshold=THRESHOLD
                                percentage of elements unique to a level below which
                                the level will be merged with the next one (default:
                                "5").
            --overflow-strategy=STRATEGY
                                the way to handle tree depth greater than the number
                                of given ratings (default: merge-bottom). available
                                options are: ('abort', 'skip-bottom', 'merge-bottom')

          Advanced options:
            --no-search-input   if set, this will disable searching for input
                                directories, otherwise ROOT/INPUT will be used
                                directly. NOTE: this will find all matching INPUT
                                directories, including nested ones.
            --no-search-output  if set, this will disable searching for RAW files, and
                                XMPs will be stored directly in the OUTPUT directory.
            -s DIR_NAME, --skip=DIR_NAME
                                list of directories to skip from searching for RAW
                                files (default: ['preview (RAW)'])
            --traverse-dir-name=DIR_NAME
                                directory used to traverse to next level (default:
                                "fav").
            --raw-extension=EXTENSION
                                use as the extension for RAW files (default: ".NEF").
            --xmp-template=PATH
                                use XMP_TEMPLATE instead of the internal template.
            --handle-existing-xmp=STRATEGY
                                the way to handle existing xmp files (default:
                                rewrite). available options are: ('abort', 'skip',
                                'rewrite')
            --skip-unknown-destinations
                                if set, skip generating .XMP files for targets that
                                can not be located. this can happen for example when
                                rating a file that was shot in JPEG or was processed
                                in cammera.

          Runtime options:
            --dry-run           run but do not create any files.

          Configuration options:
            --config-print      print current configuration and exit.
            --config-defaults-print
                                print default configuration and exit.
            --config-save-local
                                save current configuration at the root location. this
                                is a shorthand for: xmpgen ... --config-print >
                                ROOT/.xmpgen

        NOTEs: xmpgen will overwrite existing .XMP files (will be fixed soon). xmpgen
        will search for both INPUT and OUTPUT so explicit declaration is needed only
        in non-standard cases and for fine control.


The default options that can be contained in ``~/.xmpgen`` or printed by the ``--config-print`` or ``--config-print-default`` are in JSON format::

        {
            "CONFIG_SAVE_LOCAL": false,
            "HANDLE_EXISTING_XMP": "rewrite",
            "INPUT_DIR": "preview (RAW)",
            "LABELS": [
                "Second",
                "Review"
            ],
            "LABEL_CFG": ".label",
            "OUTPUT_DIR": ".",
            "OVERFLOW_STRATEGY": "merge-bottom",
            "RATE_TOP_LEVEL": false,
            "RATINGS": [
                5,
                4,
                3,
                2,
                1
            ],
            "RAW_EXTENSION": ".NEF",
            "ROOT_DIR": ".",
            "SEARCH_INPUT": true,
            "SEARCH_OUTPUT": true,
            "SKIP": [
                "preview (RAW)"
            ],
            "SKIP_UNKNOWN_DESTINATIONS": false,
            "THRESHOLD": 5,
            "TRAVERSE_DIR": "fav",
            "USE_LABELS": false,
            "VERBOSITY": 1,
            "XMP_TEMPLATE": "<x:xmpmeta xmlns:x=\"adobe:ns:meta\/\">\n\t<rdf:RDF xmlns:r
        df=\"http:\/\/www.w3.org\/1999\/02\/22-rdf-syntax-ns#\">\n\t\t<rdf:Description r
        df:about=\"\" xmlns:xap=\"http:\/\/ns.adobe.com\/xap\/1.0\/\">\n\t\t\t<xap:Creat
        orTool>XMPGen<\/xap:CreatorTool>\n\t\t\t<xap:Rating>%(rating)s<\/xap:Rating>\n\t
        \t\t<xap:Label>%(label)s<\/xap:Label>\n\t\t<\/rdf:Description>\n\t<\/rdf:RDF>\n<
        \/x:xmpmeta>"
        }


.. NOTE:: 
   The minimal config *must* contain at least a pair of curly brackets.


.. NOTE:: 
   Within the config any subset of the supported options can be included, 
   the rest will be replaced with defaults.

.. NOTE:: 
   These may get out of date, so use ``--help`` to get the actual info.


Miscellaneous Information and Notes
==================================

.. NOTE:: 
   To generate a config file just do this::

          xmpgen --config-print > ~/.xmpgen

   This can also be combined with options, these will be saved to generated config file::

          xmpgen --raw-extension=.CRW --traverse-dir-name=select --input="RAW previews" --config-print > ~/.xmpgen


.. NOTE:: 
   In general, order of flags does not matter. but order of labels given on command line is.

