SPECFILE = ai-tools.spec
FILES = ai-foreman-cli
rpmtopdir := $(shell rpm --eval %_topdir)
rpmbuild  := $(shell [ -x /usr/bin/rpmbuild ] && echo rpmbuild || echo rpm)

PACKAGE = $(shell grep -s '^Name'    $(SPECFILE) | sed -e 's/Name: *//')
VERSION = $(shell grep -s '^Version' $(SPECFILE) | sed -e 's/Version: *//')

DISTTAG ?= $(shell lsb_release -r  | sed -nr 's/^[^[:space:]]+[[:space:]]+([0-9]+)\.([0-9]+)$$/.slc\1/p' )

ifneq ($(DISTTAG), .slc6)
ifneq ($(DISTTAG), .slc5)
$(error Only SLC5/SLC6 builds are supported.)
endif
endif

rpm: $(SPECFILE)
	mkdir -p $(rpmtopdir)/{SOURCES,SPECS,BUILD,SRPMS,RPMS}
	rm -rf $(PACKAGE)-$(VERSION)
	mkdir $(PACKAGE)-$(VERSION)
	cp -rv $(FILES) $(PACKAGE)-$(VERSION)/
	tar cvfz $(rpmtopdir)/SOURCES/$(PACKAGE)-$(VERSION).tgz $(PACKAGE)-$(VERSION)
	rm -rf $(PACKAGE)-$(VERSION)
	cp -f $(SPECFILE) $(rpmtopdir)/SPECS/$(SPECFILE)
	$(rpmbuild) -ba --define "dist $(DISTTAG)" $(SPECFILE)


