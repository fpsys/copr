Name:           kiri
Version:        1.1
Release:        1%{?dist}
Summary:        Scrollable tiling window management for KDE Plasma

License:        GPL-3.0-or-later
URL:            https://github.com/SeniorMatt/kiri
Source0:        https://github.com/SeniorMatt/kiri/releases/download/v1.1/kiri_1_1.tar.gz
# SHA-256 published by the GitHub Release API for kiri_1_1.tar.gz.
%global _vpath_srcdir effect-cpp

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  extra-cmake-modules
BuildRequires:  kwin-devel >= 6.7.0
BuildRequires:  kdecoration-devel
BuildRequires:  kf6-kconfig-devel
BuildRequires:  kf6-kcoreaddons-devel
BuildRequires:  kf6-kcmutils-devel
BuildRequires:  kf6-kconfigwidgets-devel
BuildRequires:  libepoxy-devel
BuildRequires:  libdrm-devel
BuildRequires:  qt6-qtbase-devel
BuildRequires:  qt6-qtdeclarative-devel
BuildRequires:  qt6-qttools-devel

# Kiri's native effects are KWin plugins and must match the installed KWin ABI.
Requires:       kwin-common >= 6.7.0
Requires:       kwin-libs >= 6.7.0
Requires:       kf6-kconfig
Requires:       kf6-kpackage
Requires:       qt6-qttools

%description
Kiri is a KWin script for scrollable, niri-style tiling on KDE Plasma. This
package installs the KWin script system-wide, builds and installs Kiri's
native KWin effects and System Settings module against the target Fedora
KWin build, and provides the kiri-mode command for switching between Kiri
and the regular Plasma window-management mode.

%prep
echo 'cf4a5b1baef29971ba38e03f1d06f29802d45853fd646db158f8f6c26597fbf7  %{SOURCE0}' | sha256sum --check --status
%autosetup -n kiri_1_1
%build
%cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DKDE_INSTALL_QTPLUGINDIR=%{_libdir}/qt6/plugins
%cmake_build

%install
%cmake_install

# KWin discovers system-wide KWin scripts under %{_datadir}/kwin/scripts.
install -d %{buildroot}%{_datadir}/kwin/scripts/kiri
cp -a package/. %{buildroot}%{_datadir}/kwin/scripts/kiri/

install -Dpm0755 kiri-mode %{buildroot}%{_bindir}/kiri-mode
install -Dpm0644 LICENSE %{buildroot}%{_licensedir}/%{name}/LICENSE

# System-wide shortcut entry. Users can change the accelerator in System Settings.
install -Dpm0644 /dev/null %{buildroot}%{_datadir}/applications/kiri-mode.desktop
cat > %{buildroot}%{_datadir}/applications/kiri-mode.desktop <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Switch Kiri / Plasma
Comment=Switch between Kiri mode and Plasma mode
Icon=preferences-system-windows
Exec=/usr/bin/kiri-mode toggle
Terminal=false
StartupNotify=false
Categories=Utility;
X-KDE-GlobalAccel-CommandShortcut=true
X-KDE-Shortcuts=Meta+Ctrl+Shift+K
DESKTOP

%check
# Ensure the complete native plugin set and KWin script were staged.
test -s %{buildroot}%{_datadir}/kwin/scripts/kiri/metadata.json
test -x %{buildroot}%{_bindir}/kiri-mode
test -s %{buildroot}%{_libdir}/qt6/plugins/kwin/effects/plugins/kiri_decorations.so
test -s %{buildroot}%{_libdir}/qt6/plugins/kwin/effects/plugins/kiri_desktop_switch.so
test -s %{buildroot}%{_libdir}/qt6/plugins/kwin/effects/plugins/kiri_motion.so
test -s %{buildroot}%{_libdir}/qt6/plugins/kwin/effects/plugins/kiri_swipe.so
test -s %{buildroot}%{_libdir}/qt6/plugins/kwin/effects/plugins/kiri_overview.so
test -s %{buildroot}%{_libdir}/qt6/plugins/kwin/effects/configs/kcm_kiri.so

%files
%{_bindir}/kiri-mode
%{_datadir}/applications/kiri-mode.desktop
%{_datadir}/kwin/scripts/kiri/
%{_libdir}/qt6/plugins/kwin/effects/plugins/kiri_decorations.so
%{_libdir}/qt6/plugins/kwin/effects/plugins/kiri_desktop_switch.so
%{_libdir}/qt6/plugins/kwin/effects/plugins/kiri_motion.so
%{_libdir}/qt6/plugins/kwin/effects/plugins/kiri_swipe.so
%{_libdir}/qt6/plugins/kwin/effects/plugins/kiri_overview.so
%{_libdir}/qt6/plugins/kwin/effects/configs/kcm_kiri.so
%{_licensedir}/%{name}/LICENSE

%changelog
* 2026-11-25 Kiri COPR Maintainers <noreply@example.com> - 1.1-1
- Package Kiri v1.1 release for Fedora KDE Plasma.
* Wed Nov 25 2026 Kiri COPR Maintainers <noreply@example.com> - 1.1-1
- Package Kiri v1.1 release for Fedora KDE Plasma.
