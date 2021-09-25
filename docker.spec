Name: docker-engine
Version: 18.09.0
Release: 118
Summary: The open-source application container engine
Group: Tools/Docker

License: ASL 2.0
Source0: https://github.com/docker/docker-ce/archive/v18.09.0.tar.gz
Source1: patch.tar.gz
Source2: apply-patches
Source3: git-commit
Source4: series.conf
Source5: VERSION-openeuler
Source6: gen-commit.sh

URL: https://mobyproject.org

%global is_systemd 1

# required packages for build
# most are already in the container (see contrib/builder/rpm/ARCH/generate.sh)
BuildRequires: pkgconfig(systemd) golang >= 1.8.3 btrfs-progs-devel device-mapper-devel glibc-static libseccomp-devel
BuildRequires: libselinux-devel libtool-ltdl-devel pkgconfig selinux-policy selinux-policy-devel sqlite-devel systemd-devel
BuildRequires: tar containerd docker-runc docker-proxy

# required packages on install
Requires: /bin/sh iptables libcgroup tar xz device-mapper-libs >= 1.02.90-1 systemd-units

# conflicting packages
Provides: docker
Conflicts: docker-io
Conflicts: docker-engine-cs

%description
Docker is an open source project to build, ship and run any application as a
lightweight container.

Docker containers are both hardware-agnostic and platform-agnostic. This means
they can run anywhere, from your laptop to the largest EC2 compute instance and
everything in between - and they don't require you to use a particular
language, framework or packaging system. That makes them great building blocks
for deploying and scaling web apps, databases, and backend services without
depending on a particular stack or provider.

%debug_package

%prep
cp %{SOURCE0} .
cp %{SOURCE1} .
cp %{SOURCE2} .
cp %{SOURCE3} .
cp %{SOURCE4} .
cp %{SOURCE5} .

%build

sh ./apply-patches

# build docker engine
WORKDIR=$(pwd)
export VERSION=$(cat VERSION)
export DOCKER_GITCOMMIT=$(cat git-commit | head -c 7)
export AUTO_GOPATH=1
export DOCKER_BUILDTAGS="pkcs11 seccomp selinux"
cd ${WORKDIR}/components/engine
./hack/make.sh dynbinary

# buid docker cli
cd ${WORKDIR}/components/cli
mkdir -p .gopath/src/github.com/docker
export GOPATH=`pwd`/.gopath
ln -sf `pwd` .gopath/src/github.com/docker/cli
ln -sf ${WORKDIR}/components/engine .gopath/src/github.com/docker/docker
cd .gopath/src/github.com/docker/cli
make dynbinary

# man is provided in docker --help and dockerd --help
# ./man/md2man-all.sh runs outside the build container (if at all), since we don't have go-md2man here
# ./man/md2man-all.sh -q

rm -rf .gopath
cd ${WORKDIR}

%check
./components/engine/bundles/dynbinary-daemon/dockerd -v
./components/cli/build/docker -v

%install
# install binary
install -d $RPM_BUILD_ROOT/%{_bindir}
install -p -m 755 components/engine/bundles/dynbinary-daemon/dockerd $RPM_BUILD_ROOT/%{_bindir}/dockerd

# install cli
install -p -m 755 components/cli/build/docker $RPM_BUILD_ROOT/%{_bindir}/docker

# install proxy
install -p -m 755 /usr/bin/docker-proxy $RPM_BUILD_ROOT/%{_bindir}/docker-proxy

# install containerd
install -p -m 755 /usr/bin/containerd $RPM_BUILD_ROOT/%{_bindir}/containerd
install -p -m 755 /usr/bin/containerd-shim $RPM_BUILD_ROOT/%{_bindir}/containerd-shim

# install runc
install -p -m 755 /usr/local/bin/runc  $RPM_BUILD_ROOT/%{_bindir}/runc

# install udev rules
install -d $RPM_BUILD_ROOT/%{_sysconfdir}/udev/rules.d
install -p -m 644 components/engine/contrib/udev/80-docker.rules $RPM_BUILD_ROOT/%{_sysconfdir}/udev/rules.d/80-docker.rules

