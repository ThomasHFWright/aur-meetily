#!/usr/bin/env python3
"""Refresh a stable release recipe; building and publishing are separate CI steps."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.request


def release_version(release):
    tag = release['tag_name']
    if release['draft'] or release['prerelease'] or not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Expected a published stable vX.Y.Z release')
    return tag[1:]


def update_recipe(recipe, version, digest):
    recipe, count = re.subn(r'^pkgver=\d+\.\d+\.\d+$', f'pkgver={version}', recipe, flags=re.M)
    assert count == 1
    recipe, count = re.subn(r'^pkgrel=\d+$', 'pkgrel=1', recipe, flags=re.M)
    assert count == 1
    recipe, count = re.subn(r"sha256sums=\('[a-f0-9]{64}'", f"sha256sums=('{digest}'", recipe)
    assert count == 1
    return recipe


def main():
    if sys.argv[1:] == ['--self-test']:
        assert release_version(dict(tag_name='v0.17.0', draft=False, prerelease=False)) == '0.17.0'
        for tag, draft, prerelease in [('main', False, False), ('v0.18.0-rc1', False, True), ('v0.18.0', True, False)]:
            try:
                release_version(dict(tag_name=tag, draft=draft, prerelease=prerelease))
            except ValueError:
                pass
            else:
                raise AssertionError('Accepted an unpublished or non-stable release')
        recipe = "pkgver=0.17.0\npkgrel=2\nsha256sums=('" + 'a' * 64 + "'\n'local-file-hash')\n"
        updated = update_recipe(recipe, '0.18.0', 'b' * 64)
        assert 'pkgver=0.18.0\npkgrel=1' in updated and 'b' * 64 in updated
        assert "'local-file-hash'" in updated
        print('PASS stable release validation and recipe update')
        return
    request = urllib.request.Request('https://api.github.com/repos/Zackriya-Solutions/meetily/releases/latest',
                                     headers={'User-Agent': 'aur-meetily-release-check'})
    with urllib.request.urlopen(request, timeout=30) as response:
        version = release_version(json.load(response))
    paths = sorted(Path('packaging').glob('*/PKGBUILD'))
    if not paths:
        raise RuntimeError('Run from the packaging repository root')
    recipe = paths[0].read_text()
    current = re.search(r'^pkgver=(.+)$', recipe, re.M)[1]
    if int(subprocess.check_output(['vercmp', version, current])) <= 0:
        print(f'Already at {current}; latest release is {version}')
        return
    archive = Path(f'meetily-{version}.tar.gz')
    partial = archive.with_suffix('.part')
    digest = hashlib.sha256()
    url = f'https://github.com/Zackriya-Solutions/meetily/archive/refs/tags/v{version}.tar.gz'
    with urllib.request.urlopen(url, timeout=120) as response, partial.open('wb') as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
            digest.update(chunk)
    partial.replace(archive)
    for path in paths:
        path.write_text(update_recipe(path.read_text(), version, digest.hexdigest()))
        (path.parent / '.SRCINFO').write_bytes(subprocess.check_output(
            ['makepkg', '--printsrcinfo'], cwd=path.parent))
    print(f'Prepared {version}; build and tests must pass before publication')


if __name__ == '__main__':
    main()
