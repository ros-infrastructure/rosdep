Pip installation after PEP 668
==============================

`PEP-668`_ introduced `externally managed environments <externally-managed-environments>`_ to Python packaging.

rosdep is designed to use pip as an alternative system package manager, rosdep installation of pip packages requires installing packages globally as root.
Starting with Python 3.11, `PEP-668`_ compliance requires you to allow pip to install alongside externally managed packages using the ``break-system-packages`` option.

There are multiple ways to configure pip so that rosdep will succeed.


Configure using environment variable
------------------------------------

This is the way that we recommend configuring pip for rosdep usage.
We recommend configuring pip using the system environment.
Setting environment variables in your login profile, ``PIP_BREAK_SYSTEM_PACKAGES`` in your environment.
The value of the environment variable can be any of ``1``, ``yes``, or ``true``.
The string values are not case sensitive.

rosdep is designed to use ``sudo`` in order to gain root privileges for installation when not run as root.
If your system's sudo configuration prohibits the passing of environment variables use the :ref:`pip.conf <configure-using-pip.conf>` method below.


.. _configure-using-pip.conf:

Configure using pip.conf
------------------------

`Pip configuration files <pip-configuration>`_ can be used to set the desired behavior.
Pip checks for global configuration files in ``XDG_CONFIG_DIRS``, as well as ``/etc/pip.conf``.
For details on ``XDG_CONFIG_DIRS`` refer to the `XDG base directories specification <xdg-base-dirs>`_.
If you're unsure which configuration file is in use by your system, ``/etc/pip.conf`` seems like the most generic.

.. code-block:: ini

   [install]
   break-system-packages = true


.. warning:: Creating a pip.conf in your user account's ``XDG_CONFIG_HOME`` (e.g. ``~/.config/pip/pip.conf``) does not appear to be sufficent when installing packages globally.


Configuring for CI setup
------------------------

Either environment variables or configuration files can be used with your CI system.
Which one you choose will depend on how your CI environment is configured.
Perhaps the most straightforward will be to set the environent variable in the shell or script execution context before invoking ``rosdep``.

.. code-block:: bash

   sudo rosdep init
   rosdep update
   PIP_BREAK_SYSTEM_PACKAGES=1 rosdep install -r rolling --from-paths src/

If ``rosdep`` is invoked by internal processes in your CI and you need to set the configuration without having direct control over how ``rosdep install`` is run, setting the environment variable globally would also work.

.. code-block:: bash

   export PIP_BREAK_SYSTEM_PACKAGES=1
   ./path/to/ci-script.sh


If you cannot set environment variables but you can create configuration files, you can set ``/etc/pip.conf`` with the necessary configuration.

.. code-block:: bash

   printf "[install]\nbreak-system-packages = true\n" | sudo tee -a /etc/pip.conf

.. _PEP-668: https://peps.python.org/pep-0668/
.. _pip-configuration: https://pip.pypa.io/en/stable/topics/configuration/
.. _externally-managed-environments: https://packaging.python.org/en/latest/specifications/externally-managed-environments/
.. _xdg-base-dirs: https://specifications.freedesktop.org/basedir-spec/latest/