# add init scripts
install -d $RPM_BUILD_ROOT/etc/sysconfig
install -d $RPM_BUILD_ROOT/%{_initddir}
install -p -m 644 components/engine/contrib/init/sysvinit-redhat/docker.sysconfig $RPM_BUILD_ROOT/etc/sysconfig/docker 
install -p -m 644 components/engine/contrib/init/sysvinit-redhat/docker-network $RPM_BUILD_ROOT/etc/sysconfig/docker-network
install -p -m 644 components/engine/contrib/init/sysvinit-redhat/docker-storage $RPM_BUILD_ROOT/etc/sysconfig/docker-storage

install -d $RPM_BUILD_ROOT/%{_unitdir}
install -p -m 644 components/engine/contrib/init/systemd/docker.service $RPM_BUILD_ROOT/%{_unitdir}/docker.service
# add bash, zsh, and fish completions
install -d $RPM_BUILD_ROOT/usr/share/bash-completion/completions
install -d $RPM_BUILD_ROOT/usr/share/zsh/vendor-completions
install -d $RPM_BUILD_ROOT/usr/share/fish/vendor_completions.d
install -p -m 644 components/cli/contrib/completion/bash/docker $RPM_BUILD_ROOT/usr/share/bash-completion/completions/docker
install -p -m 644 components/cli/contrib/completion/zsh/_docker $RPM_BUILD_ROOT/usr/share/zsh/vendor-completions/_docker
install -p -m 644 components/cli/contrib/completion/fish/docker.fish $RPM_BUILD_ROOT/usr/share/fish/vendor_completions.d/docker.fish

# install manpages
# install -d %{buildroot}%{_mandir}/man1
# install -p -m 644 components/cli/man/man1/*.1 $RPM_BUILD_ROOT/%{_mandir}/man1
# install -d %{buildroot}%{_mandir}/man5
# install -p -m 644 components/cli/man/man5/*.5 $RPM_BUILD_ROOT/%{_mandir}/man5
# install -d %{buildroot}%{_mandir}/man8
# install -p -m 644 components/cli/man/man8/*.8 $RPM_BUILD_ROOT/%{_mandir}/man8

# add vimfiles
install -d $RPM_BUILD_ROOT/usr/share/vim/vimfiles/doc
install -d $RPM_BUILD_ROOT/usr/share/vim/vimfiles/ftdetect
install -d $RPM_BUILD_ROOT/usr/share/vim/vimfiles/syntax
install -p -m 644 components/engine/contrib/syntax/vim/doc/dockerfile.txt $RPM_BUILD_ROOT/usr/share/vim/vimfiles/doc/dockerfile.txt
install -p -m 644 components/engine/contrib/syntax/vim/ftdetect/dockerfile.vim $RPM_BUILD_ROOT/usr/share/vim/vimfiles/ftdetect/dockerfile.vim
install -p -m 644 components/engine/contrib/syntax/vim/syntax/dockerfile.vim $RPM_BUILD_ROOT/usr/share/vim/vimfiles/syntax/dockerfile.vim

# add nano
install -d $RPM_BUILD_ROOT/usr/share/nano
install -p -m 644 components/engine/contrib/syntax/nano/Dockerfile.nanorc $RPM_BUILD_ROOT/usr/share/nano/Dockerfile.nanorc

# list files owned by the package here
%files
%doc components/engine/AUTHORS components/engine/CHANGELOG.md components/engine/CONTRIBUTING.md components/engine/LICENSE components/engine/MAINTAINERS components/engine/NOTICE components/engine/README.md
/%{_bindir}/docker
/%{_bindir}/dockerd
/%{_bindir}/containerd
/%{_bindir}/docker-proxy
/%{_bindir}/containerd-shim
/%{_bindir}/runc
/%{_sysconfdir}/udev/rules.d/80-docker.rules
%if 0%{?is_systemd}
/%{_unitdir}/docker.service
%else
/%{_initddir}/docker
%endif
/usr/share/bash-completion/completions/docker
/usr/share/zsh/vendor-completions/_docker
/usr/share/fish/vendor_completions.d/docker.fish
%doc
#/%{_mandir}/man1/*
#/%{_mandir}/man5/*
#/%{_mandir}/man8/*

%config(noreplace,missingok) /etc/sysconfig/docker
%config(noreplace,missingok) /etc/sysconfig/docker-storage
%config(noreplace,missingok) /etc/sysconfig/docker-network

/usr/share/vim/vimfiles/doc/dockerfile.txt
/usr/share/vim/vimfiles/ftdetect/dockerfile.vim
/usr/share/vim/vimfiles/syntax/dockerfile.vim
/usr/share/nano/Dockerfile.nanorc

