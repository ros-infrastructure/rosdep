rosdep sources list
===================

The :command:`rosdep` command-line tool is similar to other tools like
:command:`apt` that use a *sources list* to update a local index.

``etc/ros/rosdep/sources.list.d``
---------------------------------

rosdep processes the file in this directory, sorted by filename in
ascending order.  Precedence is assigned to the files in the order
they are processed, with the first file having the highest
precendence.

Each file has a format::

    <type> <URL> [tags]

For example::

    yaml http://foo.bar/rosdep.yaml ubuntu lucid fuerte


``type``

    Type must be ``yaml``.  In the future, more types may be supported.
           
``URL``

    URL should point to the HTTP location of a rosdep YAML file. URL
    must contain an scheme (e.g. ``http://``), hostname, and path.

``tags``

    Tags are optional.  Currently, the OS name (e.g. ``ubuntu``), OS
    codename (e.g. ``lucid``), and ROS distribution codename
    (e.g. ``fuerte``) are supported.  These tags are all lower-case.

The tags constrain the configurations that the source will be loaded
on. *All* tags must match the current configuration for the source to
be considered valid.  In the example above, the source will only be
valid for the ROS Fuerte distribution on an Ubuntu Lucid platform.
    
Developer notes
---------------

The cached data is written to ``<ros-home>/rosdep/sources.cache``.
The contents of ``URL`` are written to ``sha1(URL)``.  These contents
are indexed by the file ``sources.cache/index``.  The format of this
index is similar to the normal sources list format, except the URL is
replaced with the relative filename of the downloaded rosdep data
(i.e. ``sha1(URL)``).

rosdep always reads from this cache, except when processing the
``update`` command.
