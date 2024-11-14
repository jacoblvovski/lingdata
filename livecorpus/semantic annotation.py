import pandas as pd
from nltk.tokenize import word_tokenize
import pymorphy2
import zipfile
import wget
import gensim
from ufal.udpipe import Model, Pipeline
import sys
import os



morph = pymorphy2.MorphAnalyzer()
modelfile = 'udpipe_syntagrus.model'
model_url = 'http://vectors.nlpl.eu/repository/20/180.zip'

model_file = model_url.split('/')[-1]
with zipfile.ZipFile(model_file, 'r') as archive:
    stream = archive.open('model.bin')
    model = gensim.models.KeyedVectors.load_word2vec_format(stream, binary=True)

def lemmatize(text):
    list_of_words = word_tokenize(text)
    list_of_lemmas = []
    for i in range(len(list_of_words)):
        lemma = morph.parse(list_of_words[i])[0].normal_form
        list_of_lemmas.append(lemma)
    return list_of_lemmas
def process(pipeline, text, keep_pos=True, keep_punct=False):
    entities = {'PROPN'}
    named = False  # переменная для запоминания того, что нам встретилось имя собственное
    memory = []
    mem_case = None
    mem_number = None
    tagged_propn = []
    # обрабатываем текст, получаем результат в формате conllu:
    processed = pipeline.process(text)
    # пропускаем строки со служебной информацией:
    content = [l for l in processed.split('\n') if not l.startswith('#')]
    # извлекаем из обработанного текста леммы, тэги и морфологические характеристики
    tagged = [w.split('\t') for w in content if w]
    for t in tagged:
        if len(t) != 10:  # если список короткий — строчка не содержит разбора, пропускаем
            continue
        (word_id, token, lemma, pos, xpos, feats, head, deprel, deps, misc) = t
        if not lemma or not token:  # если слово пустое — пропускаем
            continue
        if pos in entities:  # здесь отдельно обрабатываем имена собственные — они требуют особого обращения
            if '|' not in feats:
                tagged_propn.append('%s_%s' % (lemma, pos))
                continue
            morph = {el.split('=')[0]: el.split('=')[1] for el in feats.split('|')}
            if 'Case' not in morph or 'Number' not in morph:
                tagged_propn.append('%s_%s' % (lemma, pos))
                continue
            if not named:
                named = True
                mem_case = morph['Case']
                mem_number = morph['Number']
            if morph['Case'] == mem_case and morph['Number'] == mem_number:
                memory.append(lemma)
                if 'SpacesAfter=\\n' in misc or 'SpacesAfter=\s\\n' in misc:
                    named = False
                    past_lemma = '::'.join(memory)
                    memory = []
                    tagged_propn.append(past_lemma + '_PROPN ')
            else:
                named = False
                past_lemma = '::'.join(memory)
                memory = []
                tagged_propn.append(past_lemma + '_PROPN ')
                tagged_propn.append('%s_%s' % (lemma, pos))
        else:
            if not named:
                if pos == 'NUM' and token.isdigit():  # Заменяем числа на xxxxx той же длины
                    lemma = num_replace(token)
                tagged_propn.append('%s_%s' % (lemma, pos))
            else:
                named = False
                past_lemma = '::'.join(memory)
                memory = []
                tagged_propn.append(past_lemma + '_PROPN ')
                tagged_propn.append('%s_%s' % (lemma, pos))

    if not keep_punct:  # обрабатываем случай, когда пользователь попросил не сохранять пунктуацию (по умолчанию она сохраняется)
        tagged_propn = [word for word in tagged_propn if word.split('_')[1] != 'PUNCT']
    if not keep_pos:
        tagged_propn = [word.split('_')[0] for word in tagged_propn]
    return tagged_propn


def tag_ud(text, modelfile='udpipe_syntagrus.model'):
    udpipe_model_url = 'https://rusvectores.org/static/models/udpipe_syntagrus.model'
    udpipe_filename = udpipe_model_url.split('/')[-1]
    if not os.path.isfile(modelfile):
        print('UDPipe model not found. Downloading...', file=sys.stderr)
        wget.download(udpipe_model_url)
    print('\nLoading the model...', file=sys.stderr)
    model = Model.load(modelfile)
    process_pipeline = Pipeline(model, 'tokenize', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
    print('Processing input...', file=sys.stderr)
    lines = text.split('\n')
    tagged = []
    for line in lines:
        # line = unify_sym(line.strip()) # здесь могла бы быть ваша функция очистки текста
        output = process(process_pipeline, text=line)
        tagged_line = ' '.join(output)
        tagged.append(tagged_line)
    return '\n'.join(tagged)

# print(model.most_similar(positive=['яблоко_NOUN']))

def get_synonym_list(text):
    text_lemm = lemmatize(text)
    text_tagged = [tag_ud(word) for word in text_lemm]
    synonym_list = []
    for word in text_tagged:
        try:
            similar = model.most_similar(positive=[word], topn=3)
            similar = [item[0] for item in similar]
            synonym_list.extend(similar)
        except:
            pass
    return ' '.join(synonym_list)

def create_synonym_annotation(row):
    text = row['text']
    annotation = get_synonym_list(text)
    return annotation

df = pd.read_csv('exported_text_for_semantic_annotation.csv', encoding='utf-8')

df['semantic_annotation'] = df.apply(create_synonym_annotation, axis=1)
df.to_csv('sem_annotated_elan_data.tsv', sep='\t')
print(df.head())
