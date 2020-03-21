import re
import codecs
import os
from html.parser import HTMLParser
import copy
from pymongo import MongoClient

from text_cleaner import clean_html_tags


db = MongoClient('192.168.1.66')['maya_corpus']

h = HTMLParser()

max_pid = '53438.txt'

PROJ_BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
corpus_dir_1juzi = os.path.join(PROJ_BASE_DIR, 'data', '1juzi')
corpus_dir_colls = os.path.join(PROJ_BASE_DIR, 'data', 'manually')

seq_ptn = re.compile(r'^\d+\u3001')


def _flag_dirty_words(text):
    keywords = [
        u'带脏话',
        u'带脏字',
    ]

    for k in keywords:
        nonk = u'不%s' % k
        if nonk in text:
            return 0, text.replace(nonk, '')

    for k in keywords:
        if k in text:
            return 1, text.replace(k, '')
    return 2, text


def remove_stop_words(text):
    stop_words = [
        u'话语',
        u'骂人话',
        u'骂人',
        u'说说',
        u'语录',
        u'经典',
        u'大全',
        u'语句',
        u'的话',
        u'句子',
        u'宝典',
        u'的',
    ]

    for k in stop_words:
        text = text.replace(k, '')
    return text


def remove_seq(text):
    return seq_ptn.sub('', text)


def remove_ads(text):
    return text.replace(u'句子大全http://Www.1juzI.coM/', '')


def read_tags(title):
    new_text = remove_stop_words(title)
    has_dirty_words, new_text = _flag_dirty_words(new_text)
    return new_text, {
        'has_dirty_words': has_dirty_words,
        'extra_tags': [],
    }


def read_1juzi():
    for f in os.listdir(corpus_dir_1juzi):
        if f > max_pid:
            continue
        full_path = os.path.join(corpus_dir_1juzi, f)
        with codecs.open(full_path, 'r', encoding='utf8') as f:
            title = clean_html_tags(f.readline()).strip()
            newText, tags = read_tags(title)
            if newText:
                tags['extra_tags'].append(newText)

            for record in f.readlines():
                text = clean_html_tags(record).strip()
                if not text:
                    continue
                text = remove_ads(remove_seq(text))

                data = copy.deepcopy(tags)
                data['text'] = text
                data['source'] = '1juzi'
                db.texts_original.insert_one(data)


def read_manually_data():
    for f in os.listdir(corpus_dir_colls):
        full_path = os.path.join(corpus_dir_colls, f)
        with codecs.open(full_path, 'r', encoding='utf8') as f:
            for record in f.readlines():
                text = clean_html_tags(record).strip()
                if not text:
                    continue
                text = remove_seq(text)
                db.texts_original.insert_one({
                    'text': text,
                    'has_dirty_words': 2,
                    'extra_tags': [],
                    'source': 'manually'
                })


if __name__ == '__main__':
    print('dropping existing data')
    db.texts_original.drop()

    print('importing 1juzi')
    read_1juzi()

    print('importing manually_data')
    read_manually_data()

    record_cnt = db.texts_original.estimated_document_count()
    print('%s records imported' % record_cnt)
