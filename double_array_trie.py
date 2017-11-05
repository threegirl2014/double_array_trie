#!/usr/bin/python
#coding:utf-8

from collections import defaultdict
from itertools import chain


class CharDict(object):

    def __init__(self, words, split='#'):
        self._char_dict = defaultdict(int)
        char_set = set(chain(*(w.strip() for w in words)))
        if split in char_set:
            raise Exception('split character is ilegal.')
        self._split_character = split

        start = 1
        self._char_dict['#'] = start
        for index, item in enumerate(char_set):
            self._char_dict[item] = index + start + 1

    @property
    def split(self):
        return self._split_character

    def __getitem__(self, key):
        return self._char_dict[key]

    def __len__(self):
        return len(self._char_dict)

    def add_word(self, word):
        for c in word:
            if not self._char_dict[c]:
                self._char_dict[c] = len(self._char_dict) + 1

    def __str__(self):
        return str(self._char_dict)


class DoubleArrayTrie(object):

    def __init__(self, words, split='#'):
        self.chars = CharDict(words, split)
        self.base = defaultdict(int)
        self.check = defaultdict(int)
        self.tails = defaultdict(int)
        self.next_pos = 1  # tails中下一个可插入的位置
        self.root = 1   # root节点

    def search(self, word):
        word += '#'
        s = self.root
        for i, c in enumerate(word):
            n = self.chars[c]
            if not n:  # 没有这个字符
                return False

            if self.base[s] < 0:
                pos = -self.base[s]
                return True
            m = self.base[s] + n
            if self.check[m] != s:  # check为0
                return False
        pass

    def delete(self, word):
        pass

    def add(self, word):
        # word += '#'
        self.chars.add_word(word)
        s = self.root
        for i, c in enumerate(word):
            n = self.chars[c]
            m = self.base[s] + n
            if self.check[m] == 0:  # base[m]将会是独立节点
                self.base[m] = -self.next_pos
                self.check[m] = s
                self.tails[self.next_pos] = word[i+1:] + '#'
                self.next_pos += len(self.tails[self.next_pos])
            else:  # 从check[m]到m的有向边已存在
                s = self.check[m]
                if self.base[s] < 0:  # base[s]是独立节点
                    pos = -self.base[s]
                    tail1 = self.tails[pos][:-1]
                    tail2 = word[i+1:]
                    if tail1 == tail2:  # 该word已存在
                        return True
                    lcp = self.longest_common_prefix(tail1, tail2)
                    q = self.x_check(lcp)
                    self.base[s] = q
                    for new_c in lcp:  # 存储公共前缀字符串
                        new_n = self.chars[new_c]
                        new_m = self.base[s] + new_n
                        self.check[new_m] = s
                        s = new_m
                    len_lcp = len(lcp)
                    x = tail1[len_lcp:]
                    y = tail2[len_lcp:]
                    q = self.x_check(x[0]+y[0])

                    self.base[s] = q
                    n = self.chars[x[0]]
                    m = self.base[s] + n
                    self.base[m] = -pos
                    self.check[m] = s
                    self.tails[pos] = x + '#'

                    n = self.chars[y[0]]
                    m = self.base[s] + n
                    self.base[m] = -self.next_pos
                    self.check[m] = s
                    self.tails[self.next_pos] = y + '#'
                    self.next_pos += len(self.tails[self.next_pos])

        pass

    def longest_common_prefix(self, *words):
        lcp = ''
        for _, item in enumerate(zip(*words)):
            if len(set(item)) == 1:
                lcp += item[0]
            else:
                break
        return lcp

    def x_check(self, word):
        q = 1
        while 1:
            if all(self.check[q + self.chars[c]] == 0 for c in word):
                break
            q += 1
        return q

    def search_exists(self, word):
        pass


if __name__ == '__main__':
    words = ['123','abc','43df']
    c = CharDict(words)
    print c
    print 'Length: {}'.format(len(c))
    print 'split: {}'.format(c.split)
    print "c[split] = {}".format(c[c.split])
    print "c['1'] = {}".format(c['1'])
    print "c['f'] = {}".format(c['f'])
    print "c['x'] = {}".format(c['x'])
    c.add_word('xyz')
    print 'Length: {}'.format(len(c))
    print c
    print "c['x'] = {}".format(c['x'])

