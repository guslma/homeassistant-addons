"""
Points every add-on at the version its image publishes as stable.

For each <add-on>/config.yaml with an `image`, it reads which image the `latest` tag
points at and picks the version tag (one with a number) that points at the same image.
This skips betas and variants (synology, legacy, nvidia, lite...) without keeping a list
of names to ignore, and works the same on Docker Hub and the GitHub Container Registry.

Only the `version:` line of config.yaml is changed. When running in GitHub Actions, the
changed add-ons, a title and a body for the pull request are written to GITHUB_OUTPUT.
"""
import glob
import json
import os
import re

import requests

STABLE_TAG = 'latest'
MAX_LOOKUPS = 60  # Tags checked per image before giving up
TIMEOUT = 30

MANIFEST_TYPES = ', '.join([
    'application/vnd.oci.image.index.v1+json',
    'application/vnd.docker.distribution.manifest.list.v2+json',
    'application/vnd.oci.image.manifest.v1+json',
    'application/vnd.docker.distribution.manifest.v2+json',
])


class Registry:
    """Reads tags and digests through the registry API (the one `docker pull` uses)."""

    def __init__(self, image):
        if image.startswith('ghcr.io/'):
            self.repo = image.split('/', 1)[1]
            self.base = 'https://ghcr.io'
            token_url = f'https://ghcr.io/token?scope=repository:{self.repo}:pull'
        else:
            self.repo = image if '/' in image else f'library/{image}'
            self.base = 'https://registry-1.docker.io'
            token_url = ('https://auth.docker.io/token?service=registry.docker.io'
                         f'&scope=repository:{self.repo}:pull')
        self.session = requests.Session()
        token = self.session.get(token_url, timeout=TIMEOUT)
        token.raise_for_status()
        self.session.headers['Authorization'] = f'Bearer {token.json()["token"]}'

    def tags(self):
        tags, url = [], f'{self.base}/v2/{self.repo}/tags/list?n=1000'
        while url:
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            tags += response.json().get('tags') or []
            next_page = response.links.get('next', {}).get('url')
            url = f'{self.base}{next_page}' if next_page and next_page.startswith('/') else next_page
        return tags

    def digest(self, tag):
        # HEAD requests do not count against the Docker Hub pull limit
        response = self.session.head(f'{self.base}/v2/{self.repo}/manifests/{tag}',
                                     headers={'Accept': MANIFEST_TYPES}, timeout=TIMEOUT)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.headers.get('Docker-Content-Digest')


def shape(tag):
    """'v0.147.0-noble-full' -> 'v#.#.#-noble-full'"""
    return re.sub(r'\d+', '#', tag)


def numbers(tag):
    return tuple(int(n) for n in re.findall(r'\d+', tag))


def stable_version(image, current):
    """The version tag that points at the same image as `latest`, or None."""
    registry = Registry(image)
    stable = registry.digest(STABLE_TAG)
    if not stable:
        print(f'  {image} has no "{STABLE_TAG}" tag')
        return None

    # Tags shaped like the current version first (so 'v0.147.0-noble-full' is not mistaken
    # for an old '20-jammy-full-v0.93.0'), newest first, and the most specific one on a tie
    # (1.3.2 before 1.3)
    candidates = [tag for tag in registry.tags() if re.search(r'\d', tag)]
    candidates.sort(key=lambda tag: (shape(tag) == shape(current), numbers(tag), len(numbers(tag))),
                    reverse=True)

    for tag in candidates[:MAX_LOOKUPS]:
        if registry.digest(tag) == stable:
            return tag
    print(f'  No version tag points at the same image as "{STABLE_TAG}" '
          f'among the {min(len(candidates), MAX_LOOKUPS)} checked')
    return None


VERSION_LINE = re.compile(r'^version:[ \t]*(.*?)[ \t]*$', re.MULTILINE)
IMAGE_LINE = re.compile(r'^image:[ \t]*(\S+)', re.MULTILINE)
NAME_LINE = re.compile(r'^name:[ \t]*(.+?)[ \t]*$', re.MULTILINE)


def main():
    changes, failed = [], []
    for path in sorted(glob.glob('*/config.yaml')):
        with open(path) as file:
            text = file.read()
        image = IMAGE_LINE.search(text)
        if not image:
            continue
        image = image.group(1)
        addon = os.path.dirname(path)
        name = NAME_LINE.search(text).group(1)
        current = VERSION_LINE.search(text).group(1).strip('\'"')

        print(f'{name} ({image}), current version {current}')
        try:
            latest = stable_version(image, current)
        except requests.RequestException as error:
            print(f'  Error: {error}')
            latest = None
        if not latest:
            failed.append(name)
            continue
        if latest == current:
            print('  Up to date')
            continue

        print(f'  Updating to {latest}')
        # Always quoted: a tag like 2026-11-15 would otherwise be read as a date
        text = VERSION_LINE.sub(f'version: "{latest}"', text, count=1)
        with open(path, 'w') as file:
            file.write(text)
        changes.append({'addon': addon, 'name': name, 'image': image, 'from': current, 'to': latest})

    title = 'Update ' + ', '.join(f'{c["name"]} to {c["to"]}' for c in changes)
    body = '\n'.join([
        '| Add-on | From | To |',
        '| --- | --- | --- |',
        *(f'| {c["name"]} | `{c["from"]}` | `{c["to"]}` |' for c in changes),
        '',
        f'Each version is the tag that points at the same image as `{STABLE_TAG}`.',
    ])
    if failed:
        body += f'\n\nCould not check: {", ".join(failed)} (see the workflow log).'

    output = os.environ.get('GITHUB_OUTPUT')
    if output:
        with open(output, 'a') as file:
            file.write(f'addons={json.dumps([c["addon"] for c in changes])}\n')
            file.write(f'failed={", ".join(failed)}\n')
            file.write(f'title={title}\n')
            file.write(f'body<<END_OF_BODY\n{body}\nEND_OF_BODY\n')
    for name in failed:
        print(f'::warning::Could not check the version of {name}')
    if changes:
        print(f'\n{title}\n\n{body}')


if __name__ == '__main__':
    main()
