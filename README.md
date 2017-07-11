# OpenSurfaces

OpenSurfaces is a large database of annotated surfaces created from real-world
consumer photographs. Our annotation framework draws on crowdsourcing to
segment surfaces from photos, and then annotate them with rich surface
properties, including material, texture and contextual information.

Documentation is available at: http://opensurfaces.cs.cornell.edu/docs/

## Citation

If you use our code, please cite our paper:

    Sean Bell, Paul Upchurch, Noah Snavely, Kavita Bala
    OpenSurfaces: A Richly Annotated Catalog of Surface Appearance
    ACM Transactions on Graphics (SIGGRAPH 2013)

    @article{bell13opensurfaces,
		author = "Sean Bell and Paul Upchurch and Noah Snavely and Kavita Bala",
		title = "Open{S}urfaces: A Richly Annotated Catalog of Surface Appearance",
		journal = "ACM Trans. on Graphics (SIGGRAPH)",
		volume = "32",
		number = "4",
		year = "2013",
	}

and if you use the Intrinsic Images code, please also cite:

    Sean Bell, Kavita Bala, Noah Snavely
    Intrinsic Images in the Wild
    ACM Transactions on Graphics (SIGGRAPH 2014)

    @article{bell14intrinsic,
		author = "Sean Bell and Kavita Bala and Noah Snavely",
		title = "Intrinsic Images in the Wild",
		journal = "ACM Trans. on Graphics (SIGGRAPH)",
		volume = "33",
		number = "4",
		year = "2014",
	}

It's nice to see how many people are using our code; please "star" this project
on GitHub and report any bugs using the
[issue tracker](https://github.com/seanbell/opensurfaces/issues).

## Installing

**Ubuntu**:
If you are on Ubuntu 12.04.5 or later, you can run `install_all.sh` to install
all components (will use ~15G disk space).

**Other operating systems**:
I suggest installing [VirtualBox](https://www.virtualbox.org/) and running
Ubuntu 12.04.5 as a virtual machine.  There's a lot of components and it would be
difficult to port to other operating systems.

For other Linux distributions, you can probably get it to run by rewriting all
of the install scripts in the `scripts/install` directory.
