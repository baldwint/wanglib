Improved interactive plotting with :mod:`wanglib.pylab_extensions`
==================================================================

.. automodule:: wanglib.pylab_extensions

Plotting while acquiring data
+++++++++++++++++++++++++++++

To plot while acquiring data, you will need to implement your data
gathering using Python generators_. A generator is like a Python
function that, rather than returning data all at once (with the
``return`` statement), returns it point by point (with the ``yield``
statement).

.. _generators: http://wiki.python.org/moin/Generators

Suppose we have a ``spex`` spectrometer object, and a
``lockin`` object that we are using to detect the signal at
the output slit of the spectrometer. Here is an example of a
generator we might use to scan a spectrum, while yielding
values along the way:

.. code-block:: python

    def scan_wls(wls):
        for wl in wls:
            spex.set_wl(wl)
            sleep(0.1)
            val = lockin.get_x()
            yield wl, val

.. note :: This pattern is so common that a shorthand is provided for it in :func:`wanglib.util.scanner`.

Then, if we wanted to scan from 800nm to 810nm, we would do

.. code-block:: python

    scan = scan_wls(numpy.arange(800, 810, 0.1))
    for x,y in scan:
        print x,y

This will print the data to STDOUT, but we could also:

 - save it to a python list using `list comprehensions`_
 - save it as a numpy object using :func:`numpy.fromiter`
 - plot it progressively using :func:`wanglib.pylab_extensions.live_plot.plotgen`

.. _`list comprehensions`: http://docs.python.org/tutorial/datastructures.html#list-comprehensions

The ``plotgen`` function reads from your generator, plotting data as
it goes along. In the case of our ``scan_wls`` example above, we can
view the spectrum as it gets collected:

.. code-block:: python

    wls = arange(800, 810, 0.1))
    plotgen(scan_wls(wls))
    # ... measures data, plotting as it goes along ...

After your generator yields its last value, it will return the
complete array of measured X and Y values. Sometimes we want to do
extra things with that:

.. code-block:: python

    _,ref = plotgen(scan_wls(wls))   # measure reference spectrum and plot it
    _,trn = plotgen(scan_wls(wls))   # measure transmission spectrum and plot it
    plot(wls, log(ref/trn), 'k--')   # plot absorption spectrum

Additionally, ``plotgen`` can generate multiple lines. Say we wanted
to plot both the X and the Y quadrature from our lockin. We'd write
our generator like:

.. code-block:: python

    def scan_wls(wls):
        for wl in wls:
            spex.set_wl(wl)
            sleep(0.1)
            x = lockin.get_x()
            y = lockin.get_y()
            yield wl, x, wl, y

This is the same as before, but we're yielding two X,Y pairs: one with
the X quadrature ``(wl, x)`` and one with the Y quadrature ``(wl, y)``.
``plotgen`` recognizes this and plots two lines:

.. code-block:: python

    _,x,_,y = plotgen(scan_wls(wls))

By default, ``plotgen`` plots these on the same axes, but sometimes
that doesn't make sense. For example, if we're measuring the signal
magnitude (in Volts) and phase (in degrees), then those two units have
nothing to do with each other, and we should plot them on separate
axes.

.. code-block:: python

    def scan_wls(wls):
        for wl in wls:
            spex.set_wl(wl)
            sleep(0.1)
            r = lockin.get_r()
            p = lockin.get_phase()
            yield wl, r, wl, p

    # create two axes and pass them to plotgen explicitly
    ax1 = pylab.subplot(211)
    ax2 = pylab.subplot(212)
    plotgen(scan_wls(wls), ax=(ax1,ax2))

Finally, you can limit the length of the plotted lines using the
``maxlen`` parameter. This is useful for generators which yield
infinitely - such as monitoring the last five minutes of a signal.

.. code-block:: python

    def monitor_signal():
        start = time()
        while True:
            yield time() - start, lockin.get_phase()
            sleep(0.1)

.. note :: This pattern is so common that a shorthand is provided for it in :func:`wanglib.util.monitor`.

This will yield about 10 points per second forever. To cut it short
after about 5 minutes of data, try this:

.. code-block:: python

    plotgen(monitor_signal(), maxlen=10*60*5)

Full documentation for ``plotgen``:

.. autofunction:: wanglib.pylab_extensions.live_plot.plotgen


Saving/clearing traces
++++++++++++++++++++++

.. automodule:: wanglib.pylab_extensions.misc
    :members:
    :undoc-members:


Density plots
+++++++++++++

.. automodule:: wanglib.pylab_extensions.density
    :members:
    :undoc-members:


