SPECFILE = ai-tools.spec
FILES = ai-foreman-cli ai-landb-bind-mac README.judy ai-bs-vm{,.1} ai-kill-vm{,.1} userdata/common ai-gen-ssh-yaml{,.1} ai-git-cherry-pick
rpmtopdir := $(shell rpm --eval %_topdir)
rpmbuild  := $(shell [ -x /usr/bin/rpmbuild ] && echo rpmbuild || echo rpm)

PACKAGE = $(shell grep -s '^Name'    $(SPECFILE) | sed -e 's/Name: *//')
VERSION = $(shell grep -s '^Version' $(SPECFILE) | sed -e 's/Version: *//')

DISTTAG ?= $(shell lsb_release -r  | sed -nr 's/^[^[:space:]]+[[:space:]]+([0-9]+)\.([0-9]+)$$/.slc\1/p' )

ifneq ($(DISTTAG), .ai6)
ifneq ($(DISTTAG), .ai5)
$(error Only ai6/ai5 builds are supported.)
endif
endif

rpm: $(SPECFILE)
	mkdir -p $(rpmtopdir)/{SOURCES,SPECS,BUILD,SRPMS,RPMS}
	rm -rf $(PACKAGE)-$(VERSION)
	mkdir $(PACKAGE)-$(VERSION)
	cp -rv --parents $(FILES) $(PACKAGE)-$(VERSION)/
	tar cvfz $(rpmtopdir)/SOURCES/$(PACKAGE)-$(VERSION).tgz $(PACKAGE)-$(VERSION)
	rm -rf $(PACKAGE)-$(VERSION)
	cp -f $(SPECFILE) $(rpmtopdir)/SPECS/$(SPECFILE)
	$(rpmbuild) -ba --define "dist $(DISTTAG)" $(SPECFILE)



