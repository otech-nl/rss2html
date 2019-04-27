# -*- coding: utf-8 -*-
from collections import defaultdict
from os import path, mkdir
from pprint import pprint
import sys

import feedparser
import jinja2


class Renderer:

    def __init__(self, feed, out_dir='html'):        
        self.feed = feed['feed']
        self.feed['title'] = self.feed['title'] or 'My Blog'
        self.entries = feed['entries']

        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('templates'),
            trim_blocks=True
        )

        self.out_dir = self.check_dir(out_dir, 'Destination')
        print(f'Rendering to "{out_dir}"')

        # analyse entries
        self.feed.authors = defaultdict(list)
        self.feed.archive = defaultdict(list)
        self.feed.tags = defaultdict(list)
        self.feed.pages = []
        self.feed.posts = []
        
        for n, entry in enumerate(self.entries):
            # pprint(entry.keys())
            # sys.exit()
            entry['authors'] = [author.name for author in entry['authors']]
            for author in entry['authors']:
                self.feed.authors[author].append(entry)

            pub = entry['published_parsed']
            self.feed.archive[f'{pub.tm_year}-%02d' % pub.tm_mon].append(entry)

            entry_type = 'post'
            if 'tags' in entry:
                entry['tags'] = [tag.term.lower() for tag in entry['tags'] if tag.term != 'nil']
                if 'page' in entry['tags']:
                    entry_type = 'page'
                    self.feed.pages.append(entry)
                    entry['tags'].remove('page')
                else:
                    self.feed.posts.append(entry)
                # pprint(entry['tags'])
                for tag in entry['tags']:
                        self.feed.tags[tag].append(entry)

            entry['path'] = f'{entry_type}_{n}.html'

    @staticmethod
    def check_dir(name, description='Path'):
        if path.exists(name):
            if not path.isdir(name):
                print(f'{description} "{name}" exists but is not a directory')
                sys.exit(0)
        else:
            try:
                mkdir(name)
                print(f'{description} "{name}" created')
            except OSError as e:
                print(f'Failed to create {description} "{name}": {e}')
        return name


    def render(self, template, filename=None, **kwargs):
        template = self.env.get_template(template)
        content = template.render(feed=self.feed, **kwargs)

        if filename:
            with open(path.join(self.out_dir, filename), 'w') as fout:
                fout.write(content)

        return content

    def render_all(self):
        length = min(len(self.feed.posts), 5)
        self.render('feed.jinja2', 'index.html', entries=self.feed.posts[:length])
        print('Wrote index')
        for entry in self.entries:
            self.render('entry.jinja2', entry['path'], entry=entry)
        print('Wrote entries')

        self.render('list.jinja2', 'tags.html', items=sorted(self.feed.tags.items()))
        print('Wrote tags')
        self.render('list.jinja2', 'authors.html', items=sorted(self.feed.authors.items()))
        print('Wrote authors')
        self.render('list.jinja2', 'archive.html', items=sorted(self.feed.archive.items(), reverse=True))
        print('Wrote archive')


try:
    feed_file = sys.argv[1]
except IndexError:
    feed_file = 'blog.xml'
print(f'Parsing "{feed_file}"')
feed = feedparser.parse(feed_file)
Renderer(feed).render_all()