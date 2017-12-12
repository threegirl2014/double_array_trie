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
        self._char_dict[split] = start
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

    def iteritems(self):
        return self._char_dict.iteritems()

    def iterkeys(self):
        return self._char_dict.iterkeys()

    def __str__(self):
        return str(self._char_dict)


class DoubleArrayTrie(object):

    def __init__(self, word_objs=None, split='#'):
        words = [item['string'] for item in word_objs]
        self.chars = CharDict(words, split)
        self.base = defaultdict(int)
        self.check = defaultdict(int)
        self.tails = defaultdict(dict)
        self.next_pos = 1  # tails中下一个可插入的位置
        self.root = 1   # root节点
        self.base[self.root] = 1
        if word_objs is None:
            return
        for word_obj in word_objs:
            self.insert(word_obj)

    def __str__(self):
        return 'chars: {}\nbase: {}\ncheck: {}\ntails: {}'.format(str(self.chars), str(self.base), str(self.check), str(self.tails))

    @property
    def split(self):
        return self.chars.split

    def check_word(self, word):
        return False if self.split in word else True

    def compare_tails(self, start, word, i):
        pos = -self.base[start]
        tail1 = self.tails[pos].copy()
        tail2 = word[i+1:] + self.split  # 通过split字符来规避一个字符串是另一个字符串的子串的情况
        compare_result = True if tail1['string'] == tail2 else False
        return compare_result, pos, tail1, tail2

    def search(self, word, only_exist=False):
        if not self.check_word(word):
            return 'word ilegal', None
        start = self.root
        for i, c in enumerate(word):
            arc = self.chars[c]
            if not arc and not i:
                return 'not exists', None
            end = self.base[start] + arc
            if self.check[end] == 0:
                return 'not exists', None
            elif self.check[end] != start:
                #if only_exist:
                return 'not exists', None
                #else:
                    #return 'exists part prefix', self.get_node_strs(word[:i+1], start)
            else:
                start = end
                if self.base[start] < 0:
                    compare_result, pos, tail1, _ = self.compare_tails(start, word, i)
                    if compare_result:
                        tail1.update({'string': word})
                        return 'exists', [tail1,]
                    if only_exist:
                        return 'not exists', None
                    else:
                        tail1.update({'string': word[:i+1] + tail1['string'][:-1]})
                        return 'exists part prefix', [tail1,]
        end = self.base[start] + self.chars[self.split]
        if self.check[end] != start:
            if only_exist:
                return 'not exists', None
            else:
                return 'exists prefix', self.get_node_strs(word, start)
        else:
            result = self.tails[-self.base[end]].copy()
            result.update({'string': word})
            return 'exists', [result,]

    def get_node_strs(self, prefix, start):
        '''获取所有经过start节点的字符串，prefix是start节点之前的边组成的前缀字符串'''
        result = []
        for tail in self.get_node_tails(start):
            tail.update({'string': prefix+tail['string'][:-1]})
            result.append(tail)
        return result

    def get_node_tails(self, start):
        '''获取所有以start节点为开始的后缀字符串'''
        if self.base[start] < 0:
            return [self.tails[-self.base[start]].copy(),]
        else:
            arcs, c_list = self.find_arcs(start)
            result = []
            for arc,c in zip(arcs, c_list):
                end = self.base[start] + arc
                tails = self.get_node_tails(end)
                for tail in tails:
                    tail.update({'string': c+tail['string']})
                    result.append(tail)
            return result

    def delete(self, word):
        if not self.check_word(word):
            return False
        start = self.root
        for i, c in enumerate(word):
            arc = self.chars[c]
            end = self.base[start] + arc
            if self.check[end] == 0 or self.check[end] != start:
                return False
            else:
                start = end
                if self.base[start] < 0:
                    compare_result, pos, _, _ = self.compare_tails(start, word, i)
                    if compare_result:
                        self.tails.pop(pos)
                        self.base[start] = self.check[start] = 0
                        return True
                    return False
        end = self.base[start] + self.chars[self.split]
        if self.check[end] == start:
            self.tails.pop(-self.base[end])
            self.base[end] = self.check[end] = 0
            return True
        else:
            return False


    def insert(self, word_obj):
        word_obj = word_obj.copy()
        word = word_obj.get('string', self.split)
        if not self.check_word(word):
            return False
        self.chars.add_word(word)
        start = self.root
        for i, c in enumerate(word):
            arc = self.chars[c]
            end = self.base[start] + arc
            if self.check[end] == 0:
                # base[end]将会变成独立节点，后续字符串将会保存到tails中
                word_obj.update({'string': word[i+1:]+self.split})
                self.write_tail(start, end, word_obj)
                return True
            elif self.check[end] == start:
                # 从start到end的有向边已存在
                start = end
                if self.base[start] < 0:
                    # start是独立节点，需要比较word的后续字符串和tails中的字符串
                    compare_result, pos, tail1, tail2 = self.compare_tails(start, word, i)
                    if compare_result:
                        # 该word已存在
                        return True

                    lcp = self.longest_common_prefix(tail1['string'], tail2)  # 找到最长公共子串
                    if lcp is not '':
                        q = self.x_check(lcp)
                        for new_c in lcp:  # 存储公共前缀字符串
                            self.base[start] = q
                            # 下一个节点
                            start = self.add_arc(new_c, start)

                    len_lcp = len(lcp)
                    # x != y 一定成立
                    x, y = tail1['string'][len_lcp:], tail2[len_lcp:]
                    q = self.x_check(x[0]+y[0])

                    self.base[start] = q
                    # 将x保存到tails中
                    end = self.add_arc(x[0], start)
                    self.base[end] = -pos
                    tail1.update({'string': x[1:]})
                    self.tails[pos] = tail1
                    # 将y保存到tails中
                    end = self.add_arc(y[0], start)
                    word_obj.update({'string': y[1:]})
                    self.write_tail(start, end, word_obj)  # 因为返回的tail2中已包含split字符所以此处不需要再加
                    return True
            else:
                # 从start到end的有向边不存在，此时发生冲突
                old_start = self.check[end]
                conflict = {
                    start: self.find_arcs(start),
                    old_start: self.find_arcs(old_start),
                }
                # 更改冲突较小的节点
                if (start == end) or (len(conflict[start][0]) + 1 <= len(conflict[old_start][0])):
                    change_node = start
                    conflict[start][1].append(c)
                else:
                    change_node = old_start
                temp_base = self.base[change_node]
                q = self.x_check(conflict[change_node][1])
                self.base[change_node] = q
                for temp_arc in conflict[change_node][0]:
                    # 转移冲突的节点
                    old_end = temp_base + temp_arc
                    new_end = self.base[change_node] + temp_arc
                    self.base[new_end] = self.base[old_end]
                    self.check[new_end] = self.check[old_end]
                    if self.base[old_end] > 0:
                        # 当old_end是其他节点的父节点时，需要将它对应的子节点对应的父节点更改为new_end
                        for key, value in self.check.iteritems():  # 是否需要如同find_arcs方法中，使用遍历chars的方法？
                            if value == old_end:
                                self.check[key] = new_end
                    self.base[old_end] = self.check[old_end] = 0

                word_obj.update({'string': word[i+1:]+self.split})
                end = self.base[start] + arc
                assert self.base[end] == 0 and self.check[end] == 0
                #if self.base[end] or self.check[end]:
                #    print 'error'
                self.write_tail(start, end, word_obj)
                return True

    def longest_common_prefix(self, *words):
        '''返回多个字符串的最长公共子串'''
        lcp = ''
        for item in zip(*words):
            if len(set(item)) == 1:
                lcp += item[0]
            else:
                break
        return lcp

    def x_check(self, word):
        '''
        在base数组中发生冲突时，找到最近一个基准位置，确保有足够的空位保存冲突节点.
        即，要找到一个赋值给base[start]的值，能够保证所有对应的冲突节点对应的check[end]都为0.
        '''
        q = 1
        while 1:
            if all(self.check[q + self.chars[c]] == 0 for c in word):
                break
            q += 1
        return q

    def write_tail(self, start, end, word_obj):
        self.base[end] = -self.next_pos
        self.check[end] = start
        self.tails[self.next_pos] = word_obj
        self.next_pos += len(self.tails[self.next_pos]['string'])

    def add_arc(self, c, start):
        '''加一条从start节点开始，边对应的字符是c的有向边'''
        arc = self.chars[c]
        end = self.base[start] + arc
        self.check[end] = start
        return end

    def find_arcs(self, start):
        '''找到start节点对应的所有边和所有end节点'''
        arcs, c_list = [], []
#        reverse_chars = {v:k for k,v in self.chars.iteritems()}
#        for key, value in self.check.iteritems():
#            if value == start:
#                arc = key - self.base[start]
#                arcs.append(arc)
#        return arcs
        for c, arc in self.chars.iteritems():
            if self.check[self.base[start] + arc] == start:
                arcs.append(arc)
                c_list.append(c)
        return arcs, c_list

    def search_exists(self, word):
        return self.search(word, only_exist=True)


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

    words = [{'string':'baby'}, {'string':'bachelor'}, {'string': 'badage'}, {'string':'jar'}]
    trie = DoubleArrayTrie(word_objs=words)
    print trie
    print words
    for word in words:
        print trie.search(word['string'])
    words = [{'string':'ba'}, {'string':'bac'}, {'string':'be'}, {'string':'bae'}]
    trie = DoubleArrayTrie(word_objs=words)
    print trie
    print words
    for word in words:
        print trie.search(word['string'])
    print trie.search('b')
    print trie.search('a')