%post
if ! getent group docker > /dev/null; then
    groupadd --system docker
fi
%if 0%{?is_systemd}
#%systemd_post docker
systemctl enable docker
systemctl start docker
%else
# This adds the proper /etc/rc*.d links for the script
/sbin/chkconfig --add docker
%endif
if ! getent group docker > /dev/null; then
    groupadd --system docker
fi

%preun
%if 0%{?is_systemd}
%systemd_preun docker
%else
if [ $1 -eq 0 ] ; then
    /sbin/service docker stop >/dev/null 2>&1
    /sbin/chkconfig --del docker
fi
%endif

%postun
%if 0%{?is_systemd}
%systemd_postun_with_restart docker
%else
if [ "$1" -ge "1" ] ; then
    /sbin/service docker condrestart >/dev/null 2>&1 || :
fi
%endif

%changelog
* Sun Sep 26 2021 xiadanni<xiadanni1@huawei.com> - 18.09.0-118
- Type:bugfix
- CVE:NA
- SUG:NA
- DESC:update seccomp whitelist to Linux 5.10 syscall list

* Wed Sep 08 2021 xiadanni<xiadanni1@huawei.com> - 18.09.0-117
- Type:bugfix
- CVE:NA
- SUG:NA
- DESC:add clone3 to seccomp whitelist to fix curl failed in X86

* Fri Sep 03 2021 chenjiankun<chenjiankun1@huawei.com> - 18.09.0-116
- Type:bugfix
- CVE:NA
- SUG:NA
- DESC:enable debuginfo

* Thu Apr 01 2021 wangfengtu<wangfengtu@huawei.com> - 18.09.0-115
- Type:bugfix
- CVE:NA
- SUG:NA
- DESC:rollback if docker restart when doing BlkDiscard

* Thu Mar 18 2021 xiadanni<xiadanni1@huawei.com> - 18.09.0-114
- Type:bugfix
- CVE:CVE-2021-21284,CVE-2021-21285
- SUG:NA
- DESC:sync bugfix, include:
       1.fix execCommands leak in health-check
       2.check containerd pid before kill it
       3.fix CVE-2021-21284
       4.fix CVE-2021-21285

* Tue Feb 09 2021 lixiang<lixiang172@huawei.com> - 18.09.0-113
- Type:enhancement
- CVE:NA
- SUG:restart
- DESC:remove go-md2man build require

* Mon Jan 4 2021 yangyanchao<yangyanchao6@huawei.com> - 18.09.0-111
- Type:requirement
- ID:NA
- CVE:NA
- SUG:restart
- docker:components:add config files for riscv

* Mon Jan 18 2021 jingrui<jingrui@huawei.com> - 18.09.0-107
- Type:bugfix
- ID:NA
- SUG:NA
- DESC:sync bugfix include
  1. fix image cleanup failed.
  2. cleanup load tmp files.
  3. kill residual container process.
  4. resume suspend dm device.
  5. dont kill containerd during dockerd starting.
  6. handle exit event for restore failed container.
  7. wait io with timeout when start failed.
  8. support hostname mirror registry.
  9. mask unused proc files.

* Tue Dec 8 2020 xiadanni<xiadanni1@huawei.com> - 18.09.0-104
- Type:bugfix
- ID:NA
- SUG:NA
- DESC:runc don't deny all devices when update cgroup resource

* Thu Dec 3 2020 xiadanni<xiadanni1@huawei.com> - 18.09.0-103
- Type:bugfix
- ID:NA
- SUG:restart
- DESC:containerd fix CVE-2020-15257

* Fri Nov 27 2020 liuzekun<liuzekun@huawei.com> - 18.09.0-102
- Type:bugfix
- ID:NA
- CVE:NA
- SUG:restart
- DESC:
1.delete stale containerd object on start failure
2.remove redundant word item
3.delete event is not need to process
4.stat process exit file when kill process dire
5.sync cli vendor
6.fix CVE-2020-13401
7.do not add w to LDFLAGS
8.add files in proc for mask
9.fix docker load files leak
10.do not sync if BYPAAS_SYNC is false
11.fix panic on single character volumes
12.fix stats memory usage display error
13.add more messages for ops when device not found
14.mask proc pin_memory
