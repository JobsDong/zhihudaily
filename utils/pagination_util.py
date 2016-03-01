#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""分页 based on django.core.paginator
"""

__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from math import ceil
import collections


class InvalidPageError(Exception):
    pass


class EmptyPageError(InvalidPageError):
    pass


class Paginator(collections.Sequence):

    def __init__(self, object_list, cur_page, count, per_page=10):
        self.object_list = object_list
        self.cur_page = cur_page
        self.count = count
        self.per_page = per_page
        self.num_pages = int(ceil(self.count / float(self.per_page)))

    def __repr__(self):
        return '<Page %s of %s>' % (self.cur_page, self.num_pages)

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        if not isinstance(index, (slice,) + (int, long)):
            raise TypeError

        if not isinstance(self.object_list, list):
            self.object_list = list(self.object_list)
        return self.object_list[index]

    def previous_pages(self, limit=3):

        page_indexs = [self.cur_page-i for i in xrange(1, limit)
                       if self.cur_page-i >= 1]
        page_indexs.reverse()
        return page_indexs

    def next_pages(self, limit=3):
        page_indexs = [self.cur_page+i for i in xrange(1, limit)
                       if self.cur_page+i <= self.num_pages]
        return page_indexs

    @property
    def has_previous(self):
        return self.cur_page > 1

    @property
    def has_next(self):
        return self.cur_page < self.num_pages

    @property
    def next_page_number(self):
        return self.cur_page + 1

    @property
    def previous_page_number(self):
        return self.cur_page - 1

    @property
    def start_index(self):
        if self.count == 0:
            return 0
        return (self.per_page * (self.cur_page - 1)) + 1

    @property
    def end_index(self):
        if self.cur_page == self.num_pages:
            return self.count

        return self.cur_page * self.per_page